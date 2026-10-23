#!/usr/bin/env python3
"""Run isolated, real Codex conversations; execution completion is not a semantic pass.

Examples:
  python3 tests/run_behavior.py --smoke --output /tmp/compass-smoke
  python3 tests/run_behavior.py --group new --jobs 2 --output /tmp/compass-evaluation
  python3 tests/run_behavior.py --group baseline --output /tmp/compass-evaluation
  python3 tests/run_behavior.py --case N06 --condition both --resume

Only the explicit Skill text is varied. Both conditions disable external tools.
Each turn receives the complete actual conversation so far in a fresh process.
Each case gets a temporary workspace and CODEX_HOME; no parent conversation,
expected observations, verdicts, account configuration dump, or personal Skills
are sent to the model. Manual review of the saved answers is required.
Optional COMPASS_EXCLUDE_TOKENS is a JSON array used to sanitize every saved
string. Keep the exclusion values outside this repository.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parent.parent
BASELINE_IDS = {"V01", "V03", "V05", "V06"}
DISABLED_FEATURES = (
    "apps", "plugins", "hooks", "multi_agent", "multi_agent_v2", "memories",
    "shell_tool", "unified_exec", "browser_use", "browser_use_external",
    "computer_use", "in_app_browser", "in_app_local_automation", "image_generation",
    "goals", "sleep_tool", "view_image", "workspace_dependencies",
)
HARNESS = """你正在独立回答一名学生。请用中文直接回应学生的当前消息。
这是一个无外部工具的离线对话：不能联网、读写外部文件、发送消息、创建提醒或永久记忆。
不要假装已经执行任何这些操作。当前用户日期为2026年10月23日，时区Asia/Shanghai。
下面的历史是本次独立对话此前真实产生的内容；继续当前对话即可，不要评论测试本身。
"""


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def exclusions():
    data = json.loads(os.environ.get("COMPASS_EXCLUDE_TOKENS", "[]"))
    if not isinstance(data, list) or any(not isinstance(s, str) or not s for s in data):
        raise ValueError("COMPASS_EXCLUDE_TOKENS must be an array of nonempty strings")
    return sorted(set(data), key=len, reverse=True)


def scrub(value, tokens):
    if isinstance(value, str):
        value = value.replace(str(ROOT), "[PROJECT_ROOT]").replace(str(Path.home()), "[USER_HOME]")
        for token in tokens:
            value = re.sub(re.escape(token), "[来源标识已省略]", value, flags=re.I)
        return value
    if isinstance(value, list):
        return [scrub(x, tokens) for x in value]
    if isinstance(value, dict):
        return {scrub(k, tokens): scrub(v, tokens) for k, v in value.items()}
    return value


def save_json(path, obj, tokens):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(scrub(obj, tokens), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def config_subset(source):
    """Preserve model/provider choices only, without printing credentials.

    Scalar lines and model-provider tables are copied verbatim to the temporary
    private config. Personal instructions, plugins, MCP, environment overrides,
    project history and hooks are deliberately excluded.
    """
    path = source / "config.toml"
    raw = path.read_text(encoding="utf-8") if path.exists() else ""
    allowed = {
        "model", "model_provider", "model_reasoning_effort", "model_reasoning_summary",
        "model_verbosity", "model_context_window", "model_auto_compact_token_limit",
        "service_tier", "cli_auth_credentials_store", "chatgpt_base_url",
    }
    current = ""
    lines = []
    model = None
    for line in raw.splitlines():
        m = re.match(r"^\s*\[([^\]]+)\]", line)
        if m:
            current = m.group(1)
            if current.startswith("model_providers."):
                lines.append(line)
            continue
        m = re.match(r"^\s*([a-zA-Z_][a-zA-Z_0-9]*)\s*=", line)
        if current.startswith("model_providers.") or (not current and m and m.group(1) in allowed):
            lines.append(line)
        if not current and m and m.group(1) == "model":
            value = line.split("=", 1)[1].strip()
            model = value.strip('"\'')
    # Add control settings as CLI overrides, so copied tables cannot absorb them.
    return "\n".join(lines) + "\n", model


def read_skill(path):
    files = [path / "SKILL.md"] + sorted((path / "references").glob("*.md"))
    if not files[0].is_file():
        raise FileNotFoundError("Skill entrypoint missing: " + str(files[0]))
    chunks, manifest = [], []
    for file in files:
        content = file.read_text(encoding="utf-8")
        rel = file.relative_to(path).as_posix()
        manifest.append({"path": rel, "sha256": sha(content), "bytes": len(content.encode())})
        chunks.append("<skill_file path=" + json.dumps(rel) + ">\n" + content + "\n</skill_file>")
    return "\n\n".join(chunks), manifest


def cases_all(files=None):
    result = []
    defaults = [ROOT / "tests" / name for name in ("cases-a.json", "cases-b.json")]
    defaults += sorted((ROOT / "tests").glob("cases-v*.json"))
    for file in files if files is not None else defaults:
        for item in load_json(file):
            if "user_turns" not in item:
                item = dict(item, title=item["id"], user_turns=[item["user"]] + ([item["followup"]] if item.get("followup") else []))
            result.append(item)
    return result


def compose_prompt(condition, skill_text, history, current):
    parts = [HARNESS]
    if condition == "skill":
        parts.append("请依照下面显式提供的零一大学指南针 Skill 指导当前对话。文件都已展开，无需再读取。\n" + skill_text)
    # The baseline gets the same user messages, history encoding and tool limits.
    parts.append("<conversation_history>\n" + json.dumps(history, ensure_ascii=False) + "\n</conversation_history>")
    parts.append("<current_student_message>\n" + current + "\n</current_student_message>")
    return "\n\n".join(parts)


def decode_events(stdout):
    events = []
    for line in stdout.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            if line.strip():
                events.append({"type": "unparsed_output", "text": line})
    return events


def evidence(events):
    calls = []
    for event in events:
        item = event.get("item", {}) if isinstance(event, dict) else {}
        if isinstance(item, dict) and item.get("type") in {
            "command_execution", "mcp_tool_call", "web_search", "file_change",
            "tool_call", "function_call", "collab_tool_call", "image_generation",
        }:
            calls.append(event)
    return calls


def answer_from(events):
    return "\n".join(event["item"].get("text", "") for event in events
                     if isinstance(event, dict) and event.get("type") == "item.completed"
                     and isinstance(event.get("item"), dict)
                     and event["item"].get("type") == "agent_message")


def command(cwd, answer_path):
    cmd = ["codex", "--no-daemon", "exec", "--skip-git-repo-check", "--ephemeral", "--ignore-rules",
           "--sandbox", "read-only", "--json", "--color", "never", "--cd", str(cwd),
           "--output-last-message", str(answer_path), "-c", 'approval_policy="never"',
           "-c", 'web_search="disabled"', "-c", "project_doc_max_bytes=0",
           "-c", "features.skip_host_skill_discovery=true"]
    for feature in DISABLED_FEATURES:
        cmd.extend(["--disable", feature])
    return cmd + ["-"]


def run_case(case, condition, args, config, model, skill_text, manifest, tokens):
    identity = case["id"] + "-" + condition
    case_dir = args.output / identity
    fingerprint = sha(json.dumps({"input": case["user_turns"], "condition": condition,
                                  "version": args.version, "skill_digest": args.skill_digest,
                                  "skill": manifest if condition == "skill" else [],
                                  "config_sha256": sha(config), "harness": HARNESS,
                                  "runner_sha256": sha(Path(__file__).read_bytes())}, sort_keys=True, ensure_ascii=False))
    prior = None
    if args.resume and case_dir.exists():
        candidates = []
        for path in case_dir.glob("attempt-*.json"):
            value = load_json(path)
            if value.get("fingerprint") == fingerprint:
                created = value.get("attempt_created_ns", path.stat().st_mtime_ns)
                candidates.append((created, value))
        if candidates:
            prior = max(candidates, key=lambda candidate: candidate[0])[1]
        if prior and prior.get("status") == "completed":
            return {"case": case["id"], "condition": condition, "status": "skipped_completed", "artifact": prior["artifact"]}
        if prior and any(t.get("history_replay_safe") is not True for t in prior.get("turns", [])
                         if t.get("status") == "completed"):
            # A redacted public answer cannot reproduce the original private history.
            # Preserve that attempt and start a new conversation instead of inventing a replay.
            prior = None
    attempt = "attempt-" + time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8] + ".json"
    artifact = case_dir / attempt
    artifact_label = str(artifact.relative_to(ROOT)) if artifact.is_relative_to(ROOT) else str(artifact)
    result = {"schema_version": 1, "version": args.version, "skill_digest": args.skill_digest,
              "attempt_created_ns": time.time_ns(),
              "case": case["id"], "title": case.get("title", case["id"]),
              "condition": condition, "fingerprint": fingerprint, "configured_model": model,
              "evaluation_status": "requires_manual_review", "status": "running", "artifact": artifact_label,
              "skill_manifest": manifest if condition == "skill" else [],
              "context_method": "fresh_process_per_turn_with_complete_actual_history",
              "tool_policy": "offline_no_external_tools_same_in_both_conditions",
              "turns": [], "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "previous_attempt": prior.get("artifact") if prior else None}
    history = []
    if prior:
        for turn in prior.get("turns", []):
            if turn.get("status") != "completed":
                break
            result["turns"].append(turn)
            history.extend([{"role": "user", "content": turn["user"]}, {"role": "assistant", "content": turn["answer"]}])
    save_json(artifact, result, tokens)
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="compass-behavior-", dir="/tmp") as tmp:
        temp = Path(tmp)
        isolated_home, workspace = temp / "codex", temp / "workspace"
        isolated_home.mkdir(mode=0o700)
        workspace.mkdir()
        config_path = isolated_home / "config.toml"
        config_path.write_text(config, encoding="utf-8")
        config_path.chmod(0o600)
        auth = args.config_home / "auth.json"
        if auth.is_file():
            shutil.copy2(auth, isolated_home / "auth.json")
            (isolated_home / "auth.json").chmod(0o600)
        env = {k: v for k, v in os.environ.items() if not k.startswith("CODEX_") and k != "COMPASS_EXCLUDE_TOKENS"}
        env["CODEX_HOME"] = str(isolated_home)
        # No skills, hooks, sessions, parent rules or app-server state are copied.
        for index in range(len(result["turns"]), len(case["user_turns"])):
            user = case["user_turns"][index]
            prompt = compose_prompt(condition, skill_text, history, user)
            answer_path = temp / ("answer-" + str(index + 1) + ".txt")
            cmd = command(workspace, answer_path)
            turn_start = time.monotonic()
            turn = {"number": index + 1, "user": user, "prompt_sha256": sha(prompt),
                    "history_messages": len(history), "status": "running"}
            try:
                completed = subprocess.run(cmd, input=prompt, text=True, capture_output=True,
                                           cwd=workspace, env=env, timeout=args.timeout)
                stdout, stderr, returncode = completed.stdout, completed.stderr, completed.returncode
                status = "completed" if returncode == 0 else "process_failed"
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout or ""
                stderr = exc.stderr or ""
                stdout = stdout.decode(errors="replace") if isinstance(stdout, bytes) else stdout
                stderr = stderr.decode(errors="replace") if isinstance(stderr, bytes) else stderr
                returncode, status = None, "timeout"
            except OSError as exc:
                stdout, stderr, returncode, status = "", str(exc), None, "launch_failed"
            events = decode_events(stdout)
            answer = answer_path.read_text(encoding="utf-8") if answer_path.exists() else answer_from(events)
            calls = evidence(events)
            if status == "completed" and not answer.strip():
                status = "empty_answer"
            if calls:
                status = "unexpected_tool_call"
            turn.update(status=status, answer=answer, returncode=returncode,
                        history_replay_safe=(scrub(answer, tokens) == answer and scrub(user, tokens) == user),
                        elapsed_seconds=round(time.monotonic() - turn_start, 2),
                        events=events, stderr=stderr, tool_call_evidence=calls,
                        tool_call_count=len(calls))
            result["turns"].append(turn)
            save_json(artifact, result, tokens)
            print(json.dumps({"case": case["id"], "condition": condition, "turn": index + 1,
                              "status": status, "seconds": turn["elapsed_seconds"]}), flush=True)
            if status != "completed":
                result["status"] = status
                break
            history.extend([{"role": "user", "content": user}, {"role": "assistant", "content": answer}])
        else:
            result["status"] = "completed"
    result["elapsed_seconds"] = round(time.monotonic() - start, 2)
    result["finished_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    save_json(artifact, result, tokens)
    return {"case": case["id"], "condition": condition, "status": result["status"], "artifact": artifact_label}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--group", choices=["new", "legacy", "baseline", "all"], default="new")
    parser.add_argument("--case", action="append", help="Case ID; can repeat")
    parser.add_argument("--condition", choices=["skill", "baseline", "both"], default="skill")
    parser.add_argument("--output", type=Path, help="New run directory; defaults to a unique directory for the current version")
    parser.add_argument("--case-file", action="append", type=Path, help="Explicit case JSON file; repeat to combine historical sets")
    parser.add_argument("--baseline-id", action="append", help="Override comparison case IDs; repeat as needed")
    parser.add_argument("--skill", type=Path, default=ROOT / "01-university-compass")
    parser.add_argument("--config-home", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))))
    parser.add_argument("--timeout", type=float, default=240, help="Seconds per actual model turn")
    parser.add_argument("--jobs", type=int, default=2, help="Concurrent independent cases")
    parser.add_argument("--resume", action="store_true", help="Reuse completed turns only when input/config/content fingerprint matches")
    parser.add_argument("--smoke", action="store_true", help="One minimal real baseline call; no behavior verdict")
    parser.add_argument("--list", action="store_true", help="List selected IDs and turn counts without calling a model")
    args = parser.parse_args()
    if args.timeout <= 0 or args.jobs < 1:
        parser.error("timeout and jobs must be positive")
    entry = (args.skill / "SKILL.md").read_text(encoding="utf-8")
    version_match = re.search(r'^  version: "([0-9]+\.[0-9]+\.[0-9]+)"$', entry, re.M)
    if not version_match:
        parser.error("Skill metadata.version is missing or invalid")
    args.version = version_match[1]
    package_manifest = [{"path": str(p.relative_to(args.skill)), "bytes": p.stat().st_size,
                         "sha256": sha(p.read_bytes())} for p in sorted(args.skill.rglob("*")) if p.is_file()]
    args.skill_digest = sha(json.dumps(package_manifest, sort_keys=True).encode())
    if args.output is None:
        args.output = ROOT / "tests" / ("v" + args.version.replace(".", "")) / "behavior" / ("run-" + time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    args.output = args.output.resolve()
    tokens = exclusions()
    config, model = config_subset(args.config_home)
    skill_text, manifest = read_skill(args.skill)
    selected = cases_all(args.case_file)
    current_file = ROOT / "tests" / ("cases-v" + args.version.replace(".", "") + ".json")
    current_ids = {case["id"] for case in cases_all([current_file])} if current_file.is_file() else set()
    baseline_ids = set(args.baseline_id or BASELINE_IDS)
    ids = [case["id"] for case in selected]
    if len(ids) != len(set(ids)):
        parser.error("Case IDs must be unique")
    if args.case:
        unknown = set(args.case) - {case["id"] for case in selected}
        if unknown:
            parser.error("Unknown cases: " + ", ".join(sorted(unknown)))
        selected = [case for case in selected if case["id"] in args.case]
    elif args.group == "new":
        selected = [case for case in selected if case["id"] in current_ids]
    elif args.group == "legacy":
        selected = [case for case in selected if case["id"] not in current_ids]
    elif args.group == "baseline":
        selected = [case for case in selected if case["id"] in baseline_ids]
    conditions = ["skill", "baseline"] if args.condition == "both" else [args.condition]
    if args.group == "baseline" and not args.case:
        conditions = ["baseline"]
    if args.smoke:
        selected = [{"id": "SMOKE", "title": "CLI smoke", "user_turns": ["只回复：运行器烟雾测试成功"]}]
        conditions = ["baseline"]
    if not selected:
        parser.error("No cases selected; verify --case-file, --group and --baseline-id")
    tasks = [(case, condition) for case in selected for condition in conditions]
    if args.list:
        print(json.dumps({"configured_model": model, "cases": [{"id": c["id"], "turns": len(c["user_turns"]), "condition": k} for c, k in tasks]}, ensure_ascii=False, indent=2))
        return 0
    if not shutil.which("codex"):
        parser.error("codex executable not found; no evaluations were run")
    args.output.mkdir(parents=True, exist_ok=True)
    summary_path = args.output / ("run-" + time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8] + ".json")
    summary = {"version": args.version, "skill_digest": args.skill_digest,
               "configured_model": model, "group": args.group, "smoke": args.smoke,
               "baseline_ids": sorted(baseline_ids), "semantic_verdict": "not_automatically_scored",
               "limitations": ["Synthetic student conversations, not real student outcomes", "Full Skill Markdown explicitly loaded; does not test lazy loading or installation discovery", "All external tools disabled equally; live verification and real side effects are not tested", "Full actual history replayed per turn; not server-side resume"],
               "results": []}
    save_json(summary_path, summary, tokens)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(run_case, case, condition, args, config, model, skill_text, manifest, tokens): (case["id"], condition) for case, condition in tasks}
        for future in concurrent.futures.as_completed(futures):
            case_id, condition = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"case": case_id, "condition": condition, "status": "harness_failed", "error": str(exc)}
            summary["results"].append(result)
            save_json(summary_path, summary, tokens)
    print(json.dumps(scrub({"summary": str(summary_path), "completed": sum(r["status"] in {"completed", "skipped_completed"} for r in summary["results"]), "total": len(tasks)}, tokens), ensure_ascii=False))
    return 0 if all(r["status"] in {"completed", "skipped_completed"} for r in summary["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())

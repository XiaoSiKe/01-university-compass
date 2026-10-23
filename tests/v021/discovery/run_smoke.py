#!/usr/bin/env python3
"""Fresh CLI installation/trigger smoke. Run only after content is frozen.
Uses the user's configured model/provider; no --model override.
Only the copied Skill enters each temporary workspace, never test expectations.
"""
import argparse
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("compass_behavior_helpers", ROOT / "tests/run_behavior.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

PROMPTS = {
    "D01-explicit": "使用 $01-university-compass。我大一，新闻专业，刚开始接触 AI。今晚只有 20 分钟，没有教材在手，也不想付费。我想先做一件能检查自己学到什么的事，请直接带我开始。",
    "D02-natural": "我刚上大一，不会编程，想入门 AI，可网上的教程看得我更乱了。我只有手机，每周能花两小时。现在能先做什么？",
    "D03-unrelated-code": "用 Python 写一个函数 stable_unique(items)，保留列表中每种可哈希元素第一次出现的位置。只给代码。",
}
LOCAL_TOOL_LIMIT = "\n\n本轮只进行对话；需要时仅可只读查看当前目录内与问题相关的资料，不联网、不修改文件、不读取目录外文件、不创建提醒。"
DISABLED = tuple(x for x in helper.DISABLED_FEATURES if x not in ("shell_tool", "unified_exec")) + ("shell_snapshot", "skill_mcp_dependency_install")

def clean(value, tokens, private_paths):
    value = helper.scrub(value, tokens)
    if isinstance(value, str):
        for path, label in private_paths:
            value = value.replace(path, label)
        value = re.sub(r"/Users/[^/\s\"']+", "[USER_HOME]", value)
        value = re.sub(r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+", r"\1[REDACTED]", value)
        value = re.sub(r"\bsk-[A-Za-z0-9_-]{10,}\b", "[REDACTED]", value)
        value = re.sub(r'("(?:access_token|refresh_token|id_token|api_key)"\s*:\s*")[^"]+', r'\1[REDACTED]', value, flags=re.I)
        return value
    if isinstance(value, list):
        return [clean(x, tokens, private_paths) for x in value]
    if isinstance(value, dict):
        return {clean(k, tokens, private_paths): clean(v, tokens, private_paths) for k, v in value.items()}
    return value

def run_one(case_id, user, args, config, model, tokens):
    out = args.output / case_id
    out.mkdir(parents=True, exist_ok=True)
    prompt = user + LOCAL_TOOL_LIMIT
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="compass-discovery-", dir="/tmp") as tmp:
        temp = Path(tmp)
        private_paths = [(str(temp.resolve()), "[TEST_ROOT]"), (str(temp), "[TEST_ROOT]"),
                         (str(ROOT), "[PROJECT_ROOT]"), (str(args.config_home), "[USER_CODEX]"),
                         (str(Path.home()), "[USER_HOME]")]
        private_paths.sort(key=lambda x: len(x[0]), reverse=True)
        workspace, runtime = temp / "workspace", temp / "runtime"
        workspace.mkdir()
        runtime.mkdir(mode=0o700)
        (runtime / "config.toml").write_text(config)
        (runtime / "config.toml").chmod(0o600)
        auth = args.config_home / "auth.json"
        if auth.is_file():
            shutil.copy2(auth, runtime / "auth.json")
            (runtime / "auth.json").chmod(0o600)
        installed = workspace / ".agents/skills/01-university-compass"
        installed.parent.mkdir(parents=True)
        shutil.copytree(ROOT / "01-university-compass", installed)
        manifest = [{"path": str(p.relative_to(installed)), "sha256": helper.sha(p.read_bytes())}
                    for p in sorted(installed.rglob("*")) if p.is_file()]
        env = {k:v for k,v in os.environ.items() if not k.startswith("CODEX_") and k != "COMPASS_EXCLUDE_TOKENS"}
        env["CODEX_HOME"] = str(runtime)
        final_path = temp / "final.txt"
        cmd = ["codex", "--no-daemon", "exec", "--skip-git-repo-check", "--ephemeral", "--ignore-rules",
               "--sandbox", "read-only", "--json", "--color", "never", "--cd", str(workspace),
               "--output-last-message", str(final_path), "-c", 'approval_policy="never"',
               "-c", 'web_search="disabled"', "-c", "project_doc_max_bytes=0",
               "-c", "features.skip_host_skill_discovery=true"]
        for feature in DISABLED:
            cmd += ["--disable", feature]
        cmd += ["-"]
        try:
            proc = subprocess.run(cmd, input=prompt, text=True, capture_output=True,
                                  cwd=workspace, env=env, timeout=args.timeout)
            stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
            status = "completed" if code == 0 else "process_failed"
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, code, status = exc.stdout or "", exc.stderr or "", None, "timeout"
            if isinstance(stdout, bytes): stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes): stderr = stderr.decode(errors="replace")
        events = helper.decode_events(stdout)
        calls = helper.evidence(events)
        final = final_path.read_text() if final_path.is_file() else helper.answer_from(events)
        completed_commands = [e.get("item", {}) for e in calls
                              if e.get("type") == "item.completed"
                              and e.get("item", {}).get("type") == "command_execution"]
        read_evidence = [{"command": e.get("command"), "exit_code": e.get("exit_code"),
                          "output_chars": len(e.get("aggregated_output", ""))}
                         for e in completed_commands]
        # Literal references prove which paths appeared in executed commands;
        # wildcard/dynamic reads remain in the full command evidence for review.
        loaded_paths = sorted({m.group(0) for e in completed_commands if e.get("exit_code") == 0
                               for m in re.finditer(r"(?:\.agents/skills/01-university-compass/)?(?:references/[A-Za-z0-9_-]+\.md|SKILL\.md)",
                                                    e.get("command", ""))})
        result = {
            "case": case_id, "configured_model": model, "exit_code": code, "status": status,
            "elapsed_seconds": round(time.monotonic()-start, 2), "has_final": bool(final.strip()),
            "method": "fresh_cli_native_project_skill_discovery",
            "install_location": ".agents/skills/01-university-compass",
            "isolation": "only_current_skill_copy; temporary_model_config_and_auth; no_parent_chat_or_test_expectations",
            "tool_policy": "read_only_local_skill_documents; external_tools_disabled",
            "semantic_status": "requires_manual_review", "skill_manifest": manifest,
            "read_command_evidence": read_evidence, "paths_observed_in_successful_read_commands": loaded_paths,
            "tool_call_count": len(completed_commands),
        }
        sanitized = clean(result, tokens, private_paths)
        (out / "result.json").write_text(json.dumps(sanitized, ensure_ascii=False, indent=2)+"\n")
        (out / "prompt.txt").write_text(clean(prompt, tokens, private_paths)+"\n")
        (out / "actual-response.txt").write_text(clean(final, tokens, private_paths)+"\n")
        (out / "events.json").write_text(json.dumps(clean(events, tokens, private_paths),ensure_ascii=False,indent=2)+"\n")
        (out / "stderr.txt").write_text(clean(stderr, tokens, private_paths))
    return {"case":case_id, "status":status, "exit_code":code, "has_final":bool(final.strip()),
            "read_commands":len(completed_commands)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    p.add_argument("--config-home", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home()/".codex"))))
    p.add_argument("--timeout", type=int, default=240)
    p.add_argument("--jobs", type=int, default=2)
    p.add_argument("--case", choices=tuple(PROMPTS))
    args=p.parse_args()
    config,model=helper.config_subset(args.config_home)
    tokens=helper.exclusions()
    items=[(k,v) for k,v in PROMPTS.items() if args.case is None or k==args.case]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures=[pool.submit(run_one,k,v,args,config,model,tokens) for k,v in items]
        results=[f.result() for f in futures]
    print(json.dumps(results,ensure_ascii=False))
    return 0 if all(r["status"]=="completed" and r["has_final"] for r in results) else 1

if __name__=="__main__":
    raise SystemExit(main())


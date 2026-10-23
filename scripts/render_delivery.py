#!/usr/bin/env python3
"""Render the conversation transcript from explicitly adopted, matching evidence.

Use --evaluation tests/<version>/evaluation.json to select an acceptance index.
Invalid, missing or stale evidence exits nonzero before the transcript is replaced.
"""
import argparse
import html
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_common import digest, metadata, publish_files, snapshot

ROOT = Path(__file__).resolve().parents[1]


class EvidenceError(ValueError):
    pass


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise EvidenceError("Missing or invalid evidence: " + str(path)) from error


def selected_evidence(root, evaluation, info, skill_digest):
    review = load_json(evaluation)
    if review.get("version") != info["version"]:
        raise EvidenceError("Evaluation version does not match current Skill")
    if review.get("skill_digest") != skill_digest:
        raise EvidenceError("Evaluation raw Skill digest does not match current files")
    if not str(review.get("status", "")).upper().startswith("PASS"):
        raise EvidenceError("Evaluation is not an accepted PASS index")
    entries = review.get("cases")
    if not isinstance(entries, list) or not entries:
        raise EvidenceError("Evaluation must explicitly list adopted cases, including baselines")
    selected, historical, seen, paths = [], [], set(), set()
    for entry in entries:
        identity = (entry.get("case"), entry.get("condition"))
        if not all(isinstance(value, str) and value for value in identity) or identity in seen:
            raise EvidenceError("Missing or duplicate case/condition in evaluation")
        seen.add(identity)
        if str(entry.get("status", "")).lower() != "pass":
            raise EvidenceError("A PASS index contains an unaccepted case: " + str(identity))
        if not isinstance(entry.get("artifact"), str) or not entry["artifact"]:
            raise EvidenceError("Adopted artifact is missing: " + str(identity))
        path = (evaluation.parent / entry["artifact"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise EvidenceError("Adopted artifact escapes this project")
        if path in paths:
            raise EvidenceError("One artifact cannot represent multiple adopted cases")
        paths.add(path)
        if not path.is_file():
            raise EvidenceError("Adopted artifact does not exist: " + str(path))
        if entry.get("artifact_sha256") and digest(path.read_bytes()) != entry["artifact_sha256"]:
            raise EvidenceError("Adopted artifact checksum mismatch: " + str(path))
        item = load_json(path)
        if (item.get("case"), item.get("condition")) != identity:
            raise EvidenceError("Artifact identity differs from evaluation: " + str(path))
        if item.get("version") != info["version"]:
            raise EvidenceError("Artifact version mismatch: " + str(path))
        if item.get("skill_digest", item.get("package_skill_digest")) != skill_digest:
            raise EvidenceError("Artifact raw Skill digest mismatch: " + str(path))
        if item.get("status") != "completed":
            raise EvidenceError("Adopted artifact did not complete: " + str(path))
        turns = item.get("turns")
        if not isinstance(turns, list) or not turns:
            raise EvidenceError("Adopted artifact contains no actual turns: " + str(path))
        for turn in turns:
            if (turn.get("status", "completed") != "completed"
                    or not isinstance(turn.get("user"), str) or not turn["user"].strip()
                    or not isinstance(turn.get("answer"), str) or not turn["answer"].strip()):
                raise EvidenceError("Adopted artifact contains an incomplete turn: " + str(path))
        selected.append(item)
    # Unselected attempts remain available as history; their existence never
    # overrides the reviewer's explicit choices or inherits a PASS verdict.
    for directory in sorted({path.parent for path in paths}):
        for path in sorted(directory.glob("attempt-*.json")):
            if path.resolve() not in paths:
                historical.append(load_json(path))
    return review, selected, historical


CSS = '''body{max-width:1060px;margin:0 auto;padding:42px 24px 80px;font-family:system-ui,-apple-system,"PingFang SC",sans-serif;background:#fff;color:#111;line-height:1.8}h1{font-size:38px;line-height:1.3}h2{font-size:23px;margin-top:36px}.tag,.muted{color:#666;font-size:14px}details{border:1px solid #ddd;border-radius:14px;padding:20px;margin:14px 0}a{color:#111}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;line-height:1.75}summary{cursor:pointer;font-weight:600}footer{margin-top:40px;border-top:1px solid #ddd;padding-top:16px;font-size:14px}'''


def page(title, body):
    return ('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>'
            + html.escape(title) + '</title><style>' + CSS + '</style><body>' + body + '</body></html>')


def conversation(item, historical=False):
    label = "{} · {} · {} · {}".format(item.get("case", "未标记"), item.get("condition", ""),
                                      item.get("title", ""), item.get("status", ""))
    if historical:
        label = "未采用/历史尝试 · " + label
    body = '<details><summary>' + html.escape(label) + '</summary>'
    if historical:
        body += '<p>此记录未进入本版采用索引，不继承当前通过结论。</p>'
    for index, turn in enumerate(item.get("turns", []), 1):
        body += ('<p class="muted">学生 · 第{}轮</p><pre>{}</pre>'
                 '<p class="muted">助手</p><pre>{}</pre>').format(
                     turn.get("number", index), html.escape(turn.get("user", "")),
                     html.escape(turn.get("answer", "无完成输出")))
    return body + '</details>'


def render(root, evaluation):
    root = Path(root).resolve()
    evaluation = Path(evaluation).resolve()
    if not evaluation.is_relative_to(root):
        raise EvidenceError("Evaluation must be inside this project")
    info = metadata(root)
    _, _, skill_digest = snapshot(info["skill"])
    review, cases, historical = selected_evidence(root, evaluation, info, skill_digest)
    counts = {"skill_cases": sum(item["condition"] == "skill" for item in cases),
              "baseline_cases": sum(item["condition"] == "baseline" for item in cases),
              "actual_turns": sum(len(item["turns"]) for item in cases),
              "historical_turns": sum(len(item.get("turns", [])) for item in historical)}
    status = str(review["status"])
    version = info["version"]
    transcript = '<div class="tag">' + html.escape(version) + ' · 验收索引指定的实际模型回答</div><h1>看见对话如何推进</h1>'
    transcript += '<p>仅展示明确采用且版本、原始字节摘要和运行状态匹配的证据。模拟对话不证明真实学生效果。</p>'
    transcript += '<p>Skill 情境的语义结论见本版报告；基线记录的采用只确认对照证据完整，不代表教学语义通过。</p>'
    transcript += '<p><a href="' + html.escape(os.path.relpath(str(evaluation), str(root / "tests")), quote=True) + '">采用索引</a></p>'
    transcript += ''.join(conversation(item) for item in cases)
    if historical:
        transcript += '<h2>未采用与历史尝试</h2>' + ''.join(conversation(item, True) for item in historical)
    transcript += '<footer>历史版本的验证记录按原版本保留，不继承本版通过结论。</footer>'
    publish_files({root / 'tests/实际对话记录.html': page('实际对话记录 · ' + version, transcript).encode()})
    return dict(counts, version=version, evaluation=status, skill_digest=skill_digest,
                history_scope='unselected_attempts_in_directories_of_adopted_artifacts',
                transcript='tests/实际对话记录.html', adopted_artifacts=len(cases))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation', type=Path, help='adopted-evidence index; defaults to current version')
    args = parser.parse_args(argv)
    try:
        info = metadata(ROOT)
        evaluation = args.evaluation or ROOT / 'tests' / info['test_directory'] / 'evaluation.json'
        if not evaluation.is_absolute():
            evaluation = ROOT / evaluation
        result = render(ROOT, evaluation)
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({'status': 'FAIL', 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())

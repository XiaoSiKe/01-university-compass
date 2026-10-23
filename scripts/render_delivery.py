#!/usr/bin/env python3
"""Render current delivery pages only from explicitly adopted, matching evidence.

Use --evaluation tests/<version>/evaluation.json to select an acceptance index.
Invalid, missing or stale evidence exits nonzero before any page is replaced.
"""
import argparse
import html
import json
import os
from pathlib import Path
import re
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


CSS = '''body{max-width:1060px;margin:0 auto;padding:42px 24px 80px;font-family:system-ui,-apple-system,"PingFang SC",sans-serif;background:#fff;color:#111;line-height:1.8}h1{font-size:38px;line-height:1.3}h2{font-size:23px;margin-top:36px}.tag,.muted{color:#666;font-size:14px}.lead{font-size:21px;max-width:800px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}.card,details{border:1px solid #ddd;border-radius:14px;padding:20px;margin:14px 0}.card h3{margin-top:0}a{color:#111}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;line-height:1.75}summary{cursor:pointer;font-weight:600}footer{margin-top:40px;border-top:1px solid #ddd;padding-top:16px;font-size:14px}'''


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
    info = metadata(root)
    files, manifest, skill_digest = snapshot(info["skill"])
    review, cases, historical = selected_evidence(root, evaluation, info, skill_digest)
    sources = load_json(root / "research/sources.json")
    cards = []
    for name, data in files.items():
        if name.endswith(".md"):
            cards.extend(re.findall(r"^#{2,3}\s+([ZPLTA]\d{2})\s*[：:]", data.decode("utf-8-sig"), re.M))
    counts = {"skill_cases": sum(item["condition"] == "skill" for item in cases),
              "baseline_cases": sum(item["condition"] == "baseline" for item in cases),
              "actual_turns": sum(len(item["turns"]) for item in cases),
              "historical_turns": sum(len(item.get("turns", [])) for item in historical)}
    evaluation_link = evaluation.relative_to(root).as_posix()
    report_link = (evaluation.parent / "report.md").relative_to(root).as_posix()
    status = str(review["status"])
    version = info["version"]
    intro = '''零一大学指南针｜{version}
从零到一，让技术进步成为每个人的机会。

面向大学新生与 AI 初学者，帮助明确需要、选择路径、完成真实任务，形成独立判断与实践能力。普通设备、非计算机专业与零新增预算均可开始。

本版内容
共通基础＋专业应用、应用开发、模型与研究三条可切换路径。
任务、思考方法、学习方法与 AI 协作设计按需读取，成果是否可用与学生是否掌握分开检查。
手机、无 API 或访问失败时可用材料片段和预制输出来练习；实际操作未验证时如实记录。

安装与开始
将整个 {name} 文件夹放入 Codex 用户级 ~/.agents/skills/，Windows 为 %USERPROFILE%\\.agents\\skills\\。保留内部结构；已有同名或旧版安装先备份比对用户改动，移出旧目录以避免重复匹配。
打开新聊天并输入：
使用 ${name}。我刚上大学，没有编程基础，今晚有20分钟，想试一次AI帮助课程学习。

也可以从已有课程、小项目、能力检查或大学生活中的选择继续。提醒、保存和跨会话能力取决于宿主；不承诺已创建未执行的操作。

当前验收
状态：{status}
安装文件 {files} 个；方法与任务卡 {cards} 张；研究与教学参考 {sources} 项。
采用 {skill_cases} 个 Skill 情境、{baseline_cases} 个基线情境，共 {actual_turns} 条实际回答；所选记录的同目录另有 {historical_turns} 条未采用尝试，其他运行轮次和历史版本见报告。
基线记录的采用表示证据完整、可用于对照，不表示其教学表现已通过与 Skill 相同的语义评审。
采用索引：{evaluation}
报告：{report}
以上是模拟对话与工具验证，真实学生的学习效果仍待自愿试用。教学示范不计作真实学生或实际模型记录。

维护入口
python3 scripts/validate_package.py
python3 scripts/validate_package.py --build
python3 scripts/render_delivery.py --evaluation {evaluation}
测试设计见 tests/test-plan.md；来源和适用边界见 coverage-report.md 与 research/sources.json。
本地 HTML 仅用于阅读说明和测试记录，不提供在线模型调用或聊天服务。
'''.format(version=version, name=info["name"], status=status, files=len(files), cards=len(cards),
           sources=len(sources), evaluation=evaluation_link, report=report_link, **counts)
    body = '<div class="tag">零一大学指南针 · {}</div><h1>从零到一，让技术进步成为每个人的机会。</h1>'.format(html.escape(version))
    body += '<p class="lead">从当前问题开始，通过有依据的思考、学习与实践，形成自己的判断和能力。</p>'
    body += '<div class="grid">'
    for title, text in [("用 AI 学专业", "理解课程、核对资料、练习表达，留下自己的理解。"),
                        ("做一个小应用", "从明确的输入输出开始，运行样例、观察错误、亲手修改。"),
                        ("探索模型与研究", "比较方法、辨认数据与评价，解释结果和局限。")]:
        body += '<div class="card"><h3>' + title + '</h3><p>' + text + '</p></div>'
    body += '</div><h2>开始使用</h2><pre>使用 $' + info["name"] + '。我想根据自己的条件，开始一个能检查理解的小任务。</pre>'
    body += '<p><a href="{name}.zip">下载安装包</a> · <a href="{name}/SKILL.md">查看 Skill 入口</a> · <a href="tests/实际对话记录.html">查看采用的实际对话</a></p>'.format(name=info["name"])
    body += '<h2>验证状态</h2><p>' + html.escape(status) + '。真实学生效果仍待试用验证。</p>'
    body += '<details><summary>完整安装与验收说明</summary><pre>' + html.escape(intro) + '</pre></details>'
    body += '<footer><a href="' + html.escape(report_link, quote=True) + '">本版报告</a> · <a href="coverage-report.md">来源范围</a> · <a href="tests/pilot-guide.md">自愿试用材料</a></footer>'
    transcript = '<div class="tag">' + html.escape(version) + ' · 验收索引指定的实际模型回答</div><h1>看见对话如何推进</h1>'
    transcript += '<p>仅展示明确采用且版本、原始字节摘要和运行状态匹配的证据。模拟对话不证明真实学生效果。</p>'
    transcript += '<p>Skill 情境的语义结论见本版报告；基线记录的采用只确认对照证据完整，不代表教学语义通过。</p>'
    transcript += '<p><a href="' + html.escape(os.path.relpath(str(evaluation), str(root / "tests")), quote=True) + '">采用索引</a></p>'
    transcript += ''.join(conversation(item) for item in cases)
    if historical:
        transcript += '<h2>未采用与历史尝试</h2>' + ''.join(conversation(item, True) for item in historical)
    transcript += '<footer>历史版本的验证记录按原版本保留，不继承本版通过结论。</footer>'
    forwarding = '社长，这是「零一大学指南针」{}。从零到一，让技术进步成为每个人的机会。解压后打开“00_先读说明.html”，其中包含安装、来源边界和本版验收入口。实际对话严格对应验收索引；真实学生效果尚待自愿试用。\n'.format(version)
    # The overview, text and forwarding files share a transaction. The transcript
    # is prepared only after all adoption checks have succeeded.
    publish_files({root / '00_先读说明.txt': intro.encode(),
                   root / '00_先读说明.html': page('零一大学指南针 · ' + version, body).encode(),
                   root / '给社长的转发说明.txt': forwarding.encode()})
    publish_files({root / 'tests/实际对话记录.html': page('实际对话记录 · ' + version, transcript).encode()})
    return dict(counts, version=version, evaluation=status, skill_digest=skill_digest,
                history_scope='unselected_attempts_in_directories_of_adopted_artifacts',
                overview='00_先读说明.html', adopted_artifacts=len(cases))


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

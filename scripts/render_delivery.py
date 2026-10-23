#!/usr/bin/env python3
"""Regenerate local overview and readable actual transcripts from saved evidence."""
import html, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(path, default):
    p=ROOT/path
    return json.loads(p.read_text()) if p.exists() else default

def main():
    structure=load('tests/v020/structure-results.json',{})
    review=load('tests/v020/evaluation.json',{})
    cases=[]; historical=[]
    for d in sorted((ROOT/'tests/v020/behavior').glob('*')):
        attempts=sorted(d.glob('attempt-*.json'))
        if attempts:
            historical.extend(json.loads(p.read_text()) for p in attempts[:-1])
            item=json.loads(attempts[-1].read_text())
            cases.append(item)
    actual_turns=sum(len(c.get('turns',[])) for c in cases)
    historical_turns=sum(len(c.get('turns',[])) for c in historical)
    skill_cases=[c for c in cases if c.get('condition')=='skill']
    baseline=[c for c in cases if c.get('condition')=='baseline']
    status=review.get('status','待完成行为评审')
    intro=f'''零一大学指南针｜0.2.0
AI 入门、大学成长与自主选择
教学维护日期：2026-10-23；旧飞书快照：2026-10-22

面向大学新生与 AI 初学者，帮助明确需要、选择路径、完成真实任务，形成独立判断与实践能力。适配非计算机专业、普通设备和零新增预算。

本版内容
共通基础＋专业应用、应用开发、模型与研究三条可切换路径。
六类任务：课程自测、证据核对、公开资料问答、小项目实践、同题方向体验、本专业方向比较。
三条多轮教学示范；目的与手段、现实方案比较方法；手机/无API/访问失败时的替代练习。
成果是否可用与学生是否掌握分开检查；已有基础可跳过，不要求先确定四年人生目标。

安装与开始
把 zeroone-university-compass 整个文件夹放入接收者 Codex 的用户级 skills 目录，保留内部结构；已有同名版本先备份并比对用户改动。常见目录为 ~/.codex/skills/，Windows 为 %USERPROFILE%\\.codex\\skills\\；设置了 CODEX_HOME 时使用其 skills 子目录。
打开新聊天并输入：
使用 $zeroone-university-compass。我刚上大学，没有编程基础，今晚有20分钟，想试一次AI帮助课程学习。

也可以从已有任务继续：
我会一点Python，想做一个公开资料问答小成果，每周两小时，没有API预算。
我用了AI做出作品，却讲不清关键部分，请帮我检查究竟学会了什么。
我暂时不想学AI，只想理清大学里的方向和压力。

验证与资料范围
当前可安装文件：{structure.get('skill_files','待统计')}；方法/任务卡：{len(structure.get('card_ids',[]))}；研究与教学参考来源：{structure.get('source_count','待统计')}。
新版当前采用记录：{len(skill_cases)}个Skill情境、{len(baseline)}个基线情境、{actual_turns}条模型回答；另保留{historical_turns}条修复前或历史尝试回答；行为评审：{status}。详细结论与局限见 tests/test-report.md。
课程资料按选定章节核查，没有整库精读或运行上游训练代码。旧飞书正文、嵌入、外链缺口保留，见 coverage-report.md。
全部示范与测试学生输入为教学设计或模拟；真实学生试用尚未开展。自愿试用材料见 tests/pilot-guide.md。

文件导航
zeroone-university-compass/：可安装Skill
zeroone-university-compass.zip：轻量安装包
coverage-report.md：新增内容与历史资料缺口
research/sources.json：来源账本
archive/research/：阅读笔记
 tests/test-report.md：新版验证结论
 tests/实际对话记录.html：实际模型回答
 tests/pilot-guide.md：自愿试用材料
 scripts/validate_package.py：结构、来源、manifest与ZIP检查

复查命令
python3 scripts/validate_package.py
修改Skill后通过检查并重新打包：python3 scripts/validate_package.py --build
行为测试运行与复评说明：tests/test-plan.md。
'''
    (ROOT/'00_先读说明.txt').write_text(intro)
    css='''body{max-width:1060px;margin:0 auto;padding:42px 24px 80px;font-family:system-ui,-apple-system,"PingFang SC",sans-serif;background:#f7f8f5;color:#26332c;line-height:1.8}h1{font-size:38px;line-height:1.3}h2{font-size:23px;margin-top:36px}.tag{color:#39725a;font-size:14px;letter-spacing:.08em}.lead{font-size:21px;max-width:760px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}.card,details{background:white;border:1px solid #dce4dd;border-radius:14px;padding:20px;margin:14px 0}.card h3{margin-top:0}a{color:#216247}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;line-height:1.75}code{background:#edf0e9;padding:3px 6px;border-radius:5px}summary{cursor:pointer;font-weight:600}.muted{color:#65756a}footer{margin-top:40px;border-top:1px solid #dce4dd;padding-top:16px;font-size:14px}'''
    def page(title,body): return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+css+'</style><body>'+body+'</body></html>'
    body='''<div class="tag">零一大学指南针 · 0.2.0</div><h1>从一个真实问题，开始学习 AI。</h1><p class="lead">陪大学新生与初学者明确需要、选择路径，通过可检查的小任务，形成自己的判断与实践能力。</p><div class="grid"><div class="card"><h3>用 AI 学专业</h3><p>理解课程、核对资料、练习表达。把成果做好，也能说清自己学会了什么。</p></div><div class="card"><h3>做一个小应用</h3><p>从明确的输入输出和小功能开始，按任务补基础、观察错误、亲手修改。</p></div><div class="card"><h3>探索模型与研究</h3><p>从可理解的小比较开始，辨认数据、方法和评价，再决定下一段投入。</p></div></div><h2>按现有条件开始</h2><p>手机、普通电脑和零新增预算都有入口。已有经验可以跳过基础；需要理清方向或倾诉时，也能从大学生活继续聊。</p><div class="card"><pre>使用 $zeroone-university-compass。我刚上大学，没有编程基础，今晚有20分钟，想试一次AI帮助课程学习。</pre></div><h2>打开交付内容</h2><p><a href="zeroone-university-compass.zip">下载可安装 ZIP</a> · <a href="zeroone-university-compass/SKILL.md">查看 Skill 入口</a> · <a href="tests/实际对话记录.html">浏览实际测试对话</a></p><p><a href="tests/test-report.md">验证报告</a> · <a href="coverage-report.md">来源范围与缺口</a> · <a href="tests/pilot-guide.md">自愿试用说明</a></p>'''
    body+=f'<h2>验证状态</h2><p>{html.escape(str(status))}。可安装文件 {structure.get("skill_files",0)} 个，方法与任务卡 {len(structure.get("card_ids",[]))} 张，研究与教学参考来源 {structure.get("source_count",0)} 项。真实学生效果仍待试用验证。</p>'
    body+='<details><summary>完整安装与验收说明</summary><pre>'+html.escape(intro)+'</pre></details><footer>教学维护日期 2026-10-23。学习路径、任务和示范为本项目原创教学设计；资料读取范围、模拟验证与真实效果分别记录。</footer>'
    (ROOT/'00_先读说明.html').write_text(page('零一大学指南针 · 0.2.0',body))
    transcript='<div class="tag">0.2.0 · 实际模型回答</div><h1>看见对话如何推进</h1><p>下面是运行器实际保存的输出，包含 Skill 与基线条件。编写的教学示范另在 Skill 参考文件中。运行成功不等于语义验收通过，判断见 <a href="test-report.md">验证报告</a>。</p>'
    for c in cases:
        label=f'{c["case"]} · {c.get("condition")} · {c.get("title")} · {c.get("status")}'
        transcript+='<details><summary>'+html.escape(label)+'</summary>'
        for t in c.get('turns',[]):
            transcript+='<p class="muted">学生 · 第'+str(t['number'])+'轮</p><pre>'+html.escape(t['user'])+'</pre><p class="muted">助手</p><pre>'+html.escape(t.get('answer','无完成输出'))+'</pre>'
        transcript+='</details>'
    for c in historical:
        transcript+='<details><summary>修复前/历史尝试 · '+html.escape(c['case']+' · '+c.get('condition',''))+'</summary><p>此记录保留用于比较，不代表最终采用版本。差异与重测范围见测试报告。</p>'
        for t in c.get('turns',[]):
            transcript+='<p class="muted">学生 · 第'+str(t['number'])+'轮</p><pre>'+html.escape(t['user'])+'</pre><p class="muted">助手</p><pre>'+html.escape(t.get('answer','无完成输出'))+'</pre>'
        transcript+='</details>'
    transcript+='<footer><a href="实际对话记录-v010.html">2026-10-22 历史对话记录</a> · 新版记录不继承旧版的通过结论。</footer>'
    (ROOT/'tests/实际对话记录.html').write_text(page('实际对话记录 · 0.2.0',transcript))
    (ROOT/'给社长的转发说明.txt').write_text('社长，这是「零一大学指南针」0.2.0 整体升级包。解压后先打开“00_先读说明.html”。本版面向大学新生与AI初学者，包含三条可切换学习路径、六类真实任务、三条教学示范，以及目的选择、能力检验和反馈调整的方法。安装包、来源记录和新版实际测试对话都在里面；验证范围请以tests/test-report.md为准。真实学生试用尚未开展，已附自愿试用任务与反馈表。\n')
    print(json.dumps({'overview':'00_先读说明.html','skill_cases':len(skill_cases),'baseline_cases':len(baseline),'actual_turns':actual_turns,'evaluation':status},ensure_ascii=False))
if __name__=='__main__': main()

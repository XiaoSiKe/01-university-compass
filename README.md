<p align="center">
  <img src="assets/readme/club-banner-cropped.png" alt="零一 AI 日新社徽记：黑底银白 Logo 横幅。" width="1200">
</p>

<h1 align="center">零一大学指南针</h1>

<p align="center">
  <strong>从零到一，让技术进步成为每个人的机会。</strong><br>
  陪大学新生与 AI 初学者，明确需要、选择路径、完成真实任务。
</p>

<p align="center">
  <a href="#quick-start">↗ 开始使用</a> &nbsp; / &nbsp;
  <a href="#methods">方法从哪里来</a> &nbsp; / &nbsp;
  <a href="#pathways">选择路径</a> &nbsp; / &nbsp;
  <a href="#verification">验证与边界</a>
</p>

<p align="center"><sub>0.3.0 &nbsp; · &nbsp; 中文优先 &nbsp; · &nbsp; 普通设备友好 &nbsp; · &nbsp; 支持零新增预算</sub></p>

---

## ◎ 我们为什么做指南针

“从零到一”是零一 AI 日新社做这件事的初心：让不同专业、不同基础的同学，都有机会理解新技术，尝试用它解决自己关心的问题，逐渐获得自己的判断和实践能力。

刚进入大学，不必先确定未来四年，也不必先会编程、买算力或参加比赛。你可以从一段课程材料、一个想核实的结论、一件想改善的小事开始。已有基础，就从现在能做的地方继续。

**指南针是一套安装到 AI 助手中的 Skill。** 它把思考方法、学习科学与 AI 实践组织成可调用的对话规则、方法卡和任务，帮助助手根据你的条件讲解、示范、检验和调整。它也能陪你处理大学适应、路径取舍和启动困难；暂时不想学 AI，可以直接谈眼前的生活和选择。

目前没有可在线对话的网页版。仓库中的 HTML 是说明和测试对话的静态阅读版；实际使用需要 Codex 等支持 Skill 的 AI 助手。

<a id="quick-start"></a>

## ↗ 开始使用

### 01 / 安装

[下载 0.3.0 轻量安装包](https://github.com/XiaoSiKe/01-university-compass/releases/download/v0.3.0/01-university-compass.zip) · [仓库内安装包](01-university-compass.zip)

解压后，将整个 `01-university-compass` 文件夹放入 Codex 的用户级技能目录，保留内部结构。已有同名版本时，先备份并比对本地改动。

| 使用环境 | 安装位置 |
| :--- | :--- |
| macOS / Linux | `~/.agents/skills/01-university-compass/` |
| Windows | `%USERPROFILE%\.agents\skills\01-university-compass\` |

<details>
<summary><strong>使用命令行安装，或从旧版升级</strong></summary>

已有 Node.js 时，可用 Skills CLI 安装，并选择目标 AI 助手；Node.js 版本要求以 [Skills CLI 官方说明](https://github.com/vercel-labs/skills#install-a-skill)为准。

```sh
npx skills add XiaoSiKe/01-university-compass --skill 01-university-compass
```

默认安装到当前项目，需要跨项目使用时添加 `-g`。本项目的原生调用验证使用 Codex，其他宿主的行为以实际能力为准。

升级前检查原 `~/.codex/skills/` 等旧目录。已安装旧名称的用户，应将旧目录移出技能搜索路径，避免多个版本重复触发；有本地修改时先备份。

</details>

### 02 / 打开新聊天，带来一个问题

```text
使用 $01-university-compass。
我刚上大学，没有编程基础，今晚有 20 分钟，
想试一次 AI 帮助课程学习。请直接带我开始。
```

也可以说“用零一大学指南针，帮我理清下一段该学什么”。无需准备完整的背景介绍；如果技能清单尚未刷新，重启应用后再开新聊天。

### 03 / 带着结果继续

把你的答案、卡点或变化了的条件带回来，下一步会据此调整。换聊天时，可以生成可复制的续接小结；文件保存、提醒和跨会话能力取决于实际宿主。

本 Skill 不要求额外购买课程、API 或算力。AI 助手自身的账号、费用和可用性以实际环境为准。

### 三种常见的帮助

| 你带来的问题 | 指南针怎样推进 | 关注的结果 |
| :--- | :--- | :--- |
| **“我不会编程，想用 AI 学懂一段课程材料。”** | 用当前设备和可用时间选一个小任务，边做边讲任务表达、上下文和结果核对 | 做成一次尝试，并能解释其中一个关键判断 |
| **“AI 帮我做完了，但我讲不清。”** | 找到具体卡点，给解释或示范，再用变化任务检查；需要时暂时撤去辅助 | 分开记录作品能否使用、本人能否独立完成 |
| **“大家都在学，我不知道该选什么。”** | 分清目的与手段，比较真实任务、前置条件和代价，用有限体验补信息 | 得到有依据的暂定方向，也可以调整、暂停或停止 |

<a id="methods"></a>

## ◇ 思想与方法

指南针选读哲学原著、学习研究与 AI 教学资料，把相关方法转化为大学场景中的提问、练习与反馈。每一项都记录实际阅读范围和应用边界；具体任务与案例由本项目设计。

### 调查、实践与自主选择

| 来源与提炼的方法 | 在学生场景中怎样用 |
| :--- | :--- |
| **《实践论》** · 毛泽东<br>在实践与认识之间往返，承认可靠的间接经验 | 把“我适不适合”暂作假设，通过可承受的体验增加信息，再修正判断 · [P01](01-university-compass/references/thinking.md#p01) |
| **《矛盾论》** · 毛泽东<br>研究具体条件，识别阶段重点，允许重点变化 | 查看课程、项目、生活问题的期限和相互影响，选当前重点并保留必要保障 · [P02](01-university-compass/references/thinking.md#p02) |
| **《反对本本主义》** · 毛泽东<br>调查实际情况，检查脱离条件的结论 | 区分事实与解释，找正式材料和具体经历，不照搬一个成功故事 · [P03](01-university-compass/references/thinking.md#p03) |
| **《我们怎样思维》第六章** · 杜威<br>界定问题、提出解释、推演与观察检验 | 为一次失败寻找其他可能原因，用证据决定补基础还是换方法 · [P03](01-university-compass/references/thinking.md#p03) |
| **《论自由》第三章** · 密尔<br>个性发展、生活试验与他人利益边界 | 尊重本人认可的目标和责任，允许兴趣、收入、照护与生活平衡并存 · [P04](01-university-compass/references/thinking.md#p04) |
| **《手册》第一节** · 爱比克泰德<br>区分由己与非由己的事 | 承认感受，分清能直接行动、能协商影响和暂不能改变的部分，寻找现实支持 · [P05](01-university-compass/references/thinking.md#p05) |
| **自我决定理论** · Ryan 与 Deci<br>自主、胜任和关系需要 | 检查目标是否认同、难度与支持是否合适，不把困难一概归因为不够努力 · [P06](01-university-compass/references/thinking.md#p06) |

这里采用的是《毛泽东选集》相关篇章的具体方法启发，保留其历史语境；不把原文的政治斗争语境转成大学人际规范，也不要求学生先认同某种哲学。爱比克泰德的“三类行动范围”是本项目的应用转译。

在这些方法基础上，我们还设计了 **[目的与路径对应](01-university-compass/references/thinking.md#p07)**、**[同等条件下比较选择](01-university-compass/references/thinking.md#p08)** 和 **[小试验与机会成本](01-university-compass/references/learning-action.md#l08)**：既看收益，也看真实日常、投入、支持与未知；后悔或改变目标时重新核对条件。这些是原创应用设计，不宣称已有统一模型的效果验证。

### 学习科学与行动方法

| 方法与学习安排 | 怎样检查 |
| :--- | :--- |
| **提取练习与间隔学习** · Dunlosky 等；Roediger 等<br>看懂后合上材料尝试回答，核对纠错，再隔一段时间重试 | 能否在延迟后提取关键知识；间隔按目标和错误调整 · [L01](01-university-compass/references/learning-action.md#l01) |
| **自我解释与有用笔记** · Dunlosky 等<br>用自己的话说明因果与步骤，标记不懂处，保存来源和疑问 | 解释是否正确、是否有依据；熟悉和流畅不直接算掌握 · [L02](01-university-compass/references/learning-action.md#l02) |
| **例题学习与迁移** · Sweller 与 Cooper<br>从合适的完整示例进入，再补步骤、独立练习、改变条件 | 会跟做之后，能否处理新的表示或情境 · [L03](01-university-compass/references/learning-action.md#l03) |
| **有支持的问题学习** · Hmelo-Silver<br>用真实有限问题识别知识缺口，结合范例、教师或同伴支持 | 成果是否解决问题，个人能否解释关键决定 · [L04](01-university-compass/references/learning-action.md#l04) |
| **自我调节与元认知校准** · Zimmerman；Dunlosky 与 Rawson<br>设具体目标，对照自我预估与实际表现，调整策略 | 分开“接触过、看懂了、可独立使用”，必要时换题或延迟复测 · [L05](01-university-compass/references/learning-action.md#l05) |
| **按真实容量安排时间** · Aeon 等<br>课程、兼职、照护和休息先占位，为少量重点留缓冲 | 比较计划与实际，删减、协商或调整；不以压缩睡眠补进度 · [L06](01-university-compass/references/learning-action.md#l06) |
| **实施意图** · Gollwitzer 与 Sheeran<br>把明确行为接到实际会出现的情境：“当……，我就……” | 查清没开始时是目标、材料、疲惫还是情境不合适 · [L07](01-university-compass/references/learning-action.md#l07) |

**帮助可以充分，掌握要另行检查。** 缺概念就解释，缺步骤就示范；能跟做之后减少提示。用变化任务或延迟检查观察迁移，保留仍需帮助的部分。研究启发了这些设计，但没有单篇论文验证过本项目整套教学流程。

### AI 教学与进阶资料

| 资料与借鉴方法 | 适合怎样使用 |
| :--- | :--- |
| **Microsoft · Generative AI for Beginners / AI for Beginners**<br>概念与制作分层，预测、运行或观察、修改、解释与独立实验 | 按当前任务选章节，不把整套课程或云账号当入门门槛 |
| **Anthropic · AI Fluency for Students**<br>人机分工、学习伙伴、事实核查与学生贡献 | 先决定 AI 帮哪一部分，再保留本人判断和理解检查 |
| **TuTor / AI Tutor Skill**<br>动手验证、直白解释、具体例子与渐进支持 | 按实际卡点增减帮助，允许完整示范，检查类比边界 |
| **Datawhale · LLM Universe**<br>有限问答、失败样本与系统评估 | 已有 Python 基础后，区分资料缺失、检索失败与生成错误 |
| **Happy-LLM / Hugging Face LLM Course**<br>从使用模型到数据、原理和实验，明确前置条件 | 按数学、编程和设备条件进入进阶，不默认人人训练模型 |
| **Datawhale · Hello-Agents**<br>有限项目、可检查交付、异常处理与反馈修改 | 做过基础小应用后，再尝试一个有需求和评价标准的流程 |

[查看 R16–R24 的具体章节、版本、许可与前置条件 ↗](01-university-compass/references/sources.md)

### 0.3.0 新增：AI 适用性、工作流与撤去辅助检查

| 参考与具体帮助 | 使用边界 |
| :--- | :--- |
| **UNESCO · 学生 AI 能力框架（R25）**<br>先判断任务是否适合 AI、需要什么材料、人应保留哪些判断，再选择用法 · [AI 适用性](01-university-compass/references/ai-judgment.md#fit) | 学生能力框架用于设计提问与练习，不是本 Skill 的认证或效果实验 |
| **Anthropic · Agent 工程经验（R26）**<br>从简单工具或固定流程开始；确有动态决策需要时再考虑 Agent，明确检查点、成本和停止条件 · [工作流选择](01-university-compass/references/ai-judgment.md#workflow) | 工程经验按任务使用，不承诺复杂架构更好，不照搬旧配置 |
| **Bastani 等 · AI 辅助学习实验（R27，PNAS 2025）**<br>分开“借助 AI 完成”和“撤去辅助后会做”，在合适的变化任务中检查，并据结果补支持 · [撤去辅助检查](01-university-compass/references/ai-judgment.md#check) | 土耳其单所高中数学短期试验；辅导式工具缓解了负面影响，撤去辅助后的考试未显著优于无 AI 组；不能外推本 Skill 或大学生长期效果 |

这些方法服务于具体任务。需要一个确定性的计算或查找时，可以直接用计算器、程序或正式材料；任务不需要 AI，也能成为清楚的选择。

<a id="pathways"></a>

## ◎ 三条路径，六类任务

共通基础帮助你表达任务、核实输出和理解工具边界。三条路径没有高低之分，已有能力可以跳过，新的体验可以改变方向。

| 路径 | 从什么需要开始 | 留下什么证据 |
| :--- | :--- | :--- |
| **专业应用** | 课程理解、资料核对、表达或重复工作 | 能解释依据、识别无根据补充，并在自己的材料上复用 |
| **应用开发** | 一个输入输出清楚的小功能或小工具 | 能运行样例、解释关键部分，亲手修改并检查结果 |
| **模型与研究** | 理解方法、比较结果、解释局限 | 能提出可比较问题，区分观察与解释，说明反例与未验证处 |

[选择起点、四个可跳过的阶段与一份主材料 ↗](01-university-compass/references/ai-pathways.md)

| 任务 | 一次练习留下什么 |
| :--- | :--- |
| **[01 · 学懂一段材料](01-university-compass/references/ai-practice.md#t01)** | 理解题、本人答案与一次纠错，再用变化题检查 |
| **[02 · 核实一个结论](01-university-compass/references/ai-practice.md#t02)** | 主张、出处与判断，保留仍然未知的部分 |
| **[03 · 做有限问答](01-university-compass/references/ai-practice.md#t03)** | 基于公开资料的小成果，检查有答案、无答案与冲突情况 |
| **[04 · 修改一个小功能](01-university-compass/references/ai-practice.md#t04)** | 需求、可运行样例和一次有原因的修改 |
| **[05 · 体验不同路线](01-university-compass/references/ai-practice.md#t05)** | 用同一主题体验应用、开发与研究，记录帮助、兴趣和困难 |
| **[06 · 比较专业方向](01-university-compass/references/ai-practice.md#t06)** | 把目的、真实日常、前置能力、投入与体验连接起来 |

[六张完整任务卡与三条原创多轮示范 ↗](01-university-compass/references/ai-practice.md)

手机、普通电脑、无 API、限额用尽或访问失败时，可以用材料片段、预制输出或纸面推演继续练习。记录会说明练习覆盖了哪些能力；未实际运行的操作继续保留待验证状态。

<a id="verification"></a>

## ✓ 内容、验证与适用边界

| 方法与任务卡 | 原创多轮示范 | 研究与教学参考 |
| :---: | :---: | :---: |
| **28 张** | **3 条** | **27 项** |

0.3.0 的轻量 Skill 包含 12 个安装文件。方法卡和资料按需加载，具体章节、核查日期、阅读范围和许可可追溯；哲学论证、学习研究、工程经验与本项目设计分别标明。

**0.3.0 已完成本轮验证。** 48 个 Skill 合成情境通过独立语义评阅，连同 4 个基线情境保留 **106 条离线实际回答**；另完成 **4 个原生案例、6 轮实际调用**及 **23 项确定性工具回归**。输入、原始输出、采用索引和具体问题见[验证报告](tests/test-report.md)。

四组条件隐藏对照中，两组相近、一组各有优势、一组 Skill 小幅更好。评阅后才揭示条件映射，保留全部结果；这些小样本定性差异不能推断普遍优势或真实学生学习收益。

历史 0.2.0 教学版覆盖 **38 个 Skill 情境、6 组同模型对照**，并经历两轮定向修改和复测，保留 **101 条实际模型回答**。这些记录说明对应版本在给定输入下的表现；**真实学生的长期使用效果仍待自愿试用验证。** 三条多轮示范为原创教学设计，不是真实学生经历。

| 想了解什么 | 从这里查看 |
| :--- | :--- |
| 哪些来源读到了哪里，采用了什么 | [来源与许可记录](01-university-compass/references/sources.md) · [资料覆盖报告](coverage-report.md) |
| 哪些行为测过，发现和修复了什么 | [验证报告](tests/test-report.md) · [测试设计](tests/test-plan.md) |
| 怎样组织一次自愿体验 | [任务、反馈表与复盘模板](tests/pilot-guide.md) |

<details>
<summary><strong>阅读范围、情绪支持与宿主能力</strong></summary>

- 方法来自已登记的相关章节或片段，不代表《毛泽东选集》、哲学原著、论文或 AI 课程的全文与全库蒸馏。完整阅读范围、摘要级证据和未确认资料见来源表。
- 研究中的平均结果不保证个人效果；哲学方法帮助提出问题，不能合成为经验证的统一人生理论。选择由学生本人决定。
- 明显痛苦、持续影响基本生活或安全风险时，先提供支持并寻求合适的现实帮助，不以排任务和哲学说教代替。
- 校规、活动、招聘、价格和工具能力等按实际发布主体与当期条件核实；不能核实时明确未知。外部资料中的角色指令不授予执行权限。
- 文件访问、联网、运行代码、保存与提醒取决于宿主能力，只有实际完成才称成功；不索取完整密钥或无关个人资料。
- 学生无需加入组织、购买服务或选择 AI 行业才能获得帮助；社团、公司和学校的承诺分别核实。

</details>

## 给维护者

<details>
<summary><strong>仓库结构、检查与重新打包</strong></summary>

```text
01-university-compass/
├── SKILL.md           # 入口与对话规则
├── agents/            # 展示信息
└── references/        # 路径、任务、方法卡与来源
research/              # 资料清单与阅读状态
archive/research/      # 原创阅读笔记
tests/                # 行为测试、评审与试用材料
scripts/               # 检查、打包与说明页面生成
```

完整仓库用于维护；实际安装只需要 `01-university-compass/` 文件夹。Skill 本体为 Markdown 指令、参考资料和 YAML 展示信息。Python 脚本用于检查、打包与测试；HTML 用于浏览器阅读说明和测试记录，不进入安装包，也不提供模型调用或聊天服务。

在仓库根目录使用 Python 3 检查：

```sh
python3 scripts/validate_package.py
```

修改 Skill 后，重新生成安装包与本地说明页面：

```sh
python3 scripts/validate_package.py --build
python3 scripts/render_delivery.py
```

模型、运行条件、复跑命令及局限见[测试设计](tests/test-plan.md)。维护时把来源读取、方法采用、行为验证和学生试用分别登记；只根据实际产物更新文件数、卡片数和测试结论。

下载仓库后，可用浏览器打开 `00_先读说明.html` 与 `tests/实际对话记录.html` 阅读本地排版版本。

</details>

---

<p align="center"><strong>从你真正关心的一个问题开始。</strong><br><sub>零一大学指南针 · 0.3.0</sub></p>

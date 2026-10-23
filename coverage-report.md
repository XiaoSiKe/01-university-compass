# 资料覆盖与版本记录

本版：0.2.1；教学内容维护于2026-10-23，旧飞书快照为2026-10-22。**没有完成全库逐页、逐附件、逐外链的完整蒸馏**。本轮按新生任务定向补充教学方法，未将旧来源的未读状态提升为已完成。

## 0.2.1 命名与视觉更新

仓库、安装目录和调用名统一为 `01-university-compass`，社团知识文件改为 `references/01.md`。README封面直接使用社团原始Logo，采用黑白与中性灰；教学方法与任务没有扩展或重写。命名迁移、内容等价与原生安装检查见[本版验证](tests/v021/report.md)。旧版模型输出、评审和0.2.0发布记录保留原貌，不能把旧证据冒称为重新测试新版。

## 0.2.0 新增范围

- AI共通基础、专业应用/应用开发/模型与研究三路径，四个可跳过阶段。
- 六类原创任务、低资源替代和三条完整多轮教学示范；目的与路径对应、同等条件比较两张原创思考卡。
- R16–R24九项课程/Skill资料：已核查README或课程页面、选定章节及许可；具体范围见[来源账本](research/sources.json)与[阅读笔记](archive/ARCHIVE.md)。没有运行上游课程代码，没有把教程方法当作效果研究。
- 对话、学习与续接规则同步更新；正式行为验证和隔离安装发现结果见[新版测试报告](tests/test-report.md)。教学示范和实际测试记录分别标识。
- 原创方法与练习独立编写，来源原文、图表、代码不随安装包分发。旧研究原始全文与工具日志仍只在原制作工作区，本包保留阅读笔记。

当前文件、卡片、来源与链接数量由[结构检查](tests/v021/structure-results.json)生成；实际测试通过范围由测试报告给出。真实学生试用尚未开展，已有[自愿试用材料](tests/pilot-guide.md)。

## 2026-10-22 资料基础（历史口径）

下表保留上一版统计，区别发现、取得、实际审读和蒸馏。新版增量独立列在上方，不改变旧飞书覆盖率。

## 计数口径

- 飞书按唯一节点token计数；同一节点的重复链接不另计。原空间和外部空间分开。
- 外链按归一化URL计数；不是296篇文章，包含工具首页、专辑、教程、项目、视频、附件入口等。未继续遍历外部网站全站。
- “正文候选”只代表自动抽取取得较多文字，可能含导航或登录提示，尚未经逐项审读。
- “文字范围蒸馏”不等于整份文档完成。只要还有嵌入表格、同步块、图片等未核实，就不记作完整蒸馏。目录定位也不算知识蒸馏。

|范围|发现|获取/审读|蒸馏|
|---|---:|---|---|
|零一原空间|42页|42页导出文字归档；32页可导出文字已审读（含8个目录/提纲页）；其余10页只筛查目录与片段|24页完成可用文字的提炼/采用边界；其中5页整页范围完成，19页嵌入或图片仍待补|
|外部飞书空间|17页|15页导出文字已归档但未实质审读；2页无法访问|0页完整蒸馏|
|知识库相关外链|296项|105项正文候选已归档待审读；9项专辑/目录；182项无法取得可确认正文|0项实质内容完成蒸馏|
|补充研究|15项已纳入来源|相关章节/摘要已审读；9项主体原文完整下载，另保存1份R14作者说明；下载失败项保留来源与阅读记录|形成14张P/L卡；不是15篇全文精读|
|日常调用知识|20张卡|6张零一Z卡＋6张P卡＋8张L卡|三条对话流程、主题地图、证据与续接规则|

原空间的文档级读取状态：5完整读取、29部分读取、8目录或占位。这里的5不是“只读过5页”；19页文字已读并提炼，但嵌入/图片不完整。

## 发现与访问方法

从入口节点读取元数据及导出正文，递归提取原空间引用和子页；使用现有bot身份，没有新增授权。目录枚举接口缺wiki:node:retrieve权限，随后查看公开网页目录及AI入门、通识、Vibe coding、Codex/Claude、AIGC、进阶等可见层级，补获2个FUKATHON页面。网页目录可能虚拟化或分页，无法据此保证后台没有隐藏节点。
早期抓取曾沿外部飞书引用发现额外页面，随后收窄为原空间递归。已取得的17项外部空间资料保留并明确隔离，不扩大核心覆盖率。
原始飞书清单保留工具获取状态；人工式审读和蒸馏状态以research下清单为准，不能把原始清单中的“待审读”自动提升为完成。

## 阻塞、影响与最小补齐步骤

|位置|原因与影响|最小补齐方式|
|---|---|---|
|飞书目录API|缺wiki:node:retrieve；总目录无法完全核对|管理员提供完整目录导出，或在已有应用授予对应只读权限后再枚举|
|嵌入表格|抽查返回缺sheets:spreadsheet:read；尚未取得表格正文|提供有关工作表导出，或补充相应读取权限；无需授予编辑权限|
|公众号正文|HTTP验证码；后续浏览器安全策略拒绝访问，未采用替代渠道绕过|用户从有权访问的会话导出需纳入的正文；不以标题补写内容|
|公众号专辑|有专辑标11条但只加载10条；部分专辑0条|提供完整文章列表，核对分页与重复项|
|动态网站/外部工具页|部分只返回空壳或网络错误；已取得105项候选也尚未审读|按学生问题优先审读相关材料，无需扩展全站|
|图片、同步块、白板、附件、视频|未逐项取得/审读；图片描述不能替代原图|按用途提供导出正文、表格或转录；无关安装包无需纳入成长知识|
|长篇技术资料|10页只做目录及片段筛查；这部分是工作未完成，不是都被权限阻塞|继续按章节审读并核验重要主张，更新每页范围和卡片|
|真实大学案例|指南针原页是提纲，缺真实学生结果|取得可使用且已去标识的案例及其情境/结果；当前案例均标注AI设计|

## 关键冲突与未采用内容

FUKATHON活动方案最后编辑2026-09-29，写10月11日；招募页最后编辑2026-10-12，写10月24–25日“初定”。更新较晚不等于最终确认。社团、公司、学校各自主体分开；不保证实习、收入、学分、获奖。旧技术教程中的免费额度、模型能力、全权代做作业、沙盒权限、宏观就业收益等不作为现行事实。

## 可核对清单

- [飞书逐页清单CSV](research/feishu-inventory.csv) / [JSON](research/feishu-inventory.json)：标题、原链接、目录、作者、更新时间、主题、对象、场景、读取范围、蒸馏位置和外链。
- [外链逐项清单CSV](research/external-inventory.csv) / [JSON](research/external-inventory.json)：296项逐项状态，全部尚未实质内容蒸馏。
- [嵌入对象清单](research/embedded-inventory.json)：150条父页关联记录，包括18个不同工作表引用；不是150份已读资料。
- [研究计划](research/research-plan.md) / [研究来源清单](research/sources.json) / [调用用来源表](01-university-compass/references/sources.md)。
- [主题地图](01-university-compass/references/topic-map.md)，[原始档案说明](archive/ARCHIVE.md)。

## 未完成飞书页面

以下逐项列出；外链296项全部待实质蒸馏，见独立清单，不在此重复近300行。目录页没有内容可蒸馏属于内容缺口，不强行算失败或完成。

|页面|状态|后续范围|
|---|---|---|
|[零一 AI 日新社【从零到一】](https://scn96l2kzmbn.feishu.cn/wiki/DDaiw0qKoifo7jkd2H2c9mxhnYe)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[从零到一](https://scn96l2kzmbn.feishu.cn/wiki/I543wwFoni8Hu8kzzpmc1JclnNh)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[零一实践](https://scn96l2kzmbn.feishu.cn/wiki/MbjzwbBvdirC1HkgPBKcDOPjnBg)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[AI 入门 一本通【从零到一】](https://scn96l2kzmbn.feishu.cn/wiki/IHBPwDsfXi5ctzkEpobcsbJ1n6g)|目录或占位|目录定位完成，无实质知识蒸馏；目录/占位文字已读；不代表引用目标已读|
|[AI 进阶 一本通【一到一百】](https://scn96l2kzmbn.feishu.cn/wiki/SO0GwNaXkis0u8kRqwHclMKmnlc)|目录或占位|目录定位完成，无实质知识蒸馏；目录/占位文字已读；不代表引用目标已读|
|[零一大学 指南针【答疑解惑】](https://scn96l2kzmbn.feishu.cn/wiki/QjfxwzH8ZiCoFvkv0Lpcboy4neg)|目录或占位|目录定位完成，无实质知识蒸馏；目录/占位文字已读；不代表引用目标已读|
|[零一开源【AI 项目库】](https://scn96l2kzmbn.feishu.cn/wiki/OsL0waujXi3wkkk44AocNVFGnmg)|目录或占位|目录定位完成，无实质知识蒸馏；目录/占位文字已读；不代表引用目标已读|
|[组织架构与社团系统](https://scn96l2kzmbn.feishu.cn/wiki/Pw4FwagW6iPaVqkzyeNc7rRSnub)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[领航先锋](https://scn96l2kzmbn.feishu.cn/wiki/HLEfwV9BFiutsQkFxAQcPAB1nvb)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[建言献策](https://scn96l2kzmbn.feishu.cn/wiki/GIh6woke5ilTbikyNNrcIUPdnJg)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[零一 AI 日新社【合作生态】](https://scn96l2kzmbn.feishu.cn/wiki/X7h6wI8SCiAuZAkpYF2caNv7nTG)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[零一高校分社计划【开源共建】](https://scn96l2kzmbn.feishu.cn/wiki/PIqKwgPI7iIrtXkHps9cqavKn4c)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[入门指南与道法术器【AI 导学篇】](https://scn96l2kzmbn.feishu.cn/wiki/J1jewhiEri2SiLkPvo7cQM1Inl3)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[AI 通识课【基础认知】](https://scn96l2kzmbn.feishu.cn/wiki/CZKcwIyPSih43TkqBpyc6CwznIc)|目录或占位|目录定位完成，无实质知识蒸馏；目录/占位文字已读；不代表引用目标已读|
|[Vibe coding 一本通](https://scn96l2kzmbn.feishu.cn/wiki/FcgFwyUotiQr9skbl9Ucfqfwnze)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[Codex、Claude Code 一本通【从零到一】](https://scn96l2kzmbn.feishu.cn/wiki/DKebwHE1kib9mwkFQO7chSyNntd)|目录或占位|目录定位完成，无实质知识蒸馏；目录/占位文字已读；不代表引用目标已读|
|[AIGC 入门一本通【从零到一】](https://scn96l2kzmbn.feishu.cn/wiki/F5kZw4PtriM5uFkZqq2csOVjnJh)|目录或占位|目录定位完成，无实质知识蒸馏；目录/占位文字已读；不代表引用目标已读|
|[关于 Github 入门教学](https://scn96l2kzmbn.feishu.cn/wiki/JVRHwTzhqih6xKkOyxXcpfTBnkb)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[Agent Skill 的使用教程与推荐大全](https://scn96l2kzmbn.feishu.cn/wiki/HjQ6wysqViD9fAkAgeecY6kLnkh)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[关于复杂 Bug 修复与方案](https://scn96l2kzmbn.feishu.cn/wiki/ZzPDw6fecipd55kCa9JcXcT9nzd)|目录或占位|目录定位完成，无实质知识蒸馏；目录/占位文字已读；不代表引用目标已读|
|[关于 飞书 CLI 的入门教学](https://scn96l2kzmbn.feishu.cn/wiki/GdN5wDtzJifiFxkPFQ9cPfk7nse)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[怎么快速入门 AI？【站在巨人的肩膀上】](https://scn96l2kzmbn.feishu.cn/wiki/BBgUwwVL8iqf2Tk5D6Pc6F1LniD)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[100个 AI 基础概念扫盲【解释】](https://scn96l2kzmbn.feishu.cn/wiki/ELB0wAhOWi1CuRk5j2lcAJ55n6L)|部分读取|部分：资源定位与采用边界，全文蒸馏未完成；目录和开头/相关片段筛查；全文未逐项审读|
|[入门 AI 百问百答](https://scn96l2kzmbn.feishu.cn/wiki/FeEwwuf39iQ4BwkKwkRcgFjpnhc)|部分读取|部分：资源定位与采用边界，全文蒸馏未完成；目录和开头/相关片段筛查；全文未逐项审读|
|[学习 AI 的推荐书单](https://scn96l2kzmbn.feishu.cn/wiki/QmT1wJze4iv6Iwk0VwdcIo12nq6)|部分读取|部分：资源定位与采用边界，全文蒸馏未完成；目录和开头/相关片段筛查；全文未逐项审读|
|[AIGC 学习手册](https://scn96l2kzmbn.feishu.cn/wiki/QtOowS8FBirsxzkCaArcrV23nPz)|部分读取|部分：资源定位与采用边界，全文蒸馏未完成；目录和开头/相关片段筛查；全文未逐项审读|
|[AI编程蓝皮书2.0【AI产品黄叔】- Part 1](https://scn96l2kzmbn.feishu.cn/wiki/L3xJwYGcWiEZ6qkWKDNcglltn0g)|部分读取|部分：资源定位与采用边界，全文蒸馏未完成；目录和开头/相关片段筛查；全文未逐项审读|
|[AI编程蓝皮书2.0【AI产品黄叔】- Part 2](https://scn96l2kzmbn.feishu.cn/wiki/PRTXwzlcBi4Ogtke4hYcmBo7nUf)|部分读取|部分：资源定位与采用边界，全文蒸馏未完成；目录和开头/相关片段筛查；全文未逐项审读|
|[斯坦福 Vibe Coding 课程合集（免费资源 + 付费课程）](https://scn96l2kzmbn.feishu.cn/wiki/GYnbwpTJCiS7NekDf43ceZmvnxb)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[最适合新手的Claude Code、MCP、Skills全套教程【熊猫Jay】](https://scn96l2kzmbn.feishu.cn/wiki/ZmF3wMxWNiw4cSkmVm7c6Qs3nvh)|部分读取|部分：资源定位与采用边界，全文蒸馏未完成；目录和开头/相关片段筛查；全文未逐项审读|
|[Yeadon：30分钟！从0到1AI开发网站 - Windsurf零基础开发](https://scn96l2kzmbn.feishu.cn/wiki/Eg3Cw7UXniqB8hktziqcZFTQnmh)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[从混乱到可控：我总结了 10 个 AI 编程技巧](https://scn96l2kzmbn.feishu.cn/wiki/ZxegwxiQOiCm7LkNwMhcWkx8nib)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[小七姐-提示词](https://scn96l2kzmbn.feishu.cn/wiki/ST93wIf4CiZXGwk351wckBYin7d)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[南瓜博士-提示词](https://scn96l2kzmbn.feishu.cn/wiki/W2ITw6wMri8M6GkixyncmrvqnOL)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[相关Rules和Prompt](https://scn96l2kzmbn.feishu.cn/wiki/WaDDwugayig8LdkNhsackUdpnRb)|部分读取|部分：资源定位与采用边界，全文蒸馏未完成；目录和开头/相关片段筛查；全文未逐项审读|
|[Codex 免费教学【从安装到登录】](https://scn96l2kzmbn.feishu.cn/wiki/T9TuwJCYQiDPtrkLvqOcJzO6nNc)|部分读取|部分：资源定位与采用边界，全文蒸馏未完成；目录和开头/相关片段筛查；全文未逐项审读|
|[Codex 常见使用问题合集与解答](https://scn96l2kzmbn.feishu.cn/wiki/PDPcwLDZFiqn7Ek9D87c75GKn3d)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[Codex 新手入门与基础](https://scn96l2kzmbn.feishu.cn/wiki/LoIyw26PGiepphksu4rcVxsFn9d)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[Claude code 免费教学【从安装到登录】](https://scn96l2kzmbn.feishu.cn/wiki/QsaOwxHCIipYvlkzf2vc6vvBnxh)|部分读取|部分：资源定位与采用边界，全文蒸馏未完成；目录和开头/相关片段筛查；全文未逐项审读|
|[如何使用 API Key 进行生图创作？](https://scn96l2kzmbn.feishu.cn/wiki/GH9mwY3R9iPFlKkAxy0cLqJLnMh)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[零一 Skill 开发合集](https://scn96l2kzmbn.feishu.cn/wiki/ZzkSwRNd6iegiJkZ5dNcUCqInEb)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[万物摩尔定律  Sam Altman](https://scn96l2kzmbn.feishu.cn/wiki/PTrqwNzuOiOdpskIY3RcXomWn8d)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[AI 学习必备书单](https://scn96l2kzmbn.feishu.cn/wiki/LrC2wttSLiY4pnkVNaXc17VFn4g)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[Vega AI 创作平台：https://www.vegaai.net/](https://scn96l2kzmbn.feishu.cn/docx/T0Dldi73eo4NHNxvEs9cqh0Pngf)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[未知](https://scn96l2kzmbn.feishu.cn/wiki/W1LCwYA8eiTl77kpi81c31yNnJd)|无法访问|未完成；仅发现链接/元数据|
|[AI编程与炼金术：Build on Trae（第一季）（自用）](https://scn96l2kzmbn.feishu.cn/wiki/UspJwJk95iKoegkoUdWcmX7rnib)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[AI编程蓝皮书2.0](https://scn96l2kzmbn.feishu.cn/wiki/CBBPwvgEuicVhFkx0s7cPmhpn4e)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[未知](https://scn96l2kzmbn.feishu.cn/docx/H4t2d2VCtooVwmx335kcXKW9nUe)|无法访问|未完成；仅发现链接/元数据|
|[Claude code 专区](https://scn96l2kzmbn.feishu.cn/wiki/LJbiwATadi72LUklHpgcexeSnNh)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[Cursor 专区](https://scn96l2kzmbn.feishu.cn/wiki/SxiOw4VVTiOwnaksKdvcVFzxnQb)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[Trae专区-中文友好免费用Claude](https://scn96l2kzmbn.feishu.cn/wiki/W1gwwxPuriUgqWkOSe2cdp5BnVb)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[Codex 专区](https://scn96l2kzmbn.feishu.cn/wiki/SwpjwriB2iUUMYkSQ0ccBJ85nvd)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|
|[FUKATHON 01｜福州大学首届 AI 黑客松活动方案](https://scn96l2kzmbn.feishu.cn/wiki/AJzmwYCEQi8CSykuTjtcV0hWnfN)|部分读取|文字范围完成，嵌入/图片待补；可导出文字已读；嵌入/图片内容未完整审读|
|[扣子编程专区](https://scn96l2kzmbn.feishu.cn/wiki/AgcMwX91XiQQ2Jk9ibdcE7IMnng)|部分读取|未完成；正文已归档；未实质审读，不纳入核心来源|

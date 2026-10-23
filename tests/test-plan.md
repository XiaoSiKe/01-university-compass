# 0.3.1 验证设计与复跑方法

本轮聚焦通俗解释、逐渐增加帮助、纠错与对话连续性。真实学生试用仍未开展，历史通过结论不自动继承为新内容的证据。

## 两次冻结，分别验收

1. **初次冻结**：14 个针对性情境、26 轮实际离线回答；8 个新交互场景与 6 个保持原学生输入的回归情境。原生 4 例、6 轮，另有本机全新会话和 3 组旧版/新版对照。
2. **修复后冻结**：独立评阅发现“AI 自称用过工具就增加信心”的表述不可靠，补充证据规则后，重跑 6 个受影响情境、12 轮，包括新增 G15；重跑 2 个原生案例、4 轮及本机新会话。最终验收索引只采用本次冻结的回答，不把初次冻结的其他案例算成最终内容重测。

[完整案例目录](cases-v031.json)现有 15 个不同情境。[初次输入](v031/cases-initial.json)、[最终重测输入](v031/cases-final.json)与[最终验收范围](v031/suite.json)分别保存，范围文件的哈希绑定验收索引。首次 14 例不是在最终冻结文本上全量重跑；原记录与不利结果保留。

[原生输入](v031/discovery-cases.json)、[自然语言学习请求](v031/discovery-natural.json)及[修复后原生重测](v031/discovery-final.json)均由宿主自行发现隔离项目中的 Skill，不把全文注入提示。简单术语请求 D02 未观察到读取，不计为成功发现；D04 学习引导请求单独核对。用户级本机安装另外使用普通 CODEX_HOME 和空临时工作目录。

## 评阅与证据边界

每轮回放本案例此前真实回答，预期观察不发给被测模型。独立评阅关注眼前帮助、概念与例子是否准确、听不懂时是否改变帮助、提问/测验负担、目标更正与停止，以及独立检查时的证据边界；只讲解、代码或倾诉不强求练习。

三组 G01/G03/G07 对照使用 0.3.0 与初次冻结的 0.3.1，同一默认模型、学生输入与离线工具限制，后续分别使用真实历史。匿名映射后先评阅、再揭示：新版/旧版各一例偏好，一例各有优势。没有针对最终证据规则修订重新对照，不能把这些结果当作最终版本普遍更好。

运行完整性另外核对实际输入、历史、提示摘要、加载文本、模型、输出事件与覆盖集合，运行成功不自动获得语义通过。原生读取核对命令与输出内容；没有读命令不能反推宿主内部从未加载。全新本机探针曾因要求无格式的完整文件文本而标 FAIL，原记录不改写；补充检查核对真实输出的逐行内容、安装哈希和最终消息，详见报告。

## 最终内容的复跑入口

在项目根目录执行。模型测试有实际调用成本，默认沿用本机模型与提供者，不改变全局设置。建议省略输出参数自动创建唯一目录；指定时使用新目录。

```sh
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_package.py
python3 tests/run_behavior.py --case-file tests/v031/cases-final.json --group all --list
python3 tests/run_behavior.py --case-file tests/v031/cases-final.json --group all --jobs 6
python3 tests/run_discovery.py --cases-file tests/v031/discovery-final.json --jobs 2
python3 tests/check_behavior_integrity.py --evaluation tests/v031/evaluation.json --suite tests/v031/suite.json
python3 scripts/render_delivery.py --evaluation tests/v031/evaluation.json
```

`--group new`按 Skill 元数据版本选择对应案例文件，不依赖 ID 前缀；本版会列出 15 例，可用于下一次完整复跑，但不表示这 15 例已在最终冻结文本上全部跑过。`--case-file`可重复，`--case`、`--condition`、`--resume`保留；只有输入、版本、模型配置、被测文本和运行器指纹一致才复用记录。

初次冻结的完整安装内容保存在 [skill-initial.zip](v031/skill-initial.zip)，先解压到新的临时目录，再用 `--skill <临时目录>/01-university-compass`、`--evaluation tests/v031/evaluation-initial.json --suite tests/v031/suite-initial.json` 校验原证据。0.3.0 的对照源内容由内容冻结记录中的 Git 提交恢复。不能只改版本号或沿用当前文件冒充历史源。

离线对话固定合成日期为 2026-10-23，并等量禁用外部工具。认证只进临时私有目录，公开记录掩码用户/项目路径；排除标识从运行时参数传入。联网核查、保存、提醒、第三方 API 与后台执行不在此离线测试中验证。

## 发布与局限

先校验输入和候选 ZIP/manifest，再事务发布；失败保留旧文件，写入失败回滚。展示页严格采用验收索引指定且版本、摘要一致的回答，同目录历史计数与其他运行轮次区分。

“更顺畅”观察首次有用解释前的额外确认、重复背景询问和强制测验；实际延迟同时受模型、网络和宿主影响，不以少量耗时宣称速度提升。真实学生舒适度、长期掌握和持续使用效果仍待[自愿试用](pilot-guide.md)。历史：[0.3.0 设计](test-plan-v030.md) · [0.3.0 报告](test-report-v030.md)。

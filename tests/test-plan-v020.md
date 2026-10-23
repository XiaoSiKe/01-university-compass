> 历史设计，以下命令记录当时的默认值。当前复跑旧输入请显式使用 `--case-file tests/cases-a.json --case-file tests/cases-b.json --case-file tests/cases-v020.json --group all` 并选择新的输出目录；当前版本操作见 [test-plan.md](test-plan.md)。

> 当前发布为0.2.1，命名与视觉验收见[0.2.1记录](v021/report.md)。以下保留0.2.0教学测试的原始范围与结论。

# 0.2.0 验证设计与复跑方法

日期：2026-10-23。模型行为测试是合成情境，真实学生试用未开展；试用材料见 [pilot-guide.md](pilot-guide.md)。历史设计见 [test-plan-v010.md](test-plan-v010.md)。

## 三种证据

1. **结构与包装**：官方quick_validate及本项目scripts/validate_package.py。检查元数据、相对链接/锚点、来源ID、动态文件/卡片计数、manifest和ZIP。结构通过不代表教学有效。
2. **离线实际模型对话**：原16情境加新增22情境；至少10新情境包含3–5轮。运行器每轮新进程传入同一案例此前实际回答，不带其他案例、制作聊天或预期答案。Skill条件显式展开全部Skill Markdown；不验证按需读取。两条件外部工具均禁用。
3. **隔离安装发现**：临时安装副本中分别验证显式调用、自然语言新生需求、无关代码；保存实际读取文件证据。与全文注入的行为测试分开报告。

## 输入与输出

- [原A组](cases-a.json)、[原B组](cases-b.json)、[新增22例](cases-v020.json)。预期观察与关键失败只供评审，不发送给模型。
- `v020/behavior/<case>-<condition>/attempt-*.json`：原始回答、进程事件、工具调用、退出状态、被测文件哈希、前史长度和时间。失败尝试保留。
- `v020/evaluation.json`：逐例语义评审，按条件贴合、可用帮助、学习检验、反馈调整记录具体证据和问题。
- `v020/baseline-review.json`：六例盲评记录；比较时隐藏条件标签，揭盲后再映射，不将偏好伪装成统计效果。
- `v020/discovery/`：原生发现与读取证据；`v020/structure-results.json`：结构/包装/排除标识检查。

新增情境包含无代码/代码/研究分流、手机与无预算、工具失败、错误输出、掌握错觉、需求不成立、目标和资源更正、连续不知道、只倾诉、现实支持、证书用途、学习环境和路径后悔。实际轮数以输入JSON及报告为准。

## 语义验收

每例检查：是否利用并遵守已知条件；是否给出当前可用的帮助；有教学目标时是否用表现检查掌握；多轮反馈是否真正改变建议。明确的能力虚构、来源编造、隐含付费/设备要求、忽略更正、强迫路径、把AI代做当个人掌握、虚构已提醒/已求助等必须修复。没有检查机会的维度标为不适用，不强凑教学或行动。

六例对照固定为N01/N06/N09/N10/N14/N22，保持用户输入、模型配置和工具条件一致，仅改变是否提供Skill指导。每个条件使用自己的真实对话历史，因此后续上下文会随回答分化，这是多轮产品比较；不冒充逐token严格配对试验。每例一次运行不估计稳定可靠率。盲评若未发现增益，记录原因并调整受影响设计；不删除不利记录或凭数量宣称更优。

## 复跑

```sh
python3 scripts/validate_package.py
python3 tests/run_behavior.py --group all --jobs 4 --output tests/v020/behavior
python3 tests/run_behavior.py --group baseline --jobs 2 --output tests/v020/behavior
python3 tests/run_behavior.py --case N06 --condition both --resume --output tests/v020/behavior
python3 tests/v020/discovery/run_smoke.py --help
```

运行器使用当前用户已配置的模型与认证，在临时目录隔离，不把凭证写入交付包。先看`--help`；模型、网络或宿主不可用时记录失败，不把未完成写成通过。仅内容哈希和运行配置相同的尝试可断点续跑。修改Skill后，重跑受影响情境与结构校验；完成后使用`python3 scripts/validate_package.py --build`重新生成安装包，再运行`python3 scripts/render_delivery.py`更新可读页面。

排除标识由维护者在进程环境变量中提供JSON字符串数组，然后通过`--exclude-env 变量名`调用结构检查；不要将标识硬编码在项目脚本或测试输入中。扫描包括交付文本、JSON解码值和ZIP内部文件，报告只记录匹配路径及索引。

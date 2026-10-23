# v0.2.0 R2 最终包隔离安装与触发观察

核查日期：2026-10-23。这里保留**三个实际运行轮次**：`initial/` 为首次冻结包，`r1/` 为工具选择规则调整后的包，本级 `D01`—`D03` 及 `review.json` 为最终 R2 包。前两轮的提示、实际输出、事件、stderr、结果、人工复核和原说明均完整保留，未覆盖。`run_smoke.py` 始终留在原位。

三轮默认配置模型均为 **gpt-6.1-sol**，没有 --model 覆盖。每例为独立CLI新进程，将Skill安装到临时项目的 `.agents/skills/zeroone-university-compass`，只复制必要模型配置与临时认证。制作聊天、测试期望和历史回答不进入被测模型上下文。

## 三轮快照关系

三个轮次的discovery manifest都采用 **SHA-256原始文件字节**。与当前包比较也使用同一口径，未与行为测试的换行归一化文本哈希混比。

| 比较 | 唯一变化 | 核验结果 |
|---|---|---|
| initial → R1 | `references/ai-pathways.md`：工具选择默认新增预算0及可选短验证 | 前后哈希对应 `../revisions/resource-check-change.json` |
| R1 → R2 | `references/learning-action.md`：讲解和独立检验分开，记录提示程度 | 前后哈希对应 `../revisions/probe-check-change.json` |
| R2 → 当前最终包 | 无差异 | 三例整包manifest逐文件匹配 |

本轮实际访问的SKILL、AI路径和AI实践内容与R1相同；本轮未读取改动后的learning-action，因此这里不评价R2教学改动效果。该效果需看相关教学情境的专项复测。

## 本轮实际观察

| 场景 | R2实际文件证据 | R2回答观察 | 进程 |
|---|---|---|---|
| D01：首次显式 `$zeroone-university-compass` | 成功读取ai-pathways.md和ai-practice.md；没有单独读取SKILL.md的命令事件 | 提供原创校园新闻材料，直接进入证据核对练习 | exit 0；70.72秒 |
| D02：自然语言AI新手请求，不含Skill名称 | 成功读取SKILL.md、ai-pathways.md、ai-practice.md | 给出手机可做的练习和本人理解检查，编程按需要补 | exit 0；71.51秒 |
| D03：无关Python去重请求，只给代码 | 0次文件读取 | 仅输出函数；保序去重和空列表样例通过 | exit 0；18.72秒 |

D01只能直接证明两份参考文件被实际读取。显式入口可能经CLI注入，但日志没有直接展示该内部行为，所以不声称本轮独立证明SKILL.md被读取，也不依赖模型自称“已使用技能”。此前两轮的显式调用另有SKILL.md成功读取事件，可分别查阅。

D02一次目录枚举无匹配（exit 1）原样保留，没有影响后续读取和回复。三例均有关闭主机技能发现的开发中功能警告；本轮stderr为空，无进程重试。前两轮的失败命令和模型列表刷新超时仍在各自目录，未筛掉。

## 证据与复跑

每例保存 `prompt.txt`、`actual-response.txt`、净化的 `events.json`、`stderr.txt` 和 `result.json`；本轮人工复核见 `review.json`，前两轮分别见 `initial/review.json`、`r1/review.json`。

模型只允许读取临时项目内相关资料，read-only沙箱和外部工具关闭策略在三轮保持一致。临时目录与认证在每例结束后移除；保存输出已替换私人绝对路径，未保存认证。重跑应指定新输出目录，例如 `python3 tests/v020/discovery/run_smoke.py --jobs 3 --output tests/v020/discovery/another-round`，避免覆盖已有记录。

这些记录只说明当前CLI、默认模型和三条输入下的实际观察。三轮不是触发率实验，不保证其他措辞、模型或宿主；也不能替代多轮教学评价或真实学生试用。

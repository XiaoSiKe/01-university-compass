# 0.3.0 验证设计与复跑方法

状态：实施中，未完成的测试不得写成通过。历史范围与结论见 [0.2.0设计](test-plan-v020.md)、[0.2.0报告](test-report-v020.md) 和 [0.2.1记录](v021/report.md)。真实学生试用未开展。

## 分开保存的三类证据

1. **确定性工具链回归**：临时项目中检查构建失败保留旧包、双产物发布失败回滚、验收索引选择、防止证据覆盖，以及结构/来源/锚点/manifest/ZIP一致性。不需要模型或真实外部写入。
2. **实际离线模型对话**：原38情境加V01—V10，共48个Skill情境；新10例中8例为3轮。原输入不改写，预期观察不发送给被测模型。每轮新进程回放本例此前真实回答，所有Skill Markdown显式加载，不能据此证明按需读取或安装发现。
3. **原生发现与教学**：4个独立案例（显式、自然语言、无关代码、多轮教学）。只把Skill副本安装到隔离目录，由宿主发现；不注入正文。记录实际成功读取路径、文件哈希、每轮回答与工具证据。多轮输入回放此前真实回答，不带制作对话或评审结论。

行为案例见 [新增10例](cases-v030.json)、[原A组](cases-a.json)、[原B组](cases-b.json)、[0.2.0新增组](cases-v020.json)。原生案例见 [4例输入](v030/discovery-cases.json)。所有学生输入均为合成情境，不是学生试用。

## 四组条件隐藏对照

固定比较V01（核验无误）、V03（独立迁移）、V05（AI适用性）、V06（固定流程与Agent）。同一默认模型、用户输入和离线工具限制，仅改变是否提供Skill。后续历史分别使用各自真实回答，因此是多轮产品比较，后续上下文不保证逐字相同。

评阅材料随机映射为A/B并去掉条件与路径，不提供映射给评阅者；完成四例评阅后再揭示映射。记录具体依据与局限，不用偏好评分推导统计效果；负向或无增益结果如实保留。评分关注条件贴合、当前可用帮助、掌握检查和反馈是否导致调整。

## 语义验收与失败处理

严重问题包括来源/能力编造、未核实承诺付费或平台条件、忽略用户更正、强迫路径、把有提示完成算独立掌握、强行给正确材料找错、将证据不足当证伪、虚构工具运行/提醒/保存等。不是每一轮都需要提问或练习；纯代码、倾诉等维度可不适用。

进程退出0、回答非空只是运行完整性，不自动判语义通过。由独立评阅者核对实际输出，保存逐例证据。失败记录保留；修复后只重测受影响情境，记录前后版本与采用依据。未经评审的成功尝试或较新的失败尝试不得挤掉验收索引明确采用的回答。

## 复跑入口

```sh
python3 -m unittest discover -s tests -p 'test_tooling.py'
python3 scripts/validate_package.py
python3 tests/run_behavior.py --group all --list
python3 tests/run_behavior.py --group all --jobs 6 --output tests/v030/behavior/r0
python3 tests/run_behavior.py --group baseline --jobs 4 --output tests/v030/behavior/r0
python3 tests/run_discovery.py --cases-file tests/v030/discovery-cases.json --output tests/v030/discovery/r0
```

行为运行器保留`--case`、`--condition`、`--resume`，新增`--case-file`和`--baseline-id`以显式复跑历史集合；只有输入、模型配置、被测文本和运行器指纹一致才复用已完成轮次。未指定输出目录时生成当前版本唯一run目录，原生发现的非空目标拒绝覆写。

模型沿用本机已配置的默认模型与提供者，不硬编码模型、不改用户全局设置。认证只进入临时私有目录，不发布到仓库。保存时掩码项目/用户绝对路径及运行时指定的排除标识；模型回答其余内容保留，输出净化范围在完整性报告中说明。断网、超时、额度或宿主异常均记录实际失败，不补写结果。

## 打包和展示

内容冻结后先校验，再生成候选manifest与ZIP，复核候选后发布；校验失败不改变旧包，发布写入失败回滚两份产物。通过语义评审后写入当前验收索引：version、raw文件manifest的skill_digest、每例case/condition/artifact/status及artifact_sha256；artifact相对索引目录，Skill和基线都显式列出。

```sh
python3 scripts/validate_package.py --build
python3 scripts/render_delivery.py --evaluation tests/v030/evaluation.json
```

排除标识由运行时JSON数组环境变量经`--exclude-env`传入，不写入脚本、案例或发布文件；扫描交付文件及ZIP内部。README与说明页中的版本和实际计数一起核对，历史数字须标明历史版本。

本轮不验证真实联网能力、后台任务、真实学生长期学习结果或职业收益。学生自愿试用入口见 [pilot-guide.md](pilot-guide.md)。

# 一起改进零一大学指南针

欢迎参与文字纠错、使用体验反馈、方法与任务卡优化、资料核实、测试用例及维护工具改进。

## 先选一种参与方式

- 发现问题：到 [Issues](https://github.com/XiaoSiKe/01-university-compass/issues/new/choose) 说明具体位置、复现方式或改进建议。
- 交流想法：到 [Discussions](https://github.com/XiaoSiKe/01-university-compass/discussions) 分享体验，或讨论还没形成修改方案的想法。
- 已有小修改：可以直接提交 PR。大幅调整结构、教学方法或打包流程前，建议先开 Issue 对齐范围。

反馈真实对话时，请先移除姓名、联系方式、账号凭证和未获授权公开的个人材料。

## 提交第一个 PR

1. 登录 GitHub，在仓库右上角点击 **Fork**，创建自己的副本。无需申请原仓库的协作者权限。
2. 在自己的 Fork 中新建分支，例如 `docs/fix-typo` 或 `fix/package-check`，不要把不同主题的修改混在一起。
3. 修改文件并提交。简单文字修改可以直接使用 GitHub 网页编辑器；需要运行脚本时，将自己的 Fork 克隆到本地。
4. 在自己的 Fork 点击 **Contribute → Open pull request**，确认目标为 `XiaoSiKe/01-university-compass` 的 `main`。
5. 按模板说明解决什么问题、改了什么、怎样检查。尚未完成时可以提交 Draft PR。
6. 根据反馈继续提交到同一分支，PR 会自动更新。由维护者审核并决定合并。

## 修改哪些文件

| 内容 | 位置 |
| --- | --- |
| Skill 入口与调用说明 | `01-university-compass/SKILL.md`、`01-university-compass/agents/openai.yaml` |
| 方法、任务卡、示范与资料来源 | `01-university-compass/references/` |
| 面向使用者的介绍与安装说明 | `README.md` |
| 校验、打包和交付脚本 | `scripts/` |
| 测试用例、工具回归与验证记录 | `tests/` |
| 资料登记与覆盖记录 | `research/`、`coverage-report.md` |

新增研究结论或外部材料时，注明可核实的出处、采用范围和适用边界。区分来源结论、项目自己的设计及尚未验证的设想；不要把历史测试记录改写成新版本已经通过的证据。

## 提交前检查

纯文字、排版或协作模板修改，检查文字、相对链接和网页预览即可，并在 PR 中说明检查结果。

修改 Skill 内容或 Python 工具时，使用 **Python 3.9 或更新版本**，在仓库根目录运行：

```sh
python3 scripts/validate_package.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

如果修改了 Skill 内容，校验器可能提示安装包或清单与源码不一致。先完成源码检查，再运行：

```sh
python3 scripts/validate_package.py --build
```

将与修改对应的 `01-university-compass.zip` 和 `skill-manifest.json` 一并提交。版本发布及交付报告更新由维护者统筹；不要为了让检查通过而手工伪造清单、测试输出或历史评阅。

涉及教学行为变化时，说明一个具体的用户输入、预期行为和实际观察。模型相关验证的方法见 [测试设计](tests/test-plan.md)，没有运行的检查请如实标为未运行。

## 审核与权限

`main` 为受保护分支，普通写入者需要通过 PR，并获得代码所有者审核后合并；未解决的审查讨论需要先处理。当前代码所有者为 [@XiaoSiKe](https://github.com/XiaoSiKe)，管理员保留应急处理权限。

公众使用 Fork 和 PR 即可参与；直接向原仓库推送代码需要维护者单独授予权限。请围绕具体问题交流，尊重参与者与不同基础的使用者。

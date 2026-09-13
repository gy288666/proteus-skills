# 库的安装、更新与分发

环境准备是 Proteus Skills 的第一步。用户只需具备 Proteus 和可调用 skill 的 AI 工具；Agent 检查 Python，并在需要时安装 `proteus-automatic-api` 后继续电路任务。技能仓库和 Python 库独立维护，安装不依赖两者相邻，也不依赖开发者电脑上的文件。

## 固定来源

| 项目 | 值 |
|---|---|
| 技能 / 调用名 | Proteus Skills / `$proteus-skills` |
| Python 分发名 / 导入名 | `proteus-automatic-api` / `proteus_automatic_api` |
| 官方 GitHub 仓库 | https://github.com/kudoumakoto6523-design/Proteus_automatic_package |
| 默认安装来源 | 官方仓库默认分支的最新提交，解析为 SHA 后安装源码 ZIP |
| PyPI | 后续分发渠道；本工作流不等待 PyPI 更新 |

“自动找到库”指读取这个固定地址的 GitHub 元数据，不是按包名搜索任意仓库。仓库路径仍为 `Proteus_automatic_package`；不要自行改成尚未确认的 `proteus-automatic-api` URL。源码 ZIP 安装不需要 Git；pip 会处理 `pyproject.toml` 声明的构建依赖。

## 首次安装与更新

1. 从用户任务目录检查 Python 3.10+，推荐已验证的 3.12。可先检查 `py -0p`、`python --version`，选择实际可用的解释器；缺少 Python 时协助从 [Python 官方来源](https://www.python.org/downloads/windows/) 安装。不要把文档中的 `py -3.12` 当成所有电脑上都存在的命令。
2. 优先复用任务已有虚拟环境，检查库的导入、版本、来源和任务所需方法；可用就继续。缺少库时默认创建任务专用 `.venv-proteus`。若该目录已存在，先验证其中的解释器，不能覆盖不明目录。安装和运行均使用这个环境的 Python，不要求激活环境，不修改 `PYTHONPATH` 来引用库源码。
3. 查询下面的固定仓库及其默认分支，取得本次安装的提交 SHA。安装前读取同一 SHA 下的 `pyproject.toml` 和 `api/proteus_automatic_api.py`，确认 `[project].name` 为 `proteus-automatic-api` 且公开入口存在，并按任务核对对应文档。元数据或入口不匹配时停止安装，报告仓库尚未发布兼容代码，不能改装其他包冒充成功。
4. 从该 SHA 的 ZIP 安装。用户要求更新或旧构建缺少所需能力时，重新查询 SHA；即使版本号未变，也可用 `--force-reinstall` 安装新提交。已有可用环境不需要每次重装；不更改用户固定的版本，不在原生会话运行期间更新。
5. 检查安装退出码、导入、版本、模块路径、pip 记录的来源以及所需接口。通过后继续用户原本的电路任务，并在任务结果中记录解释器与提交 SHA。网络或构建失败时保留具体错误，不自动换镜像、第三方仓库或较旧的 PyPI 包。

## 执行环境准备脚本

Agent 必须实际执行 [ensure_library.py](../scripts/ensure_library.py)，不能把下列命令交给用户后结束。将 `$ProteusSkill` 设为本技能目录的绝对路径，在用户任务目录运行；Python 命令替换为本机已确认可用的解释器。

```powershell
$ProteusSetupText = py -3.12 "$ProteusSkill/scripts/ensure_library.py"
if ($LASTEXITCODE -ne 0) { throw "环境准备失败，请检查安装错误" }
$ProteusSetup = $ProteusSetupText | ConvertFrom-Json
$ProteusPython = $ProteusSetup.python
```

脚本自动检查已有库；缺少时创建或使用任务虚拟环境、查询官方 GitHub 最新提交、安装源码 ZIP，并验证包名、公开导入及安装来源。标准输出的 JSON 返回 `action`、`python`、`version`、`module`、`source`；本次安装还返回 `commit`。安装日志写入标准错误。

随后使用 `$ProteusPython` **继续用户原本的任务**，不要以“环境已就绪”结束。已有项目继续编辑，新建需求继续创建工程。后续命令统一用 `& $ProteusPython`，避免又回到没有库的全局 Python。

任务明确指定环境时可传 `--venv <环境路径>`；已有目录不是有效虚拟环境时脚本拒绝覆盖。已有可用库默认复用；用户要求更新或任务缺少所需接口时执行：

```powershell
$ProteusSetupText = & $ProteusPython "$ProteusSkill/scripts/ensure_library.py" --update
if ($LASTEXITCODE -ne 0) { throw "GitHub 更新失败" }
$ProteusSetup = $ProteusSetupText | ConvertFrom-Json
$ProteusPython = $ProteusSetup.python
```

脚本不安装 Proteus，也不替代具体电路的模型、网表和响应验证。安装失败时报告实际错误；能修复的依赖或路径问题先修复，再继续任务。

## 已有环境与离线安装

默认新建的任务虚拟环境不会与全局旧包冲突。如果必须迁移装有旧发行包的同一环境，先准备好新安装源，再用该环境的解释器卸载旧包，随后安装新包；两个包共享内部模块，不能先并装再卸载旧包。将任务脚本导入改为 `proteus_automatic_api`，不改用户无关项目。

只有用户明确提供离线 wheel 时才走离线路径，用同一解释器执行 `-m pip install --force-reinstall --no-index --no-deps <wheel绝对路径>` 并验证导入。普通首次使用不能以“请提供 wheel”结束，也不要在技能目录执行 `pip install .` 或安装同名的 `proteus-skills` Python 包。

## 验证范围

操作示例验证基线为 Python 3.12、Proteus 8.16 SP3（8.16.36097）、`proteus-automatic-api 0.2.0`。布局任务检查 `Circuit.update` 是否支持 `label_offsets`；从 MCU 模板新建任务还需根据对应提交文档确认模板旧固件项目不会覆盖新固件，并通过保存重开和实际固件响应验证。新提交、相同版本号和安装成功都不能替代这些检查。

历史三组 STM32 演示的 wheel SHA-256 为 `5b0d1ae5aa5e38478d1c8754c06ca21a162e16c7f8bfa27b2f6f2f7d0b96ad75`，证据在 [verification.json](../examples/stm32/verification.json)。该哈希用于复核已有演示，不是 GitHub 源码安装的哈希要求，也不阻止安装维护者的新提交。

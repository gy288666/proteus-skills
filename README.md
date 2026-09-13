# Proteus Skills

**简体中文** | [English](README.en.md)

[![MIT Licensed](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat-square)](LICENSE)

让 AI Agent 通过 Python 创建、编辑和验证真实的 Proteus 电路工程。

Proteus Skills 提供原理图编辑、单片机仿真、按钮与开关控制、波形读取的工作流。Agent 根据任务调用 [proteus-automatic-api](https://github.com/kudoumakoto6523-design/Proteus_automatic_package)，交付可继续编辑的 `.pdsprj`、验证脚本及实际仿真结果。

本仓库维护 skill 的指令与参考示例；Python 库在独立仓库维护，需单独安装。两者不需要放在相邻目录。

## 环境要求

- **Windows**，已安装 Proteus 及电路所需的器件模型。
- **Python 3.10+**，已安装 **proteus-automatic-api 0.2.0**，导入名为 `proteus_automatic_api`。
- **Codex**：下文提供 Codex 的 skill 安装和调用方式。

当前工作流已在 **Python 3.12 / Proteus 8.16 SP3（8.16.36097）** 上验证。定时仿真和交互控制有 Proteus DLL 版本限制，其他构建的兼容性尚未验证。Proteus 软件、模型、官方样例和固件不随本技能分发。

## 安装

### 1. 安装 Python 库

已安装旧名 `proteus-native` 的环境，请先按[迁移说明](references/distribution.md#独立安装)卸载旧包，再安装新包；两个分发包共享内部模块。

准备来源明确的 `proteus_automatic_api-0.2.0-py3-none-any.whl`，将 PowerShell 变量 `$ProteusWheel` 设为该文件的绝对路径，再执行：

```powershell
py -3.12 -m pip install --no-index --no-deps "$ProteusWheel"
py -3.12 -I -c "import proteus_automatic_api; assert proteus_automatic_api.__version__ == '0.2.0'; print(proteus_automatic_api.__file__)"
```

使用其他 Python 版本时，安装和运行须使用同一个解释器。已安装匹配版本可跳过此步。

库的当前远程仓库为 [Proteus_automatic_package](https://github.com/kudoumakoto6523-design/Proteus_automatic_package)，本技能使用改名后的 `proteus-automatic-api`。若下载页面仍提供旧名安装包，请先取得上面指定的新 wheel。新包的公开下载地址及 PyPI 发布状态尚未确认，当前采用本地 wheel 安装。

### 2. 安装 skill

在 Codex 中发送：

```text
使用 $skill-installer 安装 https://github.com/kudoumakoto6523-design/proteus-skills
仓库根目录就是技能目录，安装名称使用 proteus-skills。
```

也可以手动下载本仓库，将 `SKILL.md`、`agents/`、`references/` 和 `LICENSE` 放入同一个 `proteus-skills` 文件夹，再放到 Codex 的 `$CODEX_HOME/skills/` 下；默认位置为 `~/.codex/skills/proteus-skills/`。安装后，技能入口应位于 `proteus-skills/SKILL.md`。

安装完成后，在下一轮对话中使用 `$proteus-skills` 调用。

## 使用前准备

向 Agent 提供任务所需的工程或模板、Proteus 程序位置、输出目录；涉及 MCU 时再提供固件和目标引脚。新建电路需要含相应器件定义的模板，例如电阻、电容示例使用官方 `Rescap.pdsprj`。

这些资源使用本机实际路径，输出写入你的工作目录。库的内置路径不会自动适配所有安装位置；路径参数和已知限制见 [SKILL.md](SKILL.md#环境与版本)。

## 使用示例

### 创建并检查电路

```text
$proteus-skills
使用本机可用的 Rescap 模板，新建一个含 R1（10k）、C1（100n）的工程。
连接 R1.2 与 C1.2，将 C1.1 接地，保存到当前工作目录的 proteus-output 中。
重开工程检查元件值和连接，并用 Proteus 导出 SDF 网表。
交付工程、网表和可重跑的 Python 脚本。
```

该示例用于验证工程文件和连接；进行 RC 电气仿真还需要配置输入源等条件。

### 验证按钮与固件响应

```text
$proteus-skills
检查我提供的 STM32 工程和固件，确认 SW1 按钮与目标输入引脚的连接。
在工程副本中加载固件，运行后按下 SW1，保持 0.1 秒，再松开。
继续仿真并读取 PA5 的 GPIO 事件，验证输出是否随按钮改变。
记录按下、松开和输出变化的实际仿真时间。
```

### 导出已有波形

```text
$proteus-skills
检查我提供的工程中已有的图表和探针，运行对应分析并导出波形 CSV。
列出实际可用的电压、电流曲线，给出指定时刻的采样值和输出文件路径。
```

## 能力范围

| 任务 | 支持的工作流 |
| --- | --- |
| 工程编辑 | 新建或打开受支持的 `.pdsprj`，修改元件、属性、位置、连线和端子，保存并重开验证 |
| 连接检查 | 查询器件和引脚，导出 Proteus 原生 SDF 网表，核对网络连接 |
| MCU 仿真 | 检查和加载 ELF / HEX 固件，启停、暂停、按时长运行，读取支持的 GPIO 日志 |
| 按钮与开关 | 绑定二态控件，执行按下、松开、切换，并继续仿真验证下游响应 |
| 波形读取 | 基于已有图表和探针导出 CSV，读取电压、电流和采样值 |

文件编辑使用 Python 库，网表和仿真由真实 Proteus 进程完成。主要工作流不依赖 MCP、OCR 或屏幕坐标。

## 已知限制

- 结构编辑支持已识别的单用户页、CDB v7、FILEVER 840/847；未知对象、多页和多单元结构可能被拒绝重写。
- 器件可查询不代表可导入或可仿真；自动布线只覆盖有限的正交路径。
- 当前支持六类二态控件，共用 10 个执行器键槽，每个控件占两个，最多绑定 5 个；其他已有绑定会减少容量。
- 模拟量读取依赖已有图表和探针；尚无通用 ERC、任意图表/探针创建、通用实时引脚电压读取或原理图图片导出接口。

按钮状态、网表连接和实际电气响应分别验证。Agent 只应依据本次生成的工程、日志和数据报告结果。

## 仓库内容

| 文件 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | Agent 的技能入口、任务选择、操作顺序和验证要求 |
| [agents/openai.yaml](agents/openai.yaml) | Codex 中的显示名称和简短说明 |
| [references/api-workflows.md](references/api-workflows.md) | 工程编辑、网表、固件和测量示例 |
| [references/interactive-controls.md](references/interactive-controls.md) | 按钮与开关的绑定、时序和响应验证 |
| [references/distribution.md](references/distribution.md) | 库的安装、版本匹配、迁移和独立分发约定 |

## 许可证

本仓库的原创技能文档和示例采用 [MIT License](LICENSE)。Python 库单独分发；Proteus 软件、器件模型、第三方样例和固件适用各自的许可证。

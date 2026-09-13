# Proteus Skills

[简体中文](README.md) | **English**

[![MIT Licensed](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat-square)](LICENSE)

Let AI agents create, edit, and verify real Proteus circuit projects through Python.

Proteus Skills provides workflows for schematic editing, microcontroller simulation, button and switch control, and waveform extraction. Agents use [proteus-automatic-api](https://github.com/kudoumakoto6523-design/Proteus_automatic_package) to deliver editable `.pdsprj` projects, verification scripts, and actual simulation results.

This repository contains the skill instructions and reference examples. The Python library is maintained in a separate repository and must be installed separately. The two repositories do not need to be in adjacent directories.

## Requirements

- **Windows**, with Proteus and the device models required by your circuit installed.
- **Python 3.10+**, with **proteus-automatic-api 0.2.0** installed. The Python import name is `proteus_automatic_api`.
- **Codex**: the instructions below cover installing and invoking the skill in Codex.

The workflows have been verified with **Python 3.12 / Proteus 8.16 SP3 (8.16.36097)**. Timed simulation and interactive controls require supported Proteus DLL versions; compatibility with other builds has not been verified. Proteus software, models, official samples, and firmware are not bundled with this skill.

## Installation

### 1. Install the Python library

If your environment has the old `proteus-native` package installed, follow the [migration instructions](references/distribution.md#独立安装) to uninstall it before installing the new package. Both distributions share internal modules.

Obtain `proteus_automatic_api-0.2.0-py3-none-any.whl` from a known source and set the PowerShell variable `$ProteusWheel` to its absolute path. Then run:

```powershell
py -3.12 -m pip install --no-index --no-deps "$ProteusWheel"
py -3.12 -I -c "import proteus_automatic_api; assert proteus_automatic_api.__version__ == '0.2.0'; print(proteus_automatic_api.__file__)"
```

If you use another Python version, use the same interpreter for installation and execution. Skip this step if the matching version is already installed.

The library's current remote repository is [Proteus_automatic_package](https://github.com/kudoumakoto6523-design/Proteus_automatic_package); this skill uses the renamed `proteus-automatic-api` package. If the download page still offers the old package, obtain the new wheel specified above first. A public download URL and PyPI publication for the renamed package have not been confirmed, so these instructions use a local wheel.

### 2. Install the skill

Send this request in Codex:

```text
Use $skill-installer to install https://github.com/kudoumakoto6523-design/proteus-skills
The repository root is the skill directory. Install it with the name proteus-skills.
```

Alternatively, download this repository and place `SKILL.md`, `agents/`, `references/`, and `LICENSE` together in a folder named `proteus-skills` under Codex's `$CODEX_HOME/skills/`. The default location is `~/.codex/skills/proteus-skills/`. The installed entry point should be `proteus-skills/SKILL.md`.

After installation, invoke `$proteus-skills` in your next message.

## Before you start

Provide the agent with the project or template, the Proteus executable location, and an output directory. For MCU tasks, also provide the firmware and target pins. Creating a circuit requires a template containing the relevant device definitions; the resistor and capacitor example uses the official `Rescap.pdsprj` sample.

Use actual paths on your machine. Outputs belong in your working directory. The library's built-in paths do not automatically adapt to every installation; see [SKILL.md](SKILL.md#环境与版本) for path parameters and known limitations.

## Usage examples

### Create and verify a circuit

```text
$proteus-skills
Use the Rescap template available on this machine to create a project with R1 (10k) and C1 (100n).
Connect R1.2 to C1.2, ground C1.1, and save the project under proteus-output in the current working directory.
Reopen the project to check component values and connections, then export an SDF netlist using Proteus.
Deliver the project, netlist, and a rerunnable Python script.
```

This example verifies the project file and connections. Electrical simulation of the RC circuit requires additional setup, including an input source.

### Verify button and firmware responses

```text
$proteus-skills
Inspect the STM32 project and firmware I provided, and check the connection between SW1 and the target input pin.
Load the firmware into a copy of the project, start the simulation, press SW1, hold it for 0.1 seconds, then release it.
Continue the simulation and read PA5 GPIO events to verify whether the output follows the button.
Record the actual simulation times of the press, release, and output transitions.
```

### Export existing waveforms

```text
$proteus-skills
Inspect the existing graphs and probes in the project I provided, run the corresponding analysis, and export waveform CSV files.
List the voltage and current traces actually available, report their sampled values at the requested times, and provide the output file paths.
```

## Capabilities

| Task | Supported workflow |
| --- | --- |
| Project editing | Create or open supported `.pdsprj` files; edit components, properties, positions, wires, and terminals; save and reopen for verification |
| Connectivity checks | Query devices and pins, export native Proteus SDF netlists, and verify network connections |
| MCU simulation | Inspect and load ELF / HEX firmware; start, stop, pause, and run for a specified duration; read supported GPIO logs |
| Buttons and switches | Bind binary controls, press, release, or toggle them, and continue simulation to verify downstream responses |
| Waveform extraction | Export CSV data from existing graphs and probes, and read voltage, current, and sampled values |

The Python library edits project files. Real Proteus processes generate netlists and run simulations. The main workflows do not depend on MCP, OCR, or screen coordinates.

## Known limitations

- Structural editing supports recognized single-user-sheet projects with CDB v7 and FILEVER 840/847. Rewriting projects with unknown objects, multiple sheets, or multi-unit structures may be rejected.
- Finding a device in the library does not establish that it can be imported or simulated. Automatic routing covers a limited set of orthogonal paths.
- Six types of binary controls are supported. They share 10 actuator key slots, using two slots per control, for a maximum of five controls. Existing bindings reduce the available capacity.
- Analog measurements require existing graphs and probes. There is no general ERC, arbitrary graph or probe creation, general live pin-voltage reading, or schematic image export API.

Control state, netlist connectivity, and actual electrical response are verified separately. Agents should report results supported by the projects, logs, and data produced for the current task.

## Repository contents

The skill instructions and detailed workflow references are currently written in Chinese.

| File | Purpose |
| --- | --- |
| [SKILL.md](SKILL.md) | Agent entry point, task selection, operation order, and verification requirements |
| [agents/openai.yaml](agents/openai.yaml) | Display name and short description in Codex |
| [references/api-workflows.md](references/api-workflows.md) | Examples for project editing, netlists, firmware, and measurements |
| [references/interactive-controls.md](references/interactive-controls.md) | Button and switch binding, timing, and response verification |
| [references/distribution.md](references/distribution.md) | Library installation, version matching, migration, and separate distribution conventions |

## License

The original skill documentation and examples in this repository are licensed under the [MIT License](LICENSE). The Python library is distributed separately. Proteus software, device models, third-party samples, and firmware remain subject to their respective licenses.

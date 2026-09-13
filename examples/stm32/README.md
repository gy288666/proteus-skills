# STM32 demonstrations / STM32 演示

三个场景共用 STM32F103R6：按住点灯、单击切换、双按键独立点灯。仓库提供原创 C 与 HEX，以及只调用公开 API 的构建/验证脚本；官方工程和器件模型需要本机另行安装。

Three STM32F103R6 examples: hold to light, press to toggle, and two independent buttons/LEDs. This folder includes original C/HEX files and public-API build/verification scripts. Install the official project and device models locally.

需要 Windows、Proteus 8.16、Python 3.12，以及支持演示接口的库构建和 Pillow（被动录制/编码）。先按[安装工作流](../../references/distribution.md#首次安装与更新)准备环境，将 `$ProteusPython` 设为该环境 Python 的绝对路径；随后在此目录运行，输出目录必须是新的。

Requires Windows, Proteus 8.16, Python 3.12, a library build supporting the demo APIs, and Pillow for passive capture/encoding. Follow the [installation workflow](../../references/distribution.md#首次安装与更新) first and set `$ProteusPython` to that environment’s absolute Python path. Run from this directory and use fresh output directories.

```powershell
# Normalize a disposable copy of the installed sample through the public API.
& $ProteusPython -I normalize_template.py --sample "C:\ProgramData\program\SAMPLES\VSM for Cortex M3\STM32\STMCubeMX LED Blink\STMCubeMX LED Blink.pdsprj" --executable "D:\Proteus\BIN\PDS.EXE"

# Record every construction step, then verify the actual MCU response.
& $ProteusPython -I stm32_showcase.py hold output-hold --record
& $ProteusPython -I stm32_showcase.py toggle output-toggle --record
& $ProteusPython -I stm32_showcase.py dual output-dual --record

# Encode native screenshots only, without waiting cards or added overlays, at 6x.
& $ProteusPython -I record.py encode output-hold/recording hold.gif
& $ProteusPython -I record.py encode output-toggle/recording toggle.gif
& $ProteusPython -I record.py encode output-dual/recording dual.gif
```

安装位置不同时，传入实际 `--sample`、`--executable`；构建脚本还接受 `--template`。省略 `--record` 可仅构建和验证。`result.json`、SDF 和 `simulation.log` 保留本次真实结果；录制目录另存原始帧和同步调用时间。日志读取使用系统剪贴板。

Pass your actual `--sample` and `--executable` paths; the build script also accepts `--template`. Omit `--record` to build and verify without recording. Each run retains `result.json`, its SDF and `simulation.log`; recordings also retain native frames and synchronized API timestamps. Log extraction uses the system clipboard.

发布的 GIF 只保留 Proteus 原生界面和原生配置对话框，不添加外框、标题或 API/结果说明。没有匹配窗口的等待段及其时长已剪去，全部真实窗口帧按原顺序保留，统一 6 倍速，末帧额外停留 2 秒。实际选件查询、结果和操作时间保留在完整原始录制及事件日志中。

The published GIFs show only the native Proteus interface and configuration dialogs, with no added border, title, or API/result overlay. Waiting intervals with no matching window and their elapsed time are removed; every captured real-window frame remains in order at 6× speed, with an extra 2-second final-frame hold. Actual selection queries, results and operation times remain in the complete original recordings and event logs.

| HEX | 输入 / Input | 输出验证 / Expected output |
|---|---|---|
| [hold.hex](firmware/hold.hex) | SW1 → PA0 | PA5: 0 → 1 → 0 → 1 → 0 |
| [toggle.hex](firmware/toggle.hex) | SW1 → PA0, rising edge | PA5: 0, 1, 1, 1, 0, 0 |
| [dual.hex](firmware/dual.hex) | SW1 → PA0; SW2 → PA1 | (PA5, PA6): 00 → 10 → 11 → 01 → 00 |

固件使用内部下拉与推挽输出，采样循环用于理想仿真按钮，未实现物理按键去抖。已附 HEX 可直接运行；重新编译时，将 GNU Arm Embedded 工具加入 PATH，再运行 `& $ProteusPython -I firmware/build.py`，它会检查 ELF/HEX 内容、校验和及复位向量。

The firmware uses internal pull-downs and push-pull outputs. Its sampling loop targets ideal simulated buttons and does not implement physical switch debounce. The included HEX files are ready to use. To rebuild, place GNU Arm Embedded tools on PATH and run `& $ProteusPython -I firmware/build.py`; it checks ELF/HEX payloads, checksums and reset vectors.

完整双语提示词见 [prompts.json](prompts.json)。
Full bilingual prompts are in [prompts.json](prompts.json).

这些已验证提示词用于完整构建和原始录制；发布 GIF 按上面的画面与剪辑说明处理。
The verified prompts cover the full build and original recording; published GIFs follow the display and editing rules above.

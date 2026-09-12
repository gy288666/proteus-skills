# Proteus Skills：按钮、开关与逻辑输入

使用 `proteus-automatic-api 0.2.0` 的公共 API。支持 `BUTTON`、`SW-SPST`、`SW-SPST-MOM`、`SWITCH`、`LOGICSTATE`、`LOGICTOGGLE` 六类二态输入。需要真正的电源、连接和仿真模型；MCU 响应还需要匹配的固件。

## 先绑定，再保存重开

对用户提供、已连接好的 `BUTTON` 元件 SW1，先将 `control_project_path` 设为工程路径，将 `executable_path` 设为已确认的 PDS.EXE 路径。普通电路和 MCU 电路均可使用此流程；工程、固件和器件模型不随技能附带：

```python
from proteus_automatic_api import Circuit

c = Circuit.open(control_project_path)
print(c.components(), c.pins("SW1"))
c.bind_controls("SW1")
project = c.save("button_bound.pdsprj")
```

新建控件先 `import_device()` 再 `add()`，添加后用 `pins()` 查实际端点；例如 BUTTON 与 SW-SPST 的引脚名称不同，不能都写成 `.1/.2`。`bind_controls(*refs)` 返回 Circuit，可连续调用，但每次只选择本次要分配的控件。

- 当前 Proteus 工程共享 0–9 十个执行器键槽，两个槽用于一个控件的 INC/DEC，最多五个控件；其他元件的 INC、DEC、KEY 会占槽。命令发给自有 Session，不是发送系统全局键盘输入。
- `bind_controls("SW1", "SW2")` 保留非目标元件的已有占用，重新分配目标的 INC/DEC，并清除目标的 KEY。重复引用、未知引用、不支持器件、非法键槽或容量不足会在提交前拒绝，保持 Circuit 不变。
- 用 `c.components()` 的 `properties` 查看文件中的绑定；没有单独的 `control_bindings()` API。不要为获得槽位擅自清除其他元件的键绑定。
- **绑定修改必须保存，并用新的 Session 重开。** 已打开的 Proteus 缓存原绑定，`Session.set_properties(..., INC=..., DEC=...)` 不能完成刷新。先结束旧会话，再保存绑定、重开；不让旧 Session 覆盖新文件。

## 操作并记录实际时序

在上一段已准备的 `project` 上运行。示例验证控件状态；它本身不证明下游电气或 MCU 响应。

```python
from proteus_automatic_api import Session, Simulation

s = Session(project, executable=executable_path)
sim = Simulation(s)
try:
    controls = {item["ref"]: item for item in sim.controls()}
    assert controls["SW1"]["bound"]
    initial = sim.run_for(0.01)  # 先启动，成功后处于暂停点
    pressed = sim.press("SW1")
    assert sim.control_state("SW1") == 1
    assert sim.press("SW1")["changed"] is False
    held = sim.run_for(0.1)
    released = sim.release("SW1")
    assert sim.control_state("SW1") == 0
    settled = sim.run_for(0.01)  # 给电路/固件处理松开输入的时间
    print({"pressed": pressed, "released": released,
           "actual_hold_seconds": released["command_time_seconds"] - pressed["command_time_seconds"],
           "runs": [initial, held, settled]})
    sim.stop()
    s.save()
finally:
    try:
        sim.stop()
    finally:
        s.close()
```

若操作失败，按主入口的会话清理规则保留原错误和 `s.pid`；测试脚本才可清理自己的可丢弃进程。

| 接口 | 语义 |
|---|---|
| `controls()` | 返回支持控件的 `ref`、`device`、`state`、`kind`、`bound`；kind 是 momentary 或 latched |
| `control_state(ref)` | 返回控件当前位置/逻辑输入的 0 或 1，不导出网表 |
| `press(ref)` | 设为 1 并保持，不是自动按下后松开的 click，也没有 duration 参数 |
| `release(ref)` | 设为 0 |
| `set_switch(ref, closed)` | 参数必须是 `True`/`False`；`1`/`0` 不被接受 |

修改接口要求仿真正在运行或暂停，停止状态不能操作。原本连续运行时，读取和修改都会短暂停住，完成后恢复；原本暂停时保持暂停。只读接口在停止状态不启动仿真。频繁读取会影响墙钟执行速度，不能把它描述为完全不干扰运行的采样。同一 Session 串行调用，避免并发暂停/恢复相互干扰。

修改返回 `ref`、`state`、`changed`、`command_time_seconds`；已在目标状态时 `changed=False`，不重复派发。`bound=True` 只说明已加载 INC/DEC，不保证没有全局冲突；实际命令仍检查缓存和与所有元件（包括不对外暴露的控件）的键冲突。

`command_time_seconds` 是命令所在暂停点的实际仿真时间。按住时长用 press/release 两次该字段的差值；不要直接把请求的 `run_for(0.1)` 当作精确 100 ms。调度超出量和两种 `completion` 见 [单片机仿真](api-workflows.md#单片机仿真)。

## 验证下游响应

`control_state()==1` 只证明输入状态，不证明下游引脚电压、MCU 已读到输入或输出已变化。命令之后继续仿真，再读取实际 GPIO 日志或已有图表；同时保留命令时间与响应事件时间。接口并未新增通用 `probe_voltage()`、`read_pin()` 或强制任意引脚输入。

STM32 CM3 可用 `sim.gpio_events(ref=..., port=..., pin=...)` 或读取一次 `sim.log()` 后用 `gpio_events(log, ...)` 解析。检查目标响应确实出现在输入变化后的时间区间，并且电平/顺序符合固件；无日志事件不能视为低电平。日志读取会替换系统剪贴板，执行前简短告知。

例如，用户提供的固件若实现“读取 PA0 并驱动 PA5”，且按钮松开使 PA0 为低、按下使 PA0 为高，则在初始、按下后、松开后三段仿真中分别核对 PA5 的 0→1→0 及响应时间区间。其他工程的预期按实际固件和接线确定。不能假定本技能或 wheel 包含可用 HEX、已接线的演示工程或官方样例；需要演示资源时只使用发布者另外提供或用户指定的文件。

## 兼容性和失败定位

交互检查 ISIS.DLL、NETLIST.DLL、PRIMS.DLL 的已验证 8.16 指纹；命令时间还要求已验证的 WINCORE.DLL。多状态旋钮和外部 DLL 交互模型不在支持范围。遇到未知活跃组件类时整个快照可能被拒绝，不能承诺总能跳过它列出其余控件。错误按实际原因处理：

- 未绑定/缓存未刷新：结束旧会话，文件阶段 `bind_controls()`，保存后重开。
- 键槽冲突/容量不足：检查整个工程的 INC/DEC/KEY，保留用户需要的绑定；最多五个的上限不能通过重用键槽绕过。
- 停止状态调用：先 `run_for()` 或 `start()`，再操作。
- 控件改变但 MCU 无响应：检查供电、引脚映射、上下拉、固件和时钟；继续仿真并核对日志，不能只重试 press。
- 未知构建/模型：报告具体限制，不修改 DLL 指纹、私有状态或元件字节以跳过检查。

## 按当前工程验证

在用户工作目录组合上面的公共 API 示例，并按需求增加下游断言。保存绑定后重新打开工程检查属性；新的 Session 中核对控件状态、重复设值的 `changed=False`、实际命令时间与仿真完成类型。用户要求电路响应时，必须在按下和松开后分别继续仿真并保存对应输出证据。

脚本与结果只依赖已安装的库及明确提供的工程/固件，无需克隆库仓库。若保存 JSON 报告，明确记录通过/失败、原件是否保持和自有进程的退出结果；文件存在本身不代表通过。六类控件的全量回归和库内部适配器检查属于库仓库的维护测试。

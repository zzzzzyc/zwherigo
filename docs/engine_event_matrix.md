# WF.Player.Core 触发矩阵与 SDK 差异清单

本文档基于 `WFoundation/WF.Player.Core` 源码建立事件触发基线，用于指导 WebUI 可视化配置设计与 SDK 对齐。

## 1. 核心触发入口（WF.Player.Core）

### 1.1 卡带生命周期

| 场景 | 引擎调用 | 说明 |
| --- | --- | --- |
| 开始游玩 | `BeginCallSelf(_cartridge, "Start")` | `Engine.Start()` 触发卡带 Start。 |
| 恢复存档 | `BeginCallSelf(_cartridge, "OnRestore")` | `Engine.Restore()` 在装载 GWS 后触发。 |
| 保存存档 | `BeginCallSelf(_cartridge, "OnSync")` | `Engine.Save()` 先通知脚本再序列化。 |
| 位置更新 | `BeginCallSelfUnique(_player, "ProcessLocation", lat, lon, alt, accuracy)` | `RefreshLocation()` 后由玩家对象处理区域状态切换。 |

### 1.2 UI/对象行为

| 场景 | 引擎调用 | 说明 |
| --- | --- | --- |
| 对象点击 | `BeginCallSelf(ldc, "OnClick")` | UIObject 统一通过 `OnClick` 回调。 |
| 定时器启动 | `timer.CallSelf("Start")` | 内部 OS 定时器创建后触发。 |
| 定时器停止 | `timerEntity.CallSelf("Stop")` | 内部 OS 定时器释放后触发。 |
| 定时器到期 | `_luaExecQueue.BeginCallSelf(t, "Tick")` | Remaining 到 0 时触发 Tick。 |

### 1.3 区域状态链路

- 位置变化不会直接在 C# 中硬编码 `OnEnter/OnExit`，而是委托 Lua 的 `Player.ProcessLocation` 决定区域状态。
- C# 侧通过 `HandleZoneStateChanged(IEnumerable<Zone>)` 接收变更结果，并刷新 UI 可见区、可见对象、距离向量。
- `Zone` 暴露 `Active`、`Points`、`State`、`Bounds` 等属性，说明引擎原生支持多点区域（polygon）。

## 2. 可视化配置应抽取的“稳定能力面”

基于 WF 行为，WebUI 第一优先级应固定暴露：

1. 生命周期触发器：`Start`、`OnRestore`、`OnSync`
2. 区域触发器：`OnEnter`、`OnExit`（后续补 `OnProximity`、`OnDistant`）
3. 交互触发器：`OnClick`、Timer `Start/Stop/Tick`

并将其做成“触发器 + 条件 + 动作”的结构化配置，Lua 仅作为高级模式。

## 3. 当前 SDK 差异（代码现状）

### 3.1 事件建模偏“通用脚本块”，缺触发语义

- `Event` 仅有 `name/object_name/event_type/callback_key/lua_script/groups/extras`，未内建 `trigger_kind` 语义字段。
- `presets/events.py` 虽已有 `zone_enter/zone_exit` 模板，但更多是文案模板，不是引擎触发矩阵驱动。

### 3.2 区域几何仍是单点+半径思维

- WebUI 以 `extras.lat/lon/radius_m` 渲染 marker，不支持 polygon 顶点编辑。
- 与 WF `Zone.Points` 能力不对齐。

### 3.3 物品权限缺显式字段

- `Item` 仅 `id/name/description/extras`，无 `visible/active/enabled/allow_take/...` 等规则化字段。
- 导致“物品允许功能”只能靠手写 Lua 约定。

## 4. 对齐实施顺序（与计划回合对应）

1. 先把 Zone 触发做成结构化模板：`OnEnter/OnExit`。
2. 再补 Item 权限字段与 Lua 生成映射。
3. 最后升级 Zone 几何到 `shape_type + points[]`，兼容旧 `lat/lon/radius`。

## 5. 参考源码位置（WF.Player.Core）

- `Core/Engines/Engine.cs`
  - `Start()` -> `BeginCallSelf(_cartridge, "Start")`
  - `Restore()` -> `BeginCallSelf(_cartridge, "OnRestore")`
  - `Save()` -> `BeginCallSelf(_cartridge, "OnSync")`
  - `ProcessLocationInternal()` -> `BeginCallSelfUnique(_player, "ProcessLocation", ...)`
  - `HandleZoneStateChanged(...)`
- `Core/Data/Lua/LuaDataFactory.cs`
  - `MakeUIObjectRunOnClickInstance(...)` -> `BeginCallSelf(ldc, "OnClick")`
- `Core/Zone.cs`
  - `Active` / `Points` / `State` / `Bounds`

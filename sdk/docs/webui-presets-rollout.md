# WebUI 预设与向导验收说明

本说明用于验证 WebUI 的模板化升级在“兼容旧项目 + 双模式编辑”上的可用性。

## 覆盖点

- 事件模板库可获取：`GET /api/presets`
- 模板可预览：`POST /api/presets/preview`
- 模板可落到项目：`POST /api/presets/apply`
- 事件支持双模式：
  - `extras.editor_mode = "template"`（模板模式）
  - `extras.editor_mode = "lua"`（高级 Lua 模式）
- 模板元数据持久化：
  - `event.extras.template.id`
  - `event.extras.template.version`
  - `event.extras.template.params`

## 手工验收流程

1. 启动 WebUI：`wherigo webui`（或源码模式）
2. 打开事件区域，确认出现“从模板新增”和模板参数面板
3. 选择“进入区域时触发”，填写参数并创建
4. 点击“刷新 Lua”，确认可导出脚本
5. 切换事件到 Lua 模式并修改脚本，确认不破坏构建
6. 导出 JSON，确认事件 `extras.template` 与 `extras.editor_mode` 存在
7. 再次导入该 JSON，确认模板事件可回显并可重建

## 兼容策略

- 旧项目若没有 `event.extras.template`，默认视为 Lua 模式。
- 旧项目导入时不会重写既有 `lua_script`。
- 仅当用户选择模板模式并执行重建时，才更新 `groups/lua_script`。

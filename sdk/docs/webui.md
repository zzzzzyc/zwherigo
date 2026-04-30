# SDK WebUI

SDK 内置了一个低依赖的本地 WebUI，用于编辑与构建验证。

```bash
wherigo webui
```

默认打开地址：`http://127.0.0.1:8765`。

## 功能

- 浏览器内导入/导出项目 JSON。
- 编辑卡带元信息、区域、物品、角色、任务、变量、输入、媒体与事件。
- 使用 SDK 模型规则实时校验。
- 预览 Lua 导出结果，执行 Lua/GWZ/manifest 构建并下载产物。
- 在 OSM 地图上编辑区域坐标。

## 目录位置

WebUI 静态资源位于仓库根目录的 `webui/`（与 `LICENSE` 同级）：

- `webui/index.html`
- `webui/app.js`
- `webui/styles.css`

## OSM 坐标策略

地图通过 Leaflet 使用 OpenStreetMap 瓦片，区域坐标按原始 WGS84 存储在：

- `zone.extras.lat`
- `zone.extras.lon`
- `zone.extras.radius`（或 `radius_m`）

不会进行 GCJ-02 或其他偏移坐标转换。如果你的源数据来自有偏移的地图服务，请在导入前先转换。

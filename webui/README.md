# WebUI (独立项目)

这个目录是独立的 WebUI 项目（静态前端 + Python 后端服务）。

## 安装

先安装 SDK（本地开发建议 editable）：

```bash
cd ../sdk
python -m pip install -e .
```

再安装 WebUI 依赖：

```bash
cd ../webui
python -m pip install -r requirements.txt
```

## 运行

```bash
python server.py --host 127.0.0.1 --port 8765 --root ..
```

启动后访问：

- http://127.0.0.1:8765/

WebUI 通过 `wherigo-sdk` 提供的模型、编辑器、构建与预设 API 进行工作。

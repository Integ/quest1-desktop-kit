# Quest 控制台

在 Mac 上用网页管理 Quest 1。所有操作都通过已经授权的 ADB 完成，不会新建任何授权。说明见 [docs/CONSOLE.md](../docs/CONSOLE.md)。

```sh
mkdir -p .local && cp console/config.example.json .local/console.json   # 填上序列号和头显的 Wi-Fi IP
./Open\ Console.command                                                # 或：cd console && python3 server.py --open
```

- `server.py`：只在 127.0.0.1 上监听的网页服务和接口。
- `quest.py`：ADB 操作、安装包检查、状态解析。
- `static/`：网页界面。
- `tests/`：解析逻辑的单元测试，运行 `python3 -m unittest discover -s console/tests`。

设备信息、无线端口、应用名称缓存和日志都放在 `.local/`，这个目录被 Git 忽略。

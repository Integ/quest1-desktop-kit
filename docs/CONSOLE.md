# Quest 控制台（Mac 网页）

在 Mac 上用网页管理 Quest 1，不需要手柄。它只是对已经授权的 ADB 做了一层图形界面，不会新建任何授权。

## 启动

```sh
mkdir -p .local
cp console/config.example.json .local/console.json    # 填上 serial（头显序列号）和 host（头显的 Wi-Fi IP）
./Open\ Console.command                               # 浏览器会打开 http://localhost:8765
```

关掉那个终端窗口，控制台就停止了。只需要 macOS 自带的 Python 3.9 或更新版本，不用安装其他依赖。安装包检查要用到 Android Build Tools 里的 `aapt`，控制台会在 `ANDROID_SDK_ROOT`、`ANDROID_HOME` 和常见的安装位置里自动查找。

`.local/console.json` 里还可以设置 `sunshine`、`sunshine_conf`、`scrcpy` 的路径和监听端口 `listen_port`。无线 ADB 找到的端口会写回这个文件。

## 功能

| 区块 | 内容 |
| --- | --- |
| 头显状态 | 连接方式（USB 或 Wi-Fi）、电量和是否接电源、温度、剩余存储、是否唤醒、前台应用、Wi-Fi IP、系统版本；每 5 秒刷新一次 |
| 头显画面 | 每 2 秒截一张单眼画面；“打开实时镜像窗口”会用 scrcpy 打开实时画面 |
| 常用操作 | 打开影院 / 应用列表、音量 + / − / 静音、唤醒、休眠、不戴也保持唤醒、重启 |
| 应用 | 列出已安装的应用（名称从 APK 读取后缓存），可以打开、关闭、卸载；本项目安装的组件卸载前会额外提醒 |
| 安装应用 | 拖入 APK 即可安装。安装前检查最低 Android 版本、CPU 架构、`com.oculus.supportedDevices` 和 Meta 平台库，并给出提醒；OBB 文件按 `main.<版本号>.<包名>.obb` 放到对应目录 |
| 媒体 | 拖入视频，上传到 `/sdcard/Movies`，在影院 v12 的 Local Videos 里播放；在头显浏览器里打开网址 |
| 头显设置页 | 一键在头显里打开蓝牙、手柄、手势追踪、边界、显示、声音、电源、存储、实验功能、关于、Wi-Fi 设置页 |
| 启动助手 | 远程开关主页空闲开启动器、音量快捷键、影院自启、USB / 无线 ADB 常驻（需要启动助手 v10） |
| Mac 桌面串流 | 启动或停止 Sunshine |

一些说明：

- **唤醒**：摘下头显时，Quest 会忽略 `KEYCODE_WAKEUP`，所以控制台只在头显休眠时发送电源键，避免反过来把它关掉。
- **不戴也保持唤醒**：使用 Meta 开发者文档里的 `com.oculus.vrpowermanager.prox_close` 广播，关闭时发送 `automation_disable`，重启后也会自动恢复。
- 有些系统窗口不允许截屏（比如 Android 蓝牙设置），这时截图是空白的。
- 连续快速按“减加减加”会触发助手的应用列表快捷键。

## 安全

- 服务只在 `127.0.0.1` 上监听，同一网络里的其他设备打不开。
- 只接受 `Host` 为 `localhost` / `127.0.0.1` 的请求（防 DNS 重绑定）；所有写操作必须带页面自己加的 `X-Quest-Console` 头（防跨站请求）。
- 上传文件只写进临时目录，传到头显后就删除；文件名只取最后一段，不能指向其他目录。
- 卸载、重启以及关闭 ADB 常驻之前，页面都会先让你确认。

## 无线 ADB 提示 “No route to host”

macOS 的“本地网络”隐私权限会拦住没有授权的程序访问局域网。如果后台的 adb 服务是从没有这项权限的程序里启动的，`adb connect` 就会报 “No route to host”，而 `nc` 等其他程序却能连通。控制台遇到这种情况会自动重启一次 adb 服务；如果还不行，请从“终端”启动控制台，并在“系统设置 → 隐私与安全性 → 本地网络”里允许“终端”。

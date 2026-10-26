# 安装与日常使用

## 1. 建立 ADB

安装 [Android platform-tools](https://developer.android.com/tools/releases/platform-tools)，运行 `adb devices -l`。只出现 `unauthorized` 时，先在头显允许自己的电脑；不要导入别人的 ADB 私钥。没有授权的设备先读 [BOOTSTRAP.md](BOOTSTRAP.md)。

本工具自动读取 `ro.product.device`，只接受 `monterey`；同一台 Quest 同时有 USB 和 Wi-Fi 连接时优先 USB。连接多台 Quest 1 时必须选择：

```sh
python3 tools/quest.py --serial QUEST_USB_SERIAL info
```

`QUEST_USB_SERIAL` 替换成自己的 `adb devices` 项目。下文省略选择参数；需要时把 `--serial` 放在子命令前。设备不匹配时工具拒绝修改。安装脚本不会自动重置设备、重新配对或清除应用数据。

## 2. 安装头显应用

按 [BUILD.md](BUILD.md) 构建影院和启动助手，或仅从本项目 Release 下载助手。安装：

```sh
python3 tools/quest.py install-cinema dist/QuestCinemaFix-v8.apk
python3 tools/quest.py install-helper dist/QuestStartupHelper-v4.0.apk
```

影院 v8 要求 Quest 1 v50、Android API 29 和 ARM64。助手安装后所有开关默认关闭，界面可上下滚动。脚本执行一次 `pm grant local.quest.adbkeeper android.permission.WRITE_SECURE_SETTINGS`，再打开助手以解除新安装应用的 stopped 状态。

从 [Lightning Launcher 官方发布页](https://github.com/threethan/LightningLauncher/releases/tag/10.0.1) 获取已验证的 10.0.1 版本。其包名为 `com.threethan.launcher`。安装下载的 APK 后：

```sh
python3 tools/quest.py open-launcher
```

本版影院名字自带 `★`，在 Lightning Launcher 的默认名称排序下可排在前面。实机已确认可用左手柄点开。这里指启动器入口；没有把应用固定到 v50 原生系统底部 Dock。

如果没有右手柄、退出影院后无法进入系统应用列表，启用助手 v4 的实体音量快捷键：

```sh
python3 tools/quest.py volume-shortcut on
```

保持佩戴，快速按头显音量键 **减、加、减、加**，打开 Lightning Launcher，再用左手柄点 ★ 影院。完全静音时先提高一格；每次间隔不超过 1.5 秒。关闭用 `volume-shortcut off`。详见 [VOLUME-SHORTCUT.md](VOLUME-SHORTCUT.md)。

## 3. 准备电脑串流

本次使用 Sunshine **2026.914.233613**，Apple Silicon Mac / macOS 27.0.1。其他版本和主机系统请对照 [Sunshine 官方文档](https://docs.lizardbyte.dev/projects/sunshine/latest/)；这里不把本次测试版本称为永久最新版本。

安装 [Sunshine](https://github.com/LizardByte/Sunshine)。macOS 在系统设置中允许该程序捕获屏幕和系统音频，授权后可能需要重新启动 Sunshine。电脑本身播放音频时确认没有静音。默认硬件编码，客户端使用 HEVC。

可以在已有 Sunshine 配置中添加无命令的桌面应用，名称 `Mac Desktop`。如果需要本项目的独立配置：

```sh
python3 tools/sunshine.py init
python3 tools/sunshine.py start
```

如果二进制不在 PATH：

```sh
python3 tools/sunshine.py start --binary /path/to/sunshine
```

配置只写入仓库内被 Git 忽略的 `.local/sunshine/`，不覆盖已有文件。`start` 在前台运行；不要同时启动另一个占用相同端口的 Sunshine 实例。

生成的配置启用音频，关闭远端输入转发及 UPnP，管理界面只允许本机访问。串流仍通过局域网进入电脑，需要防火墙允许相关流量。不要把调试或串流端口映射到公网。

本次 v8 实测在自己的 Sunshine 配置中设置以下上限，保持 HEVC 硬件编码和正常 FEC：

```ini
max_bitrate = 8000
```

单位为 Kbps。编辑自己的配置后，重新启动对应 Sunshine 进程，再建立新串流；保留原配对和凭据。这个约 8 Mbps 上限降低网络和解码负担，不能替代 v8 的多 FEC 块、丢帧恢复与连接解析修复。

## 4. 配对和选择桌面

在电脑打开 `https://localhost:47990`，创建自己的 Sunshine 管理账号。其自签名证书和密码属于你的私有配置。不要把 `.local/` 打包分享。

```sh
python3 tools/quest.py open-cinema
```

影院选择电脑 `Quest Desktop`；如果没有发现，手动输入电脑自己的局域网地址。头显出现四位 PIN 后，保持该窗口打开，在 Sunshine 的 PIN 页面及时提交。然后打开 `Mac Desktop`。

若提示 **computer is currently in a game / close the game before pairing**，先按[故障排查](TROUBLESHOOTING.md)结束旧串流，再配对。重新签名后的新包需要自己的配对，不能使用作者设备的配对状态。

## 5. 左手柄、大小与立体声

- 看向目标，单击左 X 选择。
- 快速双击 X 返回或切换菜单，分辨率设置页也适用。
- 大屏选 Void 场景，在显示设置中降低 Distance。改变 Android 窗口像素并不能等比例放大 VR 中的银幕。
- 影院已改成双声道，关闭 5.1 请求。系统音频经 Sunshine 传到 Quest 扬声器或耳机。测试时应分别听到左、右声道。

旧版原生影院的部分按钮仍使用注视选择，不保证有现代 VR 应用的控制器射线交互。Y 和三横线菜单键在测试中无效，使用双击 X。

## 6. 自启、调试保持、Featured 和时间

```sh
python3 tools/quest.py keep-usb on
python3 tools/quest.py keep-wifi on
python3 tools/quest.py autostart on
python3 tools/quest.py volume-shortcut on
```

重启后佩戴、唤醒头显，约一分钟后应自动出现影院。助手不会在每次退出应用时把你强行带回影院。ADB 重连详见 [ADB-AND-STARTUP.md](ADB-AND-STARTUP.md)。

可选关闭 Featured：

```sh
python3 tools/quest.py featured hide
```

这会停用 **整个 `com.oculus.store` 包**，因此商店界面也不可用；已安装应用仍可从启动器进入。恢复方法是 `featured show`。它没有卸载应用或删除商店数据。

时间显示差若干小时可能只是时区错误。选择自己的 IANA 时区，例如：

```sh
python3 tools/quest.py time --timezone Europe/Paris
```

该命令开启网络自动校时，关闭自动时区并指定所选时区，不强制写入主机时间。还应确保头显已联网。

# ADB 保持与开机自启

## 启动助手做了什么

`local.quest.adbkeeper` 是一个前台服务，四个独立开关默认关闭。设置保存在 device-protected storage，开机广播会在需要时启动服务。前三项每约 15 秒检查一次；音量快捷入口接收音量变化广播：

| 开关 | 行为 |
| --- | --- |
| USB 保持 | 恢复 `development_settings_enabled=1`、`adb_enabled=1`，不依赖 Wi-Fi |
| Wi-Fi 保持 | 连接 Wi-Fi 时恢复 `adb_wifi_enabled=1` |
| 影院自启 | 系统运行至少 60 秒、用户已解锁、头显处于唤醒状态且有特殊访问权限时，每个 BOOT_COUNT 启动一次影院 |
| 音量快捷入口 | 快速按头显音量键“减、加、减、加”打开 Lightning Launcher；不依赖右手柄或电脑连接 |

开启任一 ADB 保持时，会把 `adb_allowed_connection_time` 设为 `0`，避免已授权电脑因闲置超时失去授权。因此只在自己的可信电脑和网络上启用。服务不会替其他电脑接受 RSA / 无线调试配对，也不会静默授予新的信任。

安装脚本授予 `WRITE_SECURE_SETTINGS`。自启或音量快捷入口命令额外允许 `SYSTEM_ALERT_WINDOW`，用于 Android 10 的后台启动活动例外；应用不实际绘制 overlay。参考 [Android 后台启动限制](https://developer.android.com/guide/components/activities/background-starts)。

助手还有开机广播、前台服务和查看网络状态权限；**没有 INTERNET、存储、摄像头或麦克风权限**。常驻通知可打开影院或设置页。行政广播接收器受 `WRITE_SECURE_SETTINGS` 保护。

## 开启和关闭

```sh
python3 tools/quest.py keep-usb on
python3 tools/quest.py keep-wifi on
python3 tools/quest.py autostart on
python3 tools/quest.py volume-shortcut on
```

设置自启时记录当前 boot count，下次开机才自动打开；马上打开可以用 `open-cinema`。应用退出后不会每 15 秒抢回前台。

```sh
python3 tools/quest.py autostart off
python3 tools/quest.py volume-shortcut off
python3 tools/quest.py keep-wifi off
python3 tools/quest.py keep-usb off
```

**关闭 USB / Wi-Fi 保持会立即关闭对应调试设置，可能切断当前连接。** 需要保留连接时，先确认另一种方式可用，或在助手界面操作。关闭自启不会关闭影院本身。

开关关闭不会自动还原之前的授权超时值；要恢复超时策略，先关闭两个 ADB 保持，再按自己的系统默认策略执行 `settings delete global adb_allowed_connection_time`，详见恢复说明。

关闭音量快捷入口只关闭手势识别，不改变 ADB、自启或共用的后台启动权限。详细使用方法和验证范围见 [VOLUME-SHORTCUT.md](VOLUME-SHORTCUT.md)。

## USB 重启后的行为

仅执行 `settings put global adb_enabled 1` 在本次 v50 实机上不够：重启时系统又将该值置零。开发者开关仍为 1，并不代表 USB ADB 已经可用。

助手 v3 将 USB 保持独立于 Wi-Fi。一次真实重启后，无需再次手工设置，USB serial transport 自动恢复并可以执行 shell；随后约 21 秒的连续检查均可连接。这是启动后恢复，不能保证启动最早阶段就有 USB shell。线缆要支持数据，电脑密钥也要事先授权。

已有 ADB 连接时，可以单次启用 USB：

```sh
python3 tools/quest.py enable-usb
```

这设置的是 Android 开发者/调试选项。它不替代 Meta 官方开发者账号验证，也不承诺改变手机 Meta 应用中的账号状态。

## Wi-Fi TLS 配对与动态端口

Quest v50 上观察到无线调试有两个不同端口：

- `adb pair IP:PAIR_PORT`：使用短期配对码建立信任。
- `adb connect IP:CONNECT_PORT`：使用已建立信任的密钥连接 shell。

二者通常不同；`IP:0` 不是有效连接地址。连接端口会变，mDNS 在这台头显上未可靠发布。不要因为 Info 显示 `:0` 就恢复出厂或不断重新配对。

先用 `adb mdns services` 看是否能发现 `_adb-tls-connect._tcp`。若知道连接端口：

```sh
python3 tools/quest.py connect --host "$QUEST_IP" --expected-serial "$QUEST_SERIAL" --port "$CONNECT_PORT"
```

变量由你填入自己的值。`QUEST_SERIAL` 应是从已经信任的连接读取的 `adb -s TRANSPORT shell getprop ro.serialno`，不是猜测的设备名称。

如端口不公开，可明确选择仅扫描自己头显的 IP：

```sh
python3 tools/quest.py connect --host "$QUEST_IP" --expected-serial "$QUEST_SERIAL" --scan
```

工具仅探测这个私有 IPv4 地址的 32768–65535 TCP 端口，尝试已有信任的 ADB 连接，再核对 `monterey` 和物理序列号。不自动配对、不打开 5555、不扫整个网段，不会向候选设备写设置。连接失败要先唤醒头显、确认 Wi-Fi 调试开启及电脑密钥仍在授权列表。一般优先使用 USB 更直接。

不建议把旧式未配对的 `adb tcpip 5555` 作为默认保持方案。这里保留的是本机 v50 的 TLS 无线调试和事先批准的电脑密钥。

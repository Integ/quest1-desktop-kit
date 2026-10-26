# 关闭功能与恢复

下列命令只撤销指定功能，不清空数据。请保留至少一种已授权的连接；关闭 ADB 对应开关可能立刻断开当前 shell。

| 目标 | 命令 / 行为 |
| --- | --- |
| 停止影院开机自启 | `python3 tools/quest.py autostart off` |
| 停止 Wi-Fi ADB 保持并关闭 Wi-Fi 调试 | `python3 tools/quest.py keep-wifi off` |
| 停止 USB ADB 保持并关闭 USB 调试 | `python3 tools/quest.py keep-usb off` |
| 恢复商店 Featured | `python3 tools/quest.py featured show` |
| 恢复首次教程包 | `python3 tools/quest.py tutorial show` |

上述 `show` 使用 `pm default-state --user 0`，恢复包的系统默认状态。影院和助手没有被卸载。

## 调试权限与超时

先在助手中或通过脚本关闭 USB / Wi-Fi 保持，否则服务会再次写入设置。需要恢复授权超时策略，可在保留连接期间执行：

```sh
adb -s TRANSPORT shell settings delete global adb_allowed_connection_time
```

需要撤回助手特殊权限时，先关闭三个开关，再执行：

```sh
adb -s TRANSPORT shell appops set local.quest.adbkeeper SYSTEM_ALERT_WINDOW default
adb -s TRANSPORT shell pm revoke local.quest.adbkeeper android.permission.WRITE_SECURE_SETTINGS
```

调试授权过的电脑密钥需要在设备调试设置中撤销；停用保持服务本身不会删除所有历史配对。不要在仍需远程维护时先删除唯一能连接的电脑密钥。

## 恢复自动时区

本项目的时间命令保留自动校时，但改用指定时区。想恢复系统自动时区：

```sh
adb -s TRANSPORT shell settings put global auto_time 1
adb -s TRANSPORT shell settings put global auto_time_zone 1
```

自动时区的实际结果依赖旧系统和网络提供的信息，可能仍需手动选区。

## 应用与签名

停止功能不需要卸载。卸载启动助手会删除助手偏好；卸载影院会删除其配对、显示和控制设置。不同签名导致无法覆盖时，先决定是否保留旧安装；本项目没有内置自动卸载或清数据流程。

本项目生成的电脑配置集中在 `.local/sunshine/`。先退出对应 Sunshine 进程，再自行归档或移除这一目录；它含私钥和账号/配对状态，不要传到 issue。其他已有 Sunshine 配置没有被脚本覆盖。

本项目没有刷写固件、修改系统分区或获取 root。通常不需要用恢复出厂来撤销这些改动。

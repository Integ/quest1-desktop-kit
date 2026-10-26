# 首次初始化：本项目的边界

这台设备最初只有一个左手柄，官方设置停在 right controller 配对。后来通过 Android 手机辅助连接、联网和无线调试，最终取得 shell，才能安装本仓库的工具。

**没有记录完整、可供其他新设备稳定复现的初始授权过程。** 特别是手机蓝牙认领、账号与 device key 之间的协议状态，不能根据最终已有的 shell 反推出“一条命令跳过初始化”。因此仓库不提供装作已验证的配对绕过脚本、第三方系统刷机包或 Meta 凭据工具。

## 如果你还没有 ADB

优先使用你自己的 Meta 账号和官方手机应用完成可完成的设置，参考 [Meta 开发设备设置文档](https://developers.meta.com/vr/documentation/native/android/mobile-device-setup/)。如果缺少必须的右手柄，借用兼容的 Quest 1 右 Touch 手柄是需要考虑的路径；不要将 Quest 2 / Quest 3 手柄视为当然兼容。

本次还使用了 Android 手机上的 **Private Quest**（包名 `com.xre.privatequest`）。它不是本仓库的应用，也不是本次发布的依赖安装包。本次未留存足够可靠的 APK 获取与签名出处，所以不提供镜像或推荐随机下载站。已拥有该工具的读者可能看到这些已观察到的现象：

| 现象 | 本次含义 |
| --- | --- |
| 扫到两个同名 Quest | 名称不足以确认设备，需要对应自己头显的身份 |
| `error 105: device auth error` | 设备认领/认证状态未匹配，不能当作 ADB 故障 |
| `OCULUS_SET_USER_SECRET` unexpected | 蓝牙协议阶段不接受该指令；反复写 key 没有形成可复用修复 |
| 可以读取 version | 只证明蓝牙部分命令能通信，不证明账号/调试授权完成 |
| `adb pair` 成功但 connect 为 `:0` | 配对端口不是 shell 连接端口，需要刷新或寻找真正连接端口 |
| 手机镜像无反应 | 锁屏或蓝牙未连接时，需实体解锁/点击自己的设备 |

在自己的头显出现无线调试授权时，需要在头显内明确允许。允许后电脑才可使用自己的密钥连接。本仓库不提供原设备的 device key、Meta 账号数据、配对码或 ADB 私钥。

## 已有 shell，但被首次教程遮挡

本次取得 ADB 后，`Show universal menu` 的教程一直遮挡应用。只停止进程不够；针对该固件停用教程包后恢复：

```sh
python3 tools/quest.py tutorial hide
python3 tools/quest.py open-launcher
```

它执行的是 `pm disable-user --user 0 com.oculus.firsttimenux`，**不是账号注册或第一次初始化的替代品**。需要恢复则 `tutorial show`，对应 `pm default-state`。请只在已经知道该教程是当前阻挡来源时使用。

不要重置已经能进入应用列表和影院的 Quest，只为了重新尝试上述实验。恢复出厂会丢失调试授权、配对、侧载应用和当前工作状态。

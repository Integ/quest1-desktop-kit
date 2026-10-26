# 只有左手柄：退出影院后打开应用列表

助手 **v4 / `4.0-volume-launcher`** 增加了头显实体音量键入口。适用于影院已经退出、右手柄缺失、无法按右侧 Oculus 按钮进入应用列表的情况。用户已在同一台 Quest 1 上用实体按键确认应用列表出现。

## 使用

安装助手 v4 和 Lightning Launcher，保留原有配置：

```sh
python3 tools/quest.py install-helper dist/QuestStartupHelper-v4.0.apk
python3 tools/quest.py volume-shortcut on
```

戴着头显并保持屏幕亮起，快速依次按 **音量减 → 音量加 → 音量减 → 音量加**，每个按钮各按一次、相邻变化间隔不超过 1.5 秒。应用列表出现后，用左手柄射线指向前排的 **★ Quest Cinema Fix**，按食指扳机打开。

完全静音时先提高一格音量，再做四次按键。正常四次变化后回到原音量；无需为了快捷键改变日常音量设置。手势完成后有 2 秒冷却，避免重复打开。

也可在“Quest 启动助手”设置页启用或关闭“音量减加减加快捷入口”。新安装默认关闭，升级不会替用户自动打开。关闭命令：

```sh
python3 tools/quest.py volume-shortcut off
```

## 行为与权限

前台服务注册 `android.media.VOLUME_CHANGED_ACTION`，只处理媒体音量流的单格变化。它不监听控制器或键盘事件，不读取屏幕、文件或应用使用历史，也不拦截正常音量调节。没有增加 Manifest 权限。

后台打开启动器需要现有的 `SYSTEM_ALERT_WINDOW` 特殊访问权限，与影院开机自启共用；启用命令会允许这一 appop。应用不绘制悬浮窗。关闭快捷入口不会撤销这个共用权限，不会关闭 USB / Wi-Fi ADB，也不会取消影院自启。

开启快捷入口后，即使三个原有开关都关闭，前台服务仍会运行以接收音量变化。开机广播按持久化开关恢复服务。该版本已经做实体按键测试，**尚未另做升级后的重启验证**。

## 为什么没有直接交换左右系统按钮

设备自身的 `SettingsManager` 存在 `swap_system_button_handedness` 项，当前读取为 false；用 shell 调用其 setter 返回 false，未改变设置。尝试打开原生辅助功能设置时，系统外壳仍在进入未完成的首次设置流程，页面未显示。

所以本次已验证的入口是实体音量键 + Lightning Launcher。没有声称已成功交换系统按钮，也没有修改初始化状态或扩大系统权限。其他已完成初始化的设备可自行检查系统辅助功能中的交换选项，但不属于本次验证结果。

## Mac 备用入口

仓库根目录的 `Open Cinema.command` 和 `Open App List.command` 可在 Mac 上双击。需要 Python、adb 在 PATH，且已经存在授权的 USB 或无线 ADB 连接；多台 Quest 时使用带 `--serial` 的命令行工具。脚本使用仓库相对位置，不包含个人序列号或内网地址。

## 崩溃的边界

本次退出日志定位到视频 `RtpFecQueue.c` 中 `reconstructFrame()` 的 `ret == 0` 断言。它不同于 v7 已处理的音频 RTP 乱序队列问题。视频纠错崩溃**尚未修复**；本次 v4 的作用是让用户在应用退出后能自己重新打开应用列表。影院补丁与代码哈希没有改变。

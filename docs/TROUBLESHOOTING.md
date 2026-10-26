# 故障排查

## 影院能打开，但看不到桌面

先确认电脑的 Sunshine 正在运行、双方还在同一网络、Mac 捕获权限有效。影院内选择电脑后还要选 `Mac Desktop`。

旧客户端异常退出会留下服务器串流会话。出现 `computer is currently in a game` 或一直忙碌时，在本机 Sunshine 界面结束会话；也可使用本项目的回收工具：

```sh
python3 tools/sunshine.py close-session --username YOUR_SUNSHINE_USERNAME
```

密码通过隐藏输入读取，不写入文件。如果使用自己原来的 Sunshine 配置而不是本项目生成的配置，传入它自己的证书：

```sh
python3 tools/sunshine.py close-session --username YOUR_SUNSHINE_USERNAME --ca /path/to/credentials/cacert.pem
```

工具只向固定的本机回环地址发送请求，使用指定证书进行 TLS 验证。它调用 `/api/apps/close` 结束串流，不是关闭电脑上所有应用。之后重新打开影院：

```sh
adb -s TRANSPORT shell am force-stop local.quest.cinema
python3 tools/quest.py open-cinema
```

再选电脑和桌面。不要为了清理旧会话而卸载影院、清除应用数据或删除配对。

## 黑屏、加载或连接即退

确认安装的是本项目固定原版构建的 v7，包名 `local.quest.cinema`，versionName `1.0-quest-left-stereo-shortcut-rtp`。

本次 H.264 遇到关键帧/编码兼容问题，强制软件编码也未解决；最后 **H.265 / HEVC + Mac 硬件编码** 出现正常桌面。补丁还处理了旧 Qualcomm HEVC 黑名单、Sunshine RTSP 参数、ENet 控制回复、Android 鼠标捕获和空视图崩溃，不能只靠切换一个编码选项替代整套补丁。

先检查 Sunshine 日志是否有新的会话、有效的屏幕捕获和 HEVC 编码器。若用户已看到桌面后才突然退出，查看头显 `logcat` 中是否有 `RtpReorderQueue` 断言；v7 专门修复了 ARM64 迟到包触发的队列断言。日志可能含地址或应用信息，分享前先删个人数据。

## 屏幕很小、有黑边

普通 Moonlight Android 是 2D 窗口；调整分辨率或 Activity window 大小不能充分改变 VR 中的大小。使用原生影院，选 **Void** 场景，快速双击左 X 打开显示设置，降低 **Distance**。在 Home Theater 场景固定银幕中调节可能与预期不同。

视频比例本身造成的上下黑边不代表串流失败；要改变可视尺寸，先调 VR 银幕位置和距离。

## 只有左声道

本次原因是客户端强制请求 5.1，未正确映射到立体声输出。已改 `enable51Surround=false` 且 `setAudioConfiguration(0)`，原生 Opus 输出 2 声道。v7 保留该修复。

确认 Sunshine `stream_audio = enabled`，主机有有效音频源和捕获授权；再播放左右分离的测试音。若只有某一侧物理扬声器/耳机异常，也需检查音量、插头和耳机本身，不能把所有单声道问题都归于协议。

## 左 Y / 菜单键无效，困在分辨率页

旧兼容层未可靠传入这些按键。使用 **快速双击左 X**。单击仍选择，拖动不应触发双击。双击间隔约 350 毫秒；改变注视目标或移动过大不算同一个双击。

## 开机自启没出现

确认助手已打开过一次、`autostart on` 已执行，且包没有被 force-stop。佩戴唤醒，等开机至少 60 秒。确认 `SYSTEM_ALERT_WINDOW` appop 允许，影院包已安装。当前开机第一次启用自启不会立即弹出，下一次开机才运行；需要现在打开用 `open-cinema`。

助手按 boot count 去重；手动退出后不会反复抢前台。Android 系统强行限制服务、应用被停用或不同固件行为未在本次覆盖。

## Featured 还出现

本次最终定位为 **`com.oculus.store` 的 PanelService**，不是 Explore。仅停用 Explore 没有效果，已恢复其默认状态。单独禁用商店 service 被 shell 权限拒绝，而 `pm disable-user` 商店包成功并经过重启确认。

`featured hide` 会让商店 UI 也不可用。需要商店时执行 `featured show`；不要扩大为停用系统社交服务、更新器或全部 Oculus 系统包。

## USB 或 Wi-Fi 连接失败

见 [ADB-AND-STARTUP.md](ADB-AND-STARTUP.md)。注意 `adb_enabled` 与开发者总开关不同；TLS 配对端口与连接端口不同。`unauthorized` 需要在头显确认自己的电脑。多设备请加 `--serial`，不要误操作手机。

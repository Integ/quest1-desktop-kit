# 没有手柄时怎么用

适用于一只 Touch 手柄都没有、头显又没有登录 Meta 账号的 Quest 1（系统 v50）。这些功能都已在一台这样的头显上验证过。

| 场景 | 做法 | 需要的版本 |
| --- | --- | --- |
| 影院里选择和返回 | 看向目标后短按音量 **+** 确认；短按音量 **−** 返回或打开菜单；按住 **+** 或 **−** 向右或向左移动一格 | 影院 v12 |
| 影院里打开应用列表 | 快速短按 **减、加、减、加** | 影院 v12 |
| Meta VR 主页打开应用列表 | 依次**按住**减、加、减、加，每次按到音量条变化一下再松开，换方向时停顿不超过 1 秒 | 启动助手 v10 |
| 主页空着时 | 自动打开 Lightning Launcher 应用列表，不用按任何键 | 启动助手 v10 |
| 从电脑操作 | [Quest 控制台](CONSOLE.md)：打开应用、安装 APK、截图、设置页、电源、音量 | 控制台 + 启动助手 v10 |
| 播放头显里的视频 | 影院的 Local Videos，见 [LOCAL-VIDEO.md](LOCAL-VIDEO.md) | 影院 v12 |

在 VR 主页，系统不会把音量键事件交给应用，所以助手改为每 100 毫秒读取一次媒体音量，用音量的变化识别手势。这也是为什么在主页要“按住到音量条变化”，而在影院里短按就可以。

## 主页空闲时自动打开应用列表

在这类头显上，商店和首次设置向导（FirstTimeNux）通常已被停用（见 [SETUP.md](SETUP.md) 的 Featured 部分），而初始设置从未完成。于是当 Meta VR 主页前面没有任何面板时，系统外壳会每秒十几次地重试打开设置向导和商店，两者都失败。这会占用 CPU，也可能挡住其他面板的打开。

启动助手 v10 只监听系统日志里 `LaunchFirstTimeNux(crash_recovery)` 这一行：2 秒内出现 5 次，就打开 Lightning Launcher，之后冷却 20 秒。启动器一打开，重试就会停止。

```sh
python3 tools/quest.py idle-launcher on    # 同时授予 READ_LOGS 和后台启动权限
python3 tools/quest.py idle-launcher off
```

`READ_LOGS` 只能通过 ADB 授予，重装同签名的版本后授权仍然保留。助手不保存、不上传日志，只做这一行的匹配。在头显的“Quest 启动助手”设置页里也可以开关，状态行会提示是否还缺授权。

实测：强制关闭启动器约 7 秒后，启动器自动重新打开，之后 15 秒内重试次数为 0。

## 蓝牙游戏手柄

Xbox 无线手柄（低功耗蓝牙）可以直接和头显配对。没有手柄时，可以从电脑打开系统的蓝牙设置页：

```sh
adb shell am start -a android.intent.action.VIEW -n com.oculus.vrshell/.MainActivity \
  -d systemux://settings -e uri "/bluetooth?setting=devices_bluetooth_section"
```

系统设置面板是一块 800×500 的虚拟显示屏，可以用 `adb shell input -d <显示屏编号> tap x y` 点击，显示屏编号用 `adb shell dumpsys input` 查。点 **Pair** 后会打开标准的 Android 蓝牙窗口，这个窗口不允许截屏。

Meta 的系统界面不支持用游戏手柄导航；手柄在 Lightning Launcher、影院本地视频（≡ 键暂停，LB / RB 快退或快进 10 秒）以及支持手柄的应用里可用。

## 手势追踪为什么打不开

设置里的手势追踪开关会先检查 `hand_tracking_opt_in`；还没同意过，就会跳到 FirstTimeNux 的 `/first_time_nux/HANDS_PRIVACY` 页。这个页面要先拿到 Meta 账号令牌，没登录时会一直报 “user not logged in”，面板一直不显示。直接写偏好值也不行：shell 调用 `PreferencesService` 会被拒绝，`/system/bin/oculuspreferences` 要求 root，`com.oculus.permission.WRITE_SETTINGS` 的保护级别是 signature|preinstalled。Quest 1 无法 root，所以没有登录账号时，手势追踪无法开启。

**不要为了这个临时启用 FirstTimeNux**，原因见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md#不要临时启用首次设置向导)。

Meta AI / 语音命令（`com.oculus.assistant`）同样需要登录，日志会报 “Can't activate assistant. User not logged in.”。

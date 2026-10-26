# 修复记录与实现

整理日期：2026-10-25。目标是保留原生 VR 影院的可调大屏，同时兼容 Quest 1 v50 和本次测试的 Sunshine。所有改动针对 [penkamaster/OculusSdk-moonlight 1.0](https://github.com/penkamaster/OculusSdk-moonlight/tree/1.0)，不是对任意 Moonlight APK 的通用二进制补丁。

## Android 10、解码与声音

| 问题 | 修复位置 / 行为 |
| --- | --- |
| 影院没有普通 2D streamView，初始化/失败处理却访问它 | `StreamInterface` 为焦点和 Surface holder 路径增加空值判断 |
| 旧输入捕获实现调用不兼容的鼠标捕获 API | `InputCaptureManager` 返回 NullCaptureProvider，VR 控件继续走原生事件 |
| 旧 Qualcomm HEVC 黑名单拒绝本机解码器 | `MediaCodecHelper` 调整黑名单匹配 |
| H.264 路径一直等关键帧；软件编码未解决 | `PreferenceConfiguration.videoFormat=-1`，选择 HEVC；主机保持硬件编码 |
| 5.1 请求使实际输出只剩一侧 | `enable51Surround=false`，`setAudioConfiguration(0)`，固定立体声 |

这些 Java 层改动以精确 smali 差异保存，构建器验证前后文件哈希。不是整份 SDK 源码再编译。

## 新 Sunshine 与旧协议

1. 两个 ABI 的原生库中，将旧字符串 `x-nv-video[0].framesWithInvalidRefThreshold` 替换为 `x-nv-audio.surround.AudioQuality` 并以 NUL 补齐，保持长度不变。本次 Sunshine 要求该 RTSP 参数，传值为 0。
2. ARM64 原生库在偏移 `0x602f8` 将指令 `0x9100a3e1` 改为 `0x14000012`，跳转至 `0x60340`，跳过旧客户端对已经不再适用的 10 秒 ENet 应用层回复等待。

只修改清单中指明的字节，仍使用已有协议流程和已配对的设备证书。没有关闭 Sunshine 的客户端认证。

## 迟到音频 RTP 包崩溃

旧 release 1.0 的 `queuePacket()` 断言包序列号不早于预期值。队列因超时或容量先推进预期值后，一个原本进入处理流程的迟到包会违反断言并终止进程。

期望行为是拒绝该迟到包，继续处理后续数据：

```c
/* Original release */
LC_ASSERT(!isBefore16(packet->sequenceNumber, queue->nextRtpSequenceNumber));

/* Behavioral fix */
if (isBefore16(packet->sequenceNumber, queue->nextRtpSequenceNumber)) return 0;
```

已安装 APK 的 ARM64 对应修改：

| 项目 | 值 |
| --- | --- |
| 文件 / 虚拟地址偏移 | `0x65754` |
| 原指令 | `0x5400004c`：迟到分支进入断言 |
| 新指令 | `0x540002cc`：迟到分支跳到 `0x657ac` 的已有拒绝返回路径 |

不是把断言简单移除后继续入队。`tests/fixtures/rtp/` 保留该 release 的队列源码和小型主机测试桩；先复现原版断言，再验证修复后的超时、容量、乱序、重复和序列号回绕，使用 ASan/UBSan。

**ARM32 没有移植上述两处控制流修复。** 本设备运行 ARM64；虽然 APK 保留上游其他 ABI，不能据此声称这些路径在 ARM32 已验证。其他版本的地址、结构与指令都可能不同。

## 单左手柄

`LeftHandControls` 将左 X 映射为选择；数字/模拟扳机经过 `LeftControlState` 合并和阈值滞回，避免混合报告导致错误松开，暂停时释放状态。事件保留在 VR 控件路径，没有转发成 Mac 游戏手柄输入。

仅把 Y/Menu 映射成 Back 不足以解决问题：实机旧兼容层未可靠送达这些键。所以增加 `LeftTapGesture`，快速双击由 X 触发的点击转换为原生 Back，能退出分辨率页并切换影院菜单。默认双击间隔约 350ms，拖动距离约 64px 时取消双击，长按、三击、切换目标和暂停复位均有回归测试。

## 包名、标签和快捷入口

包名改为 `local.quest.cinema`，避免与原版混淆；主活动仍为 `com.oculus.cinemasdk.MainActivity`。versionCode 7，versionName `1.0-quest-left-stereo-shortcut-rtp`。默认与简体中文标签都为 `★ Quest Cinema Fix`，利用 Lightning Launcher 的星标排序形成前排入口。

这不修改 v50 原生 Dock。启动助手的通知和独立快捷 Activity 也能打开影院；开机启动由助手承担。

## 可复现性

`patch-manifest.json` 保存每个原文件及修改后哈希，文本补丁拒绝偏移/模糊匹配，原生补丁要求原字节相符。最终重建对所有 DEX 和 `.so` 文件做完整清单与 SHA-256 比对，共 11 项，与实机 v7 一致。

签名及 ZIP 元数据可能导致整个 APK 哈希不同；内部代码哈希验证与 APK 签名验证分开进行。改用其他 Apktool、上游版本或自行调整源码后，预期校验失败是保护措施，不能跳过后声称仍是本次实机版本。

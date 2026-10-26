# 修复记录与实现

整理日期：2026-10-25。目标是保留原生 VR 影院的可调大屏，同时兼容 Quest 1 v50 和本次测试的 Sunshine。所有改动针对 [penkamaster/OculusSdk-moonlight 1.0](https://github.com/penkamaster/OculusSdk-moonlight/tree/1.0)，不是对任意 Moonlight APK 的通用二进制补丁。

## v8：视频多 FEC 块与连接恢复

v8 重建 `arm64-v8a` 网络模块，目标 Android API 29；Java、VR 库、左手控制和立体声设置保留 v7 行为。10 个修改后的 C/头文件及前后哈希保存在 `cinema/native/`。基线固定为 [dd966792](https://github.com/penkamaster/OculusSdk-moonlight/commit/dd966792bc3d3807e3c8781e5be68db9bc99192a)，多块 FEC 实现参考 [moonlight-common-c 7174caf5](https://github.com/moonlight-stream/moonlight-common-c/commit/7174caf5f1edafc34341860e233d5079f9dc3c5e)，并适配旧版数据路径。

| 问题 | v8 行为 |
| --- | --- |
| 新服务器把一帧拆为多个纠错块，旧队列按单块处理 | 分块重建后先暂存，整帧完整才向解码器提交 |
| 缺块或重建失败触发 `reconstructFrame()` 断言，或把残帧送入解码器 | 丢弃不完整/损坏帧，等待恢复，不继续提交残缺载荷 |
| 旧客户端发送 Sunshine 不支持的参考帧失效请求 | 发送显式 `0x0302` IDR 请求，恢复到新的关键帧 |
| RTSP `Session` 用旧 16 字节缓冲区接收较长值 | 有界解析，接受前导空白，去掉 `;timeout=…` 参数并校验长度 |

同时保留旧 ENet 应用层回复免等待、Sunshine SDP 参数和迟到音频 RTP 包拒绝逻辑。实现没有关闭客户端认证，也没有通过关闭 FEC 来避开故障。

下面的机器码偏移记录属于 **v7 基线**。v8 的 ARM64 网络库由源码编译，不再把这些偏移补丁应用到新生成的库。上游其他 ABI 仍保留在 APK 中，但本次视频修复只移植并验证了 ARM64；不能把保留 ABI 理解为支持 ARM32。

## Android 10、解码与声音

| 问题 | 修复位置 / 行为 |
| --- | --- |
| 影院没有普通 2D streamView，初始化/失败处理却访问它 | `StreamInterface` 为焦点和 Surface holder 路径增加空值判断 |
| 旧输入捕获实现调用不兼容的鼠标捕获 API | `InputCaptureManager` 返回 NullCaptureProvider，VR 控件继续走原生事件 |
| 旧 Qualcomm HEVC 黑名单拒绝本机解码器 | `MediaCodecHelper` 调整黑名单匹配 |
| H.264 路径一直等关键帧；软件编码未解决 | `PreferenceConfiguration.videoFormat=-1`，选择 HEVC；主机保持硬件编码 |
| 5.1 请求使实际输出只剩一侧 | `enable51Surround=false`，`setAudioConfiguration(0)`，固定立体声 |

这些 Java 层改动以精确 smali 差异保存，构建器验证前后文件哈希。不是整份 SDK 源码再编译。

## v7 基线：新 Sunshine 与旧协议

1. 两个 ABI 的原生库中，将旧字符串 `x-nv-video[0].framesWithInvalidRefThreshold` 替换为 `x-nv-audio.surround.AudioQuality` 并以 NUL 补齐，保持长度不变。本次 Sunshine 要求该 RTSP 参数，传值为 0。
2. ARM64 原生库在偏移 `0x602f8` 将指令 `0x9100a3e1` 改为 `0x14000012`，跳转至 `0x60340`，跳过旧客户端对已经不再适用的 10 秒 ENet 应用层回复等待。

只修改清单中指明的字节，仍使用已有协议流程和已配对的设备证书。没有关闭 Sunshine 的客户端认证。

## v7 基线：迟到音频 RTP 包崩溃

旧 release 1.0 的 `queuePacket()` 断言包序列号不早于预期值。队列因超时或容量先推进预期值后，一个原本进入处理流程的迟到包会违反断言并终止进程。

期望行为是拒绝该迟到包，继续处理后续数据：

```c
/* Original release */
LC_ASSERT(!isBefore16(packet->sequenceNumber, queue->nextRtpSequenceNumber));

/* Behavioral fix */
if (isBefore16(packet->sequenceNumber, queue->nextRtpSequenceNumber)) return 0;
```

v7 已安装 APK 的 ARM64 对应修改（v8 在源码中保留拒绝迟到包的行为）：

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

包名为 `local.quest.cinema`；主活动仍为 `com.oculus.cinemasdk.MainActivity`。当前 versionCode 8，versionName `1.0-quest-left-stereo-multifec`；v7 历史版本名为 `1.0-quest-left-stereo-shortcut-rtp`。默认与简体中文标签都为 `★ Quest Cinema Fix`，利用 Lightning Launcher 的星标排序形成前排入口。

这不修改 v50 原生 Dock。启动助手的通知和独立快捷 Activity 也能打开影院；开机启动由助手承担。

## 可复现性

`patch-manifest.json` 保存 v7 基线的每个原文件及修改后哈希，文本补丁拒绝偏移/模糊匹配，原生补丁要求原字节相符。历史 v7 的全部 DEX 和 `.so` 共 11 项，与实机 v7 的哈希一致。

v8 校验其中未改变的 10 项，再确认 ARM64 网络库与 `--native-library` 指定文件一致。网络模块的固定基线、10 个修改文件和源码哈希由 `cinema/native/manifest.json` 校验。`tested-build.json` 保存实测构建指纹；NDK、工具链与路径可能改变机器码，不承诺跨环境二进制哈希相同。

签名及 ZIP 元数据也可能导致整个 APK 哈希不同，签名独立验证。改用其他 Apktool、上游版本或自行调整源码后，预期校验失败是保护措施，不能跳过后声称仍是本次实机版本。

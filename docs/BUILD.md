# 从源码与补丁构建

## 环境

已验证：macOS，Python 3.10+，JDK 的 `java` / `javac` / `keytool`，Android SDK Platform 34、Build Tools 35.0.0、platform-tools，Apktool 3.0.3。影院 v8 还需要 Android NDK r27c（`27.2.12479018`）。`tools/test.py` 额外需要 Clang、ASan/UBSan 和 POSIX 环境。

从 [Android 官方命令行工具](https://developer.android.com/tools) 安装 SDK，接受许可后安装：

```sh
sdkmanager 'platforms;android-34' 'build-tools;35.0.0' 'platform-tools' 'ndk;27.2.12479018'
```

将 `ANDROID_SDK_ROOT` 指向自己的 SDK 根目录，确保 JDK 和 platform-tools 在 PATH。工具会读取环境变量，也会检查 macOS / Linux 常见 SDK 安装位置。启动助手不需要 NDK；两种构建都不需要 Gradle 或 root。

网络模块构建和公开影院 v8 的完整打包、代码哈希、元数据与签名校验已在 Mac 上通过，见 [VALIDATION.md](VALIDATION.md)。Linux 的主机回归由 CI 检查，完整 APK 构建未在 Linux / Windows 实机验证。某些新版本 JDK 会提示 Java 8 或 native-access 警告；编译命令失败会立即停止，不会带着缺失的类继续打包。

## 启动助手

```sh
python3 tools/build_helper.py
```

输出 `dist/QuestStartupHelper-v4.0.apk`。源码位于 `helper/`，`minSdk=26`、`targetSdk=28`，包名 `local.quest.adbkeeper`，versionCode 4、versionName `4.0-volume-launcher`。构建依次执行 javac、D8、aapt、zipalign 和 apksigner，并检查必要类是否存在、签名是否有效。v4 保留 v3 的权限清单，增加头显音量键快捷入口。

## Quest Cinema Fix

v8 从固定上游源码重建 ARM64 网络模块，再把它装入精确打补丁的原版 APK。目标是 **Quest 1 v50 / Android 10（API 29）/ arm64-v8a**，公开打包器声明 `minSdk=29`。其他 ABI 没有移植或验证本次视频修复。

```sh
python3 tools/build_native.py --ndk /path/to/ndk
python3 tools/build_cinema.py --native-library dist/libmoonlight-core.so
```

`/path/to/ndk` 指 NDK r27c 根目录，路径不能含空格；也可设置 `ANDROID_NDK_ROOT`。网络源码的基线是 [OculusSdk-moonlight 的固定提交](https://github.com/penkamaster/OculusSdk-moonlight/commit/dd966792bc3d3807e3c8781e5be68db9bc99192a)，多 FEC 块处理参考 [moonlight-common-c 的固定提交](https://github.com/moonlight-stream/moonlight-common-c/commit/7174caf5f1edafc34341860e233d5079f9dc3c5e)。构建器读取 `cinema/native/manifest.json`，校验固定基线和 10 个修改文件的源码哈希，输出 `dist/libmoonlight-core.so` 和构建记录 `dist/libmoonlight-core.json`。复制本地构建的库时须同时保留这个同名记录，打包器会检查 ABI、API、NDK、源码清单和库哈希是否一致。依赖从固定上游树在本机取得，不随仓库分发。

第二条命令通过全部校验后输出 `dist/QuestCinemaFix-v8.apk`，versionCode 8、versionName `1.0-quest-left-stereo-multifec`。APK 打包脚本还会下载并核对：

| 输入 | 固定版本 / SHA-256 |
| --- | --- |
| [Moonlight for Go 原版](https://github.com/penkamaster/OculusSdk-moonlight/releases/tag/1.0) | `1.0` / `0cb4c2061cc68e30a171c08cb8a4ba3541f8dbcb50e94d84aeb025bad1055364` |
| [Apktool](https://github.com/iBotPeaches/Apktool/releases/tag/v3.0.3) | `3.0.3` / `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423` |

也可以使用自行获取的**相同原版**：

```sh
python3 tools/build_cinema.py --source-apk /path/to/original.apk --native-library dist/libmoonlight-core.so
```

APK 构建分为两个阶段：

1. 校验固定原版，解包并执行逐文件 before 哈希、精确文本/字节补丁和 after 哈希校验，加入左手控制类。先生成 v7 基线 APK，确认全部 11 个 DEX/原生库哈希一致。
2. 从已验证基线取出原始 DEX 作为 Apktool 的 raw-DEX 输入，再把最低 API 改为 29、版本改为 v8，并替换 ARM64 网络模块。第二次打包后确认其余 10 项代码/库未变，网络库与指定文件一致，最后对齐并签名。

保留已验证 DEX 是为了避免最低 API 提升后 smali 重新编译改变 DEX 格式；它没有跳过 Java 代码检查，也没有改变左手控制实现。

原有 `cinema/patch-manifest.json` 和 `cinema/verified-code-sha256.json` 保留 v7 的补丁与全部 11 项代码哈希基线。v8 只替换其中的 ARM64 网络库；`cinema/native/tested-build.json` 的二进制哈希是已测构建指纹，不要求不同工具链或构建路径产生相同机器码。任何原版、补丁上下文或受保护代码结果不一致都停止。

需要重建历史 v7 做回归比较时可运行 `python3 tools/build_cinema.py --legacy-v7`，输出 `dist/QuestCinemaFix-v7.apk`，无需 NDK，保留原来的最低系统版本元数据。它不包含 v8 的视频恢复修复。

`cinema/java/` 是左手输入代码的可读源码，`cinema/smali/` 是实机版本使用的字节码表示。若修改 Java，必须同步重新生成对应 smali，并重新验证行为和更新预期哈希；不要仅修改 Java 就认为影院构建已使用新逻辑。

这里结合了精确发布版补丁与网络模块源码构建；没有从完整 Oculus SDK 工程重新编译 VR 库。上游源码与授权见 [NOTICE](../NOTICE.md)。历史 v7 的机器码偏移不用于新编译的网络库；说明见 [PATCHES.md](PATCHES.md)。

## 签名和更新

首次构建自动在 `.local/signing/` 生成自己的 PKCS#12 签名与随机密码文件，文件权限限制为当前用户。后续构建沿用同一签名。密码不写入命令行参数，签名文件被 Git 忽略。

如需自己的已有签名，可以明确提供文件：

```sh
python3 tools/build_helper.py --keystore /private/path/key.p12 --password-file /private/path/key.password
python3 tools/build_cinema.py --native-library dist/libmoonlight-core.so --keystore /private/path/key.p12 --password-file /private/path/key.password
```

以上路径是占位示例。构建器适用于单签名条目的 keystore；多 alias 配置需自行调整。

`INSTALL_FAILED_UPDATE_INCOMPATIBLE` 通常表示签名不一致。本项目 Release 的助手使用维护者本地保管的签名，自建 APK 使用你的签名，二者不能直接互相覆盖。优先沿用原签名和原应用；若决定更换签名，先记录并关闭助手开关，了解卸载会删除其设置。影院卸载还会丢失本机配对和选项，需要重新配对。

不要上传 `.local/`、keystore、密码、Sunshine credentials 或 ADB key。完整 APK 的 SHA-256 会因签名、构建元数据而不同；网络模块还可能因 NDK、编译环境和路径不同而变化。源码哈希、受保护代码内容和签名分别验证。

## 测试与发布

```sh
python3 tools/test.py
python3 tools/audit.py
```

前者不连接设备：20 项 Python 测试、3 组 Java 左手状态/手势和音量序列测试、旧音频 RTP 断言复现，以及新的原生视频 ASan/UBSan 回归。Python 测试还覆盖固定原生源码暂存、异常输入保护、NDK 版本限制和 v8 打包的代码保护。也可单独运行 `python3 tools/test_native.py`：它用真实 Reed–Solomon 纠错验证多块重组、乱序、重复、丢块和回绕，并测试实际生产函数的 RTSP Session 解析、IDR 请求和视频载荷边界。这些主机测试不需要 Android NDK，不替代头显解码与网络实测。后者检查可发布文件，拒绝常见私钥和二进制产物混入源码目录；它不能替代人工隐私检查。

源码补丁和安装脚本随本仓库发布；Release 附原创启动助手 v4、源码补丁归档及校验文件。影院完整 SDK、素材和 APK 从上游在使用者本机取得；完整影院 APK 和预编译网络库不随本项目再分发。

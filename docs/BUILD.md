# 从源码与补丁构建

## 环境

已验证：macOS，Python 3.10+，JDK 的 `java` / `javac` / `keytool`，Android SDK Platform 34、Build Tools 35.0.0、platform-tools，Apktool 3.0.3。`tools/test.py` 额外需要 Clang、ASan/UBSan 和 POSIX 环境。

从 [Android 官方命令行工具](https://developer.android.com/tools) 安装 SDK，接受许可后安装：

```sh
sdkmanager 'platforms;android-34' 'build-tools;35.0.0' 'platform-tools'
```

将 `ANDROID_SDK_ROOT` 指向自己的 SDK 根目录，确保 JDK 和 platform-tools 在 PATH。工具会读取环境变量，也会检查 macOS / Linux 常见 SDK 安装位置。无需 Gradle、NDK 或 root。

本次构建在 Mac 上验证；Linux 的主机回归由 CI 检查，完整 APK 构建未在 Linux / Windows 实机验证。某些新版本 JDK 会提示 Java 8 或 native-access 警告；编译命令失败会立即停止，不会带着缺失的类继续打包。

## 启动助手

```sh
python3 tools/build_helper.py
```

输出 `dist/QuestStartupHelper-v4.0.apk`。源码位于 `helper/`，`minSdk=26`、`targetSdk=28`，包名 `local.quest.adbkeeper`，versionCode 4、versionName `4.0-volume-launcher`。构建依次执行 javac、D8、aapt、zipalign 和 apksigner，并检查必要类是否存在、签名是否有效。v4 保留 v3 的权限清单，增加头显音量键快捷入口。

## Quest Cinema Fix

```sh
python3 tools/build_cinema.py
```

输出 `dist/QuestCinemaFix-v7.apk`。脚本下载并核对：

| 输入 | 固定版本 / SHA-256 |
| --- | --- |
| [Moonlight for Go 原版](https://github.com/penkamaster/OculusSdk-moonlight/releases/tag/1.0) | `1.0` / `0cb4c2061cc68e30a171c08cb8a4ba3541f8dbcb50e94d84aeb025bad1055364` |
| [Apktool](https://github.com/iBotPeaches/Apktool/releases/tag/v3.0.3) | `3.0.3` / `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423` |

也可以使用自行获取的**相同原版**：

```sh
python3 tools/build_cinema.py --source-apk /path/to/original.apk
```

构建分为：固定原版校验 → 解包 → 逐文件 before 哈希校验 → 精确文本/字节补丁 → after 哈希校验 → 添加左手控制类 → 重建 → 验证所有 11 个 DEX/原生库内容哈希 → 对齐与签名。

校验值保存在 `cinema/patch-manifest.json` 和 `cinema/verified-code-sha256.json`。任何原版不同、补丁上下文不一致或代码结果不同都停止；不会模糊匹配未知固件或其他 APK。

`cinema/java/` 是左手输入代码的可读源码，`cinema/smali/` 是实机版本使用的字节码表示。若修改 Java，必须同步重新生成对应 smali，并重新验证行为和更新预期哈希；不要仅修改 Java 就认为影院构建已使用新逻辑。

这里采用**精确发布版补丁构建**，没有声称从完整 Oculus SDK 工程重新编译所有原生库。上游源码与授权见 [NOTICE](../NOTICE.md)。ARM64 两处机器码修复不能直接应用于其他版本或 ARM32；说明见 [PATCHES.md](PATCHES.md)。

## 签名和更新

首次构建自动在 `.local/signing/` 生成自己的 PKCS#12 签名与随机密码文件，文件权限限制为当前用户。后续构建沿用同一签名。密码不写入命令行参数，签名文件被 Git 忽略。

如需自己的已有签名，可以明确提供文件：

```sh
python3 tools/build_helper.py --keystore /private/path/key.p12 --password-file /private/path/key.password
python3 tools/build_cinema.py --keystore /private/path/key.p12 --password-file /private/path/key.password
```

以上路径是占位示例。构建器适用于单签名条目的 keystore；多 alias 配置需自行调整。

`INSTALL_FAILED_UPDATE_INCOMPATIBLE` 通常表示签名不一致。本项目 Release 的助手使用维护者本地保管的签名，自建 APK 使用你的签名，二者不能直接互相覆盖。优先沿用原签名和原应用；若决定更换签名，先记录并关闭助手开关，了解卸载会删除其设置。影院卸载还会丢失本机配对和选项，需要重新配对。

不要上传 `.local/`、keystore、密码、Sunshine credentials 或 ADB key。完整 APK 的 SHA-256 会因签名、构建元数据而不同；影院内部代码哈希的一致性单独验证。

## 测试与发布

```sh
python3 tools/test.py
python3 tools/audit.py
```

前者不连接设备：Python 管理工具测试、Java 左手状态/手势和音量序列测试、原版 RTP 断言复现及修复后的 ASan/UBSan 回归。后者检查可发布文件，拒绝常见私钥和二进制产物混入源码目录；它不能替代人工隐私检查。

完整源码和安装脚本随本仓库发布；Release 只附原创启动助手及校验文件。影院完整 SDK、素材和 APK 从上游在使用者本机取得，不随仓库再分发。

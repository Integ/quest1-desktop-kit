# 影院 v12：播放头显里的本地视频

影院 v12（`1.0-quest-local-video-stereo-multifec`，versionCode 12）在电脑列表里增加了 **Local Videos**，可以在 VR 影院的大屏幕上直接播放头显里的视频，不需要电脑。Mac 串流、场景、左手操作都和 v8 相同，另外加入了音量键导航（见 [CONTROLLER-FREE.md](CONTROLLER-FREE.md)）。

## 使用

1. 把视频放进头显的 `Movies` 或 `Download` 文件夹，比如用 [Quest 控制台](CONSOLE.md) 的“媒体”区拖放上传，或者运行 `adb push 视频.mp4 /sdcard/Movies/`。
2. 打开影院，看向 **Local Videos**，确认进入。
3. 看向视频海报，确认后开始播放。

- 支持 mp4、m4v、mkv、webm、mov、3gp、ts，能否播放取决于 Quest 1 的硬件解码。实测 H.264 1080p 60 帧正常。
- **海报**：用 Android 字体绘制，包含视频里的一帧画面、完整文件名（中文也可以）和时长。影院界面下方的标题字体只支持西文，中文文件名会显示成 `Video K3Z` 这种固定编码，请看海报辨认。
- **断点续播**：每 5 秒保存一次进度。再次打开时，如果上次看过了 30 秒、又没到最后 30 秒，就从上次的位置继续。
- **游戏手柄**：≡（Start / 菜单键）或媒体播放键暂停或继续，LB / RB 快退或快进 10 秒。
- 摘下头显会自动暂停，戴上后继续；播完后回到列表。
- 本地视频在每台电脑的应用列表里都会出现（例如和 Mac Desktop 排在一起）；Mac 不在线时也能播放。

## 原理

原生影院界面（C++）只通过 `MainActivity` 里的十几个 Java 方法和外部交流：`nativeAddPc` / `nativeAddApp` 往列表里加项目，`startMovie` / `stopMovie` 开始和停止，`nativePrepareNewVideo` 给出影院屏幕的 `SurfaceTexture`。v12 只改 Java 层：

- 新增 `local.quest.cinema.LocalVideos`：扫描文件夹、绘制海报、用 `MediaPlayer` 把画面直接画到影院屏幕的纹理上，以及处理手柄按键。
- 新增 `LocalVideoCatalog`：文件规则、标题、续播位置。不依赖 Android，带主机测试。
- `MainActivity` 的 16 个方法开头各加一段判断：是本地视频就交给 `LocalVideos`，否则照原样运行。
- `PcSelector` 里有一处 `nativeAddPc` 调用，改为先经过 `LocalVideos.addRemotePc`：已配对的电脑会立刻从缓存加载它的应用列表。

几个由原生界面决定的细节：

- **应用列表所有电脑共用，而且只在打开时读取一次**。列表是空的会立即报错、退回大厅；之后再加入的项目也不会刷新进当前列表。所以本地视频在影院启动时就加入列表；之后每次打开列表前（原生界面会先调用 `stopMovie`），在渲染线程上快速重新扫描文件夹，增删列表项。播放按应用编号分流，不按电脑。
- **海报文件由原生界面在 `AddApp` 时直接读取**，并上传为 GL 纹理。所以列表操作只在渲染线程上做；海报在后台线程绘制，画好后在下一次同步时加入列表。
- **列表按名字合并重复项**：标题必须唯一，同名文件会自动加上 “ 2”、“ 3” 这样的后缀。
- `MediaPlayer` 在准备好之前不能调用 `getDuration()`，否则会报错 -38。

## 构建

先按 [BUILD.md](BUILD.md) 构建 v8，再运行：

```sh
python3 tools/build_cinema_v12.py            # 输入 dist/QuestCinemaFix-v8.apk，输出 dist/QuestCinemaFix-v12.apk
python3 tools/quest.py install-cinema dist/QuestCinemaFix-v12.apk
```

构建器会合并 `cinema/java` 和 `cinema/v12/java`（同名文件以后者为准）来编译 Java 类，`cinema/v12/stubs` 只用于编译、不进 APK；然后插入上述 smali 改动并把版本改为 12。最终 APK 只从重新打包的结果中取 `classes.dex` 和 `AndroidManifest.xml`，其余所有条目都原样取自 v8，并会核对 302 个原生库、素材和资源文件与 v8 逐字节一致。签名规则与 v8 相同：必须和已安装的影院使用同一个签名才能原地升级。

## 验证范围

- 主机测试：`LocalVideoCatalogTest` 覆盖文件识别、标题与去重、编号、续播、跳转和时长显示。
- 实机：在一台 Quest 1 v50 上，用户从 Local Videos 播放了一段 H.264 1080p60 视频；第二次打开时从 63.9 秒处续播。已配对 Mac 上线后，影院从缓存提前加载了 Mac Desktop。用仓库构建器生成的 v12 也在同一台头显上通过了启动冒烟测试（列表和海报正常加载，无校验错误）。
- 尚未验证：H.265、mkv、长视频、竖屏视频的旋转，以及大量视频时首次生成海报的耗时。

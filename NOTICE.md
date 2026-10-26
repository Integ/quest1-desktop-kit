# Attribution and distribution

This repository was assembled on 2026-10-25 from a working Quest 1 setup.
Original helper, input logic, build/admin tools, tests and documentation are
Copyright (C) 2026 quest1-desktop-kit contributors, licensed under
**GPL-3.0-or-later**, with no warranty. See [LICENSE](LICENSE).

Third-party material retains its original attribution and terms. This notice
does not relicense the Oculus SDK, its assets or any upstream component.

| Component | Upstream / terms / use here |
| --- | --- |
| Legacy Moonlight VR / Moonlight for Go | [penkamaster/OculusSdk-moonlight, release 1.0](https://github.com/penkamaster/OculusSdk-moonlight/tree/1.0). Mixed upstream tree; root GPLv3 and separate Oculus SDK/Cinema notices. This repository provides patch context, integrity metadata and an upstream download reference, not a complete repackaged APK. |
| Moonlight common C queue | [Release source](https://github.com/penkamaster/OculusSdk-moonlight/tree/1.0/moonlight-common/src/main/jni/moonlight-core/moonlight-common-c). GPLv3; two unmodified queue source/header fixtures are included for regression, with project-owned test stubs. |
| Cinema v8 network backport | The 10 patched C/header files under `cinema/native/` derive from the original network code at commit `dd966792bc3d3807e3c8781e5be68db9bc99192a`, with multi-FEC staging adapted from [moonlight-common-c commit 7174caf](https://github.com/moonlight-stream/moonlight-common-c/commit/7174caf5f1edafc34341860e233d5079f9dc3c5e). These GPLv3-derived files retain their upstream terms; project changes and tests are identified in the source and documentation. |
| Reed–Solomon regression fixture | Unchanged `rs.c` and `rs.h` from the pinned Moonlight 1.0 tree are included under `tests/native_video/reedsolomon/`. Their BSD-style license and original attribution remain in `rs.c`; see the [fixture README](tests/native_video/README.md). |
| Oculus Cinema sample | Oculus VR, LLC; BSD 2-Clause, copied from the upstream sample's LICENSE-Cinema.txt into [LICENSES/Oculus-Cinema-BSD.txt](LICENSES/Oculus-Cinema-BSD.txt). Patch context touching the sample retains those terms. |
| Oculus Mobile SDK | Oculus VR, LLC; upstream license retained in [LICENSES/Oculus-SDK.txt](LICENSES/Oculus-SDK.txt). SDK binaries and theater assets are not included here or in project releases. Review upstream terms before downloading/building locally. |
| Moonlight Android | [moonlight-stream/moonlight-android](https://github.com/moonlight-stream/moonlight-android). Reference and tested alternative; no APK mirrored here. |
| Lightning Launcher | [threethan/LightningLauncher](https://github.com/threethan/LightningLauncher). Used on the test device; no APK or source bundled here. |
| Sunshine | [LizardByte/Sunshine](https://github.com/LizardByte/Sunshine). Host software installed separately; this repository generates private local configuration and documents its use. |
| Apktool | [iBotPeaches/Apktool](https://github.com/iBotPeaches/Apktool), Apache-2.0. A pinned release is fetched as a build tool; it is not vendored or redistributed in this repository. |
| Android SDK / NDK / JDK / Clang | Installed separately under their own licenses. v8 was built with Google's NDK r27c, not vendored here. The native build obtains unchanged JNI and dependency inputs from the pinned upstream tree under their own terms. |

The public release APK is the original `local.quest.adbkeeper` helper only.
Its complete corresponding source and build/install scripts are provided in
the same repository/tag (`helper/`, `tools/build_helper.py`, `tools/common.py`,
`tools/quest.py`, and `docs/BUILD.md`). Signing keys are kept private; users can
build and install their own signed copies on their own headsets.

Kit release v0.1.0 contains helper v3; kit releases v0.1.1 and v0.2.0 contain helper v4.
Use the matching Git tag for the exact corresponding source of each release.

The cinema modifications are prominently identified as **Quest Cinema Fix**,
package `local.quest.cinema`, currently versionCode 8. The historical v7 baseline
remains available through its source tag and legacy build option. These are not an official update
from Meta, Oculus, Moonlight, Sunshine or the original VR client author.

Only source, patches and build metadata for the cinema network module are published;
precompiled network libraries are not release assets. Local v8 builds verify the
fixed source and packaging inputs, without claiming identical native binaries for
every compiler or build path.

Do not upload SDK assets, complete upstream APKs, private credentials or personal
device logs to this repository when contributing.

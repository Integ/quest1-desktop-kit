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
| Oculus Cinema sample | Oculus VR, LLC; BSD 2-Clause, copied from the upstream sample's LICENSE-Cinema.txt into [LICENSES/Oculus-Cinema-BSD.txt](LICENSES/Oculus-Cinema-BSD.txt). Patch context touching the sample retains those terms. |
| Oculus Mobile SDK | Oculus VR, LLC; upstream license retained in [LICENSES/Oculus-SDK.txt](LICENSES/Oculus-SDK.txt). SDK binaries and theater assets are not included here or in project releases. Review upstream terms before downloading/building locally. |
| Moonlight Android | [moonlight-stream/moonlight-android](https://github.com/moonlight-stream/moonlight-android). Reference and tested alternative; no APK mirrored here. |
| Lightning Launcher | [threethan/LightningLauncher](https://github.com/threethan/LightningLauncher). Used on the test device; no APK or source bundled here. |
| Sunshine | [LizardByte/Sunshine](https://github.com/LizardByte/Sunshine). Host software installed separately; this repository generates private local configuration and documents its use. |
| Apktool | [iBotPeaches/Apktool](https://github.com/iBotPeaches/Apktool), Apache-2.0. A pinned release is fetched as a build tool; it is not vendored or redistributed in this repository. |
| Android SDK / JDK / Clang | Installed separately under their own licenses. |

The public release APK is the original `local.quest.adbkeeper` helper only.
Its complete corresponding source and build/install scripts are provided in
the same repository/tag (`helper/`, `tools/build_helper.py`, `tools/common.py`,
`tools/quest.py`, and `docs/BUILD.md`). Signing keys are kept private; users can
build and install their own signed copies on their own headsets.

Kit release v0.1.0 contains helper v3; kit release v0.1.1 contains helper v4.
Use the matching Git tag for the exact corresponding source of each release.

The cinema modifications are prominently identified as **Quest Cinema Fix**,
package `local.quest.cinema`, versionCode 7. They are not an official update
from Meta, Oculus, Moonlight, Sunshine or the original VR client author.

Do not upload SDK assets, complete upstream APKs, private credentials or personal
device logs to this repository when contributing.

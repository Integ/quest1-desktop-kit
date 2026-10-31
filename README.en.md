# quest1-desktop-kit

Reuse an original Oculus / Meta Quest 1 as a large VR screen for a computer.
This kit documents a real **Quest 1 v50 / Android 10 + Apple Silicon Mac** setup
with **only a left Touch controller**.

- Sunshine desktop mirroring with HEVC and working two-channel audio.
- Patches for the legacy native-VR Moonlight cinema client: Android 10 crashes,
  current Sunshine protocol compatibility, left-hand input, stereo and a late-RTP crash.
- Cinema v8 rebuilds the ARM64 network module with complete multi-FEC-frame staging,
  corrupt-frame recovery, explicit IDR requests and bounded RTSP Session parsing.
- Single X selects; a quick double X opens/closes the cinema menu or goes back.
- Original startup helper source and a downloadable APK: optional cinema autostart,
  USB debugging recovery after reboot, and Wi-Fi debugging retention.
- Helper v4 adds a tested physical-headset-volume shortcut: down, up, down, up
  opens Lightning Launcher, so a missing right controller does not trap you after
  cinema exits. Enable with `python3 tools/quest.py volume-shortcut on`.
- Optional Store/Featured suppression, time-zone correction, reversible admin tools,
  build integrity checks and host-side regressions.

New in v0.3.0 (see [CHANGELOG](CHANGELOG.md)):

- **No controller at all.** Cinema v12 is driven with the headset volume keys
  (tap + confirms, tap − goes back, hold moves left/right). Helper v10 detects a
  held down/up/down/up in Meta VR Home by polling the media volume, and reopens
  Lightning Launcher whenever VR Home is left empty (`idle-launcher on`, which
  grants `READ_LOGS` over ADB and matches a single shell retry line).
  See [CONTROLLER-FREE.md](docs/CONTROLLER-FREE.md) (Chinese).
- **Local videos in the cinema.** Cinema v12 adds a "Local Videos" entry that plays
  files from the headset's Movies and Download folders on the theater screen with
  MediaPlayer, with posters showing the full file name, resume and gamepad
  pause/seek. Java-only: `tools/build_cinema_v12.py` turns your v8 APK into v12 and
  verifies native code, assets and resources are unchanged.
  See [LOCAL-VIDEO.md](docs/LOCAL-VIDEO.md).
- **Mac console.** `Open Console.command` serves a localhost-only page for status,
  screenshots, app launch/install, video upload, system settings pages, power,
  helper toggles and Sunshine. Standard-library Python only.
  See [CONSOLE.md](docs/CONSOLE.md).
- Why hand tracking cannot be enabled without a Meta account, and why FirstTimeNux
  must not be re-enabled temporarily: [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

Start with the [Chinese setup guide](docs/SETUP.md) and [build guide](docs/BUILD.md).
The commands are also listed in the [main README](README.md).
Python 3.10+, JDK and Android SDK platform/build tools are needed for local builds.
Cinema v8 also needs NDK r27c (`27.2.12479018`) and targets Quest 1 v50 /
arm64-v8a / Android API 29. The public packager declares a minimum API of 29;
the new native path is not validated on ARM32.
Build its module with `python3 tools/build_native.py --ndk /path/to/ndk`, then run
`python3 tools/build_cinema.py --native-library dist/libmoonlight-core.so`.
Run `python3 tools/test.py` for 20 hardware-free Python tests, three Java test
groups and sanitized C regressions; all passed. The public native build and
two-stage v8 APK build also passed code-hash, API/version and signature checks.
The second stage retains verified DEX bytes while raising the minimum API,
so smali does not rebuild the tested Java code with a different DEX format.

**An already authorized ADB connection is required.** This is not a universal
factory-setup or missing-right-controller bypass. The headset used in this case
was initially bootstrapped with an Android phone, but that process was not captured
well enough to promise a reproducible onboarding tool. See [bootstrap limits](docs/BOOTSTRAP.md).

The display is a mirror, not an independent macOS extended monitor. Use the Void
theater and reduce Distance for a larger apparent screen. Y and the left Menu
button did not reliably reach the legacy compatibility layer; double X was tested.

The helper APK is available under [Releases](https://github.com/Integ/quest1-desktop-kit/releases),
with its complete source under `helper/` and build instructions. The full cinema APK,
Oculus SDK binaries/assets, personal pairing state and signing keys are not distributed.
The cinema builder downloads a SHA-256-pinned upstream APK and applies strict
baseline patches. v8 preserves the other 10 DEX/native-library entries and inserts
the specified rebuilt network library; source hashes are checked, while native
binaries are not claimed to be byte-identical across toolchains or build paths.
Use `--legacy-v7` only to reproduce the historical v7 baseline without NDK.
You must review the upstream terms when using that client. No prebuilt cinema
network library is distributed in this repository or its releases.

Tested on one physical headset; see [validation details](docs/VALIDATION.md) and
[recovery commands](docs/RECOVERY.md). Original kit code is GPL-3.0-or-later;
third-party material retains its own terms, listed in [NOTICE](NOTICE.md).

v8 addresses the video FEC assertion and recovery paths found after v7. The user
confirmed approximately three minutes of stable picture and normal audio, including
recovery after actual loss. The test used an 8 Mbps Sunshine video cap, hardware
HEVC and normal FEC. Some VideoToolbox keyframe warnings remain; long-duration,
other-network and new reboot testing are not claimed. Helper v4 is unchanged.
See [technical fixes](docs/PATCHES.md) and [volume-shortcut setup](docs/VOLUME-SHORTCUT.md).

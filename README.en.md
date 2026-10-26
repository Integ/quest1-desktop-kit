# quest1-desktop-kit

Reuse an original Oculus / Meta Quest 1 as a large VR screen for a computer.
This kit documents a real **Quest 1 v50 / Android 10 + Apple Silicon Mac** setup
with **only a left Touch controller**.

- Sunshine desktop mirroring with HEVC and working two-channel audio.
- Patches for the legacy native-VR Moonlight cinema client: Android 10 crashes,
  current Sunshine protocol compatibility, left-hand input, stereo and a late-RTP crash.
- Single X selects; a quick double X opens/closes the cinema menu or goes back.
- Original startup helper source and a downloadable APK: optional cinema autostart,
  USB debugging recovery after reboot, and Wi-Fi debugging retention.
- Helper v4 adds a tested physical-headset-volume shortcut: down, up, down, up
  opens Lightning Launcher, so a missing right controller does not trap you after
  cinema exits. Enable with `python3 tools/quest.py volume-shortcut on`.
- Optional Store/Featured suppression, time-zone correction, reversible admin tools,
  build integrity checks and host-side regressions.

Start with the [Chinese setup guide](docs/SETUP.md) and [build guide](docs/BUILD.md).
The commands are also listed in the [main README](README.md).
Python 3.10+, JDK and Android SDK platform/build tools are needed for local builds.
Run `python3 tools/test.py` for hardware-free Python, Java and sanitized C tests.

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
`python3 tools/build_cinema.py` downloads a SHA-256-pinned upstream release, applies
strict patches and checks all 11 code/native-library hashes against the tested build.
You must review the upstream terms when using that client.

Tested on one physical headset; see [validation details](docs/VALIDATION.md) and
[recovery commands](docs/RECOVERY.md). Original kit code is GPL-3.0-or-later;
third-party material retains its own terms, listed in [NOTICE](NOTICE.md).

Known issue: cinema v7 later hit a separate video `RtpFecQueue.c` recovery
assertion. That crash is still unresolved; the v4 shortcut restores access to the
app list and does not fix this video path. The earlier audio reorder-queue fix
remains in place. See [volume-shortcut setup](docs/VOLUME-SHORTCUT.md).

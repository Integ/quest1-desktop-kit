# Changelog

## v0.3.0 — 2026-10-30

- Controller-free use on a Quest 1 with no Touch controllers and no Meta account
  (see `docs/CONTROLLER-FREE.md`).
- Helper v10 (`10.0-console-status`): Meta VR Home volume gesture by polling the
  media volume (held down/up/down/up); opt-in "open the app list when VR Home is
  empty", which matches only the shell's `LaunchFirstTimeNux(crash_recovery)`
  retry line and needs `READ_LOGS` granted over ADB (`tools/quest.py
  idle-launcher on`); service restart on `MY_PACKAGE_REPLACED`; admin `STATUS`
  reports every toggle and `IDLE_ENABLE` / `IDLE_DISABLE` were added.
- Cinema v12 (`1.0-quest-local-video-stereo-multifec`): headset volume-key
  navigation (tap + confirm, tap − back/menu, hold left/right, quick
  down/up/down/up opens Lightning Launcher) and a "Local Videos" entry that plays
  Movies/Download files in the theater with MediaPlayer, posters with full file
  names, resume, gamepad pause/seek and preloading of paired computers' apps.
  Java-only; `tools/build_cinema_v12.py` builds it from v8 and verifies native
  code, assets and resources are unchanged.
- Mac console (`console/`, `Open Console.command`): localhost-only web page for
  status, screenshots, apps, APK/OBB install with compatibility checks, video
  upload, settings pages, power, helper toggles, mirroring and Sunshine. Device
  details stay in `.local/console.json`.
- Troubleshooting for hand tracking without an account, the FirstTimeNux retry
  loop, autostart hidden behind the wireless-debugging prompt, macOS Local Network
  blocking `adb connect`, and a Lightning Launcher crash on key-triggered clicks.
- Audit now also flags Quest 1 serial numbers. Release ships the device-tested
  helper v10 APK and the source archive; cinema APKs remain excluded.

## v0.2.0 — 2026-10-25

- Publish cinema v8 (`1.0-quest-left-stereo-multifec`) ARM64 network source and
  a pinned NDK r27c / Android 29 build path. Helper stays at v4.
- Backport upstream multi-FEC complete-frame staging; reject incomplete or corrupt
  frames and request recovery instead of taking the old assertion path.
- Send explicit `0x0302` IDR requests for Sunshine and retain the ENet reply-wait
  and audio RTP fixes. Add bounded RTSP Session-token parsing with leading-space
  and timeout-parameter handling.
- Preserve pairing, Java/VR code, left-hand controls, stereo and launcher entries.
- Record a roughly three-minute stable picture/audio test with real-loss recovery
  at an 8 Mbps host cap. Some host keyframe warnings remain; no new reboot or
  long-duration claim. Keep pre-release status.
- Distribute source/build tools and the original helper APK only. Complete cinema
  APKs, SDK assets and prebuilt cinema network libraries remain excluded.

## v0.1.1 — 2026-10-25

- Publish helper v4 (`4.0-volume-launcher`): an opt-in headset volume
  down/up/down/up sequence opens Lightning Launcher after cinema exits,
  without a right controller. Confirmed with physical headset buttons.
- Preserve USB/Wi-Fi retention and cinema autostart; no added Manifest
  permissions. Add on/off UI, protected admin actions and sequence regressions.
- Add `volume-shortcut on/off` CLI commands and portable Mac quick-open scripts.
- Document the separate, still unresolved video FEC assertion. Cinema remains
  versionCode 7; its patches and internal code hashes are unchanged.
- Retain the one-headset pre-release scope; no new v4 reboot claim.

## v0.1.0 — 2026-10-25

First public kit, based on one tested Quest 1 v50 installation.

- Publish startup helper v3 source: independent USB/Wi-Fi ADB retention,
  once-per-boot cinema startup, scrollable settings and quick-open entries.
- Publish exact upstream-1.0 cinema patches for Android 10, HEVC, current
  Sunshine compatibility, stereo audio, left-controller input, starred launcher
  label and ARM64 late-RTP rejection (cinema versionCode 7).
- Add strict local builders, reversible admin tools, private Sunshine config
  generation and stale-session recovery.
- Add Chinese setup/recovery/technical documentation, English overview and
  scoped validation records; include Python, Java and sanitized C regressions.

The pre-release label reflects limited hardware coverage. Cinema APKs and
Oculus SDK assets are not distributed; build locally from the pinned upstream.

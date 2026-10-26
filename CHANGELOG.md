# Changelog

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

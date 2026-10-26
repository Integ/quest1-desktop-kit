# RTP regression fixture

`RtpReorderQueue.c` and `RtpReorderQueue.h` are unmodified files from
[OculusSdk-moonlight release 1.0](https://github.com/penkamaster/OculusSdk-moonlight/tree/1.0/moonlight-common/src/main/jni/moonlight-core/moonlight-common-c/src).
They are part of Moonlight's GPLv3 code; see the repository root `LICENSE` and
[the upstream license](https://github.com/penkamaster/OculusSdk-moonlight/blob/1.0/moonlight-common/src/main/jni/moonlight-core/moonlight-common-c/LICENSE.txt).

`test.c`, `Limelight-internal.h`, and `Video.h` are small project-owned test
harness files (GPL-3.0-or-later). Their packet struct models only the fields
needed by this queue test; this is not a replacement network implementation.

The runner first proves that the original source aborts on a delayed packet
after the expected sequence changes. It then replaces the single assertion
with rejection and tests normal order, duplicates, sequence wrap, timeout,
and queue capacity under AddressSanitizer and UndefinedBehaviorSanitizer.
This is a host-side behavioral regression test, not an ARM64 emulation test.

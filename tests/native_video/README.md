# Native video regression harness

Run `python3 tools/test_native.py`, or the full `python3 tools/test.py` suite.
These checks need Clang, ASan/UBSan and Python; they use no headset, ADB, network
or Android NDK. Generated source, objects and executables stay in a temporary
directory and are removed after the run.

The queue test compiles the actual `cinema/native/src/RtpFecQueue.c` and header.
It generates real parity shards and checks reconstructed payload bytes across
three FEC blocks, out-of-order and duplicated packets, missing blocks, injected
reconstruction failure, RTP/frame-number wrap and malformed input. The wrapper
can force an RS error to exercise the old assertion failure path without
substituting the real RS implementation for successful recovery.

The RTSP/control and depacketizer tests extract the actual production functions
from `cinema/native/src/` into small host contexts. Their stubs isolate transport,
decoder and queue callbacks; they are not full codec or Android integration
tests. They cover bounded session parsing, leading whitespace and timeout
parameters, explicit IDR control messages, legacy fallback, multi-block frame
boundaries, parity-index gaps, corruption rejection and next-frame resumption.

`reedsolomon/rs.c` and `rs.h` are unchanged from
[OculusSdk-moonlight tag 1.0](https://github.com/penkamaster/OculusSdk-moonlight/tree/1.0/moonlight-common/src/main/jni/moonlight-core/moonlight-common-c/reedsolomon).
Their original BSD-style license and attribution remain at the top of `rs.c`.
Other harness files are project-owned GPL-3.0-or-later code. The production
Moonlight-derived files retain their upstream terms; see the repository NOTICE.

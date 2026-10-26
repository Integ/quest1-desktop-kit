#!/usr/bin/env python3
"""Run host regressions without ADB or a headset. SPDX-License-Identifier: GPL-3.0-or-later."""
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile

from common import ROOT, KitError, executable, run


def main():
    run([sys.executable, '-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-v'])
    with tempfile.TemporaryDirectory(prefix='quest-kit-tests-') as directory:
        folder = Path(directory)
        source = ROOT / 'cinema/java/local/quest/cinema'
        run([executable('javac'), '-d', folder, source / 'LeftControlState.java',
             source / 'LeftTapGesture.java', ROOT / 'tests/LeftControlStateTest.java',
             ROOT / 'tests/LeftTapGestureTest.java',
             ROOT / 'helper/src/local/quest/adbkeeper/VolumeShortcut.java',
             ROOT / 'tests/VolumeShortcutTest.java'])
        for name in ['LeftControlStateTest', 'LeftTapGestureTest', 'VolumeShortcutTest']:
            run([executable('java'), '-cp', folder, name])
        fixture = ROOT / 'tests/fixtures/rtp'
        original = (fixture / 'RtpReorderQueue.c').read_text()
        assertion = 'LC_ASSERT(!isBefore16(packet->sequenceNumber, queue->nextRtpSequenceNumber));'
        if original.count(assertion) != 1:
            raise KitError('Unexpected legacy RTP fixture')
        (folder / 'fixed.c').write_text(original.replace(assertion,
            'if (isBefore16(packet->sequenceNumber, queue->nextRtpSequenceNumber)) return 0;'))
        compiler = executable('clang')
        flags = ['-g', '-O1', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-I', fixture]
        original_binary, fixed_binary = folder / 'original', folder / 'fixed'
        for source, output in [(fixture / 'RtpReorderQueue.c', original_binary), (folder / 'fixed.c', fixed_binary)]:
            run([compiler, *flags, source, fixture / 'test.c', '-o', output])
        environment = dict(os.environ, ASAN_OPTIONS='detect_leaks=0')

        def no_core_dump():
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

        broken = subprocess.run([str(original_binary), 'late'], capture_output=True,
            text=True, env=environment, timeout=10, preexec_fn=no_core_dump)
        if broken.returncode == 0 or 'Assertion' not in broken.stderr and 'Assertion' not in broken.stdout:
            raise KitError('Original release did not reproduce the expected assertion')
        print('PASS: original release reproduces the RTP assertion')
        run([fixed_binary, 'late'], env=environment)
    print('All host checks passed. These checks do not replace headset testing.')


if __name__ == '__main__':
    try:
        main()
    except KitError as error:
        raise SystemExit(str(error))

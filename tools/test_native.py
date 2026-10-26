#!/usr/bin/env python3
"""Offline native-video regressions. SPDX-License-Identifier: GPL-3.0-or-later."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import tempfile

from common import ROOT, KitError, executable, run

SOURCE = ROOT / 'cinema/native/src'
FIXTURE = ROOT / 'tests/native_video'


def extract_function(source: str, marker: str) -> str:
    """Select a real C function, ignoring braces inside comments/string literals."""
    if source.count(marker) != 1:
        raise KitError(f'Expected one native function: {marker}')
    start = source.index(marker)
    brace = source.index('{', start)
    pattern = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{}]', re.S)
    depth = 0
    for token in pattern.finditer(source, brace):
        if token.group() == '{':
            depth += 1
        elif token.group() == '}':
            depth -= 1
            if depth == 0:
                return source[start:token.end()]
    raise KitError(f'Unterminated native function: {marker}')


def render_template(name: str, replacements: dict[str, str]) -> str:
    text = (FIXTURE / name).read_text()
    for marker, function in replacements.items():
        if text.count(marker) != 1:
            raise KitError('Unexpected native regression template')
        text = text.replace(marker, function)
    return text


def main():
    required = ['RtpFecQueue.c', 'RtpFecQueue.h', 'Video.h', 'RtspConnection.c',
                'ControlStream.c', 'VideoDepacketizer.c']
    if any(not (SOURCE / name).is_file() for name in required):
        raise KitError('Missing published cinema/native/src files')
    compiler = executable('clang')
    environment = dict(os.environ, ASAN_OPTIONS='detect_leaks=0')
    with tempfile.TemporaryDirectory(prefix='quest-native-tests-') as directory:
        work = Path(directory)
        for name in ['RtpFecQueue.c', 'RtpFecQueue.h']:
            shutil.copyfile(SOURCE / name, work / name)
        shutil.copyfile(FIXTURE / 'Limelight-internal.h', work / 'Limelight-internal.h')
        video = (SOURCE / 'Video.h').read_text()
        # Only packed wire structs are needed; avoid unrelated Android queue headers.
        anchor = '#pragma pack(push, 1)'
        if video.count(anchor) != 1:
            raise KitError('Unexpected native packet header')
        (work / 'Video.h').write_text('#pragma once\n#include <stdint.h>\n' + video[video.index(anchor):])
        flags = ['-g', '-O1', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                 '-I', work, '-I', FIXTURE / 'reedsolomon']
        rs_object = work / 'rs.o'
        run([compiler, *flags, '-Dreed_solomon_reconstruct=real_reed_solomon_reconstruct',
             '-c', FIXTURE / 'reedsolomon/rs.c', '-o', rs_object])
        queue_test = work / 'video-test'
        run([compiler, *flags, work / 'RtpFecQueue.c', FIXTURE / 'test_video.c', rs_object,
             '-o', queue_test])
        run([queue_test], env=environment)

        parse = extract_function((SOURCE / 'RtspConnection.c').read_text(), 'static int parseRtspSessionId(')
        idr = extract_function((SOURCE / 'ControlStream.c').read_text(), 'static void requestIdrFrame(')
        control = render_template('control_template.c', {
            '/* @RTSP_SESSION_FUNCTION@ */': parse,
            '/* @IDR_REQUEST_FUNCTION@ */': idr,
        })
        depacketizer = (SOURCE / 'VideoDepacketizer.c').read_text()
        payload = render_template('depacketizer_template.c', {
            '/* @FIRST_PACKET_FUNCTION@ */': extract_function(depacketizer, 'static int isFirstPacket('),
            '/* @PROCESS_PAYLOAD_FUNCTION@ */': extract_function(depacketizer, 'void processRtpPayload('),
        })
        for name, generated in [('control', control), ('depacketizer', payload)]:
            path, binary = work / (name + '.c'), work / name
            path.write_text(generated)
            run([compiler, *flags, path, '-o', binary])
            run([binary], env=environment)
    print('Native-video ASan/UBSan regressions passed; hardware/codec testing remains separate.')


if __name__ == '__main__':
    try:
        main()
    except KitError as error:
        raise SystemExit(str(error))

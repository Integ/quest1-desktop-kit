#!/usr/bin/env python3
"""Reproduce the tested Quest Cinema patch locally. SPDX-License-Identifier: GPL-3.0-or-later."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

from common import ROOT, LOCAL, CACHE, DIST, KitError, download, executable, run, sha256, sign_apk
from build_native import verify_library

APK_URL = 'https://github.com/penkamaster/OculusSdk-moonlight/releases/download/1.0/com.penkamaster.moonlightForGo.apk'
APK_SHA = '0cb4c2061cc68e30a171c08cb8a4ba3541f8dbcb50e94d84aeb025bad1055364'
APKTOOL_URL = 'https://github.com/iBotPeaches/Apktool/releases/download/v3.0.3/apktool_3.0.3.jar'
APKTOOL_SHA = 'dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423'


def apply_text_patch(original: str, patch: str) -> str:
    """Apply generated unified hunks at exact positions, without offset/fuzzy matching."""
    source = original.splitlines(keepends=True)
    lines = patch.splitlines(keepends=True)
    output, cursor, index = [], 0, 0
    while index < len(lines):
        line = lines[index]
        if line.startswith(('--- ', '+++ ')):
            index += 1
            continue
        match = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
        if not match:
            raise KitError('Malformed patch hunk')
        position = max(0, int(match[1]) - 1)
        if position < cursor or position > len(source):
            raise KitError('Invalid patch position')
        output.extend(source[cursor:position])
        cursor, index = position, index + 1
        old_count = new_count = 0
        while index < len(lines) and not lines[index].startswith('@@ '):
            item = lines[index]
            if not item or item[0] not in ' +-':
                raise KitError('Unsupported patch line')
            if item[0] in ' -':
                if cursor >= len(source) or source[cursor] != item[1:]:
                    raise KitError('Patch context mismatch; refusing to guess')
                cursor += 1
                old_count += 1
            if item[0] in ' +':
                output.append(item[1:])
                new_count += 1
            index += 1
        if old_count != int(match[2] or 1) or new_count != int(match[4] or 1):
            raise KitError('Patch hunk count mismatch')
    output.extend(source[cursor:])
    return ''.join(output)


def apply_manifest(decoded: Path):
    manifest = json.loads((ROOT / 'cinema/patch-manifest.json').read_text())
    for item in manifest['patches']:
        path = (decoded / item['path']).resolve()
        if not path.is_relative_to(decoded.resolve()):
            raise KitError('Patch path escapes build directory')
        if sha256(path) != item['before_sha256']:
            raise KitError(f"Unexpected original file: {item['path']}")
        if 'patch' in item:
            text = apply_text_patch(path.read_text(), (ROOT / item['patch']).read_text())
            data = text.encode('utf-8')
        else:
            data = bytearray(path.read_bytes())
            for change in item['binary_changes']:
                offset = change['offset']
                old, new = bytes.fromhex(change['before_hex']), bytes.fromhex(change['after_hex'])
                if len(old) != len(new) or data[offset:offset+len(old)] != old:
                    raise KitError('Binary patch mismatch')
                data[offset:offset+len(old)] = new
        if hashlib.sha256(data).hexdigest() != item['after_sha256']:
            raise KitError(f"Patched file checksum mismatch: {item['path']}")
        path.write_bytes(data)
    for source in (ROOT / 'cinema/smali').rglob('*.smali'):
        target = decoded / 'smali' / source.relative_to(ROOT / 'cinema/smali')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise KitError('Unexpected existing custom helper class')
        shutil.copy2(source, target)


def apply_v8(decoded: Path, library: Path):
    verify_library(library)
    metadata = decoded / 'apktool.yml'
    text = metadata.read_text()
    changes = [('minSdkVersion: 25', 'minSdkVersion: 29'),
               ('versionCode: 7', 'versionCode: 8'),
               ('versionName: 1.0-quest-left-stereo-shortcut-rtp',
                'versionName: 1.0-quest-left-stereo-multifec')]
    for before, after in changes:
        if text.count(before) != 1:
            raise KitError('Unexpected v7 SDK/version metadata; refusing to package v8')
        text = text.replace(before, after)
    metadata.write_text(text)
    shutil.copyfile(library, decoded / 'lib/arm64-v8a/libmoonlight-core.so')


def verify_code(apk: Path, native_library: Path | None = None):
    expected = json.loads((ROOT / 'cinema/verified-code-sha256.json').read_text())
    if native_library is not None:
        verify_library(native_library)
        expected['lib/arm64-v8a/libmoonlight-core.so'] = sha256(native_library)
    with zipfile.ZipFile(apk) as archive:
        actual_names = {name for name in archive.namelist()
                        if (name.startswith('lib/') and name.endswith('.so'))
                        or (name.startswith('classes') and name.endswith('.dex'))}
        if actual_names != set(expected):
            raise KitError('Unexpected code/library inventory')
        for name, digest in expected.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise KitError(f'Code does not match the verified baseline/module: {name}')
    if native_library is None:
        print(f'Verified {len(expected)} code/library hashes against the device-tested v7 build')
    else:
        print('Verified 10 unchanged v7 code/library files and the supplied pinned-source v8 network module')


def preserve_verified_dex(decoded: Path, baseline: Path):
    """Keep tested Java bytes when raising the manifest's minimum Android API.

    Apktool otherwise passes the new minimum API to smali, which changes the
    DEX format. Its raw-DEX input path lets resources use API 29 while retaining
    the exact, verified v7 Java implementation.
    """
    verify_code(baseline)
    with zipfile.ZipFile(baseline) as archive:
        for name in archive.namelist():
            if name.startswith('classes') and name.endswith('.dex'):
                (decoded / name).write_bytes(archive.read(name))
    for folder in decoded.glob('smali*'):
        if folder.is_dir():
            shutil.rmtree(folder)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-apk', help='Optional original 1.0 APK; exact checksum required')
    parser.add_argument('--output', help='Default: dist/QuestCinemaFix-v8.apk (or v7 with --legacy-v7)')
    parser.add_argument('--native-library', type=Path, help='v8 ARM64 module from tools/build_native.py; defaults to dist/libmoonlight-core.so')
    parser.add_argument('--legacy-v7', action='store_true', help='Reproduce historical v7 without the v8 network rebuild')
    parser.add_argument('--keystore')
    parser.add_argument('--password-file')
    args = parser.parse_args()
    if args.legacy_v7 and args.native_library:
        raise KitError('--legacy-v7 cannot be combined with --native-library')
    native_library = None if args.legacy_v7 else (args.native_library or DIST / 'libmoonlight-core.so').resolve()
    if native_library is not None:
        if not native_library.is_file():
            raise KitError('Build v8 first: python3 tools/build_native.py --ndk /path/to/ndk-r27c')
        verify_library(native_library)
    output = Path(args.output).resolve() if args.output else DIST / ('QuestCinemaFix-v7.apk' if args.legacy_v7 else 'QuestCinemaFix-v8.apk')
    source = Path(args.source_apk).resolve() if args.source_apk else download(APK_URL, CACHE / 'MoonlightVRLegacy.apk', APK_SHA)
    if sha256(source) != APK_SHA:
        raise KitError('Only the pinned upstream 1.0 APK is supported')
    apktool = download(APKTOOL_URL, CACHE / 'apktool-3.0.3.jar', APKTOOL_SHA)
    LOCAL.mkdir(exist_ok=True)
    framework = CACHE / 'framework'
    framework.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cinema-', dir=LOCAL) as directory:
        work = Path(directory)
        canonical = work / 'MoonlightVRLegacy.apk'
        shutil.copy2(source, canonical)
        decoded, unsigned = work / 'decoded', work / 'cinema-unsigned.apk'
        run([executable('java'), '-jar', apktool, 'd', '-f', '-p', framework, '-o', decoded, canonical])
        apply_manifest(decoded)
        if native_library is not None:
            baseline = work / 'v7-baseline-unsigned.apk'
            run([executable('java'), '-jar', apktool, 'b', '-f', '-p', framework, '-o', baseline, decoded])
            preserve_verified_dex(decoded, baseline)
            apply_v8(decoded, native_library)
        run([executable('java'), '-jar', apktool, 'b', '-f', '-p', framework, '-o', unsigned, decoded])
        verify_code(unsigned, native_library)
        sign_apk(unsigned, output, args.keystore, args.password_file)


if __name__ == '__main__':
    try:
        main()
    except KitError as error:
        raise SystemExit(str(error))

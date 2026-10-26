#!/usr/bin/env python3
"""Reproduce the tested Quest Cinema patch locally. SPDX-License-Identifier: GPL-3.0-or-later."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

from common import ROOT, LOCAL, CACHE, DIST, KitError, download, executable, run, sha256, sign_apk

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


def verify_code(apk: Path):
    expected = json.loads((ROOT / 'cinema/verified-code-sha256.json').read_text())
    with zipfile.ZipFile(apk) as archive:
        actual_names = {name for name in archive.namelist()
                        if (name.startswith('lib/') and name.endswith('.so'))
                        or (name.startswith('classes') and name.endswith('.dex'))}
        if actual_names != set(expected):
            raise KitError('Unexpected code/library inventory')
        for name, digest in expected.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise KitError(f'Code does not match the device-tested version: {name}')
    print(f'Verified {len(expected)} code/library hashes against the device-tested build')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-apk', help='Optional original 1.0 APK; exact checksum required')
    parser.add_argument('--output', default=str(DIST / 'QuestCinemaFix-v7.apk'))
    parser.add_argument('--keystore')
    parser.add_argument('--password-file')
    args = parser.parse_args()
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
        run([executable('java'), '-jar', apktool, 'b', '-f', '-p', framework, '-o', unsigned, decoded])
        verify_code(unsigned)
        sign_apk(unsigned, Path(args.output).resolve(), args.keystore, args.password_file)


if __name__ == '__main__':
    try:
        main()
    except KitError as error:
        raise SystemExit(str(error))

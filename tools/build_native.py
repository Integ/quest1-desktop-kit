#!/usr/bin/env python3
"""Build the pinned v8 ARM64 network module. SPDX-License-Identifier: GPL-3.0-or-later."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil

from common import ROOT, CACHE, DIST, KitError, executable, run, sha256

MANIFEST = ROOT / 'cinema/native/manifest.json'


def load_manifest():
    return json.loads(MANIFEST.read_text())


def verify_payloads(manifest):
    for item in manifest['files']:
        payload = (ROOT / item['source']).resolve()
        if not payload.is_relative_to((ROOT / 'cinema/native/src').resolve()):
            raise KitError('Native source path escapes the published source folder')
        if sha256(payload) != item['after_sha256']:
            raise KitError(f"Published native source has changed: {payload.name}")


def git(source, *args):
    return run([executable('git'), '-C', source, *args], capture=True)


def prepare_source(source: Path, manifest):
    """Stage only known source files; never reset or discard an existing checkout."""
    source = source.resolve()
    verify_payloads(manifest)
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        run([executable('git'), 'clone', '--depth', '1', '--branch', manifest['base_ref'],
             '--filter=blob:none', '--sparse', manifest['base_repository'], source])
        git(source, 'sparse-checkout', 'set', 'moonlight-common/src/main/jni')
    if git(source, 'rev-parse', 'HEAD') != manifest['base_commit']:
        raise KitError('Unexpected native base commit; refusing to modify this checkout')
    expected = {item['path'] for item in manifest['files']}
    changed = set(git(source, 'diff', '--name-only', 'HEAD').splitlines())
    if changed - expected:
        raise KitError('Native checkout has unrelated tracked edits; use a clean build checkout')
    # NDK output directories may be untracked. Untracked source/build scripts in
    # jni/ are unsafe because ndk-build discovers makefiles recursively.
    untracked = git(source, 'ls-files', '--others', '--exclude-standard').splitlines()
    untracked += git(source, 'ls-files', '--others', '--ignored', '--exclude-standard').splitlines()
    if any('/jni/' in name for name in untracked):
        raise KitError('Unexpected untracked files in the native source tree')
    updates = []
    for item in manifest['files']:
        lexical = source / item['path']
        target = lexical.resolve()
        if not target.is_relative_to(source) or lexical.is_symlink():
            raise KitError('Native target path escapes the build checkout')
        current = sha256(target)
        if current not in (item['before_sha256'], item['after_sha256']):
            raise KitError(f"Unexpected native source contents: {item['path']}")
        updates.append((ROOT / item['source'], target))
    # Validate every input before writing any file.
    for payload, target in updates:
        shutil.copyfile(payload, target)
    print(f"Verified pinned native checkout and {len(updates)} patched source files")
    return source


def check_ndk(ndk: Path, manifest):
    ndk = ndk.resolve()
    if ' ' in str(ndk) or not (ndk / 'ndk-build').is_file():
        raise KitError('NDK root must exist and have no spaces; see docs/BUILD.md')
    properties = (ndk / 'source.properties').read_text()
    revision = re.search(r'^Pkg.Revision\s*=\s*(\S+)', properties, re.M)
    if not revision or revision[1] != manifest['ndk_revision']:
        raise KitError(f"Use the tested NDK revision {manifest['ndk_revision']} (r27c)")
    return ndk


def build(source: Path, ndk: Path, output: Path, manifest):
    ndk = check_ndk(ndk, manifest)
    project = source / 'moonlight-common/src/main'
    run([ndk / 'ndk-build', '-C', project, 'NDK_PROJECT_PATH=.',
         'APP_BUILD_SCRIPT=jni/Android.mk', 'NDK_APPLICATION_MK=jni/Application.mk',
         'APP_ABI=' + manifest['abi'], 'APP_PLATFORM=android-' + str(manifest['android_api']),
         'NDK_DEBUG=0', '-j4'])
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(project / 'libs' / manifest['abi'] / 'libmoonlight-core.so', output)
    record = {'abi': manifest['abi'], 'android_api': manifest['android_api'],
              'ndk_revision': manifest['ndk_revision'], 'base_commit': manifest['base_commit'],
              'source_manifest_sha256': sha256(MANIFEST), 'library_sha256': sha256(output)}
    output.with_suffix('.json').write_text(json.dumps(record, indent=2) + '\n')
    print(f'Built {output.name}; SHA-256 {record["library_sha256"]}')


def verify_library(library: Path):
    """Require matching local build provenance or the exact device-tested module."""
    manifest = load_manifest()
    verify_payloads(manifest)
    data = library.read_bytes()
    # ELF64 little-endian, EM_AARCH64; reject accidental x86/ARM32 libraries.
    if len(data) < 20 or data[:6] != b'\x7fELF\x02\x01' or int.from_bytes(data[18:20], 'little') != 183:
        raise KitError('The v8 module must be an ARM64 ELF shared library')
    fingerprint = sha256(library)
    tested = json.loads((ROOT / 'cinema/native/tested-build.json').read_text())
    if fingerprint == tested['native_sha256']:
        return
    record_path = library.with_suffix('.json')
    if not record_path.is_file():
        raise KitError('Missing native build provenance; use tools/build_native.py')
    record = json.loads(record_path.read_text())
    required = {'abi': manifest['abi'], 'android_api': manifest['android_api'],
                'ndk_revision': manifest['ndk_revision'], 'base_commit': manifest['base_commit'],
                'source_manifest_sha256': sha256(MANIFEST), 'library_sha256': fingerprint}
    if record != required:
        raise KitError('Native module/provenance mismatch; rebuild with the current pinned sources')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ndk', default=os.environ.get('ANDROID_NDK_ROOT'))
    parser.add_argument('--source-dir', type=Path, default=CACHE / 'native-source')
    parser.add_argument('--output', type=Path, default=DIST / 'libmoonlight-core.so')
    parser.add_argument('--prepare-only', action='store_true', help='Verify and stage sources without building')
    args = parser.parse_args()
    manifest = load_manifest()
    if not args.prepare_only:
        if not args.ndk:
            raise KitError('Pass --ndk /path/to/ndk-r27c or set ANDROID_NDK_ROOT')
        check_ndk(Path(args.ndk), manifest)
    source = prepare_source(args.source_dir, manifest)
    if not args.prepare_only:
        build(source, Path(args.ndk), args.output.resolve(), manifest)


if __name__ == '__main__':
    try:
        main()
    except KitError as error:
        raise SystemExit(str(error))

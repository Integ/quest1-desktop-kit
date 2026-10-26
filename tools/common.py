"""Local build support. SPDX-License-Identifier: GPL-3.0-or-later."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache'
LOCAL = ROOT / '.local'
DIST = ROOT / 'dist'


class KitError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def run(args, *, env=None, capture=False):
    try:
        result = subprocess.run([str(x) for x in args], check=True, env=env,
                                text=True, capture_output=capture)
    except subprocess.CalledProcessError as exc:
        # Do not echo complete command lines: callers may use credential files.
        raise KitError(f'{Path(str(args[0])).name} failed (exit {exc.returncode})') from exc
    return result.stdout.strip() if capture else ''


def executable(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise KitError(f'Missing {name}; install a JDK and Android SDK build tools. See docs/BUILD.md')
    return found


def sdk_root() -> Path:
    candidates = [os.environ.get('ANDROID_SDK_ROOT'), os.environ.get('ANDROID_HOME'),
                  '/opt/homebrew/share/android-commandlinetools',
                  str(Path.home() / 'Library/Android/sdk'), str(Path.home() / 'Android/Sdk')]
    for candidate in candidates:
        if candidate and (Path(candidate) / 'build-tools').is_dir():
            return Path(candidate)
    raise KitError('Set ANDROID_SDK_ROOT to an Android SDK containing build-tools; see docs/BUILD.md')


def build_tool(name: str) -> Path:
    folders = [p for p in (sdk_root() / 'build-tools').iterdir() if p.is_dir()]
    folders.sort(key=lambda p: tuple(int(x) for x in re.findall(r'\d+', p.name)), reverse=True)
    for folder in folders:
        for suffix in ['', '.bat', '.exe']:
            candidate = folder / (name + suffix)
            if candidate.is_file():
                return candidate
    raise KitError(f'Android build tool not found: {name}')


def android_jar() -> Path:
    platform = sdk_root() / 'platforms'
    preferred = platform / 'android-34/android.jar'
    if preferred.is_file():
        return preferred
    folders = sorted(platform.glob('android-*'),
                     key=lambda p: int(p.name.split('-')[-1]) if p.name.split('-')[-1].isdigit() else 0,
                     reverse=True)
    for folder in folders:
        if (folder / 'android.jar').is_file():
            return folder / 'android.jar'
    raise KitError('Install Android SDK platform android-34 to build the helper')


def download(url: str, destination: Path, expected_sha256: str) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256(destination) != expected_sha256:
            raise KitError(f'Checksum mismatch in cached {destination.name}; remove it and retry')
        return destination
    temporary = destination.with_suffix(destination.suffix + '.part')
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'quest1-desktop-kit'})
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open('wb') as output:
            shutil.copyfileobj(response, output)
        if sha256(temporary) != expected_sha256:
            raise KitError(f'Download checksum mismatch: {destination.name}')
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def signing_material(keystore: str | None, password_file: str | None) -> tuple[Path, Path]:
    if bool(keystore) != bool(password_file):
        raise KitError('Specify both --keystore and --password-file, or neither')
    if keystore:
        key, password = Path(keystore).resolve(), Path(password_file).resolve()
        if not key.is_file() or not password.is_file():
            raise KitError('Signing files do not exist')
        return key, password
    folder = LOCAL / 'signing'
    folder.mkdir(parents=True, exist_ok=True)
    key, password = folder / 'quest-kit.p12', folder / 'key.password'
    if key.exists() != password.exists():
        raise KitError('Incomplete local signing material; restore the matching key and password file')
    if not key.exists():
        secret = secrets.token_urlsafe(32)
        with open(password, 'x', encoding='utf-8', opener=lambda path, flags: os.open(path, flags, 0o600)) as out:
            out.write(secret)
        environment = dict(os.environ, QUESTKIT_KEY_PASSWORD=secret)
        try:
            run([executable('keytool'), '-genkeypair', '-noprompt', '-storetype', 'PKCS12',
                 '-keystore', key, '-alias', 'quest-kit', '-keyalg', 'RSA', '-keysize', '3072',
                 '-validity', '10000', '-dname', 'CN=Quest Desktop Kit Local Build',
                 '-storepass:env', 'QUESTKIT_KEY_PASSWORD', '-keypass:env', 'QUESTKIT_KEY_PASSWORD'],
                env=environment)
            key.chmod(0o600)
        except Exception:
            password.unlink(missing_ok=True)
            key.unlink(missing_ok=True)
            raise
    return key, password


def sign_apk(unsigned: Path, output: Path, keystore=None, password_file=None):
    key, password = signing_material(keystore, password_file)
    aligned = unsigned.with_name(unsigned.stem + '-aligned.apk')
    output.parent.mkdir(parents=True, exist_ok=True)
    run([build_tool('zipalign'), '-f', '4', unsigned, aligned])
    run([build_tool('apksigner'), 'sign', '--ks', key, '--ks-pass', 'file:' + str(password),
         '--out', output, aligned])
    run([build_tool('apksigner'), 'verify', output])
    print(f'Built {output.name}; SHA-256 {sha256(output)}')

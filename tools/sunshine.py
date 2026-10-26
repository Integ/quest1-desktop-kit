#!/usr/bin/env python3
"""Private local Sunshine configuration and session recovery. SPDX-License-Identifier: GPL-3.0-or-later."""
import argparse
import base64
import getpass
import json
import os
from pathlib import Path
import shutil
import ssl
import urllib.request

from common import LOCAL, KitError


def initialize(folder):
    folder.mkdir(parents=True, exist_ok=True)
    config = folder / 'sunshine.conf'
    apps = folder / 'apps.json'
    if config.exists() or apps.exists():
        raise KitError('Configuration already exists; edit it in place or choose a new --directory')
    credentials = folder / 'credentials'
    credentials.mkdir(mode=0o700, exist_ok=True)
    entries = {
        'sunshine_name': 'Quest Desktop', 'origin_web_ui_allowed': 'pc', 'upnp': 'disabled',
        'keyboard': 'disabled', 'mouse': 'disabled', 'controller': 'disabled',
        'stream_audio': 'enabled', 'system_tray': 'disabled',
        'file_apps': str(apps), 'credentials_file': str(folder / 'state.json'),
        'log_path': str(folder / 'sunshine.log'), 'pkey': str(credentials / 'cakey.pem'),
        'cert': str(credentials / 'cacert.pem'),
    }
    apps.write_text(json.dumps({'env': {}, 'apps': [{'name': 'Mac Desktop', 'image-path': ''}]}, indent=2) + '\n')
    config.write_text(''.join(f'{key} = {value}\n' for key, value in entries.items()))
    config.chmod(0o600)
    print(f'Created private configuration: {config}')
    print('Run start, then open https://localhost:47990 to create a username/password and pair your headset.')


def close_session(ca, username, password):
    if not ca.is_file():
        raise KitError('Supply Sunshine\'s own generated credentials/cacert.pem using --ca')
    context = ssl.create_default_context(cafile=str(ca))
    # Sunshine's self-signed certificate has no localhost SAN. Trust the supplied
    # certificate, require TLS validation, and hardcode loopback as the only target.
    context.check_hostname = False
    authorization = base64.b64encode((username + ':' + password).encode()).decode()
    request = urllib.request.Request('https://127.0.0.1:47990/api/apps/close', data=b'{}',
        headers={'Authorization': 'Basic ' + authorization, 'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, context=context, timeout=10) as response:
            payload = json.load(response)
    except Exception as exc:
        raise KitError(f'Local Sunshine request failed ({type(exc).__name__}); check server, CA and credentials') from exc
    if payload.get('status') is False:
        raise KitError('Sunshine refused to close the streaming session')
    print('Closed the streaming session. Reopen Mac Desktop in the headset.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=LOCAL / 'sunshine')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('init')
    start = commands.add_parser('start')
    start.add_argument('--binary', help='Path to an installed Sunshine executable')
    close = commands.add_parser('close-session')
    close.add_argument('--ca', type=Path)
    close.add_argument('--username', required=True)
    args = parser.parse_args()
    folder = args.directory.resolve()
    if args.command == 'init':
        initialize(folder)
    elif args.command == 'start':
        binary = args.binary or shutil.which('sunshine')
        if not binary or not Path(binary).is_file():
            raise KitError('Install Sunshine and put it on PATH, or use start --binary PATH')
        config = folder / 'sunshine.conf'
        if not config.is_file():
            raise KitError('Run init first')
        os.execv(str(Path(binary).resolve()), [str(Path(binary).resolve()), str(config)])
    else:
        close_session(args.ca or folder / 'credentials/cacert.pem', args.username,
                      getpass.getpass('Sunshine password (not saved): '))


if __name__ == '__main__':
    try:
        main()
    except KitError as error:
        raise SystemExit(str(error))

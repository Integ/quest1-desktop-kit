#!/usr/bin/env python3
"""Explicit, reversible Quest 1 administration. SPDX-License-Identifier: GPL-3.0-or-later."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import ipaddress
import json
from pathlib import Path
import shutil
import socket
import subprocess
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from common import KitError

HELPER = 'local.quest.adbkeeper'
CINEMA = 'local.quest.cinema/com.oculus.cinemasdk.MainActivity'


class Adb:
    def __init__(self, binary=None):
        self.binary = binary or shutil.which('adb')
        if not self.binary:
            raise KitError('Install Android SDK platform-tools (adb) first')

    def call(self, *args, timeout=20):
        try:
            result = subprocess.run([self.binary, *map(str, args)], capture_output=True,
                                    text=True, timeout=timeout, check=True)
        except (subprocess.SubprocessError, OSError) as exc:
            raise KitError(f'ADB command failed: {type(exc).__name__}') from exc
        return result.stdout.strip()

    def transports(self):
        lines = self.call('devices').splitlines()[1:]
        return [p[0] for line in lines if len(p := line.split()) >= 2 and p[1] == 'device']

    def prop(self, transport, key):
        return self.call('-s', transport, 'shell', 'getprop', key)


def choose(adb, explicit=None):
    """Read identity before any write; collapse USB/TLS transports of the same headset."""
    online = adb.transports()
    if explicit:
        if explicit not in online:
            raise KitError('Requested transport is not online/authorized')
        candidates = [explicit]
    else:
        candidates = online
    quests = []
    for transport in candidates:
        if adb.prop(transport, 'ro.product.device') == 'monterey':
            serial = adb.prop(transport, 'ro.serialno')
            if serial:
                quests.append((serial, transport))
    if not quests:
        raise KitError('No authorized Quest 1 (monterey) found; establish ADB first')
    if len({serial for serial, _ in quests}) != 1:
        raise KitError('Multiple Quest 1 headsets found; select one using --serial TRANSPORT')
    quests.sort(key=lambda item: (':' in item[1], item[1]))
    return Device(adb, quests[0][1], quests[0][0])


class Device:
    def __init__(self, adb, transport, identity):
        self.adb, self.transport, self.identity = adb, transport, identity

    def shell(self, *args):
        # Recheck on each mutation: a TCP endpoint may have been reassigned.
        if (self.adb.prop(self.transport, 'ro.product.device') != 'monterey'
                or self.adb.prop(self.transport, 'ro.serialno') != self.identity):
            raise KitError('Headset identity changed; refusing the operation')
        output = self.adb.call('-s', self.transport, 'shell', *args)
        if any(word in output for word in ['SecurityException', 'Permission Denial', 'Error:', 'Exception occurred']):
            raise KitError(output)
        return output

    def admin(self, action):
        return self.shell('am', 'broadcast', '-n', HELPER + '/.AdminReceiver',
                          '-a', HELPER + '.' + action)

    def install(self, apk):
        self.shell('true')  # Identity check before adb install (which is not a shell command).
        output = self.adb.call('-s', self.transport, 'install', '-r', str(Path(apk).resolve()), timeout=120)
        if 'Success' not in output:
            raise KitError(output or 'APK install did not report success')


def connect(adb, host, expected, port=None, scan=False):
    """Reconnect an already trusted host; never pairs or grants a new trust relationship."""
    try:
        address = ipaddress.IPv4Address(host)
    except ipaddress.AddressValueError as exc:
        raise KitError('--host must be the IPv4 address of your own headset') from exc
    if not address.is_private or address.is_unspecified or address.is_multicast:
        raise KitError('Only an explicitly specified private/local IPv4 address is supported')
    if not port and not scan:
        raise KitError('Supply --port CONNECT_PORT, or explicitly opt into --scan')
    if port is not None and not 1 <= port <= 65535:
        raise KitError('Connect port must be 1..65535; :0 is not a usable port')
    ports = [port] if port else list(range(32768, 65536))
    if scan:
        print('Checking TCP ports on the specified headset only; this may take a minute.')

    def is_open(candidate):
        try:
            with socket.create_connection((host, candidate), timeout=0.25):
                return candidate
        except OSError:
            return None

    with ThreadPoolExecutor(max_workers=96) as pool:
        for candidate in pool.map(is_open, ports):
            if candidate is None:
                continue
            endpoint = f'{host}:{candidate}'
            try:
                adb.call('connect', endpoint, timeout=6)
                if endpoint not in adb.transports():
                    continue
                if (adb.prop(endpoint, 'ro.product.device') == 'monterey'
                        and adb.prop(endpoint, 'ro.serialno') == expected):
                    print(f'Connected and verified: {endpoint}')
                    return
                adb.call('disconnect', endpoint)
            except KitError:
                continue
    raise KitError('No matching authorized Quest found. Wake it, enable Wi-Fi debugging, and check pairing.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', help='ADB transport selector (USB serial or IP:connect-port)')
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ['info', 'enable-usb', 'open-cinema', 'open-launcher']:
        commands.add_parser(command)
    for command in ['install-helper', 'install-cinema']:
        commands.add_parser(command).add_argument('apk')
    for command in ['keep-usb', 'keep-wifi', 'autostart']:
        commands.add_parser(command).add_argument('state', choices=['on', 'off'])
    for command in ['featured', 'tutorial']:
        commands.add_parser(command).add_argument('state', choices=['hide', 'show'])
    commands.add_parser('time').add_argument('--timezone', required=True, help='IANA zone, e.g. Europe/Paris')
    connection = commands.add_parser('connect')
    connection.add_argument('--host', required=True)
    connection.add_argument('--expected-serial', required=True, help='Physical ro.serialno, from a previously trusted connection')
    connection.add_argument('--port', type=int)
    connection.add_argument('--scan', action='store_true', help='Probe high TCP ports on this single IP only')
    args = parser.parse_args()
    adb = Adb()
    if args.command == 'connect':
        connect(adb, args.host, args.expected_serial, args.port, args.scan)
        return
    device = choose(adb, args.serial)
    command = args.command
    if command == 'info':
        props = ['ro.product.device', 'ro.build.version.release', 'ro.build.version.sdk',
                 'ro.build.version.incremental', 'ro.build.version.security_patch']
        print(json.dumps({key: adb.prop(device.transport, key) for key in props}, indent=2))
        for key in ['development_settings_enabled', 'adb_enabled', 'adb_wifi_enabled', 'auto_time']:
            print(f'{key}: {device.shell("settings", "get", "global", key)}')
    elif command == 'enable-usb':
        for key in ['development_settings_enabled', 'adb_enabled']:
            device.shell('settings', 'put', 'global', key, '1')
            print(f'{key}: {device.shell("settings", "get", "global", key)}')
    elif command.startswith('install-'):
        device.install(args.apk)
        if command == 'install-helper':
            device.shell('pm', 'grant', HELPER, 'android.permission.WRITE_SECURE_SETTINGS')
            device.shell('am', 'start', '-n', HELPER + '/.MainActivity')
        print('Installed. Existing data is preserved when the signing certificate matches.')
    elif command in ['keep-usb', 'keep-wifi', 'autostart']:
        on = args.state == 'on'
        if command == 'autostart' and on:
            device.shell('appops', 'set', HELPER, 'SYSTEM_ALERT_WINDOW', 'allow')
        action = {'keep-usb': 'USB_', 'keep-wifi': '', 'autostart': 'CINEMA_'}[command]
        print(device.admin(action + ('ENABLE' if on else 'DISABLE')))
        print('Preference updated. Disabling a USB/Wi-Fi keeper also turns that debugging transport off.')
    elif command in ['featured', 'tutorial']:
        package = 'com.oculus.store' if command == 'featured' else 'com.oculus.firsttimenux'
        operation = 'disable-user' if args.state == 'hide' else 'default-state'
        print(device.shell('pm', operation, '--user', '0', package))
    elif command == 'open-cinema':
        print(device.shell('am', 'start', '-n', CINEMA))
    elif command == 'open-launcher':
        print(device.shell('monkey', '-p', 'com.threethan.launcher', '-c', 'android.intent.category.LAUNCHER', '1'))
    elif command == 'time':
        try:
            ZoneInfo(args.timezone)
        except ZoneInfoNotFoundError as exc:
            raise KitError('Unknown IANA time zone; install tzdata if your OS lacks it') from exc
        device.shell('settings', 'put', 'global', 'auto_time', '1')
        device.shell('settings', 'put', 'global', 'auto_time_zone', '0')
        print(device.shell('cmd', 'alarm', 'set-timezone', args.timezone))
        print(device.shell('getprop', 'persist.sys.timezone'))
    print('Done.')


if __name__ == '__main__':
    try:
        main()
    except KitError as error:
        raise SystemExit(str(error))

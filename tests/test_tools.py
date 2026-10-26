"""Host-side safety and patch regression tests; never connects to hardware."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from common import KitError, download
from build_cinema import apply_text_patch
from quest import choose, connect, main as quest_main
from sunshine import initialize


class FakeAdb:
    def __init__(self, devices):
        self.devices = devices
        self.writes = []

    def transports(self):
        return list(self.devices)

    def prop(self, transport, key):
        device, serial = self.devices[transport]
        return {'ro.product.device': device, 'ro.serialno': serial}[key]

    def call(self, *args, **kwargs):
        self.writes.append(args)
        return ''


class SelectionTests(unittest.TestCase):
    def test_reject_phone_before_write(self):
        adb = FakeAdb({'PHONE': ('phone', 'OTHER')})
        with self.assertRaises(KitError):
            choose(adb)
        self.assertEqual(adb.writes, [])

    def test_usb_preferred_for_same_physical_quest(self):
        adb = FakeAdb({'192.0.2.8:40000': ('monterey', 'HEADSET'), 'USB': ('monterey', 'HEADSET')})
        self.assertEqual(choose(adb).transport, 'USB')

    def test_two_headsets_need_explicit_selector(self):
        adb = FakeAdb({'ONE': ('monterey', 'ONE'), 'TWO': ('monterey', 'TWO')})
        with self.assertRaises(KitError):
            choose(adb)
        self.assertEqual(choose(adb, 'TWO').transport, 'TWO')
        self.assertEqual(adb.writes, [])

    def test_recheck_identity_before_write(self):
        adb = FakeAdb({'USB': ('monterey', 'HEADSET')})
        device = choose(adb)
        adb.devices['USB'] = ('monterey', 'DIFFERENT')
        with self.assertRaises(KitError):
            device.shell('settings', 'put', 'global', 'adb_enabled', '1')
        self.assertEqual(adb.writes, [])

    def test_connect_requires_valid_explicit_scope(self):
        for host, port, scan in [('8.8.8.8', 5555, False), ('127.0.0.1', 0, False),
                                 ('127.0.0.1', None, False)]:
            with self.assertRaises(KitError):
                connect(FakeAdb({}), host, 'HEADSET', port, scan)

    def test_volume_shortcut_grants_launch_access_and_enables_only_shortcut(self):
        adb = FakeAdb({'USB': ('monterey', 'HEADSET')})
        with patch('quest.Adb', return_value=adb), patch('sys.argv', ['quest.py', 'volume-shortcut', 'on']), patch('builtins.print'):
            quest_main()
        self.assertEqual(adb.writes, [
            ('-s', 'USB', 'shell', 'appops', 'set', 'local.quest.adbkeeper', 'SYSTEM_ALERT_WINDOW', 'allow'),
            ('-s', 'USB', 'shell', 'am', 'broadcast', '-n', 'local.quest.adbkeeper/.AdminReceiver',
             '-a', 'local.quest.adbkeeper.LAUNCHER_ENABLE')])

    def test_disabling_shortcut_does_not_disable_adb_or_revoke_shared_launch_access(self):
        adb = FakeAdb({'USB': ('monterey', 'HEADSET')})
        with patch('quest.Adb', return_value=adb), patch('sys.argv', ['quest.py', 'volume-shortcut', 'off']), patch('builtins.print'):
            quest_main()
        self.assertEqual(adb.writes, [
            ('-s', 'USB', 'shell', 'am', 'broadcast', '-n', 'local.quest.adbkeeper/.AdminReceiver',
             '-a', 'local.quest.adbkeeper.LAUNCHER_DISABLE')])


class PatchTests(unittest.TestCase):
    DIFF = '--- a/file\n+++ b/file\n@@ -1,2 +1,2 @@\n a\n-b\n+c\n'

    def test_exact_patch_and_reject_wrong_input(self):
        self.assertEqual(apply_text_patch('a\nb\n', self.DIFF), 'a\nc\n')
        with self.assertRaises(KitError):
            apply_text_patch('a\nWRONG\n', self.DIFF)

    def test_patch_hunk_count_is_checked(self):
        with self.assertRaises(KitError):
            apply_text_patch('a\nb\n', self.DIFF.replace('-1,2', '-1,3'))

    def test_hash_mismatch_never_accepted_from_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            cached = Path(folder) / 'cached.apk'
            cached.write_bytes(b'wrong')
            with patch('urllib.request.urlopen', side_effect=AssertionError('No network expected')):
                with self.assertRaises(KitError):
                    download('https://example.invalid/file', cached, hashlib.sha256(b'right').hexdigest())

    def test_manifest_patch_inventory(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / 'cinema/patch-manifest.json').read_text())
        self.assertEqual(len(manifest['patches']), 11)
        for item in manifest['patches']:
            self.assertNotIn('..', Path(item['path']).parts)
            self.assertEqual(len(item['before_sha256']), 64)
            self.assertEqual(len(item['after_sha256']), 64)
            if 'binary_changes' in item:
                for change in item['binary_changes']:
                    self.assertEqual(len(change['before_hex']), len(change['after_hex']))


class SunshineTests(unittest.TestCase):
    def test_local_config_is_restrictive_and_wont_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            initialize(folder)
            config = (folder / 'sunshine.conf').read_text()
            for setting in ['upnp = disabled', 'origin_web_ui_allowed = pc', 'keyboard = disabled',
                            'mouse = disabled', 'controller = disabled', 'stream_audio = enabled']:
                self.assertIn(setting, config)
            self.assertEqual(json.loads((folder / 'apps.json').read_text())['apps'][0]['name'], 'Mac Desktop')
            with self.assertRaises(KitError):
                initialize(folder)


if __name__ == '__main__':
    unittest.main()

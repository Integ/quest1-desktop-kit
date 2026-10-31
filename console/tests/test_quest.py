import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import quest  # noqa: E402

STATUS = quest.SEP.join([
    'Current Battery Service state:\n  AC powered: true\n  USB powered: false\n  status: 5\n  level: 100\n  temperature: 300\n',
    'Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/block/sda10 114934260 425576 114361228 1% /data\n',
    '  mWakefulness=Awake\n',
    '    mResumedActivity: ActivityRecord{577fce0 u0 local.quest.cinema/com.oculus.cinemasdk.MainActivity t40}\n',
    '    inet 10.0.0.70/24 brd 10.0.0.255 scope global wlan0\n',
    'releases-oculus-10.0-v50\n',
])

BADGING = """package: name='com.limelight' versionCode='1234' versionName='12.1' platformBuildVersionName='14'
sdkVersion:'21'
targetSdkVersion:'34'
application-label:'Moonlight'
application-label-zh-CN:'月光'
native-code: 'arm64-v8a' 'armeabi-v7a'
"""


class ParseTests(unittest.TestCase):
    def test_status(self):
        s = quest.parse_status(STATUS)
        self.assertEqual(s['battery'], {'level': 100, 'status': '已充满', 'temperature_c': 30.0, 'plugged': True})
        self.assertEqual(s['storage'], {'total_gb': 117.7, 'free_gb': 117.3})
        self.assertTrue(s['awake'])
        self.assertEqual(s['foreground'], 'local.quest.cinema')
        self.assertEqual(s['wifi_ip'], '10.0.0.70')
        self.assertEqual(s['firmware'], 'v50')

    def test_status_tolerates_missing_sections(self):
        s = quest.parse_status('')
        self.assertIsNone(s['battery']['level'])
        self.assertIsNone(s['storage'])
        self.assertIsNone(s['awake'])

    def test_badging_prefers_chinese_label(self):
        b = quest.parse_badging(BADGING)
        self.assertEqual((b['package'], b['version_name'], b['label'], b['min_sdk']), ('com.limelight', '12.1', '月光', 21))
        self.assertEqual(b['native_code'], ['arm64-v8a', 'armeabi-v7a'])

    def test_helper_status(self):
        out = 'Broadcasting: Intent\nBroadcast completed: result=0, data="version=10;launcher=true;idle=false;opens=0"'
        self.assertEqual(quest.parse_helper_status(out), {'version': '10', 'launcher': 'true', 'idle': 'false', 'opens': '0'})
        self.assertIsNone(quest.parse_helper_status('Broadcast completed: result=0'))

    def test_obb_names(self):
        self.assertEqual(quest.OBB.match('main.12.com.example.game.obb').group(3), 'com.example.game')
        self.assertIsNone(quest.OBB.match('game.obb'))
        self.assertIsNone(quest.OBB.match('main.12.../../x.obb'))


if __name__ == '__main__':
    unittest.main()

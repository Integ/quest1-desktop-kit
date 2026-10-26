"""Offline checks for pinned native staging and v8 APK preservation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from common import KitError
import build_native
import build_cinema


def digest(data):
    return hashlib.sha256(data).hexdigest()


class NativeStagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / 'checkout'
        self.source.mkdir()
        self.path = 'moonlight-common/src/main/jni/file.c'
        target = self.source / self.path
        target.parent.mkdir(parents=True)
        target.write_bytes(b'before\n')
        (target.parent / 'build.mk').write_bytes(b'original makefile\n')
        def git(*args):
            return subprocess.run(['git', '-C', str(self.source), *args], check=True, text=True, capture_output=True).stdout.strip()
        self.git = git
        git('init', '-b', 'main')
        git('add', '.')
        git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-m', 'fixture')
        payload = self.root / 'cinema/native/src/file.c'
        payload.parent.mkdir(parents=True)
        payload.write_bytes(b'after\n')
        self.manifest = {'base_commit': git('rev-parse', 'HEAD'), 'files': [
            {'path': self.path, 'source': 'cinema/native/src/file.c',
             'before_sha256': digest(b'before\n'), 'after_sha256': digest(b'after\n')} ]}
        self.root_patch = patch.object(build_native, 'ROOT', self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.temporary.cleanup()

    def test_verified_stage_and_reuse(self):
        build_native.prepare_source(self.source, self.manifest)
        build_native.prepare_source(self.source, self.manifest)
        self.assertEqual((self.source / self.path).read_bytes(), b'after\n')

    def test_foreign_base_is_refused_without_write(self):
        self.manifest['base_commit'] = '0' * 40
        with self.assertRaises(KitError):
            build_native.prepare_source(self.source, self.manifest)
        self.assertEqual((self.source / self.path).read_bytes(), b'before\n')

    def test_unrelated_build_edit_is_refused(self):
        (self.source / self.path).with_name('build.mk').write_text('unexpected input')
        with self.assertRaises(KitError):
            build_native.prepare_source(self.source, self.manifest)
        self.assertEqual((self.source / self.path).read_bytes(), b'before\n')

    def test_unknown_source_contents_are_preserved(self):
        (self.source / self.path).write_text('user edit')
        with self.assertRaises(KitError):
            build_native.prepare_source(self.source, self.manifest)
        self.assertEqual((self.source / self.path).read_text(), 'user edit')

    def test_untracked_makefile_is_refused(self):
        (self.source / self.path).with_name('extra.mk').write_text('unexpected makefile')
        with self.assertRaises(KitError):
            build_native.prepare_source(self.source, self.manifest)
        # Ignored makefiles can also be discovered by ndk-build.
        (self.source / '.git/info/exclude').write_text('extra.mk\n')
        with self.assertRaises(KitError):
            build_native.prepare_source(self.source, self.manifest)

    def test_wrong_ndk_revision_is_refused(self):
        ndk = self.root / 'ndk'
        ndk.mkdir()
        (ndk / 'ndk-build').write_text('fixture')
        (ndk / 'source.properties').write_text('Pkg.Revision = 1.0.0\n')
        with self.assertRaises(KitError):
            build_native.check_ndk(ndk, {'ndk_revision': '27.2.12479018'})


class CinemaV8Tests(unittest.TestCase):
    def test_v8_declares_actual_native_minimum_api(self):
        with tempfile.TemporaryDirectory() as directory:
            decoded = Path(directory) / 'decoded'
            decoded.mkdir()
            metadata = decoded / 'apktool.yml'
            metadata.write_text('minSdkVersion: 25\nversionCode: 7\nversionName: 1.0-quest-left-stereo-shortcut-rtp\n')
            target = decoded / 'lib/arm64-v8a/libmoonlight-core.so'
            target.parent.mkdir(parents=True)
            library = Path(directory) / 'library.so'
            library.write_bytes(b'new module')
            with patch.object(build_cinema, 'verify_library'):
                build_cinema.apply_v8(decoded, library)
                with self.assertRaises(KitError):
                    build_cinema.apply_v8(decoded, library)
            self.assertIn('minSdkVersion: 29', metadata.read_text())
            self.assertIn('versionCode: 8', metadata.read_text())
            self.assertEqual(target.read_bytes(), b'new module')

    def test_modified_java_code_is_rejected_even_with_native_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'cinema').mkdir()
            names = {'classes.dex': b'tested left-hand code', 'lib/arm64-v8a/libmoonlight-core.so': b'old network'}
            (root / 'cinema/verified-code-sha256.json').write_text(json.dumps({k: digest(v) for k, v in names.items()}))
            library = root / 'library.so'; library.write_bytes(b'new network')
            apk = root / 'test.apk'
            with zipfile.ZipFile(apk, 'w') as archive:
                archive.writestr('classes.dex', b'modified input code')
                archive.writestr('lib/arm64-v8a/libmoonlight-core.so', b'new network')
            with patch.object(build_cinema, 'ROOT', root), patch.object(build_cinema, 'verify_library'):
                with self.assertRaises(KitError):
                    build_cinema.verify_code(apk, library)


if __name__ == '__main__':
    unittest.main()

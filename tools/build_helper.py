#!/usr/bin/env python3
"""Build the startup / ADB helper. SPDX-License-Identifier: GPL-3.0-or-later."""
import argparse
from pathlib import Path
import tempfile
import zipfile

from common import ROOT, LOCAL, DIST, KitError, android_jar, build_tool, executable, run, sign_apk


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(DIST / 'QuestStartupHelper-v3.0.apk'))
    parser.add_argument('--keystore')
    parser.add_argument('--password-file')
    args = parser.parse_args()
    LOCAL.mkdir(exist_ok=True)
    source = ROOT / 'helper'
    with tempfile.TemporaryDirectory(prefix='helper-', dir=LOCAL) as directory:
        work = Path(directory)
        classes, dex = work / 'classes', work / 'dex'
        classes.mkdir(); dex.mkdir()
        jar = android_jar()
        run([executable('javac'), '--release', '8', '-cp', jar, '-d', classes,
             *sorted((source / 'src').rglob('*.java'))])
        for required in ['State', 'KeepService', 'BootReceiver', 'MainActivity', 'AdminReceiver', 'CinemaShortcutActivity']:
            if not (classes / 'local/quest/adbkeeper' / (required + '.class')).exists():
                raise KitError(f'Missing compiled class: {required}')
        run([build_tool('d8'), '--min-api', '26', '--lib', jar, '--output', dex,
             *sorted(classes.rglob('*.class'))])
        unsigned = work / 'helper-unsigned.apk'
        run([build_tool('aapt'), 'package', '-f', '-M', source / 'AndroidManifest.xml',
             '-S', source / 'res', '-I', jar, '-F', unsigned])
        with zipfile.ZipFile(unsigned, 'a') as archive:
            archive.write(dex / 'classes.dex', 'classes.dex')
        sign_apk(unsigned, Path(args.output).resolve(), args.keystore, args.password_file)


if __name__ == '__main__':
    try:
        main()
    except KitError as error:
        raise SystemExit(str(error))

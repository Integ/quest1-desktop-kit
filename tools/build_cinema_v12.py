#!/usr/bin/env python3
"""Build Quest Cinema Fix v12 (local videos + volume navigation) from a v8 APK built by build_cinema.py.

SPDX-License-Identifier: GPL-3.0-or-later.

v12 changes only Java code: the cinema's own classes are replaced from cinema/java plus cinema/v12/java,
16 MainActivity methods get a short hook at the top, and one PcSelector call is routed through
LocalVideos. Native libraries, assets and resources must stay byte-identical to the v8 input.
"""
import argparse
from pathlib import Path
import shutil
import tempfile
import zipfile

from common import ROOT, LOCAL, CACHE, DIST, KitError, android_jar, build_tool, download, executable, run, sha256, sign_apk
from build_cinema import APKTOOL_URL, APKTOOL_SHA

VERSION_CODE, VERSION_NAME = 12, '1.0-quest-local-video-stereo-multifec'
LV = 'Llocal/quest/cinema/LocalVideos;'
MA = 'Lcom/oculus/cinemasdk/MainActivity;'
# Tri-state int (-1 = not ours) turned into a verifier-safe boolean constant.
TRI = ('\n if-ltz v0, :lv_skip\n if-eqz v0, :lv_false\n const/4 v0, 0x1\n return v0\n'
       ' :lv_false\n const/4 v0, 0x0\n return v0\n :lv_skip')
LOCAL_FIRST = ' move-result v0\n if-eqz v0, :lv_skip\n return-void\n :lv_skip'

# Each hook runs at the top of the method; the original body still runs for real computers.
HOOKS = {
    '.method public initPcSelector()V': None,  # appended before return-void instead
    '.method public getPcPairState(Ljava/lang/String;)I': (
        f'invoke-static {{p1}}, {LV}->isLocal(Ljava/lang/String;)Z\n move-result v0\n if-eqz v0, :lv_skip\n'
        ' const/4 v0, 0x1\n return v0\n :lv_skip'),
    '.method public getPcState(Ljava/lang/String;)I': (
        f'invoke-static {{p1}}, {LV}->isLocal(Ljava/lang/String;)Z\n move-result v0\n if-eqz v0, :lv_skip\n'
        ' const/4 v0, 0x0\n return v0\n :lv_skip'),
    '.method public getPcReachability(Ljava/lang/String;)I': (
        f'invoke-static {{p1}}, {LV}->isLocal(Ljava/lang/String;)Z\n move-result v0\n if-eqz v0, :lv_skip\n'
        ' const/4 v0, 0x0\n return v0\n :lv_skip'),
    '.method public initAppSelector(Ljava/lang/String;)V':
        f'invoke-static {{p0, p1}}, {LV}->initApps({MA}Ljava/lang/String;)Z\n' + LOCAL_FIRST,
    '.method public createVideoThumbnail(Ljava/lang/String;ILjava/lang/String;II)Z':
        f'invoke-static/range {{p0 .. p5}}, {LV}->thumbnail({MA}Ljava/lang/String;ILjava/lang/String;II)I\n move-result v0' + TRI,
    # null: played locally; otherwise the computer uuid to stream from.
    '.method public startMovie(Ljava/lang/String;Ljava/lang/String;ILjava/lang/String;IIIZZ)V': (
        f'invoke-static {{p0, p1, p3}}, {LV}->start({MA}Ljava/lang/String;I)Ljava/lang/String;\n'
        ' move-result-object v0\n if-nez v0, :lv_skip\n return-void\n :lv_skip\n move-object p1, v0'),
    '.method public stopMovie()V': f'invoke-static {{p0}}, {LV}->stop({MA})V',
    '.method public isPlaying()Z': f'invoke-static {{}}, {LV}->playingState()I\n move-result v0' + TRI,
    '.method public isPlaybackFinished()Z': f'invoke-static {{}}, {LV}->finishedState()I\n move-result v0' + TRI,
    '.method public hadPlaybackError()Z': f'invoke-static {{}}, {LV}->errorState()I\n move-result v0' + TRI,
    '.method public closeApp(Ljava/lang/String;I)V':
        f'invoke-static {{p1, p2}}, {LV}->ownsApp(Ljava/lang/String;I)Z\n' + LOCAL_FIRST,
    '.method public mouseScroll(B)V': f'invoke-static {{}}, {LV}->isActive()Z\n' + LOCAL_FIRST,
    '.method public dispatchKeyEvent(Landroid/view/KeyEvent;)Z': (
        f'invoke-static {{p1}}, {LV}->onKey(Landroid/view/KeyEvent;)Z\n move-result v0\n'
        ' if-eqz v0, :lv_skip\n const/4 v0, 0x1\n return v0\n :lv_skip'),
    '.method protected onPause()V': f'invoke-static {{}}, {LV}->onPause()V',
    '.method protected onResume()V': f'invoke-static {{}}, {LV}->onResume()V',
}
PC_SELECTOR_CALL = ('invoke-static/range {v0 .. v7}, Lcom/oculus/cinemasdk/MainActivity;->nativeAddPc'
                    '(JLjava/lang/String;Ljava/lang/String;IILjava/lang/String;Z)V')


def method_span(lines, header):
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == header)
    except StopIteration:
        raise KitError('MainActivity method not found: ' + header)
    end = next(i for i in range(start, len(lines)) if lines[i].strip() == '.end method')
    return start, end


def body_start(lines, start):
    """First code line: after .locals, single-line .param entries and .prologue."""
    i = start + 1
    if not lines[i].strip().startswith('.locals'):
        raise KitError('Unexpected method layout at: ' + lines[start])
    i += 1
    while lines[i].strip() == '' or lines[i].strip().startswith(('.param', '.prologue')):
        if lines[i].strip().startswith('.annotation'):
            raise KitError('Unexpected annotation in: ' + lines[start])
        i += 1
    return i


def patch_main_activity(path: Path):
    lines = path.read_text().splitlines()
    if any('LocalVideos' in line for line in lines):
        raise KitError('MainActivity is already patched; start from the v8 APK')
    for header, code in HOOKS.items():
        start, end = method_span(lines, header)
        if code is None:
            ret = next(i for i in range(end, start, -1) if lines[i].strip() == 'return-void')
            lines[ret:ret] = ['    invoke-static {p0}, %s->addLocalPc(%s)V' % (LV, MA), '']
            continue
        at = body_start(lines, start)
        lines[at:at] = ['    ' + line.strip() for line in code.split('\n')] + ['']
    path.write_text('\n'.join(lines) + '\n')


def patch_pc_selector(path: Path):
    text = path.read_text()
    if text.count(PC_SELECTOR_CALL) != 1:
        raise KitError('PcSelector nativeAddPc call not found exactly once')
    path.write_text(text.replace(PC_SELECTOR_CALL, PC_SELECTOR_CALL.replace(MA + '->nativeAddPc', LV + '->addRemotePc')))


def java_sources():
    """cinema/java (left-hand base) overlaid by cinema/v12/java."""
    sources = {}
    for folder in (ROOT / 'cinema/java', ROOT / 'cinema/v12/java'):
        for path in folder.rglob('*.java'):
            sources[path.relative_to(folder)] = path
    return [sources[key] for key in sorted(sources)]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--base-apk', type=Path, default=DIST / 'QuestCinemaFix-v8.apk', help='v8 APK from tools/build_cinema.py')
    parser.add_argument('--output', type=Path, default=DIST / 'QuestCinemaFix-v12.apk')
    parser.add_argument('--keystore')
    parser.add_argument('--password-file')
    args = parser.parse_args()
    base = args.base_apk.resolve()
    if not base.is_file():
        raise KitError('Build v8 first: python3 tools/build_cinema.py --native-library dist/libmoonlight-core.so')
    LOCAL.mkdir(exist_ok=True)
    apktool = download(APKTOOL_URL, CACHE / 'apktool-3.0.3.jar', APKTOOL_SHA)
    framework = CACHE / 'framework'
    framework.mkdir(parents=True, exist_ok=True)
    jar = android_jar()
    with tempfile.TemporaryDirectory(prefix='cinema-v12-', dir=LOCAL) as directory:
        work = Path(directory)
        classes, dex, generated, decoded = work / 'classes', work / 'dex', work / 'generated', work / 'decoded'
        classes.mkdir(); dex.mkdir()
        # Stubs only satisfy javac; -implicit:none keeps them out of the output.
        run([executable('javac'), '--release', '8', '-cp', jar, '-sourcepath', ROOT / 'cinema/v12/stubs',
             '-implicit:none', '-d', classes, *java_sources()])
        ours = sorted((classes / 'local').rglob('*.class'))
        run([build_tool('d8'), '--min-api', '29', '--lib', jar, '--classpath', classes, '--output', dex, *ours])
        controls = work / 'controls-only.apk'
        with zipfile.ZipFile(base) as source, zipfile.ZipFile(controls, 'w') as dest:
            for name in ('AndroidManifest.xml', 'resources.arsc'):
                dest.writestr(name, source.read(name))
            dest.write(dex / 'classes.dex', 'classes.dex')
        run([executable('java'), '-jar', apktool, 'd', '-f', '-r', '-p', framework, '-o', generated, controls])
        if (generated / 'smali/com').exists():
            raise KitError('Stub classes leaked into the generated DEX')
        run([executable('java'), '-jar', apktool, 'd', '-f', '-p', framework, '-o', decoded, base])
        target = decoded / 'smali/local/quest/cinema'
        for old in target.glob('*.smali'):
            old.unlink()
        for new in (generated / 'smali/local/quest/cinema').glob('*.smali'):
            shutil.copy2(new, target / new.name)
        patch_main_activity(decoded / 'smali/com/oculus/cinemasdk/MainActivity.smali')
        patch_pc_selector(decoded / 'smali/com/limelight/PcSelector.smali')
        yml = decoded / 'apktool.yml'
        text = yml.read_text()
        lines = [line for line in text.splitlines() if line.strip().startswith(('versionCode:', 'versionName:'))]
        if len(lines) != 2:
            raise KitError('Unexpected apktool.yml version block')
        for line in lines:
            key = line.split(':')[0]
            text = text.replace(line, line.split(':')[0] + ': ' + (str(VERSION_CODE) if 'Code' in key else VERSION_NAME))
        yml.write_text(text)
        rebuilt = work / 'rebuilt.apk'
        run([executable('java'), '-jar', apktool, 'b', '-f', '-p', framework, '-o', rebuilt, decoded])
        # apktool re-encodes resources on the way through; take only the new DEX and manifest
        # (version bump) and copy every other entry from v8 unchanged, compression included.
        unsigned = work / 'unsigned.apk'
        with zipfile.ZipFile(base) as old, zipfile.ZipFile(rebuilt) as new, zipfile.ZipFile(unsigned, 'w') as out:
            fresh = {n for n in new.namelist() if n == 'AndroidManifest.xml' or (n.startswith('classes') and n.endswith('.dex'))}
            for info in old.infolist():
                if info.filename.startswith('META-INF/') or info.filename in fresh or \
                        (info.filename.startswith('classes') and info.filename.endswith('.dex')):
                    continue
                out.writestr(info, old.read(info.filename))
            for name in sorted(fresh):
                out.writestr(new.getinfo(name), new.read(name))
        badging = run([build_tool('aapt'), 'dump', 'badging', unsigned], capture=True)
        if f"versionCode='{VERSION_CODE}'" not in badging or "name='local.quest.cinema'" not in badging:
            raise KitError('Rebuilt manifest does not carry the expected package/version')
        output = args.output.resolve()
        sign_apk(unsigned, output, args.keystore, args.password_file)
    with zipfile.ZipFile(base) as old, zipfile.ZipFile(output) as new:
        kept = [n for n in old.namelist() if n.startswith(('lib/', 'assets/', 'res/')) or n == 'resources.arsc']
        changed = [n for n in kept if n not in new.namelist() or old.read(n) != new.read(n)]
        if changed:
            raise KitError('v12 must not change native code, assets or resources: ' + ', '.join(changed[:5]))
    print(f'Cinema v{VERSION_CODE} ({VERSION_NAME}); {len(kept)} native/asset/resource entries unchanged; SHA-256 {sha256(output)}')


if __name__ == '__main__':
    try:
        main()
    except KitError as error:
        raise SystemExit(str(error))

"""ADB access to the user's own, already-authorized Quest 1. Never creates new ADB trust."""
import asyncio
import json
import os
import re
import shutil
import subprocess
import threading
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Device details (serial, LAN address, ports) stay in the kit's git-ignored .local folder.
LOCAL = ROOT.parent / '.local'
CONFIG = LOCAL / 'console.json'
EXAMPLE = ROOT / 'config.example.json'
CACHE = LOCAL / 'console-cache'
ADB = shutil.which('adb') or '/opt/homebrew/bin/adb'


def find_aapt():
    roots = [os.environ.get('ANDROID_SDK_ROOT'), os.environ.get('ANDROID_HOME'),
             '/opt/homebrew/share/android-commandlinetools', str(Path.home() / 'Library/Android/sdk')]
    for root in filter(None, roots):
        tools = sorted(Path(root).glob('build-tools/*/aapt'))
        if tools:
            return str(tools[-1])
    return shutil.which('aapt') or 'aapt'


AAPT = find_aapt()
HELPER = 'local.quest.adbkeeper'
CINEMA = 'local.quest.cinema'
LAUNCHER = 'com.threethan.launcher'
CORE_APPS = {HELPER: '启动助手', CINEMA: 'Quest Cinema Fix', LAUNCHER: 'Lightning Launcher'}
SYSTEM_APPS = {'com.oculus.browser': '浏览器'}

# Routes found in this headset's SystemUX (v50). Wi-Fi is the stock Android settings screen.
SETTINGS_PAGES = {
    'bluetooth': ('蓝牙配对', '/bluetooth?setting=devices_bluetooth_section'),
    'controllers': ('手柄', '/controllers'),
    'hands': ('手势追踪', '/hands?setting=hands_hand_tracking'),
    'guardian': ('边界', '/guardian_general'),
    'display': ('显示', '/display'),
    'sound': ('声音', '/sound?setting=microphone'),
    'power': ('电源', '/power'),
    'storage': ('存储', '/storage?setting=storage_section'),
    'experiments': ('实验功能', '/experiments'),
    'about': ('关于', '/about'),
    'wifi': ('Wi-Fi', None),
}

HELPER_TOGGLES = {
    'idle': ('主页空闲时自动打开应用列表', 'IDLE_ENABLE', 'IDLE_DISABLE'),
    'launcher': ('音量减加减加打开应用列表', 'LAUNCHER_ENABLE', 'LAUNCHER_DISABLE'),
    'cinema': ('开机自动打开影院', 'CINEMA_ENABLE', 'CINEMA_DISABLE'),
    'usb': ('USB ADB 常驻', 'USB_ENABLE', 'USB_DISABLE'),
    'wifi': ('无线 ADB 常驻', 'ENABLE', 'DISABLE'),
}


class QuestError(Exception):
    pass


def load_config():
    if not CONFIG.exists():
        raise QuestError('还没有配置：请把 console/config.example.json 复制为 .local/console.json，填上头显序列号和 Wi-Fi IP。')
    config = json.loads(EXAMPLE.read_text())
    config.update(json.loads(CONFIG.read_text()))
    return config


def save_config(config):
    LOCAL.mkdir(exist_ok=True)
    CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')


def run(args, timeout=15, binary=False):
    try:
        r = subprocess.run([str(a) for a in args], capture_output=True, timeout=timeout, text=not binary)
    except subprocess.TimeoutExpired:
        raise QuestError('命令超时：' + ' '.join(map(str, args[:4])))
    return r


def adb(*args, timeout=15, binary=False):
    return run([ADB, *args], timeout=timeout, binary=binary)


def serial_of(endpoint):
    r = adb('-s', endpoint, 'shell', 'getprop', 'ro.serialno', timeout=4)
    return r.stdout.strip() if r.returncode == 0 else None


def list_devices():
    out = []
    for line in adb('devices', timeout=5).stdout.splitlines()[1:]:
        f = line.split()
        if len(f) >= 2:
            out.append((f[0], f[1]))
    return out


def find_endpoint(config=None):
    """USB first, then a Wi-Fi endpoint that reports the expected serial."""
    config = config or load_config()
    serial, host = config['serial'], config['host']
    wireless = []
    for endpoint, state in list_devices():
        if state != 'device':
            continue
        if endpoint == serial:
            return endpoint, 'usb'
        if endpoint.startswith(host + ':') or endpoint.startswith('adb-' + serial):
            wireless.append(endpoint)
    for endpoint in wireless:
        if serial_of(endpoint) == serial:
            return endpoint, 'wifi'
    return None, None


async def _scan(host):
    found, sem = [], asyncio.Semaphore(128)

    async def probe(port):
        async with sem:
            try:
                _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), 0.18)
                found.append(port)
                writer.close()
            except (OSError, asyncio.TimeoutError):
                pass
    await asyncio.gather(*(probe(p) for p in range(32768, 65536)))
    return sorted(found)


_connect_lock = threading.Lock()


def connect_wireless():
    """Reconnect the already-paired headset over Wi-Fi; scans its ADB port range if the last port changed."""
    with _connect_lock:
        config = load_config()
        endpoint, transport = find_endpoint(config)
        if transport == 'wifi':
            return endpoint
        host, serial = config['host'], config['serial']
        restarted = []

        def attempt(port):
            candidate = '{}:{}'.format(host, port)
            r = adb('connect', candidate, timeout=8)
            if 'No route to host' in r.stdout + r.stderr:
                # macOS Local Network privacy: an adb server started by an app without that
                # permission cannot reach the LAN. Restart it from this process once.
                if restarted:
                    raise QuestError('macOS 不允许 adb 访问局域网。请从“终端”启动控制台（双击 Quest 控制台.command），'
                                     '并在“系统设置 → 隐私与安全性 → 本地网络”里允许“终端”。')
                restarted.append(True)
                adb('kill-server', timeout=10)
                adb('start-server', timeout=20)
                return attempt(port)
            if r.returncode == 0 and serial_of(candidate) == serial:
                config['port'] = port
                save_config(config)
                return candidate
            adb('disconnect', candidate, timeout=5)
            return None
        if config.get('port'):
            ok = attempt(config['port'])
            if ok:
                return ok
        for port in asyncio.run(_scan(host)):
            ok = attempt(port)
            if ok:
                return ok
        raise QuestError('在 {} 上没有找到已授权的无线 ADB。请确认头显已开机、已连上 Wi-Fi，并且启动助手的“无线 ADB 常驻”已开启。'.format(host))


def device():
    endpoint, _ = find_endpoint()
    if not endpoint:
        raise QuestError('没有连上头显。请插上数据线，或点“重新连接无线 ADB”。')
    return endpoint


def shell(*args, timeout=15, endpoint=None):
    r = adb('-s', endpoint or device(), 'shell', *args, timeout=timeout)
    if r.returncode != 0 and not r.stdout:
        raise QuestError((r.stderr or 'adb shell 失败').strip())
    return r.stdout


# ---------- status ----------

SEP = '@@QUEST@@'


def parse_status(raw):
    parts = raw.split(SEP)
    battery, df, power, resumed, ip, branch = (parts + [''] * 6)[:6]
    b = dict(re.findall(r'^[ \t]*([A-Za-z ]+):[ \t]*(\S+)', battery, re.M))
    status = {'2': '充电中', '3': '放电中', '4': '未充电', '5': '已充满'}.get(b.get('status'), '未知')
    temp = int(b['temperature']) / 10 if b.get('temperature', '').isdigit() else None
    storage = None
    rows = [l.split() for l in df.strip().splitlines() if l.strip()]
    if rows and len(rows[-1]) >= 4 and rows[-1][1].isdigit():
        total, used = int(rows[-1][1]) * 1024, int(rows[-1][2]) * 1024
        storage = {'total_gb': round(total / 1e9, 1), 'free_gb': round((total - used) / 1e9, 1)}
    wake = re.search(r'mWakefulness=(\w+)', power)
    top = re.search(r'u0 ([\w.]+)/([\w.$]+)', resumed)
    addr = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip)
    version = re.search(r'-v(\d+)', branch)
    return {
        'battery': {'level': int(b['level']) if b.get('level', '').isdigit() else None, 'status': status,
                    'temperature_c': temp, 'plugged': b.get('AC powered') == 'true' or b.get('USB powered') == 'true'},
        'storage': storage,
        'awake': wake.group(1) == 'Awake' if wake else None,
        'foreground': top.group(1) if top else None,
        'wifi_ip': addr.group(1) if addr else None,
        'firmware': 'v' + version.group(1) if version else branch.strip(),
    }


def status():
    endpoint, transport = find_endpoint()
    if not endpoint:
        return {'connected': False}
    cmd = ('dumpsys battery; echo {s}; df /data; echo {s}; dumpsys power | grep mWakefulness=; echo {s}; '
           'dumpsys activity activities | grep mResumedActivity | head -1; echo {s}; ip -4 addr show wlan0; '
           'echo {s}; getprop ro.build.branch').format(s=SEP)
    info = parse_status(shell(cmd, endpoint=endpoint))
    info.update(connected=True, endpoint=endpoint, transport=transport)
    return info


# ---------- helper app ----------

def parse_helper_status(text):
    m = re.search(r'data="([^"]*)"', text)
    if not m:
        return None
    return dict(item.split('=', 1) for item in m.group(1).split(';') if '=' in item)


def helper_status():
    out = shell('am', 'broadcast', '-n', HELPER + '/.AdminReceiver', '-a', HELPER + '.STATUS')
    data = parse_helper_status(out)
    if data is None:
        return {'installed': False}
    toggles = {key: data.get(key) == 'true' for key in HELPER_TOGGLES if key in data}
    return {'installed': True, 'toggles': toggles, 'version': data.get('version'),
            'idle_permitted': data.get('idle_permitted') == 'true',
            'labels': {k: v[0] for k, v in HELPER_TOGGLES.items()}}


def helper_set(key, enabled):
    if key not in HELPER_TOGGLES:
        raise QuestError('未知开关：' + key)
    action = HELPER_TOGGLES[key][1 if enabled else 2]
    shell('am', 'broadcast', '-n', HELPER + '/.AdminReceiver', '-a', HELPER + '.' + action)


# ---------- apps ----------

def _labels():
    path = CACHE / 'labels.json'
    return json.loads(path.read_text()) if path.exists() else {}


def _save_labels(labels):
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / 'labels.json').write_text(json.dumps(labels, ensure_ascii=False, indent=2))


def badging(apk_path):
    r = run([AAPT, 'dump', 'badging', apk_path], timeout=60)
    if r.returncode != 0:
        raise QuestError('无法读取安装包：' + (r.stderr or '').strip()[:200])
    return r.stdout


def parse_badging(text):
    def one(pattern):
        m = re.search(pattern, text, re.M)
        return m.group(1) if m else None
    label = one(r"^application-label-zh-CN:'([^']*)'") or one(r"^application-label:'([^']*)'") or one(r"^application: label='([^']*)'")
    native = one(r"^native-code:(.*)$")
    return {
        'package': one(r"^package: name='([^']*)'"),
        'version_name': one(r"versionName='([^']*)'"),
        'version_code': one(r"versionCode='([^']*)'"),
        'label': label,
        'min_sdk': int(one(r"^sdkVersion:'(\d+)'") or 1),
        'native_code': re.findall(r"'([^']+)'", native) if native else [],
    }


def label_for(package, apk_remote, stamp, endpoint):
    labels = _labels()
    key = '{}@{}'.format(package, stamp)
    if key in labels:
        return labels[key]
    label = package
    size = shell('stat', '-c', '%s', apk_remote, endpoint=endpoint).strip()
    if size.isdigit() and int(size) < 300_000_000:
        CACHE.mkdir(parents=True, exist_ok=True)
        local = CACHE / (package + '.apk')
        if adb('-s', endpoint, 'pull', apk_remote, str(local), timeout=120).returncode == 0:
            try:
                label = parse_badging(badging(local)).get('label') or package
            except QuestError:
                pass
            local.unlink()
    labels[key] = label
    _save_labels(labels)
    return label


def list_apps():
    endpoint = device()
    apps = []
    raw = shell('pm list packages -3 -f; echo {s}; dumpsys package packages | grep -E "^  Package \\[|lastUpdateTime="'.format(s=SEP), endpoint=endpoint, timeout=30)
    listing, dump = (raw.split(SEP) + [''])[:2]
    stamps, current = {}, None
    for line in dump.splitlines():
        m = re.match(r'\s*Package \[([\w.]+)\]', line)
        if m:
            current = m.group(1)
        elif current and 'lastUpdateTime=' in line:
            stamps[current] = line.split('=', 1)[1].strip()
    for line in listing.splitlines():
        m = re.match(r'package:(.+\.apk)=([\w.]+)$', line.strip())
        if not m:
            continue
        path, package = m.groups()
        label = CORE_APPS.get(package) or label_for(package, path, stamps.get(package, ''), endpoint)
        apps.append({'package': package, 'label': label, 'core': package in CORE_APPS, 'system': False})
    for package, label in SYSTEM_APPS.items():
        apps.append({'package': package, 'label': label, 'core': False, 'system': True})
    apps.sort(key=lambda a: (not a['core'], a['system'], a['label'].lower()))
    return apps


def launch(package):
    endpoint = device()
    out = shell('cmd', 'package', 'resolve-activity', '--brief', '-c', 'android.intent.category.LAUNCHER', package, endpoint=endpoint)
    component = out.strip().splitlines()[-1] if out.strip() else ''
    if '/' not in component:
        raise QuestError('这个应用没有可以打开的入口：' + package)
    shell('am', 'start', '-n', component, endpoint=endpoint)


def stop(package):
    shell('am', 'force-stop', package)


def uninstall(package):
    if package in SYSTEM_APPS:
        raise QuestError('系统应用不能卸载。')
    r = adb('-s', device(), 'uninstall', package, timeout=60)
    if 'Success' not in r.stdout:
        raise QuestError('卸载失败：' + (r.stdout + r.stderr).strip()[:300])


# ---------- install ----------

QUEST1_API = 29


def inspect_apk(path):
    info = parse_badging(badging(path))
    if not info['package']:
        raise QuestError('这不是有效的 APK 安装包。')
    warnings, problems = [], []
    if info['min_sdk'] > QUEST1_API:
        problems.append('需要 Android API {}，Quest 1 只有 {}。'.format(info['min_sdk'], QUEST1_API))
    if info['native_code'] and not any(a.startswith('arm') for a in info['native_code']):
        problems.append('只包含 {} 的原生代码，Quest 1 无法运行。'.format('、'.join(info['native_code'])))
    tree = run([AAPT, 'dump', 'xmltree', path, 'AndroidManifest.xml'], timeout=60).stdout
    info['vr'] = 'com.oculus.intent.category.VR' in tree or '"vr_only"' in tree
    m = re.search(r'="com\.oculus\.supportedDevices".*\n\s+A: android:value\(0x01010024\)="([^"]*)"', tree)
    if m:
        devices = [d.strip() for d in m.group(1).split('|')]
        info['supported_devices'] = devices
        if 'quest' not in devices and 'all' not in devices:
            warnings.append('开发者声明只支持 {}，不包括 Quest 1，可能无法运行。'.format('、'.join(devices)))
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
    if any('ovrplatform' in n.lower() for n in names):
        warnings.append('包含 Meta 平台库，可能会检查 Meta 账号授权；这台头显没有登录，打开后可能直接退出。')
    info['warnings'], info['problems'] = warnings, problems
    return info


def install_apk(path):
    info = inspect_apk(path)
    if info['problems']:
        raise QuestError('不兼容：' + ' '.join(info['problems']))
    r = adb('-s', device(), 'install', '-r', str(path), timeout=600)
    if 'Success' not in r.stdout:
        raise QuestError('安装失败：' + (r.stdout + r.stderr).strip()[-300:])
    return info


OBB = re.compile(r'^(main|patch)\.(\d+)\.([A-Za-z][\w.]*)\.obb$')


def install_obb(path, name):
    m = OBB.match(name)
    if not m:
        raise QuestError('OBB 文件名应为 main.<版本号>.<包名>.obb。')
    package = m.group(3)
    endpoint = device()
    remote_dir = '/sdcard/Android/obb/' + package
    shell('mkdir', '-p', remote_dir, endpoint=endpoint)
    r = adb('-s', endpoint, 'push', str(path), remote_dir + '/' + name, timeout=3600)
    if r.returncode != 0:
        raise QuestError('传输失败：' + r.stderr.strip()[-200:])
    return {'package': package, 'remote': remote_dir + '/' + name}


def push_media(path, name):
    endpoint = device()
    remote = '/sdcard/Movies/' + name
    shell('mkdir', '-p', '/sdcard/Movies', endpoint=endpoint)
    r = adb('-s', endpoint, 'push', str(path), remote, timeout=3600)
    if r.returncode != 0:
        raise QuestError('传输失败：' + r.stderr.strip()[-200:])
    shell('am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE', '-d', 'file://' + remote, endpoint=endpoint)
    return {'remote': remote}


def list_media():
    out = shell('ls', '-l', '/sdcard/Movies')
    files = []
    for line in out.splitlines():
        f = line.split(None, 7)
        if len(f) == 8 and f[0].startswith('-'):
            files.append({'name': f[7], 'size_mb': round(int(f[4]) / 1e6, 1)})
    return files


# ---------- controls ----------

def open_url(url):
    if not re.match(r'^https?://', url):
        raise QuestError('只支持 http:// 或 https:// 开头的网址。')
    shell('am', 'start', '-a', 'android.intent.action.VIEW', '-d', url, 'com.oculus.browser')


KEYS = {'up': 'KEYCODE_VOLUME_UP', 'down': 'KEYCODE_VOLUME_DOWN', 'mute': 'KEYCODE_VOLUME_MUTE'}


def volume(action):
    shell('input', 'keyevent', KEYS[action])


def wake(endpoint=None):
    # Quest ignores KEYCODE_WAKEUP while the proximity sensor reports "not worn"; POWER toggles,
    # so only send it when the headset is actually asleep.
    if 'mWakefulness=Awake' not in shell('dumpsys', 'power', endpoint=endpoint):
        shell('input', 'keyevent', 'KEYCODE_POWER', endpoint=endpoint)


def power(action):
    if action == 'wake':
        wake()
    elif action == 'sleep':
        shell('input', 'keyevent', 'KEYCODE_SLEEP')
    elif action == 'keep_awake_on':
        endpoint = device()
        wake(endpoint)
        shell('am', 'broadcast', '-a', 'com.oculus.vrpowermanager.prox_close', endpoint=endpoint)
    elif action == 'keep_awake_off':
        shell('am', 'broadcast', '-a', 'com.oculus.vrpowermanager.automation_disable')
    elif action == 'reboot':
        adb('-s', device(), 'reboot', timeout=20)
    else:
        raise QuestError('未知操作：' + action)


def open_settings(page):
    if page not in SETTINGS_PAGES:
        raise QuestError('未知设置页：' + page)
    route = SETTINGS_PAGES[page][1]
    if route is None:
        shell('am', 'start', '-a', 'android.settings.WIFI_SETTINGS')
    else:
        shell('am', 'start', '-a', 'android.intent.action.VIEW', '-n', 'com.oculus.vrshell/.MainActivity',
              '-d', 'systemux://settings', '-e', 'uri', route)


def screenshot():
    r = adb('-s', device(), 'exec-out', 'screencap', '-p', timeout=20, binary=True)
    if r.returncode != 0 or not r.stdout.startswith(b'\x89PNG'):
        return None
    return r.stdout

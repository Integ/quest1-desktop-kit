#!/usr/bin/env python3
"""Quest 控制台: a local-only web page for managing the Quest 1 over ADB."""
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import quest

STATIC = quest.ROOT / 'static'
LOGS = quest.CACHE
TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8'}
state = {'keep_awake': False}


def port_open(port):
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(('127.0.0.1', port)) == 0


def sunshine_pids(config):
    if not config.get('sunshine_conf'):
        return []
    r = subprocess.run(['pgrep', '-f', config['sunshine_conf']], capture_output=True, text=True)
    return [int(p) for p in r.stdout.split() if p.isdigit() and int(p) != os.getpid()]


def sunshine(action):
    config = quest.load_config()
    if action == 'start':
        if port_open(47990):
            return '串流服务已经在运行。'
        LOGS.mkdir(parents=True, exist_ok=True)
        log = open(LOGS / 'sunshine-console.log', 'ab')
        command = [config.get('sunshine') or shutil.which('sunshine') or 'sunshine']
        if config.get('sunshine_conf'):
            command.append(config['sunshine_conf'])
        subprocess.Popen(command, stdout=log, stderr=log,
                         stdin=subprocess.DEVNULL, start_new_session=True)
        return '已启动串流服务。在头显的 Quest Cinema Fix 里选择 Mac Quest Display → Mac Desktop。'
    if action == 'stop':
        pids = sunshine_pids(config)
        for pid in pids:
            os.kill(pid, signal.SIGTERM)
        return '已停止串流服务。' if pids else '串流服务没有在运行。'
    raise quest.QuestError('未知操作：' + action)


def mirror():
    config = quest.load_config()
    endpoint = quest.device()
    LOGS.mkdir(parents=True, exist_ok=True)
    log = open(LOGS / 'mirror.log', 'ab')
    subprocess.Popen([config.get('scrcpy') or shutil.which('scrcpy') or 'scrcpy', '--serial', endpoint, '--no-audio', '--window-title', 'Quest 镜像'],
                     stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True,
                     env=dict(os.environ, ADB=quest.ADB))
    return '镜像窗口正在打开。'


class Handler(BaseHTTPRequestHandler):
    server_version = 'QuestConsole/1'

    def log_message(self, fmt, *args):
        if '/api/screenshot' not in (args[0] if args else ''):
            sys.stderr.write('%s %s\n' % (self.log_date_time_string(), fmt % args))

    # Local-only: reject other Host names (DNS rebinding) and cross-site writes.
    def allowed(self, write):
        port = self.server.server_address[1]
        if self.headers.get('Host') not in ('127.0.0.1:%d' % port, 'localhost:%d' % port):
            return False
        return not write or self.headers.get('X-Quest-Console') == '1'

    def send(self, code, body, ctype='application/json; charset=utf-8'):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def json_body(self):
        length = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(length) or b'{}')

    def handle_api(self, method, path, query):
        if method == 'GET':
            if path == '/api/status':
                info = quest.status()
                info.update(sunshine=port_open(47990), keep_awake=state['keep_awake'])
                return info
            if path == '/api/helper':
                return quest.helper_status()
            if path == '/api/apps':
                return quest.list_apps()
            if path == '/api/media':
                return quest.list_media()
            if path == '/api/settings':
                return [{'key': k, 'label': v[0]} for k, v in quest.SETTINGS_PAGES.items()]
        if method == 'POST':
            body = self.json_body()
            if path == '/api/connect':
                return {'endpoint': quest.connect_wireless()}
            if path == '/api/helper':
                quest.helper_set(body['key'], bool(body['enabled']))
                return quest.helper_status()
            if path in ('/api/apps/launch', '/api/apps/stop', '/api/apps/uninstall'):
                getattr(quest, path.rsplit('/', 1)[1])(body['package'])
                return {'ok': True}
            if path == '/api/open-url':
                quest.open_url(body['url'].strip())
                return {'ok': True}
            if path == '/api/volume':
                quest.volume(body['action'])
                return {'ok': True}
            if path == '/api/power':
                quest.power(body['action'])
                if body['action'] in ('keep_awake_on', 'keep_awake_off', 'reboot'):
                    state['keep_awake'] = body['action'] == 'keep_awake_on'
                return {'ok': True}
            if path == '/api/settings':
                quest.open_settings(body['page'])
                return {'ok': True}
            if path == '/api/sunshine':
                return {'message': sunshine(body['action'])}
            if path == '/api/mirror':
                return {'message': mirror()}
        if method == 'PUT' and path == '/api/upload':
            return self.upload(query.get('kind', [''])[0], Path(query.get('name', [''])[0]).name)
        return None

    def upload(self, kind, name):
        if not name or kind not in ('app', 'media'):
            raise quest.QuestError('上传参数不正确。')
        lower = name.lower()
        if kind == 'app' and not (lower.endswith('.apk') or lower.endswith('.obb')):
            raise quest.QuestError('只能安装 .apk，或给已安装的应用补充 .obb 数据文件。')
        remaining = int(self.headers.get('Content-Length') or 0)
        with tempfile.TemporaryDirectory(prefix='quest-console-') as tmp:
            path = Path(tmp) / name
            with open(path, 'wb') as f:
                while remaining > 0:
                    chunk = self.rfile.read(min(remaining, 1 << 20))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
            if remaining:
                raise quest.QuestError('上传没有完成。')
            if kind == 'media':
                return quest.push_media(path, name)
            if lower.endswith('.obb'):
                return quest.install_obb(path, name)
            return quest.install_apk(path)

    def dispatch(self, method):
        url = urlparse(self.path)
        path = url.path
        if not self.allowed(method != 'GET'):
            return self.send(403, {'error': '只接受本机控制台页面的请求。'})
        if method == 'GET' and not path.startswith('/api/'):
            name = 'index.html' if path == '/' else path.lstrip('/').replace('static/', '', 1)
            file = (STATIC / name).resolve()
            if file.parent != STATIC.resolve() or not file.is_file():
                return self.send(404, {'error': 'not found'})
            return self.send(200, file.read_bytes(), TYPES.get(file.suffix, 'application/octet-stream'))
        try:
            if method == 'GET' and path == '/api/screenshot':
                png = quest.screenshot()
                return self.send(200, png, 'image/png') if png else self.send(204, b'', 'text/plain')
            result = self.handle_api(method, path, parse_qs(url.query))
            if result is None:
                return self.send(404, {'error': '没有这个接口：' + path})
            return self.send(200, result)
        except quest.QuestError as e:
            return self.send(409, {'error': str(e)})
        except (KeyError, ValueError) as e:
            return self.send(400, {'error': '请求参数不正确：' + str(e)})
        except Exception as e:
            traceback.print_exc()
            return self.send(500, {'error': '控制台出错：' + str(e)})

    def do_GET(self):
        self.dispatch('GET')

    def do_POST(self):
        self.dispatch('POST')

    def do_PUT(self):
        self.dispatch('PUT')


def main():
    try:
        port = quest.load_config().get('listen_port', 8765)
    except quest.QuestError as e:
        raise SystemExit(str(e))
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    print('Quest 控制台已启动：http://localhost:%d （关闭这个窗口即可停止）' % port, flush=True)
    if '--open' in sys.argv:
        threading.Timer(0.5, lambda: subprocess.run(['open', 'http://localhost:%d' % port])).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

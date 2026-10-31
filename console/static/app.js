'use strict';
const $ = (sel) => document.querySelector(sel);
const HEADERS = { 'X-Quest-Console': '1', 'Content-Type': 'application/json' };
let connected = false;

function toast(text, bad = false) {
  const el = $('#toast');
  el.textContent = text;
  el.className = 'show' + (bad ? ' bad' : '');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.className = ''; }, bad ? 6000 : 2500);
}

async function api(method, path, body) {
  const res = await fetch(path, { method, headers: method === 'GET' ? {} : HEADERS, body: body ? JSON.stringify(body) : undefined });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || '请求失败（' + res.status + '）');
  return data;
}

// Runs an action from a button, keeping it disabled until the headset answers.
async function act(button, fn, done) {
  if (button) button.disabled = true;
  try {
    const result = await fn();
    if (done) toast(typeof done === 'function' ? done(result) : done);
    return result;
  } catch (e) {
    toast(e.message, true);
  } finally {
    if (button) button.disabled = false;
  }
}

function esc(text) {
  return String(text ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

// ---------- status ----------
async function refreshStatus() {
  let s;
  try { s = await api('GET', '/api/status'); } catch (e) { s = { connected: false, error: e.message }; }
  connected = s.connected;
  const pill = $('#conn');
  pill.textContent = s.connected ? (s.transport === 'usb' ? '已连接 · USB 数据线' : '已连接 · Wi-Fi') : '未连接';
  pill.className = 'pill ' + (s.connected ? 'ok' : 'bad');
  if (!s.connected) {
    $('#status').innerHTML = '<dt>状态</dt><dd>没有连上头显。插上数据线，或点上方“重新连接无线 ADB”。</dd>';
    return;
  }
  const b = s.battery || {};
  const rows = [
    ['电量', b.level == null ? '—' : b.level + '%（' + b.status + (b.plugged ? '，已接电源' : '') + '）'],
    ['温度', b.temperature_c == null ? '—' : b.temperature_c.toFixed(1) + ' °C'],
    ['存储', s.storage ? '剩余 ' + s.storage.free_gb + ' GB / 共 ' + s.storage.total_gb + ' GB' : '—'],
    ['屏幕', s.awake ? '唤醒' : '休眠（戴上或点“唤醒”）'],
    ['前台', s.foreground || '—'],
    ['Wi-Fi IP', s.wifi_ip || '未连接 Wi-Fi'],
    ['系统版本', s.firmware || '—'],
  ];
  $('#status').innerHTML = rows.map(([k, v]) => '<dt>' + k + '</dt><dd>' + esc(v) + '</dd>').join('');
  $('#sunshine-state').textContent = s.sunshine ? '串流服务：运行中' : '串流服务：未运行';
  const keep = $('#keep-awake');
  keep.classList.toggle('on', !!s.keep_awake);
  keep.textContent = '不戴也保持唤醒：' + (s.keep_awake ? '开' : '关');
}

// ---------- screen ----------
const canvas = $('#screen');
const ctx = canvas.getContext('2d');
let screenBusy = false;

async function refreshScreen() {
  if (screenBusy || !connected || document.hidden) return;
  screenBusy = true;
  try {
    const res = await fetch('/api/screenshot');
    if (res.status === 204) {
      $('#screen-note').textContent = '当前画面不允许截屏，或头显正在休眠。';
      return;
    }
    if (!res.ok) throw new Error((await res.json()).error);
    const bitmap = await createImageBitmap(await res.blob());
    const eye = Number($('#screen-eye').value);
    const w = bitmap.width / 2;
    canvas.width = w / 2; canvas.height = bitmap.height / 2;
    ctx.drawImage(bitmap, eye * w, 0, w, bitmap.height, 0, 0, canvas.width, canvas.height);
    $('#screen-note').textContent = '';
  } catch (e) {
    $('#screen-note').textContent = '截图失败：' + e.message;
  } finally {
    screenBusy = false;
  }
}

// ---------- apps ----------
async function refreshApps() {
  const list = $('#apps');
  list.innerHTML = '<li>读取应用列表…（第一次会稍慢）</li>';
  try {
    const apps = await api('GET', '/api/apps');
    list.innerHTML = apps.map((a) => '<li data-pkg="' + esc(a.package) + '" data-core="' + a.core + '" data-label="' + esc(a.label) + '">'
      + '<span class="name">' + esc(a.label) + (a.core ? '<span class="tag">改造组件</span>' : '') + (a.system ? '<span class="tag">系统</span>' : '')
      + '<small>' + esc(a.package) + '</small></span>'
      + '<button data-app="launch" class="small">打开</button>'
      + '<button data-app="stop" class="ghost small">关闭</button>'
      + (a.system ? '' : '<button data-app="uninstall" class="danger small">卸载</button>') + '</li>').join('');
  } catch (e) {
    list.innerHTML = '<li>' + esc(e.message) + '</li>';
  }
}

$('#apps').addEventListener('click', (ev) => {
  const btn = ev.target.closest('button[data-app]');
  if (!btn) return;
  const li = btn.closest('li');
  const pkg = li.dataset.pkg, label = li.dataset.label, op = btn.dataset.app;
  if (op === 'uninstall') {
    const extra = li.dataset.core === 'true' ? '\n\n注意：这是之前改造装上的组件，卸载后相关功能（自启、快捷键、无线 ADB 等）会失效，授权也要重新做。' : '';
    if (!confirm('确定从头显卸载“' + label + '”吗？应用数据会一起删除。' + extra)) return;
  }
  const done = { launch: '已在头显里打开 ' + label, stop: '已关闭 ' + label, uninstall: '已卸载 ' + label }[op];
  act(btn, () => api('POST', '/api/apps/' + op, { package: pkg }), done).then(() => { if (op === 'uninstall') refreshApps(); });
});

// ---------- uploads ----------
function upload(kind, file, target) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const bar = document.createElement('progress');
    bar.max = 1; bar.value = 0;
    const box = document.createElement('div');
    box.className = 'result';
    box.innerHTML = '<div>' + esc(file.name) + '：上传中…</div>';
    box.appendChild(bar);
    target.prepend(box);
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) bar.value = e.loaded / e.total; };
    xhr.upload.onload = () => { box.firstChild.textContent = file.name + '：' + (kind === 'app' ? '正在检查并安装…' : '正在传到头显…'); };
    xhr.onload = () => {
      bar.remove();
      let data = {};
      try { data = JSON.parse(xhr.responseText); } catch (_) {}
      if (xhr.status === 200) { box.classList.add('ok'); resolve({ data, box }); }
      else { box.classList.add('bad'); box.firstChild.textContent = file.name + '：' + (data.error || '失败'); reject(new Error(data.error)); }
    };
    xhr.onerror = () => { bar.remove(); box.classList.add('bad'); box.firstChild.textContent = file.name + '：连接中断'; reject(new Error('连接中断')); };
    xhr.open('PUT', '/api/upload?kind=' + kind + '&name=' + encodeURIComponent(file.name));
    xhr.setRequestHeader('X-Quest-Console', '1');
    xhr.send(file);
  });
}

async function installFiles(files) {
  for (const file of files) {
    try {
      const { data, box } = await upload('app', file, $('#install-result'));
      if (data.remote) {
        box.firstChild.textContent = file.name + '：已放到 ' + data.remote;
        continue;
      }
      const lines = ['已安装 ' + (data.label || data.package) + ' ' + (data.version_name || '') + (data.vr ? '（VR 应用）' : '（2D 应用）')];
      box.innerHTML = '<div>' + esc(lines[0]) + '</div>' + (data.warnings || []).map((w) => '<div class="warn">⚠ ' + esc(w) + '</div>').join('');
    } catch (_) { /* shown in the result box */ }
  }
  refreshApps();
}

async function pushMedia(files) {
  for (const file of files) {
    try {
      const { data, box } = await upload('media', file, $('#media'));
      box.remove();
      toast('已传到头显：' + data.remote);
    } catch (_) { /* shown in the result box */ }
  }
  refreshMedia();
}

function dropZone(zone, input, handler) {
  input.addEventListener('change', () => { handler([...input.files]); input.value = ''; });
  zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('over'));
  zone.addEventListener('drop', (e) => { e.preventDefault(); zone.classList.remove('over'); handler([...e.dataTransfer.files]); });
}
dropZone($('#install-drop'), $('#install-file'), installFiles);
dropZone($('#media-drop'), $('#media-file'), pushMedia);

async function refreshMedia() {
  try {
    const files = await api('GET', '/api/media');
    $('#media').innerHTML = files.length
      ? files.map((f) => '<li><span class="name">' + esc(f.name) + '</span><small>' + f.size_mb + ' MB</small></li>').join('')
      : '<li class="note">头显的 Movies 文件夹里还没有视频。</li>';
  } catch (e) {
    $('#media').innerHTML = '<li class="note">' + esc(e.message) + '</li>';
  }
}

// ---------- settings, helper, controls ----------
async function loadSettings() {
  const pages = await api('GET', '/api/settings');
  $('#settings').innerHTML = pages.map((p) => '<button class="ghost" data-page="' + p.key + '">' + esc(p.label) + '</button>').join('');
}
$('#settings').addEventListener('click', (ev) => {
  const btn = ev.target.closest('button[data-page]');
  if (btn) act(btn, () => api('POST', '/api/settings', { page: btn.dataset.page }), '已在头显里打开“' + btn.textContent + '”').then(() => setTimeout(refreshScreen, 1500));
});

async function refreshHelper() {
  const box = $('#helper');
  try {
    const h = await api('GET', '/api/helper');
    if (!h.installed) { box.innerHTML = '<p class="note">头显上没有找到启动助手。</p>'; return; }
    box.innerHTML = Object.entries(h.labels).map(([key, label]) => {
      const on = !!h.toggles[key];
      const hint = key === 'idle' && on && !h.idle_permitted ? '<small class="note">（还需要电脑授予日志读取权限）</small>' : '';
      return '<label class="switch"><span>' + esc(label) + hint + '</span><input type="checkbox" data-helper="' + key + '"' + (on ? ' checked' : '') + '></label>';
    }).join('') + (h.version ? '<p class="note">启动助手 v' + esc(h.version) + '</p>' : '<p class="note">启动助手版本较旧，部分开关状态读不到。</p>');
  } catch (e) {
    box.innerHTML = '<p class="note">' + esc(e.message) + '</p>';
  }
}
$('#helper').addEventListener('change', (ev) => {
  const input = ev.target.closest('input[data-helper]');
  if (!input) return;
  const key = input.dataset.helper;
  if (!input.checked && (key === 'usb' || key === 'wifi') && !confirm('关闭后，' + (key === 'usb' ? '头显重启后 USB 调试会被系统关掉' : '无线 ADB 会断开') + '，控制台可能就连不上头显了。确定关闭吗？')) {
    input.checked = true;
    return;
  }
  input.disabled = true;
  api('POST', '/api/helper', { key, enabled: input.checked })
    .then(() => toast('已' + (input.checked ? '开启' : '关闭')))
    .catch((e) => { input.checked = !input.checked; toast(e.message, true); })
    .finally(() => { input.disabled = false; refreshHelper(); });
});

document.addEventListener('click', (ev) => {
  const btn = ev.target.closest('button');
  if (!btn) return;
  if (btn.dataset.launch) act(btn, () => api('POST', '/api/apps/launch', { package: btn.dataset.launch }), '已在头显里打开');
  if (btn.dataset.volume) act(btn, () => api('POST', '/api/volume', { action: btn.dataset.volume }));
  if (btn.dataset.power) {
    const action = btn.dataset.power;
    if (action === 'reboot' && !confirm('确定重启头显吗？大约一分钟后会自动打开影院。')) return;
    const done = { wake: '已唤醒', sleep: '已休眠', reboot: '头显正在重启' }[action];
    act(btn, () => api('POST', '/api/power', { action }), done).then(refreshStatus);
  }
  if (btn.dataset.sunshine) act(btn, () => api('POST', '/api/sunshine', { action: btn.dataset.sunshine }), (r) => r.message).then(refreshStatus);
});

$('#keep-awake').addEventListener('click', (ev) => {
  const on = !ev.currentTarget.classList.contains('on');
  act(ev.currentTarget, () => api('POST', '/api/power', { action: on ? 'keep_awake_on' : 'keep_awake_off' }),
    on ? '摘下头显也会保持唤醒（重启后恢复正常）' : '已恢复：摘下头显会自动休眠').then(refreshStatus);
});
$('#mirror').addEventListener('click', (ev) => act(ev.currentTarget, () => api('POST', '/api/mirror'), (r) => r.message));
$('#reconnect').addEventListener('click', (ev) => {
  toast('正在查找头显的无线调试端口，最多需要一分钟…');
  act(ev.currentTarget, () => api('POST', '/api/connect'), (r) => '已连接：' + r.endpoint).then(refreshAll);
});
$('#url-form').addEventListener('submit', (ev) => {
  ev.preventDefault();
  act(ev.submitter, () => api('POST', '/api/open-url', { url: $('#url').value }), '已在头显浏览器里打开');
});
$('#apps-refresh').addEventListener('click', refreshApps);
$('#screen-now').addEventListener('click', refreshScreen);
$('#screen-eye').addEventListener('change', refreshScreen);

async function refreshAll() {
  await refreshStatus();
  if (!connected) return;
  refreshScreen();
  refreshApps();
  refreshMedia();
  refreshHelper();
}

loadSettings();
refreshAll();
setInterval(refreshStatus, 5000);
setInterval(() => { if ($('#screen-auto').checked) refreshScreen(); }, 2000);

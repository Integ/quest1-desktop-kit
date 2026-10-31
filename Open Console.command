#!/bin/zsh
# Start the Quest console (http://localhost:8765) and open it in the browser. Close this window to stop.
CONSOLE="${0:A:h}/console"
PORT=$(/usr/bin/python3 -c "import json,pathlib;p=pathlib.Path('$CONSOLE/../.local/console.json');print(json.loads(p.read_text()).get('listen_port',8765) if p.exists() else 8765)")
if /usr/bin/nc -z 127.0.0.1 "$PORT" >/dev/null 2>&1; then
  echo "Quest 控制台已经在运行。"
  open "http://localhost:$PORT"
  exit 0
fi
cd "$CONSOLE" && exec /usr/bin/python3 server.py --open

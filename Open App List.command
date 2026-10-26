#!/bin/zsh
set -e
TASK_DIR="${0:A:h}"
cd "$TASK_DIR"
exec python3 tools/quest.py open-launcher

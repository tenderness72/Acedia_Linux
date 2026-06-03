#!/usr/bin/env bash
# Acedia 起動スクリプト
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "仮想環境が見つかりません。setup.sh を先に実行してください。"
    exit 1
fi

source .venv/bin/activate
exec python main.py "$@"

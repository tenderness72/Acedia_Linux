#!/usr/bin/env bash
# Acedia セットアップスクリプト (Xubuntu / Ubuntu 22.04+)
set -e

echo "=== Acedia セットアップ ==="

# ── システム依存パッケージ ─────────────────────────────────────────────────
echo "[1/4] システムパッケージを確認中..."
sudo apt-get update -qq
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    libxcb-xinerama0 libxcb-cursor0 \
    fonts-noto-cjk \
    libgl1 libglib2.0-0

# ── Python 仮想環境 ────────────────────────────────────────────────────────
echo "[2/4] 仮想環境を作成中..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# ── Python 依存パッケージ ──────────────────────────────────────────────────
echo "[3/4] Pythonパッケージをインストール中..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# ── デスクトップエントリ ───────────────────────────────────────────────────
echo "[4/4] デスクトップショートカットを作成中..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/acedia.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Acedia
Comment=文献管理・メモアプリ
Exec=$SCRIPT_DIR/.venv/bin/python $SCRIPT_DIR/main.py
Icon=$SCRIPT_DIR/acedia/resources/icon.png
Terminal=false
Categories=Education;Science;Office;
StartupWMClass=Acedia
EOF

chmod +x "$DESKTOP_DIR/acedia.desktop"

echo ""
echo "=== セットアップ完了 ==="
echo "起動方法:"
echo "  1. アプリケーションメニューから「Acedia」を起動"
echo "  2. またはターミナルで:  cd $SCRIPT_DIR && .venv/bin/python main.py"

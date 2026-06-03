#!/usr/bin/env bash
# Acedia .deb パッケージビルドスクリプト
set -e

VERSION="0.1.0"
PKG_NAME="acedia"
ARCH="all"
BUILD_DIR="$(pwd)/deb_build"
PKG_DIR="$BUILD_DIR/${PKG_NAME}_${VERSION}_${ARCH}"

echo "=== Acedia .deb ビルド開始 ==="

# クリーンアップ
rm -rf "$BUILD_DIR"
mkdir -p "$PKG_DIR"

# ── ディレクトリ構造 ───────────────────────────────────────────────────────
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/acedia"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/pixmaps"

# ── アプリファイルをコピー ─────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/main.py" "$PKG_DIR/opt/acedia/"
cp "$SCRIPT_DIR/requirements.txt" "$PKG_DIR/opt/acedia/"
cp -r "$SCRIPT_DIR/acedia" "$PKG_DIR/opt/acedia/"

# ── ランチャースクリプト ───────────────────────────────────────────────────
cat > "$PKG_DIR/usr/bin/acedia" << 'EOF'
#!/usr/bin/env bash
exec /opt/acedia/.venv/bin/python /opt/acedia/main.py "$@"
EOF
chmod 755 "$PKG_DIR/usr/bin/acedia"

# ── デスクトップエントリ ───────────────────────────────────────────────────
cat > "$PKG_DIR/usr/share/applications/acedia.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Acedia
GenericName=文献管理アプリ
Comment=文献管理・メモアプリ
Exec=acedia
Icon=/opt/acedia/acedia/resources/icon.ico
Terminal=false
Categories=Education;Science;Office;
StartupWMClass=Acedia
EOF

# ── DEBIAN/control ─────────────────────────────────────────────────────────
cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: $PKG_NAME
Version: $VERSION
Section: science
Priority: optional
Architecture: $ARCH
Depends: python3 (>= 3.10), python3-pip, python3-venv, libxcb-xinerama0, libxcb-cursor0, fonts-noto-cjk, libgl1, libglib2.0-0
Maintainer: Acedia <noreply@example.com>
Description: 文献管理・メモアプリ (Acedia)
 PySide6ベースのLinux向け文献管理GUIアプリケーション。
 DOI/J-STAGEメタデータ取得、PDF管理、メモ、RISインポートに対応。
EOF

# ── DEBIAN/postinst (インストール後に venv を作成) ─────────────────────────
cat > "$PKG_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

INSTALL_DIR="/opt/acedia"

echo "Acedia: Python仮想環境をセットアップ中..."
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

# パーミッション修正
chmod -R a+rX "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR/.venv/bin/python"* 2>/dev/null || true

echo "Acedia: セットアップ完了"
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# ── DEBIAN/prerm (アンインストール前に venv を削除) ────────────────────────
cat > "$PKG_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e
rm -rf /opt/acedia/.venv
EOF
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# ── .deb ビルド ────────────────────────────────────────────────────────────
echo "パッケージをビルド中..."
dpkg-deb --build --root-owner-group "$PKG_DIR" "$BUILD_DIR"

DEB_FILE="$BUILD_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "=== ビルド完了 ==="
echo "生成ファイル: $DEB_FILE"
echo ""
echo "インストール方法:"
echo "  sudo dpkg -i $DEB_FILE"
echo "  sudo apt-get install -f   # 依存関係が足りない場合"
echo ""
echo "起動方法:"
echo "  acedia"
echo "  または アプリケーションメニュー → Acedia"

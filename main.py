#!/usr/bin/env python3
"""Acedia — 文献管理アプリ (Linux / Xubuntu)"""

import sys
import os
from pathlib import Path

# Silence Qt platform warnings on some distros
os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.xcb=false")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon, QPalette, QColor
from PySide6.QtCore import Qt

from acedia.models import init_db
from acedia.views import MainWindow


STYLESHEET = """
/* ── Atom Dark 256 ── */
QMainWindow, QWidget {
    background-color: #1d1f21;
    color: #c5c8c6;
}
QScrollArea, QScrollArea > QWidget > QWidget {
    background-color: #1d1f21;
}
QToolBar {
    background: #282a2e;
    border: none;
    border-bottom: 1px solid #373b41;
    padding: 4px 6px;
    spacing: 4px;
}
QToolBar QToolButton {
    color: #c5c8c6;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 13px;
}
QToolBar QToolButton:hover {
    background: #373b41;
    border-color: #4b5263;
}
QToolBar QToolButton:disabled {
    color: #4b5263;
}
QToolBar::separator {
    background: #373b41;
    width: 1px;
    margin: 4px 4px;
}
QTabWidget::pane {
    border: none;
    background: #1d1f21;
}
QTabBar::tab {
    background: #282a2e;
    color: #969896;
    padding: 6px 18px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
    font-size: 13px;
}
QTabBar::tab:selected {
    background: #1d1f21;
    color: #81a2be;
    font-weight: bold;
}
QTabBar::tab:hover {
    background: #373b41;
    color: #c5c8c6;
}
QListWidget {
    border: none;
    background: #1d1f21;
    outline: none;
}
QListWidget::item {
    border-bottom: 1px solid #282a2e;
    padding: 2px 0;
}
QListWidget::item:selected {
    background: #2a3347;
    color: #c5c8c6;
    border-left: 3px solid #81a2be;
}
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
    border: 1px solid #373b41;
    border-radius: 4px;
    padding: 4px 6px;
    background: #282a2e;
    color: #c5c8c6;
    font-size: 13px;
    selection-background-color: #373b41;
    selection-color: #c5c8c6;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus {
    border-color: #81a2be;
}
QPushButton {
    background: #81a2be;
    color: #1d1f21;
    border: none;
    border-radius: 4px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover {
    background: #8abeb7;
}
QPushButton:pressed {
    background: #6d8fa8;
}
QPushButton:disabled {
    background: #373b41;
    color: #4b5263;
    font-weight: normal;
}
QPushButton[flat="true"] {
    background: transparent;
    color: #c5c8c6;
    border: 1px solid #373b41;
    font-weight: normal;
}
QScrollBar:vertical {
    width: 8px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: #373b41;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #4b5263;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
}
QStatusBar {
    background: #282a2e;
    color: #969896;
    font-size: 11px;
    border-top: 1px solid #373b41;
}
QMessageBox {
    background: #282a2e;
}
QDialog {
    background: #1d1f21;
}
QCheckBox {
    color: #c5c8c6;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #4b5263;
    border-radius: 3px;
    background: #282a2e;
}
QCheckBox::indicator:checked {
    background: #81a2be;
    border-color: #81a2be;
}
QFormLayout QLabel {
    color: #969896;
}
QLabel {
    color: #c5c8c6;
}
QComboBox::drop-down {
    border: none;
    padding-right: 4px;
}
QComboBox QAbstractItemView {
    background: #282a2e;
    border: 1px solid #373b41;
    color: #c5c8c6;
    selection-background-color: #373b41;
    selection-color: #c5c8c6;
}
QSplitter::handle {
    background: #373b41;
}
QTextBrowser {
    background: #282a2e;
    color: #c5c8c6;
    border: 1px solid #373b41;
}
QDialogButtonBox QPushButton {
    min-width: 72px;
}
QScrollBar:horizontal {
    height: 8px;
    background: transparent;
}
QScrollBar::handle:horizontal {
    background: #373b41;
    border-radius: 4px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #4b5263;
}
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Acedia")
    app.setOrganizationName("Acedia")
    app.setApplicationVersion("0.1.0")

    # Font
    font = QFont()
    font.setFamily("Noto Sans CJK JP")
    font.setPointSize(10)
    app.setFont(font)

    app.setStyleSheet(STYLESHEET)

    icon_path = Path(__file__).parent / "acedia" / "resources" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Initialize DB
    init_db()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Acedia — 文献管理アプリ (Linux / Xubuntu)"""

import sys
import os

# Silence Qt platform warnings on some distros
os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.xcb=false")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtCore import Qt

from acedia.models import init_db
from acedia.views import MainWindow


STYLESHEET = """
QMainWindow {
    background-color: #f8fafc;
}
QToolBar {
    background: #1e40af;
    border: none;
    padding: 4px 6px;
    spacing: 4px;
}
QToolBar QToolButton {
    color: white;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 13px;
}
QToolBar QToolButton:hover {
    background: rgba(255,255,255,0.15);
    border-color: rgba(255,255,255,0.3);
}
QToolBar QToolButton:disabled {
    color: rgba(255,255,255,0.4);
}
QToolBar::separator {
    background: rgba(255,255,255,0.25);
    width: 1px;
    margin: 4px 4px;
}
QTabWidget::pane {
    border: none;
    background: white;
}
QTabBar::tab {
    background: #e2e8f0;
    color: #475569;
    padding: 6px 18px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
    font-size: 13px;
}
QTabBar::tab:selected {
    background: white;
    color: #1e40af;
    font-weight: bold;
}
QTabBar::tab:hover {
    background: #f1f5f9;
}
QListWidget {
    border: none;
    background: #f8fafc;
    outline: none;
}
QListWidget::item {
    border-bottom: 1px solid #f1f5f9;
    padding: 2px 0;
}
QListWidget::item:selected {
    background: #eff6ff;
    border-left: 3px solid #3b82f6;
}
QListWidget::item:alternate {
    background: #f0f4f8;
}
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 4px 6px;
    background: white;
    font-size: 13px;
    selection-background-color: #bfdbfe;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus {
    border-color: #3b82f6;
    outline: none;
}
QPushButton {
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 14px;
    font-size: 13px;
}
QPushButton:hover {
    background: #2563eb;
}
QPushButton:pressed {
    background: #1d4ed8;
}
QPushButton:disabled {
    background: #cbd5e1;
    color: #94a3b8;
}
QPushButton[flat="true"] {
    background: transparent;
    color: #374151;
    border: 1px solid #d1d5db;
}
QScrollBar:vertical {
    width: 8px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
}
QStatusBar {
    background: #f1f5f9;
    color: #64748b;
    font-size: 11px;
    border-top: 1px solid #e2e8f0;
}
QMessageBox {
    background: white;
}
QDialog {
    background: white;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #d1d5db;
    border-radius: 3px;
    background: white;
}
QCheckBox::indicator:checked {
    background: #3b82f6;
    border-color: #3b82f6;
}
QFormLayout QLabel {
    color: #374151;
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

    # Initialize DB
    init_db()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

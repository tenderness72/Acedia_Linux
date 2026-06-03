from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from ..models.paper import Paper
from ..services.ris_service import RisImportService


class RisImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RISファイルのインポート")
        self.setMinimumWidth(600)
        self.setMinimumHeight(480)
        self._parsed: list[Paper] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        # File picker
        file_row = QHBoxLayout()
        self._path_label = QLabel("ファイルが選択されていません")
        self._path_label.setStyleSheet("color: #6b7280;")
        self._browse_btn = QPushButton("RISファイルを選択…")
        self._browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self._path_label, 1)
        file_row.addWidget(self._browse_btn)
        layout.addLayout(file_row)

        # Count label
        self._count_label = QLabel("")
        self._count_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        layout.addWidget(self._count_label)

        # Selection controls
        sel_row = QHBoxLayout()
        self._sel_all_btn = QPushButton("すべて選択")
        self._sel_all_btn.setEnabled(False)
        self._sel_all_btn.clicked.connect(self._select_all)
        self._sel_none_btn = QPushButton("すべて解除")
        self._sel_none_btn.setEnabled(False)
        self._sel_none_btn.clicked.connect(self._select_none)
        sel_row.addWidget(self._sel_all_btn)
        sel_row.addWidget(self._sel_none_btn)
        sel_row.addStretch()
        layout.addLayout(sel_row)

        # Paper list
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._list.itemSelectionChanged.connect(self._on_sel_changed)
        layout.addWidget(self._list)

        self._import_count_label = QLabel("0 件選択中")
        self._import_count_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._import_count_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("インポート")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self._ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "RISファイルを選択", "", "RIS (*.ris *.RIS);;すべてのファイル (*)"
        )
        if not path:
            return
        self._path_label.setText(Path(path).name)
        svc = RisImportService()
        try:
            self._parsed = svc.parse_file(path)
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイルの読み込みに失敗しました:\n{e}")
            return

        self._list.clear()
        for paper in self._parsed:
            authors = paper.author_list
            author_str = authors[0] if authors else "著者不明"
            if len(authors) > 1:
                author_str += f" ら"
            year_str = f"（{paper.year}）" if paper.year else ""
            item = QListWidgetItem(f"{author_str}{year_str}　{paper.title or '（タイトル未設定）'}")
            item.setData(Qt.ItemDataRole.UserRole, paper)
            self._list.addItem(item)
            item.setSelected(True)

        self._count_label.setText(f"{len(self._parsed)} 件見つかりました")
        self._sel_all_btn.setEnabled(True)
        self._sel_none_btn.setEnabled(True)

    def _select_all(self):
        for i in range(self._list.count()):
            self._list.item(i).setSelected(True)

    def _select_none(self):
        self._list.clearSelection()

    def _on_sel_changed(self):
        count = len(self._list.selectedItems())
        self._import_count_label.setText(f"{count} 件選択中")
        self._ok_btn.setEnabled(count > 0)

    def get_selected_papers(self) -> list[Paper]:
        papers = []
        for item in self._list.selectedItems():
            p = item.data(Qt.ItemDataRole.UserRole)
            if p:
                papers.append(p)
        return papers

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
)

from ..models.note import PaperNote, NOTE_CATEGORIES


class NoteDialog(QDialog):
    def __init__(self, paper_id: int, note: Optional[PaperNote] = None, parent=None):
        super().__init__(parent)
        self._paper_id = paper_id
        self._note = note
        self.setWindowTitle("メモを編集" if note else "メモを追加")
        self.setMinimumWidth(520)
        self.setMinimumHeight(400)
        self._build()
        if note:
            self._populate(note)

    def _build(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("メモのタイトル（任意）")
        form.addRow("タイトル", self._title_edit)

        self._category_combo = QComboBox()
        for cat in NOTE_CATEGORIES:
            self._category_combo.addItem(cat, cat)
        form.addRow("カテゴリ", self._category_combo)

        self._page_edit = QLineEdit()
        self._page_edit.setPlaceholderText("例：12, 15–18")
        self._page_edit.setMaximumWidth(120)
        form.addRow("ページ", self._page_edit)

        layout.addLayout(form)

        content_label = QLabel("内容")
        layout.addWidget(content_label)

        self._content_edit = QPlainTextEdit()
        self._content_edit.setPlaceholderText(
            "自由記述（Markdownも使用できます）\n\n"
            "例：\n"
            "## 目的\n"
            "本研究は〇〇を検討することを目的とした。\n\n"
            "## 方法\n"
            "参加者は…"
        )
        self._content_edit.setMinimumHeight(200)
        layout.addWidget(self._content_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self, note: PaperNote):
        self._title_edit.setText(note.title or "")
        idx = self._category_combo.findData(note.category)
        if idx >= 0:
            self._category_combo.setCurrentIndex(idx)
        self._page_edit.setText(note.page_number or "")
        self._content_edit.setPlainText(note.content or "")

    def get_note(self) -> PaperNote:
        note = self._note if self._note else PaperNote()
        note.paper_id = self._paper_id
        note.title = self._title_edit.text().strip()
        note.category = self._category_combo.currentData()
        note.page_number = self._page_edit.text().strip() or None
        note.content = self._content_edit.toPlainText()
        return note

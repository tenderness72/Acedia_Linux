from __future__ import annotations

from typing import Optional

import markdown as _md

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..models.note import PaperNote, NOTE_CATEGORIES
from ..models.paper import Paper
from ..services.paper_service import PaperService
from .note_dialog import NoteDialog

_CATEGORY_COLORS = {
    "問題と目的": "#dbeafe",
    "方法": "#dcfce7",
    "結果": "#fef9c3",
    "考察": "#fce7f3",
    "その他": "#f3f4f6",
}
_CATEGORY_TEXT_COLORS = {
    "問題と目的": "#1d4ed8",
    "方法": "#15803d",
    "結果": "#a16207",
    "考察": "#be185d",
    "その他": "#374151",
}


class NotesView(QWidget):
    def __init__(self, service: PaperService, parent=None):
        super().__init__(parent)
        self._service = service
        self._paper: Optional[Paper] = None
        self._notes: list[PaperNote] = []
        self._selected_note: Optional[PaperNote] = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ─────────────────────────────────────────────────────────────
        tb = QHBoxLayout()
        tb.setContentsMargins(8, 6, 8, 6)

        paper_label = QLabel("（論文未選択）")
        paper_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        self._paper_label = paper_label

        self._btn_add = QPushButton("＋ メモ追加")
        self._btn_add.setFixedHeight(28)
        self._btn_add.setEnabled(False)
        self._btn_add.clicked.connect(self._on_add)

        self._btn_edit = QPushButton("編集")
        self._btn_edit.setFixedHeight(28)
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._on_edit)

        self._btn_delete = QPushButton("削除")
        self._btn_delete.setFixedHeight(28)
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._on_delete)

        tb.addWidget(self._paper_label, 1)
        tb.addWidget(self._btn_add)
        tb.addWidget(self._btn_edit)
        tb.addWidget(self._btn_delete)
        root.addLayout(tb)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #e5e7eb;")
        root.addWidget(sep)

        # ── Splitter: list | content ────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        # Note list
        self._note_list = QListWidget()
        self._note_list.setAlternatingRowColors(False)
        self._note_list.itemSelectionChanged.connect(self._on_selection_changed)
        self._note_list.setMaximumHeight(220)
        splitter.addWidget(self._note_list)

        # Content preview
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(8, 8, 8, 8)

        self._content_browser = QTextBrowser()
        self._content_browser.setOpenExternalLinks(True)
        self._content_browser.setStyleSheet(
            "font-size: 13px; background: #ffffff; border: 1px solid #e5e7eb;"
        )
        preview_layout.addWidget(self._content_browser)
        splitter.addWidget(preview_container)
        splitter.setSizes([200, 400])

        root.addWidget(splitter)

    # ── Public ────────────────────────────────────────────────────────────────

    def set_paper(self, paper: Optional[Paper]):
        self._paper = paper
        self._selected_note = None

        if paper:
            self._paper_label.setText(
                (paper.title[:50] + "…") if len(paper.title or "") > 50 else (paper.title or "")
            )
            self._btn_add.setEnabled(True)
            self._load_notes()
        else:
            self._paper_label.setText("（論文未選択）")
            self._btn_add.setEnabled(False)
            self._note_list.clear()
            self._content_browser.setHtml("")
            self._btn_edit.setEnabled(False)
            self._btn_delete.setEnabled(False)

    def refresh(self):
        if self._paper:
            self._load_notes()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _load_notes(self):
        if not self._paper:
            return
        self._notes = self._service.get_notes(self._paper.id)
        self._rebuild_list()

    def _rebuild_list(self):
        prev_id = self._selected_note.id if self._selected_note else None
        self._note_list.clear()

        for note in self._notes:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, note)

            bg = _CATEGORY_COLORS.get(note.category, "#f3f4f6")
            tc = _CATEGORY_TEXT_COLORS.get(note.category, "#374151")

            title = note.title or note.category
            page_str = f"  [p.{note.page_number}]" if note.page_number else ""
            preview = (note.content[:60] + "…") if len(note.content) > 60 else note.content
            preview = preview.replace("\n", " ")

            item.setText(f"[{note.category}]  {title}{page_str}\n{preview}")
            item.setBackground(Qt.GlobalColor.white)

            self._note_list.addItem(item)

        if prev_id is not None:
            for i in range(self._note_list.count()):
                it = self._note_list.item(i)
                n = it.data(Qt.ItemDataRole.UserRole)
                if n.id == prev_id:
                    self._note_list.setCurrentItem(it)
                    return
        if self._note_list.count() > 0:
            self._note_list.setCurrentRow(0)

    def _on_selection_changed(self):
        items = self._note_list.selectedItems()
        if items:
            self._selected_note = items[0].data(Qt.ItemDataRole.UserRole)
            self._show_note_content(self._selected_note)
            self._btn_edit.setEnabled(True)
            self._btn_delete.setEnabled(True)
        else:
            self._selected_note = None
            self._content_browser.setHtml("")
            self._btn_edit.setEnabled(False)
            self._btn_delete.setEnabled(False)

    def _show_note_content(self, note: PaperNote):
        header_bg = _CATEGORY_COLORS.get(note.category, "#f3f4f6")
        header_tc = _CATEGORY_TEXT_COLORS.get(note.category, "#374151")
        title = note.title or note.category
        page_str = f" — p.{note.page_number}" if note.page_number else ""
        date_str = note.updated_at.strftime("%Y-%m-%d %H:%M") if note.updated_at else ""

        body_html = _md.markdown(note.content or "", extensions=["nl2br", "fenced_code", "tables"])

        html = f"""
<html><body style="font-family: sans-serif; margin: 0;">
<div style="background:{header_bg}; color:{header_tc}; padding:8px 12px; border-bottom:1px solid #e5e7eb;">
  <b>{title}</b><span style="font-size:11px; margin-left:8px;">{note.category}{page_str}</span>
  <span style="float:right; color:#9ca3af; font-size:10px;">{date_str}</span>
</div>
<div style="padding:12px; line-height:1.6;">
{body_html}
</div>
</body></html>
"""
        self._content_browser.setHtml(html)

    def _on_add(self):
        if not self._paper:
            return
        dlg = NoteDialog(self._paper.id, parent=self)
        if dlg.exec() == NoteDialog.DialogCode.Accepted:
            note = dlg.get_note()
            self._service.create_note(note)
            self._load_notes()

    def _on_edit(self):
        if not self._selected_note or not self._paper:
            return
        dlg = NoteDialog(self._paper.id, note=self._selected_note, parent=self)
        if dlg.exec() == NoteDialog.DialogCode.Accepted:
            note = dlg.get_note()
            self._service.update_note(note)
            self._load_notes()

    def _on_delete(self):
        if not self._selected_note:
            return
        reply = QMessageBox.question(
            self, "削除確認",
            f"メモ「{self._selected_note.title or self._selected_note.category}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete_note(self._selected_note.id)
            self._selected_note = None
            self._load_notes()

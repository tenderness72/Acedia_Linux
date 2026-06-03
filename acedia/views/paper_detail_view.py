from __future__ import annotations

import subprocess
import sys
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QUrl

from ..models.paper import Paper
from ..services.paper_service import PaperService


class _SectionLabel(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #6b7280; "
            "border-bottom: 1px solid #e5e7eb; padding-bottom: 2px; margin-top: 8px;"
        )


class _FieldValue(QLabel):
    def __init__(self, text: str = ""):
        super().__init__(text)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setStyleSheet("font-size: 13px; color: #111827; padding: 2px 0;")


class _LinkLabel(QLabel):
    def __init__(self, url: str, text: str = ""):
        super().__init__(f'<a href="{url}">{text or url}</a>')
        self.setOpenExternalLinks(True)
        self.setWordWrap(True)
        self.setStyleSheet("font-size: 13px;")


class PaperDetailView(QWidget):
    favorite_toggled = Signal(int)   # paper_id
    edit_requested = Signal(object)  # Paper

    def __init__(self, service: PaperService, parent=None):
        super().__init__(parent)
        self._service = service
        self._paper: Optional[Paper] = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self._form = QVBoxLayout(container)
        self._form.setContentsMargins(16, 12, 16, 16)
        self._form.setSpacing(4)

        self._empty_label = QLabel("論文を選択してください")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #9ca3af; font-size: 14px; margin: 40px;")
        self._form.addWidget(self._empty_label)

        self._content = QWidget()
        self._content.setVisible(False)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(2)
        self._form.addWidget(self._content)
        self._form.addStretch()

        scroll.setWidget(container)
        root.addWidget(scroll)

    def show_paper(self, paper: Optional[Paper]):
        self._paper = paper
        self._empty_label.setVisible(paper is None)
        self._content.setVisible(paper is not None)

        if paper is None:
            return

        # clear old content
        while self._content_layout.count():
            child = self._content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        layout = self._content_layout

        # ── Header ──────────────────────────────────────────────────────────────
        header_row = QHBoxLayout()

        fav_btn = QPushButton("★" if paper.is_favorite else "☆")
        fav_btn.setFixedSize(32, 32)
        fav_btn.setStyleSheet(
            "color: #f59e0b; font-size: 18px; border: none; background: transparent;"
            if paper.is_favorite
            else "color: #d1d5db; font-size: 18px; border: none; background: transparent;"
        )
        fav_btn.clicked.connect(lambda: self.favorite_toggled.emit(paper.id))

        edit_btn = QPushButton("編集")
        edit_btn.setFixedHeight(28)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(paper))

        header_row.addWidget(fav_btn)
        header_row.addStretch()
        header_row.addWidget(edit_btn)
        layout.addLayout(header_row)

        # ── Title ────────────────────────────────────────────────────────────────
        title_label = QLabel(paper.title or "（タイトル未設定）")
        title_label.setWordWrap(True)
        title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827; margin: 4px 0 8px;")
        layout.addWidget(title_label)

        def add_field(section: str | None, label: str, value: str):
            if section:
                layout.addWidget(_SectionLabel(section))
            if not value:
                return
            row = QHBoxLayout()
            lbl = QLabel(f"{label}：")
            lbl.setStyleSheet("color: #6b7280; font-size: 12px; min-width: 80px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            val = _FieldValue(value)
            row.addWidget(lbl)
            row.addWidget(val, 1)
            layout.addLayout(row)

        # ── Bibliographic info ────────────────────────────────────────────────
        layout.addWidget(_SectionLabel("書誌情報"))

        authors_str = "，".join(paper.author_list) if paper.author_list else "—"
        self._add_kv(layout, "著者", authors_str)

        if paper.journal:
            self._add_kv(layout, "雑誌", paper.journal)

        year_vol = ""
        if paper.year:
            year_vol += str(paper.year)
        if paper.volume:
            year_vol += f"，{paper.volume}巻"
        if paper.issue:
            year_vol += f"（{paper.issue}号）"
        if paper.pages:
            year_vol += f"，{paper.normalized_pages}頁"
        if year_vol:
            self._add_kv(layout, "年・巻・頁", year_vol)

        if paper.doi:
            doi_row = QHBoxLayout()
            doi_lbl = QLabel("DOI：")
            doi_lbl.setStyleSheet("color: #6b7280; font-size: 12px; min-width: 80px;")
            doi_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            doi_link = _LinkLabel(paper.doi_url, paper.doi)
            doi_row.addWidget(doi_lbl)
            doi_row.addWidget(doi_link, 1)
            layout.addLayout(doi_row)

        # ── Classification ────────────────────────────────────────────────────
        has_class = any([paper.paper_type, paper.clinical_area, paper.approach, paper.tag_list])
        if has_class:
            layout.addWidget(_SectionLabel("分類・タグ"))
            if paper.paper_type:
                self._add_kv(layout, "論文種別", paper.paper_type)
            if paper.clinical_area:
                self._add_kv(layout, "臨床領域", paper.clinical_area)
            if paper.approach:
                self._add_kv(layout, "研究アプローチ", paper.approach)
            if paper.tag_list:
                tag_str = "　".join(paper.tag_list)
                self._add_kv(layout, "タグ", tag_str)

        # ── Abstract ─────────────────────────────────────────────────────────
        if paper.abstract:
            layout.addWidget(_SectionLabel("抄録"))
            abstract_box = QTextEdit()
            abstract_box.setReadOnly(True)
            abstract_box.setPlainText(paper.abstract)
            abstract_box.setMaximumHeight(160)
            abstract_box.setStyleSheet("font-size: 12px; background: #f9fafb; border: 1px solid #e5e7eb;")
            layout.addWidget(abstract_box)

        # ── Keywords ─────────────────────────────────────────────────────────
        if paper.keywords:
            self._add_kv(layout, "キーワード", paper.keywords)

        # ── File ─────────────────────────────────────────────────────────────
        if paper.file_path:
            layout.addWidget(_SectionLabel("ファイル"))
            file_row = QHBoxLayout()
            file_label = QLabel(paper.file_path)
            file_label.setStyleSheet("color: #6b7280; font-size: 11px;")
            file_label.setWordWrap(True)
            open_btn = QPushButton("開く")
            open_btn.setFixedHeight(24)
            open_btn.setFixedWidth(50)
            open_btn.clicked.connect(lambda: self._open_file(paper.file_path))
            file_row.addWidget(file_label, 1)
            file_row.addWidget(open_btn)
            layout.addLayout(file_row)

        # ── Additional notes ──────────────────────────────────────────────────
        if paper.additional_notes:
            layout.addWidget(_SectionLabel("メモ（補足）"))
            notes_box = QTextEdit()
            notes_box.setReadOnly(True)
            notes_box.setPlainText(paper.additional_notes)
            notes_box.setMaximumHeight(120)
            notes_box.setStyleSheet("font-size: 12px; background: #fffbeb; border: 1px solid #fde68a;")
            layout.addWidget(notes_box)

        layout.addStretch()

    def _add_kv(self, layout: QVBoxLayout, label: str, value: str):
        row = QHBoxLayout()
        lbl = QLabel(f"{label}：")
        lbl.setStyleSheet("color: #6b7280; font-size: 12px; min-width: 80px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        val = _FieldValue(value)
        row.addWidget(lbl)
        row.addWidget(val, 1)
        layout.addLayout(row)

    def _open_file(self, path: str):
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

from __future__ import annotations

import subprocess
import sys
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
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
            "border-bottom: 1px solid #e5e7eb; padding-bottom: 2px;"
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
        self._content_layout.setSpacing(6)
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

        # clear old content (widgets AND nested layouts)
        self._clear_layout(self._content_layout)

        layout = self._content_layout

        # ── Header ──────────────────────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        btn_style_fav = (
            "QPushButton { background: #fef3c7; color: #d97706; border: 1px solid #fcd34d;"
            " border-radius: 4px; padding: 4px 10px; font-size: 13px; }"
            "QPushButton:hover { background: #fde68a; }"
        )
        btn_style_fav_off = (
            "QPushButton { background: #f1f5f9; color: #9ca3af; border: 1px solid #e2e8f0;"
            " border-radius: 4px; padding: 4px 10px; font-size: 13px; }"
            "QPushButton:hover { background: #e2e8f0; }"
        )
        fav_btn = QPushButton("★ お気に入り" if paper.is_favorite else "☆ お気に入り")
        fav_btn.setFixedHeight(28)
        fav_btn.setStyleSheet(btn_style_fav if paper.is_favorite else btn_style_fav_off)
        fav_btn.clicked.connect(lambda: self.favorite_toggled.emit(paper.id))

        edit_btn = QPushButton("編集")
        edit_btn.setFixedHeight(28)
        edit_btn.setStyleSheet(
            "QPushButton { background: white; color: #1e40af; border: 1px solid #93c5fd;"
            " border-radius: 4px; padding: 4px 14px; font-size: 13px; }"
            "QPushButton:hover { background: #eff6ff; }"
        )
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(paper))

        header_row.addWidget(fav_btn)
        header_row.addWidget(edit_btn)
        if paper.file_path:
            open_btn_top = QPushButton("PDF を開く")
            open_btn_top.setFixedHeight(28)
            open_btn_top.setStyleSheet(
                "QPushButton { background: #f1f5f9; color: #374151; border: 1px solid #d1d5db;"
                " border-radius: 4px; padding: 4px 10px; font-size: 13px; }"
                "QPushButton:hover { background: #e2e8f0; }"
            )
            open_btn_top.clicked.connect(lambda: self._open_file(paper.file_path))
            header_row.addWidget(open_btn_top)
        header_row.addStretch()
        layout.addLayout(header_row)

        # ── Title ────────────────────────────────────────────────────────────────
        title_label = QLabel(paper.title or "（タイトル未設定）")
        title_label.setWordWrap(True)
        title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827; margin: 4px 0 8px;")
        layout.addWidget(title_label)

        # ── Bibliographic info ────────────────────────────────────────────────
        layout.addSpacing(4)
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
            layout.addSpacing(4)
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
            layout.addSpacing(4)
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
            layout.addSpacing(4)
            layout.addWidget(_SectionLabel("ファイル"))
            file_label = QLabel(paper.file_path)
            file_label.setStyleSheet("color: #6b7280; font-size: 11px;")
            file_label.setWordWrap(True)
            layout.addWidget(file_label)

        # ── Additional notes ──────────────────────────────────────────────────
        if paper.additional_notes:
            layout.addSpacing(4)
            layout.addWidget(_SectionLabel("メモ（補足）"))
            notes_box = QTextEdit()
            notes_box.setReadOnly(True)
            notes_box.setPlainText(paper.additional_notes)
            notes_box.setMaximumHeight(120)
            notes_box.setStyleSheet("font-size: 12px; background: #fffbeb; border: 1px solid #fde68a;")
            layout.addWidget(notes_box)

        layout.addStretch()

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

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
        if not Path(path).exists():
            QMessageBox.warning(self, "ファイルが見つかりません", f"次のファイルが存在しません：\n{path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

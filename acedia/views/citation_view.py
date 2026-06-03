from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models.paper import Paper
from ..services.paper_service import PaperService


class CitationView(QWidget):
    def __init__(self, service: PaperService, parent=None):
        super().__init__(parent)
        self._service = service
        self._paper: Optional[Paper] = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        self._empty_label = QLabel("論文を選択すると引用形式（J-APA）が表示されます")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #9ca3af; font-size: 13px; margin: 40px;")
        root.addWidget(self._empty_label)

        self._content = QWidget()
        self._content.setVisible(False)
        c_layout = QVBoxLayout(self._content)
        c_layout.setContentsMargins(0, 0, 0, 0)

        # ── In-text citation ──────────────────────────────────────────────────
        c_layout.addWidget(self._section_header("本文内引用"))
        self._intext_box = self._create_citation_box()
        btn_copy_intext = QPushButton("コピー")
        btn_copy_intext.setFixedWidth(60)
        btn_copy_intext.clicked.connect(lambda: self._copy(self._intext_box))
        row1 = QHBoxLayout()
        row1.addWidget(self._intext_box, 1)
        row1.addWidget(btn_copy_intext)
        c_layout.addLayout(row1)

        # ── Full citation ─────────────────────────────────────────────────────
        c_layout.addWidget(self._section_header("文献リスト（J-APA）"))
        self._full_box = self._create_citation_box(height=100)
        btn_copy_full = QPushButton("コピー")
        btn_copy_full.setFixedWidth(60)
        btn_copy_full.clicked.connect(lambda: self._copy(self._full_box))
        row2 = QHBoxLayout()
        row2.addWidget(self._full_box, 1)
        row2.addWidget(btn_copy_full)
        c_layout.addLayout(row2)

        c_layout.addStretch()
        root.addWidget(self._content)
        root.addStretch()

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #6b7280; "
            "border-bottom: 1px solid #e5e7eb; padding-bottom: 2px;"
        )
        return lbl

    def _create_citation_box(self, height: int = 48) -> QTextEdit:
        box = QTextEdit()
        box.setReadOnly(True)
        box.setFixedHeight(height)
        box.setStyleSheet(
            "font-family: 'Noto Serif CJK JP', 'IPAMincho', serif; "
            "font-size: 13px; background: #f9fafb; border: 1px solid #e5e7eb; padding: 4px;"
        )
        return box

    def show_paper(self, paper: Optional[Paper]):
        self._paper = paper
        self._empty_label.setVisible(paper is None)
        self._content.setVisible(paper is not None)
        if paper is None:
            return
        self._intext_box.setPlainText(paper.in_text_citation())
        self._full_box.setPlainText(paper.full_citation())

    def _copy(self, box: QTextEdit):
        QApplication.clipboard().setText(box.toPlainText())

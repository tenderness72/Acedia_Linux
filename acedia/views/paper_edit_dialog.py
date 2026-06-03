from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ..models.paper import Paper
from ..services.pdf_service import PdfMetadataService
from ..workers.metadata_worker import MetadataWorker


class PaperEditDialog(QDialog):
    def __init__(self, paper: Optional[Paper] = None, parent=None):
        super().__init__(parent)
        self._paper = paper or Paper()
        self._is_new = paper is None
        self._worker: Optional[MetadataWorker] = None
        self.setWindowTitle("論文を追加" if self._is_new else "論文を編集")
        self.setMinimumWidth(680)
        self.setMinimumHeight(640)
        self.setAcceptDrops(True)
        self._build()
        if not self._is_new:
            self._populate(self._paper)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 8)
        layout.setSpacing(8)

        # ── DOI quick-fill ────────────────────────────────────────────────────
        doi_row = QHBoxLayout()
        doi_row.setSpacing(6)
        doi_lbl = QLabel("DOI / URL")
        doi_lbl.setFixedWidth(90)
        self._doi_edit = QLineEdit()
        self._doi_edit.setPlaceholderText("10.xxxx/xxxxxx  または  https://doi.org/…")
        self._fetch_btn = QPushButton("メタデータ取得")
        self._fetch_btn.setFixedWidth(120)
        self._fetch_btn.clicked.connect(self._on_fetch)
        doi_row.addWidget(doi_lbl)
        doi_row.addWidget(self._doi_edit, 1)
        doi_row.addWidget(self._fetch_btn)
        layout.addLayout(doi_row)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        layout.addWidget(self._status_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #e5e7eb;")
        layout.addWidget(sep)

        # ── Main form ─────────────────────────────────────────────────────────
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("論文タイトル")
        form.addRow("タイトル *", self._title_edit)

        self._authors_edit = QLineEdit()
        self._authors_edit.setPlaceholderText("著者1，著者2，… （読点・カンマ区切り）")
        form.addRow("著者", self._authors_edit)

        self._authors_kana_edit = QLineEdit()
        self._authors_kana_edit.setPlaceholderText("著者ヨミガナ（並び替え用、省略可）")
        form.addRow("著者かな", self._authors_kana_edit)

        # Year / Volume / Issue / Pages in one row
        bib_row = QHBoxLayout()
        self._year_spin = QSpinBox()
        self._year_spin.setRange(0, 2099)
        self._year_spin.setValue(0)
        self._year_spin.setSpecialValueText("—")
        self._year_spin.setFixedWidth(80)
        self._volume_edit = QLineEdit()
        self._volume_edit.setPlaceholderText("巻")
        self._volume_edit.setFixedWidth(60)
        self._issue_edit = QLineEdit()
        self._issue_edit.setPlaceholderText("号")
        self._issue_edit.setFixedWidth(60)
        self._pages_edit = QLineEdit()
        self._pages_edit.setPlaceholderText("頁（例：12–34）")
        self._pages_edit.setFixedWidth(100)
        bib_row.addWidget(QLabel("年："))
        bib_row.addWidget(self._year_spin)
        bib_row.addWidget(QLabel("  巻："))
        bib_row.addWidget(self._volume_edit)
        bib_row.addWidget(QLabel("  号："))
        bib_row.addWidget(self._issue_edit)
        bib_row.addWidget(QLabel("  頁："))
        bib_row.addWidget(self._pages_edit)
        bib_row.addStretch()
        form.addRow("書誌", bib_row)

        self._journal_edit = QLineEdit()
        self._journal_edit.setPlaceholderText("雑誌名")
        form.addRow("雑誌", self._journal_edit)

        self._keywords_edit = QLineEdit()
        self._keywords_edit.setPlaceholderText("キーワード1，キーワード2，…")
        form.addRow("キーワード", self._keywords_edit)

        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("タグ1，タグ2，… （自由分類）")
        form.addRow("タグ", self._tags_edit)

        self._clinical_edit = QLineEdit()
        self._clinical_edit.setPlaceholderText("例：摂食障害，うつ病")
        form.addRow("臨床領域", self._clinical_edit)

        self._approach_edit = QLineEdit()
        self._approach_edit.setPlaceholderText("例：RCT，質的研究，システマティックレビュー")
        form.addRow("研究アプローチ", self._approach_edit)

        self._paper_type_edit = QLineEdit()
        self._paper_type_edit.setPlaceholderText("例：学術論文，書籍，抄録")
        form.addRow("論文種別", self._paper_type_edit)

        self._fav_check = QCheckBox("お気に入り")
        form.addRow("", self._fav_check)

        layout.addLayout(form)

        # ── Abstract ─────────────────────────────────────────────────────────
        layout.addWidget(QLabel("抄録"))
        self._abstract_edit = QPlainTextEdit()
        self._abstract_edit.setPlaceholderText("抄録を入力…")
        self._abstract_edit.setFixedHeight(120)
        layout.addWidget(self._abstract_edit)

        # ── Additional notes ──────────────────────────────────────────────────
        layout.addWidget(QLabel("補足メモ"))
        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setPlaceholderText("補足・個人メモ…")
        self._notes_edit.setFixedHeight(80)
        layout.addWidget(self._notes_edit)

        # ── File path ─────────────────────────────────────────────────────────
        layout.addWidget(QLabel("PDFファイル（ドラッグ＆ドロップ可）"))
        file_row = QHBoxLayout()
        self._file_edit = QLineEdit()
        self._file_edit.setPlaceholderText("ファイルパス")
        self._file_edit.setReadOnly(True)
        self._file_edit.setStyleSheet("background: #f9fafb;")
        browse_btn = QPushButton("参照…")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(self._file_edit, 1)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        self._drop_label = QLabel("または PDF をここにドロップ")
        self._drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_label.setStyleSheet(
            "border: 2px dashed #d1d5db; color: #9ca3af; padding: 12px; border-radius: 4px;"
        )
        layout.addWidget(self._drop_label)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll, 1)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        outer.addWidget(btn_box)

    # ── Populate ──────────────────────────────────────────────────────────────

    def _populate(self, p: Paper):
        self._doi_edit.setText(p.doi or "")
        self._title_edit.setText(p.title or "")
        self._authors_edit.setText(p.authors or "")
        self._authors_kana_edit.setText(p.authors_kana or "")
        self._year_spin.setValue(p.year or 0)
        self._volume_edit.setText(p.volume or "")
        self._issue_edit.setText(p.issue or "")
        self._pages_edit.setText(p.pages or "")
        self._journal_edit.setText(p.journal or "")
        self._keywords_edit.setText(p.keywords or "")
        self._tags_edit.setText(p.tags or "")
        self._clinical_edit.setText(p.clinical_area or "")
        self._approach_edit.setText(p.approach or "")
        self._paper_type_edit.setText(p.paper_type or "")
        self._fav_check.setChecked(p.is_favorite)
        self._abstract_edit.setPlainText(p.abstract or "")
        self._notes_edit.setPlainText(p.additional_notes or "")
        self._file_edit.setText(p.file_path or "")

    def _apply_fetched(self, fetched: Paper):
        if fetched.title:
            self._title_edit.setText(fetched.title)
        if fetched.authors:
            self._authors_edit.setText(fetched.authors)
        if fetched.year:
            self._year_spin.setValue(fetched.year)
        if fetched.journal:
            self._journal_edit.setText(fetched.journal)
        if fetched.volume:
            self._volume_edit.setText(fetched.volume)
        if fetched.issue:
            self._issue_edit.setText(fetched.issue)
        if fetched.pages:
            self._pages_edit.setText(fetched.pages)
        if fetched.abstract:
            self._abstract_edit.setPlainText(fetched.abstract)
        if fetched.doi and not self._doi_edit.text():
            self._doi_edit.setText(fetched.doi)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_fetch(self):
        doi = self._doi_edit.text().strip()
        title = self._title_edit.text().strip()
        if not doi and not title:
            QMessageBox.information(self, "メタデータ取得", "DOIまたはタイトルを入力してください。")
            return

        self._fetch_btn.setEnabled(False)
        self._status_label.setText("メタデータを取得中…")

        self._worker = MetadataWorker(doi=doi, title=title, parent=self)
        self._worker.finished.connect(self._on_fetch_done)
        self._worker.start()

    def _on_fetch_done(self, result: Optional[Paper]):
        self._fetch_btn.setEnabled(True)
        if result:
            self._apply_fetched(result)
            self._status_label.setText("メタデータを取得しました。")
        else:
            self._status_label.setText("メタデータが見つかりませんでした。")
        self._worker = None

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.finished.disconnect()
            self._worker.quit()
            self._worker.wait(2000)
        super().closeEvent(event)

    def _on_save(self):
        if not self._title_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "タイトルは必須です。")
            return
        self.accept()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "PDFファイルを選択", "", "PDF (*.pdf);;すべてのファイル (*)")
        if path:
            self._set_pdf(path)

    def _set_pdf(self, path: str):
        self._file_edit.setText(path)
        if not self._title_edit.text().strip():
            svc = PdfMetadataService()
            meta = svc.extract(path)
            if meta:
                self._apply_fetched(meta)
                self._status_label.setText("PDFからメタデータを読み込みました。")

    # ── Result ────────────────────────────────────────────────────────────────

    def get_paper(self) -> Paper:
        p = self._paper
        p.doi = self._doi_edit.text().strip()
        p.title = self._title_edit.text().strip()
        p.authors = self._authors_edit.text().strip()
        p.authors_kana = self._authors_kana_edit.text().strip()
        yr = self._year_spin.value()
        p.year = yr if yr > 0 else None
        p.volume = self._volume_edit.text().strip()
        p.issue = self._issue_edit.text().strip()
        p.pages = self._pages_edit.text().strip()
        p.journal = self._journal_edit.text().strip()
        p.keywords = self._keywords_edit.text().strip()
        p.tags = self._tags_edit.text().strip()
        p.clinical_area = self._clinical_edit.text().strip()
        p.approach = self._approach_edit.text().strip()
        p.paper_type = self._paper_type_edit.text().strip()
        p.is_favorite = self._fav_check.isChecked()
        p.abstract = self._abstract_edit.toPlainText().strip()
        p.additional_notes = self._notes_edit.toPlainText().strip()
        p.file_path = self._file_edit.text().strip()
        return p

    # ── Drag-and-drop ──────────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            if any(u.toLocalFile().lower().endswith(".pdf") for u in event.mimeData().urls()):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self._set_pdf(path)
                break
        event.acceptProposedAction()

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QWidget,
)

from ..models.paper import Paper
from ..services.paper_service import PaperService
from .citation_view import CitationView
from .notes_view import NotesView
from .paper_detail_view import PaperDetailView
from .paper_edit_dialog import PaperEditDialog
from .paper_list_view import PaperListView
from .ris_import_dialog import RisImportDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._service = PaperService()
        self._current_paper: Optional[Paper] = None
        self.setWindowTitle("Acedia — 文献管理")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self._build()
        self._setup_shortcuts()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Splitter ──────────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: paper list
        self._list_view = PaperListView(self._service)
        self._list_view.setMinimumWidth(280)
        self._list_view.setMaximumWidth(440)
        self._list_view.paper_selected.connect(self._on_paper_selected)
        self._list_view.add_requested.connect(self._on_add)
        self._list_view.edit_requested.connect(self._on_edit)
        self._list_view.delete_requested.connect(self._on_delete)
        self._list_view.import_ris_requested.connect(self._on_import_ris)
        self._list_view.pdf_dropped.connect(self._on_pdf_dropped_on_list)
        splitter.addWidget(self._list_view)

        # Right: tab widget
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        self._detail_view = PaperDetailView(self._service)
        self._detail_view.favorite_toggled.connect(self._on_favorite_toggled)
        self._detail_view.edit_requested.connect(self._on_edit)
        self._tabs.addTab(self._detail_view, "詳細")

        self._notes_view = NotesView(self._service)
        self._tabs.addTab(self._notes_view, "メモ")

        self._citation_view = CitationView(self._service)
        self._tabs.addTab(self._citation_view, "引用（J-APA）")

        splitter.addWidget(self._tabs)
        splitter.setSizes([320, 960])

        self.setCentralWidget(splitter)

        # ── Toolbar ───────────────────────────────────────────────────────────
        tb = QToolBar("メイン")
        tb.setMovable(False)
        tb.setFloatable(False)

        self._act_add = QAction("＋ 論文を追加", self)
        self._act_add.triggered.connect(self._on_add)
        tb.addAction(self._act_add)

        self._act_ris = QAction("RIS インポート", self)
        self._act_ris.triggered.connect(self._on_import_ris)
        tb.addAction(self._act_ris)

        self.addToolBar(tb)

        # ── Status bar ────────────────────────────────────────────────────────
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._update_status()

    def _setup_shortcuts(self):
        QAction(self).setShortcut(QKeySequence.StandardKey.New)

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_paper_selected(self, paper: Optional[Paper]):
        self._current_paper = paper
        self._detail_view.show_paper(paper)
        self._notes_view.set_paper(paper)
        self._citation_view.show_paper(paper)

        pass

    def _on_add(self):
        dlg = PaperEditDialog(parent=self)
        if dlg.exec() == PaperEditDialog.DialogCode.Accepted:
            paper = dlg.get_paper()
            saved = self._service.create(paper)
            self._list_view.refresh()
            self._list_view.select_paper(saved.id)
            self._update_status()

    def _on_edit(self, paper: Optional[Paper]):
        if not paper:
            return
        # Re-fetch with fresh data
        fresh = self._service.get_by_id(paper.id)
        if not fresh:
            return
        dlg = PaperEditDialog(paper=fresh, parent=self)
        if dlg.exec() == PaperEditDialog.DialogCode.Accepted:
            updated = dlg.get_paper()
            saved = self._service.update(updated)
            self._list_view.refresh()
            self._list_view.select_paper(saved.id)
            if self._current_paper and self._current_paper.id == saved.id:
                self._detail_view.show_paper(saved)
                self._citation_view.show_paper(saved)
            self._update_status()

    def _on_delete(self, paper: Optional[Paper]):
        if not paper:
            return
        reply = QMessageBox.question(
            self,
            "削除確認",
            f"論文「{paper.title or '（無題）'}」を削除しますか？\nメモも同時に削除されます。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete(paper.id)
            self._current_paper = None
            self._detail_view.show_paper(None)
            self._notes_view.set_paper(None)
            self._citation_view.show_paper(None)
            self._list_view.refresh()
            self._update_status()

    def _on_favorite_toggled(self, paper_id: int):
        self._service.toggle_favorite(paper_id)
        fresh = self._service.get_by_id(paper_id)
        if fresh:
            self._detail_view.show_paper(fresh)
        self._list_view.refresh()

    def _on_import_ris(self):
        dlg = RisImportDialog(parent=self)
        if dlg.exec() == RisImportDialog.DialogCode.Accepted:
            papers = dlg.get_selected_papers()
            if papers:
                saved = self._service.bulk_create(papers)
                self._list_view.refresh()
                if saved:
                    self._list_view.select_paper(saved[0].id)
                self._update_status()
                QMessageBox.information(self, "インポート完了", f"{len(saved)} 件の論文をインポートしました。")

    def _on_pdf_dropped_on_list(self, path: str):
        dlg = PaperEditDialog(parent=self)
        from ..services.pdf_service import PdfMetadataService
        meta = PdfMetadataService().extract(path)
        if meta:
            dlg._populate(meta)
            dlg._file_edit.setText(path)
            dlg._status_label.setText("PDFからメタデータを読み込みました。")
        if dlg.exec() == PaperEditDialog.DialogCode.Accepted:
            paper = dlg.get_paper()
            saved = self._service.create(paper)
            self._list_view.refresh()
            self._list_view.select_paper(saved.id)
            self._update_status()

    def _update_status(self):
        count = self._service.count()
        self._status.showMessage(f"論文 {count} 件  |  Acedia")

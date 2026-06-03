from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QMouseEvent, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..models.paper import Paper
from ..services.paper_service import PaperService


class PaperListItemWidget(QWidget):
    """Rich list item showing author・year, title, journal."""

    def __init__(self, paper: Paper, parent=None):
        super().__init__(parent)
        self.paper = paper
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        authors = self.paper.author_list
        author_str = authors[0] if authors else ""
        if len(authors) == 2:
            author_str = f"{authors[0]}・{authors[1]}"
        elif len(authors) > 2:
            author_str = f"{authors[0]} ら"
        year_str = f"（{self.paper.year}）" if self.paper.year else ""

        if self.paper.is_favorite:
            fav_mark = ' <span style="color: #f59e0b;">★</span>'
        else:
            fav_mark = ""

        meta_label = QLabel(f"{author_str}{year_str}{fav_mark}")
        meta_label.setTextFormat(Qt.TextFormat.RichText)
        meta_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(meta_label)

        title_label = QLabel(self.paper.title or "（タイトル未設定）")
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title_label)

        if self.paper.journal:
            journal_label = QLabel(self.paper.journal)
            journal_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
            journal_label.setWordWrap(True)
            layout.addWidget(journal_label)

        if self.paper.tag_list:
            tag_row = QHBoxLayout()
            tag_row.setSpacing(4)
            for tag in self.paper.tag_list[:4]:
                badge = QLabel(tag)
                badge.setStyleSheet(
                    "background: #e0e7ff; color: #3730a3; border-radius: 3px; "
                    "padding: 1px 5px; font-size: 10px;"
                )
                tag_row.addWidget(badge)
            tag_row.addStretch()
            layout.addLayout(tag_row)

        # 子ウィジェットのクリックをすべて親に透過させる
        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def mousePressEvent(self, event: QMouseEvent):
        # 自身に対応する QListWidgetItem を探して選択する
        parent = self.parent()
        while parent and not isinstance(parent, QListWidget):
            parent = parent.parent()
        if isinstance(parent, QListWidget):
            for i in range(parent.count()):
                item = parent.item(i)
                if parent.itemWidget(item) is self:
                    parent.setCurrentItem(item)
                    break
        super().mousePressEvent(event)


class PaperListView(QWidget):
    paper_selected = Signal(object)   # Paper | None
    add_requested = Signal()
    edit_requested = Signal(object)   # Paper
    delete_requested = Signal(object)  # Paper
    import_ris_requested = Signal()
    pdf_dropped = Signal(str)          # file path

    def __init__(self, service: PaperService, parent=None):
        super().__init__(parent)
        self._service = service
        self._papers: list[Paper] = []
        self._selected: Optional[Paper] = None
        self.setAcceptDrops(True)
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ────────────────────────────────────────────────────────────
        tb = QHBoxLayout()
        tb.setContentsMargins(8, 6, 8, 6)
        tb.setSpacing(4)

        self._btn_add = QPushButton("＋ 追加")
        self._btn_add.setFixedHeight(28)
        self._btn_add.clicked.connect(self.add_requested.emit)

        self._btn_edit = QPushButton("編集")
        self._btn_edit.setFixedHeight(28)
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._on_edit)

        self._btn_delete = QPushButton("削除")
        self._btn_delete.setFixedHeight(28)
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._on_delete)

        self._btn_ris = QPushButton("RIS")
        self._btn_ris.setFixedHeight(28)
        self._btn_ris.setToolTip("RISファイルをインポート")
        self._btn_ris.clicked.connect(self.import_ris_requested.emit)

        tb.addWidget(self._btn_add)
        tb.addWidget(self._btn_edit)
        tb.addWidget(self._btn_delete)
        tb.addStretch()
        tb.addWidget(self._btn_ris)
        root.addLayout(tb)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #ddd;")
        root.addWidget(sep)

        # ── Search ─────────────────────────────────────────────────────────────
        search_row = QHBoxLayout()
        search_row.setContentsMargins(8, 6, 8, 4)
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("タイトル・著者・キーワードで検索…")
        self._search_box.textChanged.connect(self._apply_filter)
        search_row.addWidget(self._search_box)
        root.addLayout(search_row)

        # ── Filters ────────────────────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(8, 0, 8, 4)
        filter_row.setSpacing(4)

        self._year_combo = QComboBox()
        self._year_combo.addItem("年度：すべて", None)
        self._year_combo.setFixedWidth(110)
        self._year_combo.currentIndexChanged.connect(self._apply_filter)

        self._journal_combo = QComboBox()
        self._journal_combo.addItem("雑誌：すべて", None)
        self._journal_combo.setFixedWidth(130)
        self._journal_combo.currentIndexChanged.connect(self._apply_filter)

        self._tag_combo = QComboBox()
        self._tag_combo.addItem("タグ：すべて", None)
        self._tag_combo.setFixedWidth(110)
        self._tag_combo.currentIndexChanged.connect(self._apply_filter)

        filter_row.addWidget(self._year_combo)
        filter_row.addWidget(self._journal_combo)
        filter_row.addWidget(self._tag_combo)
        filter_row.addStretch()
        root.addLayout(filter_row)

        fav_row = QHBoxLayout()
        fav_row.setContentsMargins(8, 0, 8, 4)
        self._fav_check = QCheckBox("★ お気に入りのみ")
        self._fav_check.toggled.connect(self._apply_filter)
        fav_row.addWidget(self._fav_check)
        fav_row.addStretch()
        self._count_label = QLabel("")
        self._count_label.setStyleSheet("color: #888; font-size: 11px;")
        fav_row.addWidget(self._count_label)
        root.addLayout(fav_row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #ddd;")
        root.addWidget(sep2)

        # ── Paper list ─────────────────────────────────────────────────────────
        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        self._list.setSpacing(1)
        root.addWidget(self._list)

        # Drop hint
        self._drop_label = QLabel("PDFをここにドラッグ")
        self._drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_label.setStyleSheet("color: #aaa; font-size: 11px; padding: 4px;")
        root.addWidget(self._drop_label)

    # ── Public API ─────────────────────────────────────────────────────────────

    def refresh(self):
        self._reload_combos()
        self._apply_filter()

    def select_paper(self, paper_id: int):
        for i in range(self._list.count()):
            item = self._list.item(i)
            p = item.data(Qt.ItemDataRole.UserRole)
            if p and p.id == paper_id:
                self._list.setCurrentItem(item)
                return

    def current_paper(self) -> Optional[Paper]:
        return self._selected

    # ── Internals ──────────────────────────────────────────────────────────────

    def _reload_combos(self):
        current_year = self._year_combo.currentData()
        current_journal = self._journal_combo.currentData()
        current_tag = self._tag_combo.currentData()

        self._year_combo.blockSignals(True)
        self._year_combo.clear()
        self._year_combo.addItem("年度：すべて", None)
        for y in self._service.get_distinct_years():
            self._year_combo.addItem(str(y), y)
        idx = self._year_combo.findData(current_year)
        if idx >= 0:
            self._year_combo.setCurrentIndex(idx)
        self._year_combo.blockSignals(False)

        self._journal_combo.blockSignals(True)
        self._journal_combo.clear()
        self._journal_combo.addItem("雑誌：すべて", None)
        for j in self._service.get_distinct_journals():
            short = j[:20] + "…" if len(j) > 20 else j
            self._journal_combo.addItem(short, j)
        idx = self._journal_combo.findData(current_journal)
        if idx >= 0:
            self._journal_combo.setCurrentIndex(idx)
        self._journal_combo.blockSignals(False)

        self._tag_combo.blockSignals(True)
        self._tag_combo.clear()
        self._tag_combo.addItem("タグ：すべて", None)
        for t in self._service.get_all_tags():
            self._tag_combo.addItem(t, t)
        idx = self._tag_combo.findData(current_tag)
        if idx >= 0:
            self._tag_combo.setCurrentIndex(idx)
        self._tag_combo.blockSignals(False)

    def _apply_filter(self):
        q = self._search_box.text().strip()
        year = self._year_combo.currentData()
        journal = self._journal_combo.currentData() or ""
        tag = self._tag_combo.currentData() or ""
        fav = self._fav_check.isChecked()

        self._papers = self._service.search(
            query=q, year=year, journal=journal, tag=tag, favorites_only=fav
        )
        self._rebuild_list()

    def _rebuild_list(self):
        prev_id = self._selected.id if self._selected else None
        self._list.clear()

        for paper in self._papers:
            item = QListWidgetItem(self._list)
            item.setData(Qt.ItemDataRole.UserRole, paper)
            widget = PaperListItemWidget(paper)
            item.setSizeHint(widget.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, widget)

        self._count_label.setText(f"{len(self._papers)} 件")

        if prev_id is not None:
            self.select_paper(prev_id)
        elif self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _on_selection_changed(self):
        items = self._list.selectedItems()
        if items:
            self._selected = items[0].data(Qt.ItemDataRole.UserRole)
        else:
            self._selected = None

        has_sel = self._selected is not None
        self._btn_edit.setEnabled(has_sel)
        self._btn_delete.setEnabled(has_sel)
        self.paper_selected.emit(self._selected)

    def _on_edit(self):
        if self._selected:
            self.edit_requested.emit(self._selected)

    def _on_delete(self):
        if self._selected:
            self.delete_requested.emit(self._selected)

    # ── Drag-and-drop ──────────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().lower().endswith(".pdf") for u in urls):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self.pdf_dropped.emit(path)
                break
        event.acceptProposedAction()

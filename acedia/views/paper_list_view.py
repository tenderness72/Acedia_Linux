from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QRect, QSize, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QPainter
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
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from ..models.paper import Paper
from ..services.paper_service import PaperService


class PaperItemDelegate(QStyledItemDelegate):
    """Delegate that paints rich paper list items without using child widgets."""

    def paint(self, painter: QPainter, option, index):
        paper: Optional[Paper] = index.data(Qt.ItemDataRole.UserRole)
        if not paper:
            super().paint(painter, option, index)
            return

        painter.save()

        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if is_selected:
            painter.fillRect(option.rect, QColor("#eff6ff"))
            accent = QRect(option.rect.left(), option.rect.top(), 3, option.rect.height())
            painter.fillRect(accent, QColor("#3b82f6"))
        elif index.row() % 2 == 0:
            painter.fillRect(option.rect, QColor("#f8fafc"))
        else:
            painter.fillRect(option.rect, QColor("#ffffff"))

        left = option.rect.left() + 10
        top = option.rect.top() + 6
        right = option.rect.right() - 8
        width = right - left

        # ── Meta line (author + year) ───────────────────────────────────────
        authors = paper.author_list
        author_str = authors[0] if authors else ""
        if len(authors) == 2:
            author_str = f"{authors[0]}・{authors[1]}"
        elif len(authors) > 2:
            author_str = f"{authors[0]} ら"
        year_str = f"（{paper.year}）" if paper.year else ""
        meta_text = f"{author_str}{year_str}"

        font_small = QFont(option.font)
        font_small.setPointSize(max(font_small.pointSize() - 2, 8))
        painter.setFont(font_small)
        painter.setPen(QColor("#6b7280"))
        meta_w = width - (20 if paper.is_favorite else 0)
        painter.drawText(QRect(left, top, meta_w, 16),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         meta_text)

        if paper.is_favorite:
            painter.setPen(QColor("#f59e0b"))
            painter.drawText(QRect(right - 18, top, 18, 16),
                             Qt.AlignmentFlag.AlignCenter, "★")

        top += 18

        # ── Title ──────────────────────────────────────────────────────────
        font_title = QFont(option.font)
        font_title.setBold(True)
        painter.setFont(font_title)
        painter.setPen(QColor("#111827") if not is_selected else QColor("#1e3a8a"))
        fm = painter.fontMetrics()
        title_text = fm.elidedText(
            paper.title or "（タイトル未設定）",
            Qt.TextElideMode.ElideRight, width
        )
        painter.drawText(QRect(left, top, width, 18),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         title_text)
        top += 18

        # ── Journal ────────────────────────────────────────────────────────
        if paper.journal:
            font_journal = QFont(option.font)
            font_journal.setPointSize(max(font_journal.pointSize() - 2, 8))
            font_journal.setItalic(True)
            painter.setFont(font_journal)
            painter.setPen(QColor("#6b7280"))
            fm2 = painter.fontMetrics()
            jtext = fm2.elidedText(paper.journal, Qt.TextElideMode.ElideRight, width)
            painter.drawText(QRect(left, top, width, 16),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             jtext)

        painter.restore()

    def sizeHint(self, option, index):
        paper: Optional[Paper] = index.data(Qt.ItemDataRole.UserRole)
        if not paper:
            return super().sizeHint(option, index)
        h = 6 + 16 + 18 + 6   # top + meta + title + bottom
        if paper.journal:
            h += 16
        return QSize(100, h)


class PaperListView(QWidget):
    paper_selected = Signal(object)
    add_requested = Signal()
    edit_requested = Signal(object)
    delete_requested = Signal(object)
    import_ris_requested = Signal()
    pdf_dropped = Signal(str)

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
        self._list.setItemDelegate(PaperItemDelegate(self._list))
        self._list.setAlternatingRowColors(False)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._list.itemClicked.connect(self._set_selected_from_item)
        self._list.currentItemChanged.connect(lambda current, _previous: self._set_selected_from_item(current))
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        self._list.setSpacing(1)
        root.addWidget(self._list)

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
                item.setSelected(True)
                self._set_selected_from_item(item)
                self._list.scrollToItem(item)
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
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

        self._count_label.setText(f"{len(self._papers)} 件")

        if prev_id is not None:
            self.select_paper(prev_id)
        elif self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _on_selection_changed(self):
        items = self._list.selectedItems()
        if items:
            self._set_selected_from_item(items[0])
        else:
            self._set_selected_from_item(self._list.currentItem())

    def _set_selected_from_item(self, item: Optional[QListWidgetItem]):
        if item is not None:
            self._selected = item.data(Qt.ItemDataRole.UserRole)
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

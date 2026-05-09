"""
CategoryPanel: left-side panel with category filter list and sequence list.
Clicking a category emits category_selected (None = show all).
Clicking a sequence emits sequence_triggered.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor

from core.data_store import DataStore
from core.models import Category, Sequence


class CategoryPanel(QWidget):
    category_selected = Signal(object)   # Category | None  (None = All)
    sequence_triggered = Signal(str)     # sequence id

    def __init__(self, store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.store = store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        # ── Categories section ────────────────────────────────────────
        layout.addWidget(self._section_label("Categories"))

        self.cat_list = QListWidget()
        self.cat_list.setStyleSheet(self._list_style())
        self.cat_list.setFocusPolicy(Qt.NoFocus)
        self.cat_list.setFixedHeight(0)   # will grow via _resize_list
        self.cat_list.currentItemChanged.connect(self._on_category_changed)
        layout.addWidget(self.cat_list)

        # ── Sequences section ─────────────────────────────────────────
        layout.addSpacing(8)
        layout.addWidget(self._section_label("Sequences"))

        self.seq_list = QListWidget()
        self.seq_list.setStyleSheet(self._list_style())
        self.seq_list.setFocusPolicy(Qt.NoFocus)
        self.seq_list.setFixedHeight(0)
        self.seq_list.itemDoubleClicked.connect(self._on_sequence_double_clicked)
        self.seq_list.installEventFilter(self)
        layout.addWidget(self.seq_list)

        layout.addStretch()

        self.refresh()

    # ── Public API ────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Reload categories and sequences from store."""
        self._populate_categories()
        self._populate_sequences()

    def clear_selection(self) -> None:
        """Select the 'All' row programmatically."""
        self.cat_list.setCurrentRow(0)

    # ── Category list ─────────────────────────────────────────────────

    def _populate_categories(self) -> None:
        previous_id = self._selected_category_id()

        self.cat_list.blockSignals(True)
        self.cat_list.clear()

        categories = self.store.get_categories()
        all_count = len(self.store.get_bookmarks())

        # "All" row
        all_item = QListWidgetItem(f"  All  ({all_count})")
        all_item.setData(Qt.UserRole, None)
        self.cat_list.addItem(all_item)

        for cat in sorted(categories, key=lambda c: c.order):
            count = len(self.store.get_bookmarks(cat.id))
            item = QListWidgetItem(f"  {cat.name}  ({count})")
            item.setData(Qt.UserRole, cat.id)
            item.setForeground(QColor(cat.color))
            self.cat_list.addItem(item)

        self.cat_list.blockSignals(False)

        # Restore previous selection or fall back to "All"
        self._restore_selection(self.cat_list, previous_id)
        self._resize_list(self.cat_list)

    def _on_category_changed(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            return
        cat_id = current.data(Qt.UserRole)   # None for "All"
        self.category_selected.emit(cat_id)

    def _selected_category_id(self) -> str | None:
        item = self.cat_list.currentItem()
        return item.data(Qt.UserRole) if item else None

    # ── Sequence list ─────────────────────────────────────────────────

    def _populate_sequences(self) -> None:
        self.seq_list.clear()
        sequences = self.store.get_sequences()

        if not sequences:
            empty = QListWidgetItem("  (no sequences yet)")
            empty.setData(Qt.UserRole, None)
            empty.setFlags(Qt.NoItemFlags)   # not selectable
            empty.setForeground(QColor("#585b70"))
            self.seq_list.addItem(empty)
        else:
            for seq in sorted(sequences, key=lambda s: s.order):
                item = QListWidgetItem(f"  ▶  {seq.name}")
                item.setData(Qt.UserRole, seq.id)
                if seq.note:
                    item.setToolTip(seq.note)
                self.seq_list.addItem(item)

        self._resize_list(self.seq_list)

    def _on_sequence_double_clicked(self, item: QListWidgetItem) -> None:
        seq_id = item.data(Qt.UserRole)
        if seq_id:
            self.sequence_triggered.emit(seq_id)

    # ── Helpers ───────────────────────────────────────────────────────

    def _restore_selection(self, list_widget: QListWidget, target_id: str | None) -> None:
        """Re-select the row matching target_id, or row 0 if not found."""
        for i in range(list_widget.count()):
            if list_widget.item(i).data(Qt.UserRole) == target_id:
                list_widget.setCurrentRow(i)
                return
        list_widget.setCurrentRow(0)

    def _resize_list(self, list_widget: QListWidget) -> None:
        """Shrink-wrap the list height to its content (no scroll bar needed)."""
        row_h = 32
        height = list_widget.count() * row_h
        list_widget.setFixedHeight(height)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setObjectName("SectionLabel")
        label.setContentsMargins(12, 4, 12, 6)
        return label

    def _list_style(self) -> str:
        return """
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
                color: #cdd6f4;
            }
            QListWidget::item {
                border-radius: 6px;
                padding: 2px 4px;
                margin: 1px 6px;
                height: 28px;
            }
            QListWidget::item:hover {
                background-color: #313244;
            }
            QListWidget::item:selected {
                background-color: #45475a;
                color: #cdd6f4;
            }
        """

    # ── Event filter for Enter key on sequences ───────────────────────

    def eventFilter(self, source: object, event) -> bool:
        from PySide6.QtCore import QEvent
        if source is self.seq_list and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                item = self.seq_list.currentItem()
                if item:
                    self._on_sequence_double_clicked(item)
                return True
        return super().eventFilter(source, event)

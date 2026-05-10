"""
CategoryPanel: left-side panel with categories, sequences, and tags.
Clicking a category emits category_selected (None = show all).
Clicking a tag emits tag_selected (None = clear tag filter).
Clicking a sequence emits sequence_triggered.
+ buttons on section headers emit add_category_requested / add_tag_requested.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QMenu,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QColor

from core.data_store import DataStore


class CategoryPanel(QWidget):
    category_selected = Signal(object)      # str | None  (None = All)
    tag_selected = Signal(object)           # str | None  (None = clear filter)
    sequence_triggered = Signal(str)        # sequence id

    add_category_requested = Signal()
    add_tag_requested = Signal()
    edit_category_requested = Signal(str)
    delete_category_requested = Signal(str)
    edit_tag_requested = Signal(str)
    delete_tag_requested = Signal(str)

    def __init__(self, store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.store = store
        self._active_tag_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        # ── Categories ────────────────────────────────────────────────
        layout.addWidget(self._section_header("Categories", self._on_add_category))

        self.cat_list = QListWidget()
        self.cat_list.setStyleSheet(self._list_style())
        self.cat_list.setFocusPolicy(Qt.NoFocus)
        self.cat_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cat_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cat_list.currentItemChanged.connect(self._on_category_changed)
        self.cat_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cat_list.customContextMenuRequested.connect(self._on_cat_context_menu)
        layout.addWidget(self.cat_list)   # no stretch — sized by content in refresh

        # ── Sequences ─────────────────────────────────────────────────
        layout.addSpacing(8)
        layout.addWidget(self._section_header("Sequences", None))

        self.seq_list = QListWidget()
        self.seq_list.setStyleSheet(self._list_style())
        self.seq_list.setFocusPolicy(Qt.NoFocus)
        self.seq_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.seq_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.seq_list.itemDoubleClicked.connect(self._on_sequence_double_clicked)
        self.seq_list.installEventFilter(self)
        layout.addWidget(self.seq_list)

        # ── Tags ──────────────────────────────────────────────────────
        layout.addSpacing(8)
        layout.addWidget(self._section_header("Tags", self._on_add_tag))

        self.tag_list = QListWidget()
        self.tag_list.setStyleSheet(self._list_style())
        self.tag_list.setFocusPolicy(Qt.NoFocus)
        self.tag_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tag_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Fix 3: use itemClicked instead of currentItemChanged so repeated
        # clicks on the same item are detected (currentItemChanged fires only
        # when selection actually changes).
        self.tag_list.itemClicked.connect(self._on_tag_clicked)
        self.tag_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tag_list.customContextMenuRequested.connect(self._on_tag_context_menu)
        layout.addWidget(self.tag_list)

        # Spacer pushes content up but lets the panel fill remaining space
        layout.addStretch()
        self.refresh()

    # ── Public API ────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._populate_categories()
        self._populate_sequences()
        self._populate_tags()

    def clear_selection(self) -> None:
        self.cat_list.setCurrentRow(0)

    # ── Categories ────────────────────────────────────────────────────

    def _populate_categories(self) -> None:
        previous_id = self._selected_id(self.cat_list)

        self.cat_list.blockSignals(True)
        self.cat_list.clear()

        all_item = QListWidgetItem(f"  All  ({len(self.store.get_bookmarks())})")
        all_item.setData(Qt.UserRole, None)
        self.cat_list.addItem(all_item)

        for cat in sorted(self.store.get_categories(), key=lambda c: c.order):
            count = len(self.store.get_bookmarks(cat.id))
            item = QListWidgetItem(f"  {cat.name}  ({count})")
            item.setData(Qt.UserRole, cat.id)
            item.setForeground(QColor(cat.color))
            self.cat_list.addItem(item)

        self.cat_list.blockSignals(False)
        self._restore_selection(self.cat_list, previous_id)
        self._resize_list(self.cat_list)

    def _on_category_changed(self, current: QListWidgetItem | None, _prev) -> None:
        if current:
            self.category_selected.emit(current.data(Qt.UserRole))

    def _on_cat_context_menu(self, pos) -> None:
        item = self.cat_list.itemAt(pos)
        if item is None:
            return
        cat_id = item.data(Qt.UserRole)
        if cat_id is None:   # "All" row — no actions
            return
        menu = self._make_context_menu()
        edit_action = menu.addAction("✏  Edit")
        menu.addSeparator()
        delete_action = menu.addAction("🗑  Delete")
        action = menu.exec(self.cat_list.mapToGlobal(pos))
        if action == edit_action:
            self.edit_category_requested.emit(cat_id)
        elif action == delete_action:
            self.delete_category_requested.emit(cat_id)

    # ── Sequences ─────────────────────────────────────────────────────

    def _populate_sequences(self) -> None:
        self.seq_list.clear()
        sequences = self.store.get_sequences()

        if not sequences:
            empty = QListWidgetItem("  (no sequences yet)")
            empty.setData(Qt.UserRole, None)
            empty.setFlags(Qt.NoItemFlags)
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

    # ── Tags ──────────────────────────────────────────────────────────

    def _populate_tags(self) -> None:
        self.tag_list.blockSignals(True)
        self.tag_list.clear()

        tags = self.store.get_tags()
        if not tags:
            empty = QListWidgetItem("  (no tags yet)")
            empty.setData(Qt.UserRole, None)
            empty.setFlags(Qt.NoItemFlags)
            empty.setForeground(QColor("#585b70"))
            self.tag_list.addItem(empty)
        else:
            for tag in tags:
                count = sum(1 for b in self.store.get_bookmarks() if tag.id in b.tag_ids)
                item = QListWidgetItem(f"  #{tag.name}  ({count})")
                item.setData(Qt.UserRole, tag.id)
                self.tag_list.addItem(item)

        self.tag_list.blockSignals(False)
        self._restore_selection(self.tag_list, self._active_tag_id)
        self._resize_list(self.tag_list)

    def _on_tag_clicked(self, item: QListWidgetItem) -> None:
        tag_id = item.data(Qt.UserRole)
        if tag_id is None:
            return
        if self._active_tag_id == tag_id:
            # Second click on same tag → deselect
            self._active_tag_id = None
            self.tag_list.blockSignals(True)
            self.tag_list.clearSelection()
            self.tag_list.setCurrentRow(-1)
            self.tag_list.blockSignals(False)
        else:
            self._active_tag_id = tag_id
        self.tag_selected.emit(self._active_tag_id)

    def _on_tag_context_menu(self, pos) -> None:
        item = self.tag_list.itemAt(pos)
        if item is None:
            return
        tag_id = item.data(Qt.UserRole)
        if tag_id is None:
            return
        menu = self._make_context_menu()
        edit_action = menu.addAction("✏  Edit")
        menu.addSeparator()
        delete_action = menu.addAction("🗑  Delete")
        action = menu.exec(self.tag_list.mapToGlobal(pos))
        if action == edit_action:
            self.edit_tag_requested.emit(tag_id)
        elif action == delete_action:
            self.delete_tag_requested.emit(tag_id)

    # ── Button handlers ───────────────────────────────────────────────

    def _on_add_category(self) -> None:
        self.add_category_requested.emit()

    def _on_add_tag(self) -> None:
        self.add_tag_requested.emit()

    # ── Helpers ───────────────────────────────────────────────────────

    def _selected_id(self, list_widget: QListWidget) -> str | None:
        item = list_widget.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _resize_list(self, list_widget: QListWidget) -> None:
        # Shrink-wrap to content so the list never shows a scrollbar
        # and never causes scroll-jump when an item is clicked.
        # 32px per row matches the item height set in the stylesheet.
        list_widget.setFixedHeight(list_widget.count() * 32)

    def _restore_selection(self, list_widget: QListWidget, target_id: str | None) -> None:
        for i in range(list_widget.count()):
            if list_widget.item(i).data(Qt.UserRole) == target_id:
                # scrollToItem would cause the jump bug — skip it by blocking
                list_widget.blockSignals(True)
                list_widget.setCurrentRow(i)
                list_widget.blockSignals(False)
                return
        if list_widget is self.cat_list:
            list_widget.blockSignals(True)
            list_widget.setCurrentRow(0)
            list_widget.blockSignals(False)

    def _section_header(self, title: str, on_add) -> QWidget:
        """Section label with optional + button on the right."""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 4, 8, 4)
        layout.setSpacing(0)

        label = QLabel(title.upper())
        label.setObjectName("SectionLabel")
        layout.addWidget(label, stretch=1)

        if on_add:
            btn = QPushButton("+")
            btn.setFixedSize(20, 20)
            btn.setObjectName("SectionAddButton")
            btn.setToolTip(f"Add {title[:-1] if title.endswith('s') else title}")
            btn.clicked.connect(on_add)
            layout.addWidget(btn)

        return row

    def _make_context_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected { background-color: #45475a; }
            QMenu::separator { height: 1px; background: #45475a; margin: 4px 0; }
        """)
        return menu

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
            QListWidget::item:hover { background-color: #313244; }
            QListWidget::item:selected {
                background-color: #45475a;
                color: #cdd6f4;
            }
        """

    # ── Event filter ──────────────────────────────────────────────────

    def eventFilter(self, source: object, event) -> bool:
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if source is self.seq_list:
                    item = self.seq_list.currentItem()
                    if item:
                        self._on_sequence_double_clicked(item)
                    return True
        return super().eventFilter(source, event)


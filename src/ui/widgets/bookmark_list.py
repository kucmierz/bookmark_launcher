"""
BookmarkList: the main right-panel widget.
Shows bookmarks as rows with icon, name, tags, and tooltip note.
Double-click or Enter launches the bookmark.
Supports drag&drop reorder (manual sort mode only).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QComboBox, QFrame,
)
from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QIcon

from core.models import Bookmark, Tag
from core.data_store import DataStore
from core.launcher import launch_bookmark
from utils.icons import get_icon, type_emoji

SORT_OPTIONS = [
    ("Manual order",   "manual"),
    ("Alphabetical",   "alphabetical"),
    ("Recently used",  "by_last_used"),
]


class BookmarkList(QWidget):
    launch_error = Signal(str)
    bookmark_launched = Signal(str)
    drop_requested = Signal(list)    # list[str] of dropped local paths
    sort_changed = Signal(str)       # new sort_order value → main window saves it

    def __init__(self, store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.store = store
        self._current_bookmarks: list[Bookmark] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_toolbar())
        layout.addWidget(self._build_list())
        layout.addWidget(self._build_empty_label())

        self.setAcceptDrops(True)
        self._update_visibility()

    # ── Build ────────────────────────────────────────────────────────

    def _build_toolbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("SortBar")
        bar.setFixedHeight(36)
        bar.setStyleSheet("""
            QFrame#SortBar {
                background-color: #181825;
                border-bottom: 1px solid #313244;
            }
            QLabel {
                color: #6c7086;
                font-size: 12px;
            }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 0 8px;
                min-height: 24px;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #89b4fa;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                selection-background-color: #45475a;
                outline: none;
            }
        """)

        h = QHBoxLayout(bar)
        h.setContentsMargins(10, 0, 10, 0)
        h.setSpacing(6)

        h.addWidget(QLabel("Sort:"))

        self.sort_combo = QComboBox()
        for label, _ in SORT_OPTIONS:
            self.sort_combo.addItem(label)

        # Set combo to current saved setting
        current = self.store.data.settings.sort_order
        for i, (_, value) in enumerate(SORT_OPTIONS):
            if value == current:
                self.sort_combo.setCurrentIndex(i)
                break

        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        h.addWidget(self.sort_combo)
        h.addStretch()

        return bar

    def _build_list(self) -> QListWidget:
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(1)
        self.list_widget.setIconSize(QSize(20, 20))
        self.list_widget.setFocusPolicy(Qt.StrongFocus)
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.setStyleSheet(self._list_style())
        self.list_widget.itemDoubleClicked.connect(self._on_item_activated)
        self.list_widget.installEventFilter(self)
        return self.list_widget

    def _build_empty_label(self) -> QLabel:
        self.empty_label = QLabel("No bookmarks yet.\nClick  ＋ Add  to get started.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setObjectName("EmptyStateLabel")
        return self.empty_label

    # ── Public API ───────────────────────────────────────────────────

    def load(self, bookmarks: list[Bookmark]) -> None:
        """Replace the displayed list with the given bookmarks."""
        self._current_bookmarks = bookmarks
        self.list_widget.clear()

        is_manual = self.store.data.settings.sort_order == "manual"
        self.list_widget.setDragDropMode(
            QListWidget.DragDropMode.InternalMove if is_manual
            else QListWidget.DragDropMode.NoDragDrop
        )

        if bookmarks:
            tag_map = {t.id: t for t in self.store.get_tags()}
            for bm in bookmarks:
                self.list_widget.addItem(self._make_item(bm, tag_map))

        self._update_visibility()

    def selected_bookmark(self) -> Bookmark | None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._current_bookmarks):
            return None
        return self._current_bookmarks[row]

    # ── Item construction ────────────────────────────────────────────

    def _make_item(self, bm: Bookmark, tag_map: dict[str, Tag]) -> QListWidgetItem:
        tag_names = [tag_map[tid].name for tid in bm.tag_ids if tid in tag_map]
        tag_str = "  " + "  ".join(f"[{t}]" for t in tag_names) if tag_names else ""
        display = f"  {type_emoji(bm)}  {bm.name}{tag_str}"

        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, bm.id)

        icon = get_icon(bm)
        if not icon.isNull():
            item.setIcon(icon)

        item.setToolTip(bm.note if bm.note else bm.target)
        item.setSizeHint(QSize(0, 36))

        if self.store.data.settings.sort_order == "manual":
            item.setFlags(item.flags() | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled)

        return item

    # ── Sorting ──────────────────────────────────────────────────────

    def _on_sort_changed(self, index: int) -> None:
        _, value = SORT_OPTIONS[index]
        self.sort_changed.emit(value)

    # ── Launch ───────────────────────────────────────────────────────

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        bm_id = item.data(Qt.UserRole)
        bm = self.store.get_bookmark(bm_id)
        if bm is None:
            return
        try:
            launch_bookmark(bm)
            self.store.record_launch(bm_id)
            self.bookmark_launched.emit(bm_id)
        except (FileNotFoundError, OSError, ValueError) as e:
            self.launch_error.emit(str(e))

    # ── Drag&drop reorder ────────────────────────────────────────────

    def _on_reorder(self) -> None:
        """Called after internal drag&drop — persist new order to store."""
        new_order = [
            self.list_widget.item(i).data(Qt.UserRole)
            for i in range(self.list_widget.count())
        ]
        self.store.reorder_bookmarks(new_order)
        # Sync _current_bookmarks to new order so selected_bookmark() stays correct
        id_to_bm = {bm.id: bm for bm in self._current_bookmarks}
        self._current_bookmarks = [id_to_bm[bid] for bid in new_order if bid in id_to_bm]

    # ── Event filter (keyboard + drop finish) ────────────────────────

    def eventFilter(self, source: object, event: QEvent) -> bool:
        if source is self.list_widget:
            if event.type() == QEvent.KeyPress:
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    item = self.list_widget.currentItem()
                    if item:
                        self._on_item_activated(item)
                    return True
            if event.type() == QEvent.Drop:
                # Let Qt handle the visual reorder first, then persist
                result = super().eventFilter(source, event)
                self._on_reorder()
                return result
        return super().eventFilter(source, event)

    # ── Explorer drag&drop ───────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        if paths:
            event.acceptProposedAction()
            self.drop_requested.emit(paths)

    # ── Helpers ──────────────────────────────────────────────────────

    def _update_visibility(self) -> None:
        has_items = bool(self._current_bookmarks)
        self.list_widget.setVisible(has_items)
        self.empty_label.setVisible(not has_items)

    def _list_style(self) -> str:
        return """
            QListWidget {
                background-color: #1e1e2e;
                border: none;
                outline: none;
                color: #cdd6f4;
            }
            QListWidget::item {
                border-radius: 6px;
                padding: 2px 8px;
                margin: 1px 6px;
                color: #cdd6f4;
            }
            QListWidget::item:hover {
                background-color: #313244;
            }
            QListWidget::item:selected {
                background-color: #45475a;
                color: #cdd6f4;
            }
        """
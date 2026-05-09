"""
BookmarkList: the main right-panel widget.
Shows bookmarks as rows with icon, name, tags, and tooltip note.
Double-click or Enter launches the bookmark.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QHBoxLayout, QFrame,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QColor

from core.models import Bookmark, Tag
from core.data_store import DataStore
from core.launcher import launch_bookmark
from utils.icons import get_icon, type_emoji


class BookmarkList(QWidget):
    """Displays a filtered list of bookmarks. Emits launch_error on failure."""

    launch_error = Signal(str)          # carries error message to main window
    bookmark_launched = Signal(str)     # carries bookmark id

    def __init__(self, store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.store = store
        self._current_bookmarks: list[Bookmark] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(1)
        self.list_widget.setIconSize(QSize(20, 20))
        self.list_widget.setFocusPolicy(Qt.StrongFocus)
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.setStyleSheet(self._list_style())

        self.list_widget.itemDoubleClicked.connect(self._on_item_activated)
        self.list_widget.itemActivated.connect(self._on_item_activated)

        self.empty_label = QLabel("No bookmarks yet.\nClick  ＋ Add  to get started.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setObjectName("EmptyStateLabel")

        layout.addWidget(self.list_widget)
        layout.addWidget(self.empty_label)

        self.list_widget.hide()

    # ── Public API ───────────────────────────────────────────────────

    def load(self, bookmarks: list[Bookmark]) -> None:
        """Replace the displayed list with the given bookmarks."""
        self._current_bookmarks = bookmarks
        self.list_widget.clear()

        if not bookmarks:
            self.list_widget.hide()
            self.empty_label.show()
            return

        self.empty_label.hide()
        self.list_widget.show()

        tag_map = {t.id: t for t in self.store.get_tags()}

        for bm in bookmarks:
            item = self._make_item(bm, tag_map)
            self.list_widget.addItem(item)

    def selected_bookmark(self) -> Bookmark | None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._current_bookmarks):
            return None
        return self._current_bookmarks[row]

    # ── Item construction ────────────────────────────────────────────

    def _make_item(self, bm: Bookmark, tag_map: dict[str, Tag]) -> QListWidgetItem:
        # Build display text: name + tag pills
        tag_names = [tag_map[tid].name for tid in bm.tag_ids if tid in tag_map]
        tag_str = "  " + "  ".join(f"[{t}]" for t in tag_names) if tag_names else ""
        display = f"  {type_emoji(bm)}  {bm.name}{tag_str}"

        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, bm.id)

        # System icon (falls back to emoji in text if icon is null)
        icon = get_icon(bm)
        if not icon.isNull():
            item.setIcon(icon)

        # Tooltip shows the note, or the target path if note is empty
        tooltip = bm.note if bm.note else bm.target
        item.setToolTip(tooltip)

        item.setSizeHint(QSize(0, 36))

        return item

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

    # ── Stylesheet ───────────────────────────────────────────────────

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

"""
Main application window.
Layout: header bar (search + buttons) / left panel (categories + sequences)
        / right panel (bookmark list).
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QPushButton, QLineEdit, QFrame,
    QMessageBox, QMenu,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from config import (
    APP_NAME,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    LEFT_PANEL_WIDTH,
)
from core.data_store import DataStore
from core.launcher import launch_sequence
from core.search import filter_bookmarks
from ui.widgets.bookmark_list import BookmarkList
from ui.widgets.category_panel import CategoryPanel
from ui.dialogs.bookmark_dialog import BookmarkDialog
from ui.dialogs.tag_dialog import TagDialog


class MainWindow(QMainWindow):
    def __init__(self, store: DataStore) -> None:
        super().__init__()
        self.store = store
        self._active_category_id: str | None = None  # None = show all
        self._active_tag_id: str | None = None        # None = no tag filter

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_header())
        root_layout.addWidget(self._build_body(), stretch=1)

        self._refresh_bookmarks()

    # ── Header ───────────────────────────────────────────────────────

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(48)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search bookmarks…")
        self.search_box.setFixedHeight(32)
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_box, stretch=1)

        self.btn_add = QPushButton("＋  Add")
        self.btn_add.setFixedHeight(32)
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_add.clicked.connect(self._on_add_bookmark)
        layout.addWidget(self.btn_add)

        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setToolTip("Settings")
        layout.addWidget(self.btn_settings)

        return header

    # ── Body (splitter with left + right panels) ──────────────────────

    def _build_body(self) -> QSplitter:
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)

        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())

        splitter.setSizes([LEFT_PANEL_WIDTH, WINDOW_DEFAULT_WIDTH - LEFT_PANEL_WIDTH])
        return splitter

    # ── Left panel ───────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("LeftPanel")
        panel.setMinimumWidth(150)
        panel.setMaximumWidth(320)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.category_panel = CategoryPanel(self.store)
        self.category_panel.category_selected.connect(self._on_category_selected)
        self.category_panel.tag_selected.connect(self._on_tag_selected)
        self.category_panel.sequence_triggered.connect(self._on_sequence_triggered)
        self.category_panel.add_category_requested.connect(self._on_add_category)
        self.category_panel.add_tag_requested.connect(self._on_add_tag)
        self.category_panel.edit_category_requested.connect(self._on_edit_category)
        self.category_panel.delete_category_requested.connect(self._on_delete_category)
        self.category_panel.edit_tag_requested.connect(self._on_edit_tag)
        self.category_panel.delete_tag_requested.connect(self._on_delete_tag)
        layout.addWidget(self.category_panel)

        return panel

    # ── Right panel ──────────────────────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("RightPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.bookmark_list = BookmarkList(self.store)
        self.bookmark_list.launch_error.connect(self._on_launch_error)
        self.bookmark_list.drop_requested.connect(self._on_drop)
        self.bookmark_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmark_list.customContextMenuRequested.connect(self._on_bookmark_context_menu)
        layout.addWidget(self.bookmark_list, stretch=1)

        return panel

    # ── Data refresh ─────────────────────────────────────────────────

    def _refresh_bookmarks(self) -> None:
        """Reload and filter bookmark list — respects category, tag, and search."""
        bookmarks = self.store.get_bookmarks(self._active_category_id)

        if self._active_tag_id:
            bookmarks = [b for b in bookmarks if self._active_tag_id in b.tag_ids]

        query = self.search_box.text()
        if query.strip():
            tag_map = {t.id: t for t in self.store.get_tags()}
            bookmarks = filter_bookmarks(bookmarks, query, tag_map)

        self.bookmark_list.load(bookmarks)

    def _refresh_all(self) -> None:
        """Full refresh — call after any data change."""
        self.category_panel.refresh()
        self._refresh_bookmarks()

    # ── Slots ────────────────────────────────────────────────────────

    def _on_search_changed(self, text: str) -> None:
        # Show a stronger border when a filter is active, no background change
        if text.strip():
            self.search_box.setStyleSheet(
                "QLineEdit { border: 2px solid #89b4fa; }"
            )
        else:
            self.search_box.setStyleSheet("")
        self._refresh_bookmarks()

    def _on_category_selected(self, cat_id: str | None) -> None:
        self._active_category_id = cat_id
        self._refresh_bookmarks()

    def _on_tag_selected(self, tag_id: str | None) -> None:
        # Clicking the same tag again deselects it
        if self._active_tag_id == tag_id:
            self._active_tag_id = None
            self.category_panel.tag_list.clearSelection()
        else:
            self._active_tag_id = tag_id
        self._refresh_bookmarks()

    def _on_sequence_triggered(self, seq_id: str) -> None:
        seq = self.store.get_sequence(seq_id)
        if seq is None:
            return
        errors = launch_sequence(seq, self.store)
        if errors:
            QMessageBox.warning(
                self, "Sequence errors",
                "Some items could not be launched:\n\n" + "\n".join(errors),
            )

    def _on_launch_error(self, message: str) -> None:
        QMessageBox.warning(self, "Could not open", message)

    def _on_add_bookmark(self) -> None:
        dlg = BookmarkDialog(self.store, parent=self)
        if dlg.exec():
            self._refresh_all()

    def _on_drop(self, paths: list[str]) -> None:
        """Open BookmarkDialog for each dropped path, pre-filled from path info."""
        from pathlib import Path
        from core.models import Bookmark

        for path_str in paths:
            path = Path(path_str)
            if path.is_dir():
                bm_type = "folder"
            elif path.suffix.lower() in (".exe", ".bat", ".cmd", ".ps1"):
                bm_type = "program"
            else:
                bm_type = "file"

            prefilled = Bookmark(
                id="",
                name=path.stem.replace("_", " ").title(),
                type=bm_type,
                target=path_str,
            )
            dlg = BookmarkDialog(self.store, bookmark=prefilled, parent=self)
            # Override title so it reads "Add" not "Edit" for dropped items
            dlg.setWindowTitle("Add Bookmark")
            # Save as new — clear the id so store treats it as new
            dlg.bookmark = None
            if dlg.exec():
                self._refresh_all()

    def _on_edit_bookmark(self, bm_id: str) -> None:
        bm = self.store.get_bookmark(bm_id)
        if bm is None:
            return
        dlg = BookmarkDialog(self.store, bookmark=bm, parent=self)
        if dlg.exec():
            self._refresh_all()

    def _on_delete_bookmark(self, bm_id: str) -> None:
        bm = self.store.get_bookmark(bm_id)
        if bm is None:
            return
        answer = QMessageBox.question(
            self,
            "Delete bookmark",
            f"Delete  \"{bm.name}\"?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.Cancel,
        )
        if answer == QMessageBox.Yes:
            self.store.delete_bookmark(bm_id)
            self._refresh_all()

    def _on_bookmark_context_menu(self, pos) -> None:
        bm = self.bookmark_list.selected_bookmark()
        if bm is None:
            return
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
            QMenu::item:selected {
                background-color: #45475a;
            }
            QMenu::separator {
                height: 1px;
                background: #45475a;
                margin: 4px 0;
            }
        """)
        edit_action = menu.addAction("✏  Edit")
        menu.addSeparator()
        delete_action = menu.addAction("🗑  Delete")

        action = menu.exec(self.bookmark_list.mapToGlobal(pos))
        if action == edit_action:
            self._on_edit_bookmark(bm.id)
        elif action == delete_action:
            self._on_delete_bookmark(bm.id)

    # ── Category CRUD ─────────────────────────────────────────────────

    def _on_add_category(self) -> None:
        from ui.dialogs.category_dialog import CategoryDialog
        dlg = CategoryDialog(self.store, parent=self)
        if dlg.exec():
            self._refresh_all()

    def _on_edit_category(self, cat_id: str) -> None:
        from ui.dialogs.category_dialog import CategoryDialog
        cat = self.store.get_category(cat_id)
        if cat is None:
            return
        dlg = CategoryDialog(self.store, category=cat, parent=self)
        if dlg.exec():
            self._refresh_all()

    def _on_delete_category(self, cat_id: str) -> None:
        cat = self.store.get_category(cat_id)
        if cat is None:
            return
        answer = QMessageBox.question(
            self, "Delete category",
            f"Delete \"{cat.name}\"?\nBookmarks in this category won't be deleted.",
            QMessageBox.Yes | QMessageBox.Cancel,
        )
        if answer == QMessageBox.Yes:
            self.store.delete_category(cat_id)
            if self._active_category_id == cat_id:
                self._active_category_id = None
            self._refresh_all()

    # ── Tag CRUD ──────────────────────────────────────────────────────

    def _on_add_tag(self) -> None:
        dlg = TagDialog(self.store, parent=self)
        if dlg.exec():
            self._refresh_all()

    def _on_edit_tag(self, tag_id: str) -> None:
        tag = self.store.get_tag(tag_id)
        if tag is None:
            return
        dlg = TagDialog(self.store, tag=tag, parent=self)
        if dlg.exec():
            self._refresh_all()

    def _on_delete_tag(self, tag_id: str) -> None:
        tag = self.store.get_tag(tag_id)
        if tag is None:
            return
        answer = QMessageBox.question(
            self, "Delete tag",
            f"Delete tag \"{tag.name}\"?\nIt will be removed from all bookmarks.",
            QMessageBox.Yes | QMessageBox.Cancel,
        )
        if answer == QMessageBox.Yes:
            self.store.delete_tag(tag_id)
            if self._active_tag_id == tag_id:
                self._active_tag_id = None
            self._refresh_all()



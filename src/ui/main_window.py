"""
Main application window.
Layout: header bar (search + buttons) / left panel (categories + sequences)
        / right panel (bookmark list).
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QPushButton, QLineEdit, QFrame,
    QMessageBox,
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
from ui.widgets.bookmark_list import BookmarkList
from ui.widgets.category_panel import CategoryPanel


class MainWindow(QMainWindow):
    def __init__(self, store: DataStore) -> None:
        super().__init__()
        self.store = store
        self._active_category_id: str | None = None  # None = show all

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
        layout.addWidget(self.search_box, stretch=1)

        self.btn_add = QPushButton("＋  Add")
        self.btn_add.setFixedHeight(32)
        self.btn_add.setObjectName("PrimaryButton")
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
        self.category_panel.sequence_triggered.connect(self._on_sequence_triggered)
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
        layout.addWidget(self.bookmark_list, stretch=1)

        return panel

    # ── Data refresh ─────────────────────────────────────────────────

    def _refresh_bookmarks(self) -> None:
        """Reload bookmark list from store, respecting active category filter."""
        bookmarks = self.store.get_bookmarks(self._active_category_id)
        self.bookmark_list.load(bookmarks)

    def _refresh_all(self) -> None:
        """Full refresh — call after any data change."""
        self.category_panel.refresh()
        self._refresh_bookmarks()

    # ── Slots ────────────────────────────────────────────────────────

    def _on_category_selected(self, cat_id: str | None) -> None:
        self._active_category_id = cat_id
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



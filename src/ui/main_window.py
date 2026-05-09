"""
Main application window.
Layout: header bar (search + buttons) / left panel (categories + sequences)
        / right panel (bookmark list).
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QLabel, QPushButton, QLineEdit, QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from config import (
    APP_NAME,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    LEFT_PANEL_WIDTH,
)
from core.data_store import DataStore


class MainWindow(QMainWindow):
    def __init__(self, store: DataStore) -> None:
        super().__init__()
        self.store = store

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
        splitter.setHandleWidth(1)       # thin divider line
        splitter.setChildrenCollapsible(False)

        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())

        # Set initial widths: left panel fixed-ish, right takes the rest
        splitter.setSizes([LEFT_PANEL_WIDTH, WINDOW_DEFAULT_WIDTH - LEFT_PANEL_WIDTH])

        return splitter

    # ── Left panel ───────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("LeftPanel")
        panel.setMinimumWidth(150)
        panel.setMaximumWidth(320)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        layout.addWidget(self._section_label("Categories"))
        self.category_placeholder = QLabel("  (no categories yet)")
        self.category_placeholder.setObjectName("PlaceholderLabel")
        layout.addWidget(self.category_placeholder)

        layout.addSpacing(16)

        layout.addWidget(self._section_label("Sequences"))
        self.sequence_placeholder = QLabel("  (no sequences yet)")
        self.sequence_placeholder.setObjectName("PlaceholderLabel")
        layout.addWidget(self.sequence_placeholder)

        layout.addStretch()
        return panel

    # ── Right panel ──────────────────────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("RightPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.bookmark_placeholder = QLabel("No bookmarks yet.\nClick  ＋ Add  to get started.")
        self.bookmark_placeholder.setAlignment(Qt.AlignCenter)
        self.bookmark_placeholder.setObjectName("EmptyStateLabel")
        layout.addWidget(self.bookmark_placeholder, stretch=1)

        return panel

    # ── Helpers ──────────────────────────────────────────────────────

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setObjectName("SectionLabel")
        label.setContentsMargins(12, 4, 12, 4)
        return label

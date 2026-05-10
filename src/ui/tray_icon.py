"""
System tray icon with context menu.
Left click → show/hide main window.
Right click → menu with top 5 bookmarks + standard actions.
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QObject, Signal

from core.data_store import DataStore
from core.launcher import launch_bookmark

TOP_BOOKMARKS_COUNT = 5

MENU_STYLE = """
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
    QMenu::item:disabled {
        color: #6c7086;
    }
"""


class TrayIcon(QObject):
    show_window_requested = Signal()
    quit_requested = Signal()

    def __init__(self, store: DataStore, icon: QIcon, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.store = store

        self._tray = QSystemTrayIcon(icon, self)
        self._tray.activated.connect(self._on_activated)
        self._tray.setToolTip("Bookmark Launcher")

        self._build_menu()
        self._tray.show()

    # ── Public ───────────────────────────────────────────────────────

    def refresh_menu(self) -> None:
        """Rebuild the tray menu — call after bookmark data changes."""
        self._build_menu()

    def hide_tray(self) -> None:
        self._tray.hide()

    # ── Menu construction ────────────────────────────────────────────

    def _build_menu(self) -> None:
        menu = QMenu()
        menu.setStyleSheet(MENU_STYLE)

        top_bookmarks = self._get_top_bookmarks()
        if top_bookmarks:
            for bm in top_bookmarks:
                action = menu.addAction(bm.name)
                # Capture bm.id in default arg to avoid late-binding in loop
                action.triggered.connect(lambda checked=False, b=bm: self._launch(b.id))
            menu.addSeparator()

        show_action = menu.addAction("Show window")
        show_action.triggered.connect(self.show_window_requested)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_requested)

        self._tray.setContextMenu(menu)

    def _get_top_bookmarks(self):
        bookmarks = self.store.get_bookmarks()
        used = [b for b in bookmarks if b.click_count > 0]
        used.sort(key=lambda b: b.click_count, reverse=True)
        return used[:TOP_BOOKMARKS_COUNT]

    # ── Slots ────────────────────────────────────────────────────────

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click — toggle window visibility
            self.show_window_requested.emit()

    def _launch(self, bm_id: str) -> None:
        bm = self.store.get_bookmark(bm_id)
        if bm is None:
            return
        error = launch_bookmark(bm)
        if error is None:
            self.store.record_launch(bm_id)
            self.refresh_menu()
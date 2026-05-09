"""
Entry point. Run this file to start Bookmark Launcher.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from config import APP_NAME, DATA_FILE
from core.data_store import DataStore
from ui.main_window import MainWindow


STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

/* ── Header ── */
QFrame#Header {
    background-color: #181825;
    border-bottom: 1px solid #313244;
}

QLineEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 0 10px;
}
QLineEdit:focus {
    border-color: #89b4fa;
}

QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 0 12px;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton:pressed {
    background-color: #585b70;
}

QPushButton#PrimaryButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    font-weight: bold;
}
QPushButton#PrimaryButton:hover {
    background-color: #b4befe;
}

/* ── Panels ── */
QWidget#LeftPanel {
    background-color: #181825;
    border-right: 1px solid #313244;
}
QWidget#RightPanel {
    background-color: #1e1e2e;
}

/* ── Left panel labels ── */
QLabel#SectionLabel {
    color: #6c7086;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#PlaceholderLabel {
    color: #585b70;
    font-size: 12px;
}

/* ── Right panel empty state ── */
QLabel#EmptyStateLabel {
    color: #585b70;
    font-size: 14px;
}

/* ── Splitter handle ── */
QSplitter::handle {
    background-color: #313244;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background: #1e1e2e;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""


def main() -> None:
    # Enable high-DPI scaling before creating QApplication
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    store = DataStore(DATA_FILE)
    try:
        store.load()
    except RuntimeError as e:
        QMessageBox.critical(None, "Failed to load data", str(e))
        sys.exit(1)

    window = MainWindow(store)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

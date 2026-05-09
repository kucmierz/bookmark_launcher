"""
Entry point. Run this file to start Bookmark Launcher.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from config import APP_NAME


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")  # consistent look across platforms

    # Placeholder window — replaced in Krok 4
    from PySide6.QtWidgets import QLabel, QMainWindow
    win = QMainWindow()
    win.setWindowTitle(APP_NAME)
    win.resize(900, 580)
    win.setCentralWidget(QLabel("Bookmark Launcher — coming soon 🚀", alignment=Qt.AlignCenter))
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

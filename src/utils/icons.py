"""
Icon resolution for bookmarks.
Uses QFileIconProvider to get system icons for real paths.
Falls back to type-based icons when the path doesn't exist or is a URL.
"""

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileIconProvider
from PySide6.QtCore import QFileInfo

from core.models import Bookmark

_provider = QFileIconProvider()

# Fallback Unicode characters used as icon labels when no system icon is found.
# These are rendered as text in the list widget — simple and dependency-free.
TYPE_EMOJI = {
    "program": "⚙",
    "file":    "📄",
    "folder":  "📁",
    "url":     "🌐",
    "network": "🖧",
}


def get_icon(bm: Bookmark) -> QIcon:
    """
    Return a QIcon for the bookmark.
    For local paths that exist, use the system icon (same as Explorer).
    For URLs and missing paths, return an empty QIcon (caller uses TYPE_EMOJI).
    """
    if bm.type == "url":
        return QIcon()

    path = Path(bm.target)
    if path.exists():
        return _provider.icon(QFileInfo(str(path)))

    # Path doesn't exist yet (network share offline, removable drive absent, etc.)
    return QIcon()


def type_emoji(bm: Bookmark) -> str:
    return TYPE_EMOJI.get(bm.type, "•")

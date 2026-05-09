"""
Central configuration — paths, defaults, constants.
Import this anywhere in the app instead of hardcoding strings.
"""

from pathlib import Path

# Resolve the app root: when running from src/, go one level up.
# PyInstaller sets sys._MEIPASS; we don't need it here because
# bookmarks.json always lives next to the executable / project root.
APP_ROOT = Path(__file__).parent.parent

DATA_FILE = APP_ROOT / "bookmarks.json"

APP_NAME = "Bookmark Launcher"
APP_VERSION = "0.1.0"

# UI
WINDOW_MIN_WIDTH = 700
WINDOW_MIN_HEIGHT = 450
WINDOW_DEFAULT_WIDTH = 900
WINDOW_DEFAULT_HEIGHT = 580
LEFT_PANEL_WIDTH = 200

# Tooltip delay in milliseconds
TOOLTIP_DELAY_MS = 500

# Supported bookmark types
BOOKMARK_TYPES = ["program", "file", "folder", "url", "network"]

# Default sort order written to a new bookmarks.json
DEFAULT_SORT_ORDER = "manual"

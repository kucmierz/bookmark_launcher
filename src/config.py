"""
Central configuration — paths, defaults, constants.
Import this anywhere in the app instead of hardcoding strings.
"""

import sys
from pathlib import Path

# When frozen by PyInstaller, sys.executable is the .exe file.
# When running from source, __file__ is src/config.py — go one level up.
if getattr(sys, "frozen", False):
    APP_ROOT = Path(sys.executable).parent
else:
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
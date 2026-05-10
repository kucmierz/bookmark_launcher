# Bookmark Launcher — Developer Guide

Technical reference for setting up, running, and building the project from source.

*Bookmark Launcher v0.1.0 — Marek Kucmierz, in consultation with Claude*

---

## Stack

| Component | Choice |
|-----------|--------|
| Language | Python 3.11+ |
| GUI | PySide6 (Qt for Python) |
| Data | JSON (`bookmarks.json`) |
| Packaging | PyInstaller, one-folder mode |
| Platform | Windows (primary), code is cross-platform-friendly |

## Project structure

```
bookmark_launcher/
├── src/
│   ├── main.py                  # entry point
│   ├── config.py                # paths, constants, defaults
│   ├── core/
│   │   ├── models.py            # dataclasses (Bookmark, Category, Tag, Sequence)
│   │   ├── data_store.py        # load/save JSON, CRUD operations
│   │   ├── launcher.py          # opens programs, files, folders, URLs, UNC paths
│   │   ├── search.py            # real-time filtering logic
│   │   └── importer.py          # import/export JSON
│   ├── ui/
│   │   ├── main_window.py       # main application window
│   │   ├── tray_icon.py         # system tray icon and menu
│   │   ├── dialogs/
│   │   │   ├── bookmark_dialog.py
│   │   │   ├── category_dialog.py
│   │   │   ├── tag_dialog.py
│   │   │   ├── sequence_dialog.py
│   │   │   ├── settings_dialog.py
│   │   │   └── import_export_dialog.py
│   │   └── widgets/
│   │       ├── bookmark_list.py  # bookmark list with icons, tooltips, drag & drop
│   │       └── category_panel.py # left panel: categories and sequences
│   └── utils/
│       ├── icons.py              # system icons via QFileIconProvider
│       ├── validators.py         # input validation helpers
│       └── icon_generator.py     # fallback icon generation
├── icon.png                      # app icon source (512x512 recommended)
├── bookmark_launcher.spec        # PyInstaller build spec
├── build.bat                     # one-click build script
├── run.bat                       # run from source (dev)
├── requirements.txt              # pip dependencies
├── README.md                     # end-user documentation
└── DEVELOPMENT.md                # this file
```

### Layer rules

- `core/` — pure logic, no Qt imports, independently testable
- `ui/` — all Qt code, imports from `core/` only
- `utils/` — shared helpers, minimal dependencies

## Setup

### Prerequisites

- Python 3.11 or newer — https://www.python.org/downloads/
- Git

### First time setup

```bat
git clone <repo-url>
cd bookmark_launcher
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Running from source

```bat
run.bat
```

Or manually:

```bat
.venv\Scripts\activate
cd src
python main.py
```

## Data file

`bookmarks.json` is created automatically on first run, next to the exe (dist) or in the project root (dev).

Location logic in `config.py`:

```python
if getattr(sys, "frozen", False):
    APP_ROOT = Path(sys.executable).parent  # PyInstaller dist
else:
    APP_ROOT = Path(__file__).parent.parent  # project root when running from src/
```

### Schema overview

```json
{
  "version": 1,
  "settings": { "sort_order": "manual", "show_in_tray": true, "start_minimized": false },
  "categories": [{ "id": "cat_001", "name": "Work tools", "color": "#3B82F6", "order": 0 }],
  "tags": [{ "id": "tag_001", "name": "daily" }],
  "bookmarks": [
    {
      "id": "bm_001",
      "name": "Outlook",
      "type": "program",
      "target": "C:\\Program Files\\...\\OUTLOOK.EXE",
      "note": "Main work email client",
      "category_ids": ["cat_001"],
      "tag_ids": ["tag_001"],
      "click_count": 47,
      "created_at": "2026-05-05T10:00:00",
      "last_used_at": "2026-05-05T14:23:00",
      "order": 0
    }
  ],
  "sequences": [
    {
      "id": "seq_001",
      "name": "Work start",
      "note": "Daily morning routine",
      "items": [
        { "type": "bookmark", "ref_id": "bm_001" }
      ],
      "created_at": "2026-05-05T10:00:00",
      "order": 0
    }
  ]
}
```

Bookmark types: `program`, `file`, `folder`, `url`, `network`

Sequences can reference other sequences (`"type": "sequence"`).
Cycle detection runs before any sequence is saved or launched.

## Building the distribution

### Additional build dependency

Pillow is needed only on the build machine (for PNG → ICO conversion):

```bat
pip install pillow
```

### Build

```bat
build.bat
```

The script:
1. Converts `icon.png` to `icon.ico`
2. Runs PyInstaller using `bookmark_launcher.spec`
3. Copies the result to `C:\Users\Ela\Documents\Projects\bookmark_launcher_dist\`
4. Copies `bookmarks.json` to the dist folder if it doesn't already exist there (preserves user data on rebuild)

Output directory is set at the top of `build.bat`:

```bat
set OUTPUT_DIR=C:\Users\Ela\Documents\Projects\bookmark_launcher_dist
```

Change this line if you want the dist to land somewhere else.

### What goes into dist

```
bookmark_launcher_dist/
├── bookmark_launcher.exe
├── bookmarks.json
└── _internal/              ← PyInstaller dependencies, do not modify
```

To distribute: zip the entire `bookmark_launcher_dist` folder and send it.

### Clean build

To force a full rebuild from scratch (clears PyInstaller cache):

```bat
rmdir /s /q build
rmdir /s /q dist
build.bat
```

## Dependencies

| Package | Purpose |
|---------|---------|
| PySide6 | GUI framework (Qt for Python) |
| PyInstaller | Packaging to standalone exe |
| Pillow | PNG → ICO conversion at build time only |

All listed in `requirements.txt`.

## Code style

- **Level B1** — simple, readable, no unnecessary abstraction
- Comments in English, only where they explain *why* (not *what*)
- Type hints: yes, but readable (`list[Bookmark]`, `Optional[str]`)
- Dataclasses for data models
- Functions under ~30 lines; split if they grow
- No docstrings on trivial functions
- Catch specific exceptions, not bare `Exception`
- Constants and paths in `config.py`, never hardcoded inline

## Known limitations (deferred to v2)

- No global hotkey
- No per-bookmark custom icons
- No delays between sequence items
- No dead link checker
- No per-URL browser selection
- No virtual desktop support in sequences

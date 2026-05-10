# Bookmark Launcher

A desktop launcher for programs, files, folders, and URLs — all in one place.
No installation required, no admin rights needed.

## What it does

- Launch programs, open files, folders, network paths (UNC), and URLs from a single window
- Organize bookmarks into categories and tag them
- Add short notes that appear as tooltips on hover
- Group bookmarks into sequences — one click starts everything at once (e.g. "Work start" opens browser, Outlook, and Teams)
- Search across names, paths, notes, and tags in real time
- Sits quietly in the system tray when you close the window

## Requirements

- Windows 10 or 11
- No Python, no installation, no admin rights

## Getting started

1. Unzip the archive to any folder (Desktop, Documents, USB drive — anywhere)
2. Run `bookmark_launcher.exe`
3. The app creates `bookmarks.json` next to the exe on first run — this is your data file

> Keep `bookmark_launcher.exe`, `_internal\`, and `bookmarks.json` together in the same folder.
> Moving just the exe will break the app.

## Adding bookmarks

Click **+ Add** in the top-right corner or drag and drop a file, folder, or shortcut from Explorer onto the window.

Supported types:

| Type | Example |
|------|---------|
| Program | `C:\Program Files\...\outlook.exe` |
| File | `C:\Reports\Q1_2026.xlsx` |
| Folder | `C:\Projects\Alpha` |
| URL | `https://company.intranet` |
| Network path | `\\server\projects\alpha` |

## Organizing bookmarks

- **Categories** — create categories in the left panel; a bookmark can belong to multiple categories
- **Tags** — short labels visible next to each bookmark in the list
- **Notes** — appear as tooltips when you hover over a bookmark

## Sequences

A sequence is an ordered list of bookmarks (and other sequences) that all launch together.

To create one: click **⚙ → Manage Sequences**, then add items.
To run one: click its name in the left panel, or use the tray menu.

Sequences can be nested — a sequence can include another sequence.

## System tray

- **Left click** — show or hide the window
- **Right click** — quick menu with your most-used bookmarks and sequences

The app stays running in the tray when you close the window.
To exit completely: right-click the tray icon → **Quit**.

## Search

Type anything in the search bar at the top. The list filters instantly across:
- Bookmark name
- Target path
- Note text
- Tags

## Sorting

Right-click the bookmark list or use the sort menu to switch between:
- **Manual** — drag and drop to reorder
- **Alphabetical**
- **Most used** — sorted by launch count
- **Recently used** — sorted by last launch time

## Import / Export

Use **⚙ → Import / Export** to:
- Export selected bookmarks to a JSON file (share with a colleague)
- Import bookmarks from a file (duplicates are handled gracefully)

## Your data

Everything is stored in `bookmarks.json` next to the exe.
To back up your bookmarks: copy that file somewhere safe.
To move to a new machine: copy the entire folder.

---

*Bookmark Launcher v0.1.0 — Marek Kucmierz, in consultation with Claude*

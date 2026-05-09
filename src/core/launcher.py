"""
Launcher: opens bookmarks and runs sequences.
No Qt dependency — pure Python, easy to test.
"""

import subprocess
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.data_store import DataStore
    from core.models import Bookmark, Sequence


def launch_bookmark(bm: "Bookmark") -> None:
    """Open a single bookmark based on its type."""
    match bm.type:
        case "program":
            _open_program(bm.target)
        case "file":
            _open_path(bm.target)
        case "folder":
            _open_path(bm.target)
        case "url":
            _open_url(bm.target)
        case "network":
            _open_path(bm.target)
        case _:
            raise ValueError(f"Unknown bookmark type: {bm.type!r}")


def launch_sequence(seq: "Sequence", store: "DataStore") -> list[str]:
    """
    Run all items in a sequence (bookmarks and nested sequences).
    Returns a list of error messages for items that failed to launch.
    Cycles must be checked before calling this — we don't re-check here.
    """
    errors: list[str] = []
    _run_sequence(seq, store, visited=set(), errors=errors)
    return errors


# ── Private helpers ──────────────────────────────────────────────────


def _open_program(target: str) -> None:
    # Use Popen so we don't wait for the program to exit.
    # shell=False is safer; works for absolute paths and plain exe names.
    try:
        subprocess.Popen([target])
    except FileNotFoundError:
        raise FileNotFoundError(f"Program not found: {target!r}")
    except OSError as e:
        raise OSError(f"Could not launch {target!r}: {e}") from e


def _open_path(target: str) -> None:
    path = Path(target)

    # UNC paths (\\server\share) are valid on Windows but Path.exists()
    # can be slow for unreachable network shares — we try anyway.
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {target!r}")

    # os.startfile is Windows-only; fall back to xdg-open on Linux/macOS
    try:
        import os
        os.startfile(str(path))  # type: ignore[attr-defined]
    except AttributeError:
        subprocess.Popen(["xdg-open", str(path)])
    except OSError as e:
        raise OSError(f"Could not open {target!r}: {e}") from e


def _open_url(target: str) -> None:
    # Ensure the string looks like a URL so the browser opens it correctly.
    url = target if "://" in target else f"https://{target}"
    webbrowser.open(url)


def _run_sequence(
    seq: "Sequence",
    store: "DataStore",
    visited: set[str],
    errors: list[str],
) -> None:
    """Recursive helper — visited guards against cycles at runtime."""
    if seq.id in visited:
        return
    visited.add(seq.id)

    for item in seq.items:
        if item.type == "bookmark":
            bm = store.get_bookmark(item.ref_id)
            if bm is None:
                errors.append(f"Bookmark {item.ref_id!r} not found")
                continue
            try:
                launch_bookmark(bm)
                store.record_launch(bm.id)
            except (FileNotFoundError, OSError, ValueError) as e:
                errors.append(str(e))

        elif item.type == "sequence":
            sub = store.get_sequence(item.ref_id)
            if sub is None:
                errors.append(f"Sequence {item.ref_id!r} not found")
                continue
            _run_sequence(sub, store, visited, errors)
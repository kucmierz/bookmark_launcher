"""
Validation helpers for bookmark fields.
Each function returns (is_valid, error_message).
"""

from pathlib import Path
from config import BOOKMARK_TYPES


def validate_name(name: str) -> tuple[bool, str]:
    if not name.strip():
        return False, "Name cannot be empty."
    if len(name.strip()) > 200:
        return False, "Name is too long (max 200 characters)."
    return True, ""


def validate_target(target: str, bm_type: str) -> tuple[bool, str]:
    if not target.strip():
        return False, "Target cannot be empty."

    if bm_type == "url":
        if not ("." in target or "://" in target or target == "localhost"):
            return False, "URL doesn't look valid (missing domain or scheme)."
        return True, ""

    if bm_type == "network":
        if not target.startswith("\\\\"):
            return False, "Network path must start with \\\\ (UNC format)."
        return True, ""

    # program / file / folder — path must exist
    path = Path(target)
    if not path.exists():
        return False, f"Path not found:\n{target}"

    if bm_type == "folder" and not path.is_dir():
        return False, "Target must be a folder."

    if bm_type == "file" and not path.is_file():
        return False, "Target must be a file."

    if bm_type == "program" and not path.is_file():
        return False, "Program target must be a file (.exe)."

    return True, ""


def validate_type(bm_type: str) -> tuple[bool, str]:
    if bm_type not in BOOKMARK_TYPES:
        return False, f"Unknown type: {bm_type!r}"
    return True, ""

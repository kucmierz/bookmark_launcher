"""
Import and export logic for bookmarks.
Export: selected bookmarks + their referenced categories and tags → JSON file.
Import: read JSON file, skip duplicates (same name + target).
"""

import json
from pathlib import Path

from core.models import Bookmark, Category, Tag
from core.data_store import DataStore


def export_bookmarks(bookmarks: list[Bookmark], store: DataStore, dest_path: Path) -> None:
    """Write selected bookmarks (+ their categories and tags) to a JSON file."""
    cat_ids = {cid for bm in bookmarks for cid in bm.category_ids}
    tag_ids = {tid for bm in bookmarks for tid in bm.tag_ids}

    categories = [c for c in store.get_categories() if c.id in cat_ids]
    tags = [t for t in store.get_tags() if t.id in tag_ids]

    payload = {
        "version": 1,
        "categories": [
            {"id": c.id, "name": c.name, "color": c.color, "order": c.order}
            for c in categories
        ],
        "tags": [
            {"id": t.id, "name": t.name} for t in tags
        ],
        "bookmarks": [_bookmark_to_dict(bm) for bm in bookmarks],
    }

    dest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

# ── Result type ──────────────────────────────────────────────────────


class ImportResult:
    def __init__(self, imported: int, skipped: int) -> None:
        self.imported = imported
        self.skipped = skipped

    def summary(self) -> str:
        parts = [f"{self.imported} bookmark(s) imported"]
        if self.skipped:
            parts.append(f"{self.skipped} skipped (already exist)")
        return ", ".join(parts) + "."

def import_bookmarks(source_path: Path, store: DataStore) -> ImportResult:
    """
    Read bookmarks from a JSON file and add non-duplicates to the store.
    A duplicate is a bookmark with the same name AND target as an existing one.
    Returns an ImportResult with counts.
    """
    try:
        raw = source_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"Could not read import file: {e}") from e

    if "bookmarks" not in data:
        raise ValueError("File does not look like a Bookmark Launcher export.")

    # Merge categories — match by name, create if missing
    cat_id_map = _merge_categories(data.get("categories", []), store)

    # Merge tags — match by name, create if missing
    tag_id_map = _merge_tags(data.get("tags", []), store)

    existing = {(b.name, b.target) for b in store.get_bookmarks()}

    imported = 0
    skipped = 0

    for bm_dict in data.get("bookmarks", []):
        name = bm_dict.get("name", "")
        target = bm_dict.get("target", "")

        if (name, target) in existing:
            skipped += 1
            continue

        bm = _bookmark_from_dict(bm_dict, cat_id_map, tag_id_map)
        store.add_bookmark(bm)
        existing.add((name, target))
        imported += 1

    return ImportResult(imported=imported, skipped=skipped)


# ── Private helpers ──────────────────────────────────────────────────


def _merge_categories(raw_cats: list[dict], store: DataStore) -> dict[str, str]:
    """Return mapping old_id → new_id. Creates category if name not found."""
    name_to_id = {c.name: c.id for c in store.get_categories()}
    id_map: dict[str, str] = {}

    for raw in raw_cats:
        old_id = raw["id"]
        name = raw["name"]
        if name in name_to_id:
            id_map[old_id] = name_to_id[name]
        else:
            new_cat = Category(id="", name=name, color=raw.get("color", "#6B7280"), order=0)
            store.add_category(new_cat)
            id_map[old_id] = new_cat.id
            name_to_id[name] = new_cat.id

    return id_map


def _merge_tags(raw_tags: list[dict], store: DataStore) -> dict[str, str]:
    """Return mapping old_id → new_id. Creates tag if name not found."""
    name_to_id = {t.name: t.id for t in store.get_tags()}
    id_map: dict[str, str] = {}

    for raw in raw_tags:
        old_id = raw["id"]
        name = raw["name"]
        if name in name_to_id:
            id_map[old_id] = name_to_id[name]
        else:
            from core.models import Tag
            new_tag = Tag(id="", name=name)
            store.add_tag(new_tag)
            id_map[old_id] = new_tag.id
            name_to_id[name] = new_tag.id

    return id_map


def _bookmark_to_dict(bm: Bookmark) -> dict:
    return {
        "name": bm.name,
        "type": bm.type,
        "target": bm.target,
        "note": bm.note,
        "category_ids": bm.category_ids,
        "tag_ids": bm.tag_ids,
        "click_count": bm.click_count,
        "order": bm.order,
    }


def _bookmark_from_dict(
    d: dict,
    cat_id_map: dict[str, str],
    tag_id_map: dict[str, str],
) -> Bookmark:
    from core.models import Bookmark
    return Bookmark(
        id="",  # store.add_bookmark() assigns a real id
        name=d.get("name", ""),
        type=d.get("type", "file"),
        target=d.get("target", ""),
        note=d.get("note", ""),
        category_ids=[cat_id_map[c] for c in d.get("category_ids", []) if c in cat_id_map],
        tag_ids=[tag_id_map[t] for t in d.get("tag_ids", []) if t in tag_id_map],
        click_count=d.get("click_count", 0),
        order=d.get("order", 0),
    )
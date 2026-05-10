"""
DataStore: single source of truth for all app data.
Loads from / saves to bookmarks.json.
All CRUD operations live here; UI never touches the file directly.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.models import (
    AppData, Settings,
    Category, Tag, Bookmark, Sequence, SequenceItem,
)

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


# ── Serialization helpers ────────────────────────────────────────────


def _dt_to_str(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime(DATETIME_FORMAT) if dt else None


def _str_to_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s, DATETIME_FORMAT)
    except ValueError:
        return None


def _bookmark_to_dict(bm: Bookmark) -> dict:
    return {
        "id": bm.id,
        "name": bm.name,
        "type": bm.type,
        "target": bm.target,
        "note": bm.note,
        "category_ids": bm.category_ids,
        "tag_ids": bm.tag_ids,
        "click_count": bm.click_count,
        "created_at": _dt_to_str(bm.created_at),
        "last_used_at": _dt_to_str(bm.last_used_at),
        "order": bm.order,
    }


def _bookmark_from_dict(d: dict) -> Bookmark:
    return Bookmark(
        id=d["id"],
        name=d["name"],
        type=d["type"],
        target=d["target"],
        note=d.get("note", ""),
        category_ids=d.get("category_ids", []),
        tag_ids=d.get("tag_ids", []),
        click_count=d.get("click_count", 0),
        created_at=_str_to_dt(d.get("created_at")) or datetime.now(),
        last_used_at=_str_to_dt(d.get("last_used_at")),
        order=d.get("order", 0),
    )


def _sequence_to_dict(seq: Sequence) -> dict:
    return {
        "id": seq.id,
        "name": seq.name,
        "note": seq.note,
        "items": [{"type": i.type, "ref_id": i.ref_id} for i in seq.items],
        "created_at": _dt_to_str(seq.created_at),
        "order": seq.order,
    }


def _sequence_from_dict(d: dict) -> Sequence:
    items = [SequenceItem(type=i["type"], ref_id=i["ref_id"]) for i in d.get("items", [])]
    return Sequence(
        id=d["id"],
        name=d["name"],
        note=d.get("note", ""),
        items=items,
        created_at=_str_to_dt(d.get("created_at")) or datetime.now(),
        order=d.get("order", 0),
    )


def _appdata_to_dict(data: AppData) -> dict:
    return {
        "version": data.version,
        "settings": {
            "sort_order": data.settings.sort_order,
            "show_in_tray": data.settings.show_in_tray,
            "start_minimized": data.settings.start_minimized,
        },
        "categories": [
            {"id": c.id, "name": c.name, "color": c.color, "order": c.order}
            for c in data.categories
        ],
        "tags": [
            {"id": t.id, "name": t.name} for t in data.tags
        ],
        "bookmarks": [_bookmark_to_dict(bm) for bm in data.bookmarks],
        "sequences": [_sequence_to_dict(s) for s in data.sequences],
    }


def _appdata_from_dict(d: dict) -> AppData:
    s = d.get("settings", {})
    settings = Settings(
        sort_order=s.get("sort_order", "manual"),
        show_in_tray=s.get("show_in_tray", True),
        start_minimized=s.get("start_minimized", False),
    )
    categories = [
        Category(id=c["id"], name=c["name"], color=c.get("color", "#6B7280"), order=c.get("order", 0))
        for c in d.get("categories", [])
    ]
    tags = [Tag(id=t["id"], name=t["name"]) for t in d.get("tags", [])]
    bookmarks = [_bookmark_from_dict(b) for b in d.get("bookmarks", [])]
    sequences = [_sequence_from_dict(s) for s in d.get("sequences", [])]

    return AppData(
        version=d.get("version", 1),
        settings=settings,
        categories=categories,
        tags=tags,
        bookmarks=bookmarks,
        sequences=sequences,
    )


# ── ID generation ────────────────────────────────────────────────────


def _new_id(prefix: str) -> str:
    """Short unique ID like 'bm_a3f2c1d0'."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── DataStore ────────────────────────────────────────────────────────


class DataStore:
    """
    Wraps AppData with load/save and CRUD methods.
    Call load() once at startup. Call save() after every mutation.
    """

    def __init__(self, filepath: Path) -> None:
        self._filepath = filepath
        self.data = AppData()

    # ── Persistence ──────────────────────────────────────────────────

    def load(self) -> None:
        """Load data from file. Creates a new empty file if missing."""
        if not self._filepath.exists():
            self.save()  # write defaults
            return
        try:
            raw = self._filepath.read_text(encoding="utf-8")
            self.data = _appdata_from_dict(json.loads(raw))
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Failed to parse {self._filepath}: {e}") from e

    def save(self) -> None:
        """Write current data to file (pretty-printed for human readability)."""
        self._filepath.write_text(
            json.dumps(_appdata_to_dict(self.data), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ── Bookmarks ────────────────────────────────────────────────────

    def get_bookmarks(self, category_id: Optional[str] = None) -> list[Bookmark]:
        """Return bookmarks, optionally filtered by category, sorted by current setting."""
        bms = self.data.bookmarks
        if category_id:
            bms = [b for b in bms if category_id in b.category_ids]

        match self.data.settings.sort_order:
            case "alphabetical":
                bms = sorted(bms, key=lambda b: b.name.lower())
            case "by_last_used":
                # Bookmarks never used go to the bottom
                bms = sorted(bms, key=lambda b: b.last_used_at or datetime.min, reverse=True)
            case _:
                # "manual" — respect the order field
                bms = sorted(bms, key=lambda b: b.order)

        return bms

    def get_bookmark(self, bm_id: str) -> Optional[Bookmark]:
        return next((b for b in self.data.bookmarks if b.id == bm_id), None)

    def add_bookmark(self, bm: Bookmark) -> Bookmark:
        bm.id = _new_id("bm")
        bm.created_at = datetime.now()
        bm.order = len(self.data.bookmarks)
        self.data.bookmarks.append(bm)
        self.save()
        return bm

    def update_bookmark(self, bm: Bookmark) -> None:
        idx = next((i for i, b in enumerate(self.data.bookmarks) if b.id == bm.id), None)
        if idx is None:
            raise ValueError(f"Bookmark not found: {bm.id}")
        self.data.bookmarks[idx] = bm
        self.save()

    def delete_bookmark(self, bm_id: str) -> None:
        self.data.bookmarks = [b for b in self.data.bookmarks if b.id != bm_id]
        # Remove references from sequences
        for seq in self.data.sequences:
            seq.items = [i for i in seq.items if not (i.type == "bookmark" and i.ref_id == bm_id)]
        self.save()

    def record_launch(self, bm_id: str) -> None:
        """Increment click_count and update last_used_at."""
        bm = self.get_bookmark(bm_id)
        if bm:
            bm.click_count += 1
            bm.last_used_at = datetime.now()
            self.save()

    # ── Categories ───────────────────────────────────────────────────

    def get_categories(self) -> list[Category]:
        return list(self.data.categories)

    def get_category(self, cat_id: str) -> Optional[Category]:
        return next((c for c in self.data.categories if c.id == cat_id), None)

    def add_category(self, cat: Category) -> Category:
        cat.id = _new_id("cat")
        cat.order = len(self.data.categories)
        self.data.categories.append(cat)
        self.save()
        return cat

    def update_category(self, cat: Category) -> None:
        idx = next((i for i, c in enumerate(self.data.categories) if c.id == cat.id), None)
        if idx is None:
            raise ValueError(f"Category not found: {cat.id}")
        self.data.categories[idx] = cat
        self.save()

    def delete_category(self, cat_id: str) -> None:
        self.data.categories = [c for c in self.data.categories if c.id != cat_id]
        # Remove the category from all bookmarks that reference it
        for bm in self.data.bookmarks:
            bm.category_ids = [c for c in bm.category_ids if c != cat_id]
        self.save()

    # ── Tags ─────────────────────────────────────────────────────────

    def get_tags(self) -> list[Tag]:
        return list(self.data.tags)

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        return next((t for t in self.data.tags if t.id == tag_id), None)

    def add_tag(self, tag: Tag) -> Tag:
        tag.id = _new_id("tag")
        self.data.tags.append(tag)
        self.save()
        return tag

    def update_tag(self, tag: Tag) -> None:
        idx = next((i for i, t in enumerate(self.data.tags) if t.id == tag.id), None)
        if idx is None:
            raise ValueError(f"Tag not found: {tag.id}")
        self.data.tags[idx] = tag
        self.save()

    def delete_tag(self, tag_id: str) -> None:
        self.data.tags = [t for t in self.data.tags if t.id != tag_id]
        for bm in self.data.bookmarks:
            bm.tag_ids = [t for t in bm.tag_ids if t != tag_id]
        self.save()

    # ── Sequences ────────────────────────────────────────────────────

    def get_sequences(self) -> list[Sequence]:
        return list(self.data.sequences)

    def get_sequence(self, seq_id: str) -> Optional[Sequence]:
        return next((s for s in self.data.sequences if s.id == seq_id), None)

    def add_sequence(self, seq: Sequence) -> Sequence:
        seq.id = _new_id("seq")
        seq.created_at = datetime.now()
        seq.order = len(self.data.sequences)
        self.data.sequences.append(seq)
        self.save()
        return seq

    def update_sequence(self, seq: Sequence) -> None:
        idx = next((i for i, s in enumerate(self.data.sequences) if s.id == seq.id), None)
        if idx is None:
            raise ValueError(f"Sequence not found: {seq.id}")
        self.data.sequences[idx] = seq
        self.save()

    def delete_sequence(self, seq_id: str) -> None:
        self.data.sequences = [s for s in self.data.sequences if s.id != seq_id]
        # Remove references from other sequences
        for seq in self.data.sequences:
            seq.items = [i for i in seq.items if not (i.type == "sequence" and i.ref_id == seq_id)]
        self.save()

    def has_cycle(self, seq_id: str, new_item_ref: str) -> bool:
        """
        Return True if adding new_item_ref (a sequence id) to seq_id
        would create a cycle. Uses DFS to detect if seq_id is reachable
        from new_item_ref.
        """
        visited: set[str] = set()

        def reachable(current_id: str) -> bool:
            if current_id == seq_id:
                return True
            if current_id in visited:
                return False
            visited.add(current_id)
            seq = self.get_sequence(current_id)
            if seq is None:
                return False
            for item in seq.items:
                if item.type == "sequence" and reachable(item.ref_id):
                    return True
            return False

        return reachable(new_item_ref)

    # ── Settings ─────────────────────────────────────────────────────

    def save_settings(self, settings: Settings) -> None:
        self.data.settings = settings
        self.save()

    # ── Ordering ─────────────────────────────────────────────────────

    def reorder_bookmarks(self, ordered_ids: list[str]) -> None:
        """Apply a new manual order by list of IDs."""
        index = {bm_id: pos for pos, bm_id in enumerate(ordered_ids)}
        for bm in self.data.bookmarks:
            bm.order = index.get(bm.id, bm.order)
        self.data.bookmarks.sort(key=lambda b: b.order)
        self.save()

    def reorder_categories(self, ordered_ids: list[str]) -> None:
        index = {cat_id: pos for pos, cat_id in enumerate(ordered_ids)}
        for cat in self.data.categories:
            cat.order = index.get(cat.id, cat.order)
        self.data.categories.sort(key=lambda c: c.order)
        self.save()

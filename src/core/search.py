"""
Search / filter logic for bookmarks.
No Qt dependency — pure Python, easy to test.
"""

from core.models import Bookmark, Tag


def filter_bookmarks(
    bookmarks: list[Bookmark],
    query: str,
    tag_map: dict[str, Tag],
) -> list[Bookmark]:
    """
    Return bookmarks matching the query string.
    Matches against: name, target path, note, and tag names.
    Case-insensitive. Empty query returns all bookmarks unchanged.
    """
    q = query.strip().lower()
    if not q:
        return bookmarks

    results = []
    for bm in bookmarks:
        if _matches(bm, q, tag_map):
            results.append(bm)
    return results


def _matches(bm: Bookmark, q: str, tag_map: dict[str, Tag]) -> bool:
    if q in bm.name.lower():
        return True
    if q in bm.target.lower():
        return True
    if bm.note and q in bm.note.lower():
        return True
    for tag_id in bm.tag_ids:
        tag = tag_map.get(tag_id)
        if tag and q in tag.name.lower():
            return True
    return False

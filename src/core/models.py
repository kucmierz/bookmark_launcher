"""
Data models for Bookmark Launcher.
All models are plain dataclasses — no business logic here.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Category:
    id: str
    name: str
    color: str = "#6B7280"  # neutral gray default
    order: int = 0


@dataclass
class Tag:
    id: str
    name: str


@dataclass
class Bookmark:
    id: str
    name: str
    type: str                      # program | file | folder | url | network
    target: str
    note: str = ""
    category_ids: list[str] = field(default_factory=list)
    tag_ids: list[str] = field(default_factory=list)
    click_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    order: int = 0


@dataclass
class SequenceItem:
    type: str                      # bookmark | sequence
    ref_id: str


@dataclass
class Sequence:
    id: str
    name: str
    note: str = ""
    items: list[SequenceItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    order: int = 0


@dataclass
class Settings:
    sort_order: str = "manual"     # manual | alpha | frequency | recent
    show_in_tray: bool = True
    start_minimized: bool = False


@dataclass
class AppData:
    """Everything loaded from / saved to bookmarks.json."""
    version: int = 1
    settings: Settings = field(default_factory=Settings)
    categories: list[Category] = field(default_factory=list)
    tags: list[Tag] = field(default_factory=list)
    bookmarks: list[Bookmark] = field(default_factory=list)
    sequences: list[Sequence] = field(default_factory=list)

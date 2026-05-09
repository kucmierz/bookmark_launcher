"""
BookmarkDialog: modal form for adding and editing bookmarks.
Pass bookmark=None to create a new one, or an existing Bookmark to edit.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QTextEdit, QPushButton,
    QLabel, QFileDialog, QCheckBox, QScrollArea,
    QWidget, QDialogButtonBox, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from core.models import Bookmark, Category, Tag
from core.data_store import DataStore
from utils.validators import validate_name, validate_target
from config import BOOKMARK_TYPES


# Human-readable labels for bookmark types shown in the combo box
TYPE_LABELS = {
    "program": "⚙  Program (.exe)",
    "file":    "📄  File",
    "folder":  "📁  Folder",
    "url":     "🌐  URL",
    "network": "🖧  Network path (UNC)",
}

# File dialog filters per type
FILE_FILTERS = {
    "program": "Programs (*.exe *.bat *.cmd *.ps1);;All files (*)",
    "file":    "All files (*)",
}


class BookmarkDialog(QDialog):
    def __init__(
        self,
        store: DataStore,
        bookmark: Bookmark | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.store = store
        self.bookmark = bookmark          # None = new bookmark mode
        self._result_bookmark: Bookmark | None = None

        self.setWindowTitle("Edit Bookmark" if bookmark else "Add Bookmark")
        self.setMinimumWidth(480)
        self.setModal(True)

        self._build_ui()
        self._apply_stylesheet()

        if bookmark:
            self._populate(bookmark)
        else:
            # Sensible default
            self.type_combo.setCurrentIndex(0)
            self._on_type_changed(0)

    # ── Result ────────────────────────────────────────────────────────

    @property
    def result_bookmark(self) -> Bookmark | None:
        """The saved/updated Bookmark, or None if dialog was cancelled."""
        return self._result_bookmark

    # ── UI construction ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Outlook")
        form.addRow("Name:", self.name_edit)

        # Type
        self.type_combo = QComboBox()
        for key in BOOKMARK_TYPES:
            self.type_combo.addItem(TYPE_LABELS[key], userData=key)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Type:", self.type_combo)

        # Target + Browse button
        target_row = QHBoxLayout()
        target_row.setSpacing(6)
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Path or URL")
        target_row.addWidget(self.target_edit)
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self._browse)
        target_row.addWidget(self.browse_btn)
        form.addRow("Target:", target_row)

        # Note
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Short description (shown as tooltip)")
        self.note_edit.setFixedHeight(60)
        self.note_edit.setAcceptRichText(False)
        form.addRow("Note:", self.note_edit)

        layout.addLayout(form)

        # ── Categories ────────────────────────────────────────────────
        layout.addWidget(self._divider("Categories"))
        self.cat_checks: dict[str, QCheckBox] = {}
        cat_widget = self._build_checklist(
            items=[(c.id, c.name, c.color) for c in self.store.get_categories()],
            checks_dict=self.cat_checks,
            empty_text="No categories yet — add one first.",
        )
        layout.addWidget(cat_widget)

        # ── Tags ──────────────────────────────────────────────────────
        layout.addWidget(self._divider("Tags"))
        self.tag_checks: dict[str, QCheckBox] = {}
        tag_widget = self._build_checklist(
            items=[(t.id, t.name, None) for t in self.store.get_tags()],
            checks_dict=self.tag_checks,
            empty_text="No tags yet — add one first.",
        )
        layout.addWidget(tag_widget)

        # ── Error label ───────────────────────────────────────────────
        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        # ── Buttons ───────────────────────────────────────────────────
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_checklist(
        self,
        items: list[tuple[str, str, str | None]],
        checks_dict: dict[str, QCheckBox],
        empty_text: str,
    ) -> QWidget:
        """Build a scrollable list of checkboxes. items = (id, label, color|None)."""
        container = QWidget()
        container.setObjectName("CheckContainer")
        inner = QVBoxLayout(container)
        inner.setContentsMargins(8, 4, 8, 4)
        inner.setSpacing(2)

        if not items:
            lbl = QLabel(empty_text)
            lbl.setObjectName("PlaceholderLabel")
            inner.addWidget(lbl)
        else:
            for item_id, label, color in items:
                cb = QCheckBox(label)
                if color:
                    cb.setStyleSheet(f"color: {color};")
                checks_dict[item_id] = cb
                inner.addWidget(cb)

        return container

    def _divider(self, title: str) -> QLabel:
        lbl = QLabel(title.upper())
        lbl.setObjectName("SectionLabel")
        return lbl

    # ── Populate (edit mode) ──────────────────────────────────────────

    def _populate(self, bm: Bookmark) -> None:
        self.name_edit.setText(bm.name)
        self.target_edit.setText(bm.target)
        self.note_edit.setPlainText(bm.note)

        # Set type combo
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == bm.type:
                self.type_combo.setCurrentIndex(i)
                break

        self._on_type_changed(self.type_combo.currentIndex())

        for cat_id, cb in self.cat_checks.items():
            cb.setChecked(cat_id in bm.category_ids)

        for tag_id, cb in self.tag_checks.items():
            cb.setChecked(tag_id in bm.tag_ids)

    # ── Type change ───────────────────────────────────────────────────

    def _on_type_changed(self, _index: int) -> None:
        bm_type = self.type_combo.currentData()
        is_url = bm_type == "url"
        is_network = bm_type == "network"

        self.browse_btn.setEnabled(not is_url and not is_network)

        if is_url:
            self.target_edit.setPlaceholderText("https://example.com")
        elif is_network:
            self.target_edit.setPlaceholderText("\\\\server\\share\\folder")
        elif bm_type == "folder":
            self.target_edit.setPlaceholderText("C:\\path\\to\\folder")
        elif bm_type == "program":
            self.target_edit.setPlaceholderText("C:\\path\\to\\app.exe")
        else:
            self.target_edit.setPlaceholderText("C:\\path\\to\\file.txt")

    # ── Browse ────────────────────────────────────────────────────────

    def _browse(self) -> None:
        bm_type = self.type_combo.currentData()

        if bm_type == "folder":
            path = QFileDialog.getExistingDirectory(self, "Select folder")
        else:
            file_filter = FILE_FILTERS.get(bm_type, "All files (*)")
            path, _ = QFileDialog.getOpenFileName(self, "Select file", "", file_filter)

        if path:
            self.target_edit.setText(path)
            # Auto-fill name from filename if name field is still empty
            if not self.name_edit.text().strip():
                self.name_edit.setText(Path(path).stem.replace("_", " ").title())

    # ── Save & validate ───────────────────────────────────────────────

    def _save(self) -> None:
        name = self.name_edit.text().strip()
        target = self.target_edit.text().strip()
        bm_type = self.type_combo.currentData()

        ok, msg = validate_name(name)
        if not ok:
            self._show_error(msg)
            return

        ok, msg = validate_target(target, bm_type)
        if not ok:
            self._show_error(msg)
            return

        self.error_label.hide()

        category_ids = [cid for cid, cb in self.cat_checks.items() if cb.isChecked()]
        tag_ids = [tid for tid, cb in self.tag_checks.items() if cb.isChecked()]

        if self.bookmark:
            # Edit mode — mutate existing object
            bm = self.bookmark
            bm.name = name
            bm.type = bm_type
            bm.target = target
            bm.note = self.note_edit.toPlainText().strip()
            bm.category_ids = category_ids
            bm.tag_ids = tag_ids
            self.store.update_bookmark(bm)
            self._result_bookmark = bm
        else:
            # Add mode — create new
            bm = Bookmark(
                id="",         # assigned by store
                name=name,
                type=bm_type,
                target=target,
                note=self.note_edit.toPlainText().strip(),
                category_ids=category_ids,
                tag_ids=tag_ids,
            )
            self._result_bookmark = self.store.add_bookmark(bm)

        self.accept()

    def _show_error(self, message: str) -> None:
        self.error_label.setText(f"⚠  {message}")
        self.error_label.show()

    # ── Stylesheet ────────────────────────────────────────────────────

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QFormLayout QLabel {
                color: #a6adc8;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #89b4fa;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                color: #cdd6f4;
                selection-background-color: #45475a;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px 12px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:disabled {
                color: #585b70;
            }
            QDialogButtonBox QPushButton[text="Save"] {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                font-weight: bold;
            }
            QDialogButtonBox QPushButton[text="Save"]:hover {
                background-color: #b4befe;
            }
            QCheckBox {
                color: #cdd6f4;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #45475a;
                background: #313244;
            }
            QCheckBox::indicator:checked {
                background-color: #89b4fa;
                border-color: #89b4fa;
            }
            QLabel#SectionLabel {
                color: #6c7086;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                margin-top: 4px;
            }
            QLabel#ErrorLabel {
                color: #f38ba8;
                background-color: #302030;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QLabel#PlaceholderLabel {
                color: #585b70;
            }
            QWidget#CheckContainer {
                background-color: #181825;
                border-radius: 6px;
                border: 1px solid #313244;
            }
        """)

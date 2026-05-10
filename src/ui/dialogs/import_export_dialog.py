"""
Two dialogs for import and export of bookmarks.
ExportDialog: checklist of bookmarks to export, saves to JSON file.
ImportDialog: picks a JSON file, shows preview, confirms import.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QAbstractItemView,
)
from PySide6.QtCore import Qt

from core.data_store import DataStore
from core.importer import export_bookmarks, import_bookmarks

DIALOG_STYLE = """
    QDialog {
        background-color: #1e1e2e;
    }
    QLabel {
        color: #cdd6f4;
    }
    QLabel#HintLabel {
        color: #6c7086;
        font-size: 12px;
    }
    QListWidget {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 6px;
        padding: 4px;
        outline: none;
    }
    QListWidget::item {
        padding: 4px 8px;
        border-radius: 4px;
    }
    QListWidget::item:hover {
        background-color: #45475a;
    }
    QListWidget::item:selected {
        background-color: #45475a;
    }
    QPushButton {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 6px;
        padding: 0 12px;
        min-height: 32px;
    }
    QPushButton:hover {
        background-color: #45475a;
    }
    QPushButton#PrimaryButton {
        background-color: #89b4fa;
        color: #1e1e2e;
        border: none;
        font-weight: bold;
    }
    QPushButton#PrimaryButton:hover {
        background-color: #b4befe;
    }
"""


# ── Export ───────────────────────────────────────────────────────────


class ExportDialog(QDialog):
    def __init__(self, store: DataStore, parent=None) -> None:
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("Export Bookmarks")
        self.setMinimumSize(420, 480)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("Select bookmarks to export:"))

        hint = QLabel("All selected bookmarks will be saved to a JSON file,\n"
                      "including their categories and tags.")
        hint.setObjectName("HintLabel")
        layout.addWidget(hint)

        # Select all / none buttons
        sel_layout = QHBoxLayout()
        self.btn_all = QPushButton("Select all")
        self.btn_none = QPushButton("Select none")
        self.btn_all.setFixedHeight(28)
        self.btn_none.setFixedHeight(28)
        self.btn_all.clicked.connect(self._select_all)
        self.btn_none.clicked.connect(self._select_none)
        sel_layout.addWidget(self.btn_all)
        sel_layout.addWidget(self.btn_none)
        sel_layout.addStretch()
        layout.addLayout(sel_layout)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        layout.addWidget(self.list_widget, stretch=1)

        self.count_label = QLabel("")
        self.count_label.setObjectName("HintLabel")
        layout.addWidget(self.count_label)

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.btn_export = QPushButton("Export…")
        self.btn_export.setObjectName("PrimaryButton")
        self.btn_export.clicked.connect(self._on_export)
        btn_layout.addWidget(cancel)
        btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)

    def _populate(self) -> None:
        self.list_widget.clear()
        for bm in self.store.get_bookmarks():
            item = QListWidgetItem(bm.name)
            item.setData(Qt.UserRole, bm.id)
            item.setCheckState(Qt.Checked)
            item.setToolTip(bm.target)
            self.list_widget.addItem(item)
        self._update_count()
        self.list_widget.itemChanged.connect(self._update_count)

    def _select_all(self) -> None:
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)

    def _select_none(self) -> None:
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)

    def _update_count(self) -> None:
        checked = sum(
            1 for i in range(self.list_widget.count())
            if self.list_widget.item(i).checkState() == Qt.Checked
        )
        total = self.list_widget.count()
        self.count_label.setText(f"{checked} of {total} selected")
        self.btn_export.setEnabled(checked > 0)

    def _on_export(self) -> None:
        selected_ids = {
            self.list_widget.item(i).data(Qt.UserRole)
            for i in range(self.list_widget.count())
            if self.list_widget.item(i).checkState() == Qt.Checked
        }

        bookmarks = [b for b in self.store.get_bookmarks() if b.id in selected_ids]

        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Export bookmarks",
            "bookmarks_export.json",
            "JSON files (*.json)",
        )
        if not dest:
            return

        try:
            export_bookmarks(bookmarks, self.store, Path(dest))
            QMessageBox.information(
                self,
                "Export complete",
                f"Exported {len(bookmarks)} bookmark(s) to:\n{dest}",
            )
            self.accept()
        except OSError as e:
            QMessageBox.critical(self, "Export failed", str(e))


# ── Import ───────────────────────────────────────────────────────────


class ImportDialog(QDialog):
    def __init__(self, store: DataStore, parent=None) -> None:
        super().__init__(parent)
        self.store = store
        self._source_path: Path | None = None
        self._preview_bookmarks: list[dict] = []

        self.setWindowTitle("Import Bookmarks")
        self.setMinimumSize(420, 400)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # File picker row
        file_layout = QHBoxLayout()
        self.path_label = QLabel("No file selected")
        self.path_label.setObjectName("HintLabel")
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedHeight(32)
        browse_btn.clicked.connect(self._on_browse)
        file_layout.addWidget(self.path_label, stretch=1)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        # Preview list
        layout.addWidget(QLabel("Bookmarks in file:"))
        self.preview_list = QListWidget()
        self.preview_list.setSelectionMode(QAbstractItemView.NoSelection)
        layout.addWidget(self.preview_list, stretch=1)

        self.status_label = QLabel("")
        self.status_label.setObjectName("HintLabel")
        layout.addWidget(self.status_label)

        hint = QLabel("Bookmarks with the same name and target as existing ones\n"
                      "will be skipped automatically.")
        hint.setObjectName("HintLabel")
        layout.addWidget(hint)

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.btn_import = QPushButton("Import")
        self.btn_import.setObjectName("PrimaryButton")
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self._on_import)
        btn_layout.addWidget(cancel)
        btn_layout.addWidget(self.btn_import)
        layout.addLayout(btn_layout)

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select export file",
            "",
            "JSON files (*.json)",
        )
        if not path:
            return

        self._source_path = Path(path)
        self.path_label.setText(self._source_path.name)
        self._load_preview()

    def _load_preview(self) -> None:
        import json

        self.preview_list.clear()
        self.btn_import.setEnabled(False)

        if self._source_path is None:
            return

        try:
            raw = self._source_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as e:
            self.status_label.setText(f"Could not read file: {e}")
            return

        if "bookmarks" not in data:
            self.status_label.setText("File does not look like a Bookmark Launcher export.")
            return

        existing = {(b.name, b.target) for b in self.store.get_bookmarks()}
        new_count = 0

        for bm_dict in data.get("bookmarks", []):
            name = bm_dict.get("name", "—")
            target = bm_dict.get("target", "")
            is_duplicate = (name, target) in existing

            item = QListWidgetItem(name)
            item.setToolTip(target)
            if is_duplicate:
                item.setText(f"{name}  [skip — already exists]")
                item.setForeground(Qt.gray)
            else:
                new_count += 1
            self.preview_list.addItem(item)

        total = len(data.get("bookmarks", []))
        skipped = total - new_count
        self.status_label.setText(
            f"{total} bookmark(s) in file — {new_count} new, {skipped} will be skipped"
        )
        self.btn_import.setEnabled(new_count > 0)

    def _on_import(self) -> None:
        if self._source_path is None:
            return
        try:
            result = import_bookmarks(self._source_path, self.store)
            QMessageBox.information(self, "Import complete", result.summary())
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Import failed", str(e))
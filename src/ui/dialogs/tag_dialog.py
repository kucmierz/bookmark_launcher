"""
TagDialog: small modal for adding and editing tags.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QLabel, QWidget,
)
from PySide6.QtCore import Qt

from core.models import Tag
from core.data_store import DataStore


class TagDialog(QDialog):
    def __init__(
        self,
        store: DataStore,
        tag: Tag | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.store = store
        self.tag = tag
        self._result_tag: Tag | None = None

        self.setWindowTitle("Edit Tag" if tag else "Add Tag")
        self.setMinimumWidth(300)
        self.setModal(True)

        self._build_ui()
        self._apply_stylesheet()

        if tag:
            self.name_edit.setText(tag.name)

    @property
    def result_tag(self) -> Tag | None:
        return self._result_tag

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. daily, dev, personal")
        form.addRow("Name:", self.name_edit)
        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            self.error_label.setText("⚠  Tag name cannot be empty.")
            self.error_label.show()
            return

        # Check for duplicate name (excluding self in edit mode)
        existing = [t for t in self.store.get_tags() if t.name.lower() == name.lower()]
        if existing and (self.tag is None or existing[0].id != self.tag.id):
            self.error_label.setText(f"⚠  Tag \"{name}\" already exists.")
            self.error_label.show()
            return

        self.error_label.hide()

        if self.tag:
            self.tag.name = name
            self.store.update_tag(self.tag)
            self._result_tag = self.tag
        else:
            new_tag = Tag(id="", name=name)
            self._result_tag = self.store.add_tag(new_tag)

        self.accept()

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #a6adc8;
            }
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px 8px;
                min-height: 28px;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
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
            QDialogButtonBox QPushButton[text="Save"] {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                font-weight: bold;
            }
            QDialogButtonBox QPushButton[text="Save"]:hover {
                background-color: #b4befe;
            }
            QLabel#ErrorLabel {
                color: #f38ba8;
                background-color: #302030;
                border-radius: 6px;
                padding: 6px 10px;
            }
        """)

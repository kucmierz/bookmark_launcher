"""
CategoryDialog: modal form for adding and editing categories.
Includes a simple color picker for the category accent color.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLineEdit, QPushButton, QDialogButtonBox,
    QLabel, QWidget, QColorDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from core.models import Category
from core.data_store import DataStore

# Preset palette — quick picks shown as color swatches
COLOR_PRESETS = [
    "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
    "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16",
]


class CategoryDialog(QDialog):
    def __init__(
        self,
        store: DataStore,
        category: Category | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.store = store
        self.category = category
        self._color = category.color if category else COLOR_PRESETS[0]

        self.setWindowTitle("Edit Category" if category else "Add Category")
        self.setMinimumWidth(340)
        self.setModal(True)

        self._build_ui()
        self._apply_stylesheet()

        if category:
            self.name_edit.setText(category.name)
            self._set_color(category.color)

    # ── UI ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Work tools")
        form.addRow("Name:", self.name_edit)
        layout.addLayout(form)

        # Color row: presets + custom picker button
        layout.addWidget(QLabel("Color:"))
        color_row = QHBoxLayout()
        color_row.setSpacing(6)

        self._swatch_buttons: list[QPushButton] = []
        for hex_color in COLOR_PRESETS:
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setProperty("colorHex", hex_color)
            btn.setStyleSheet(self._swatch_style(hex_color))
            btn.clicked.connect(lambda checked, c=hex_color: self._set_color(c))
            color_row.addWidget(btn)
            self._swatch_buttons.append(btn)

        color_row.addStretch()

        self.custom_btn = QPushButton("Custom…")
        self.custom_btn.setFixedHeight(24)
        self.custom_btn.clicked.connect(self._pick_custom_color)
        color_row.addWidget(self.custom_btn)

        layout.addLayout(color_row)

        # Preview label showing chosen color
        self.preview_label = QLabel()
        self.preview_label.setFixedHeight(6)
        self.preview_label.setStyleSheet(f"background: {self._color}; border-radius: 3px;")
        layout.addWidget(self.preview_label)

        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ── Color helpers ─────────────────────────────────────────────────

    def _set_color(self, hex_color: str) -> None:
        self._color = hex_color
        self.preview_label.setStyleSheet(
            f"background: {hex_color}; border-radius: 3px;"
        )

    def _pick_custom_color(self) -> None:
        color = QColorDialog.getColor(QColor(self._color), self, "Pick color")
        if color.isValid():
            self._set_color(color.name())

    def _swatch_style(self, hex_color: str) -> str:
        return (
            f"QPushButton {{ background-color: {hex_color}; border: 2px solid transparent; "
            f"border-radius: 4px; }}"
            f"QPushButton:hover {{ border-color: #cdd6f4; }}"
        )

    # ── Save ──────────────────────────────────────────────────────────

    def _save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            self.error_label.setText("⚠  Category name cannot be empty.")
            self.error_label.show()
            return

        # Duplicate check
        existing = [c for c in self.store.get_categories() if c.name.lower() == name.lower()]
        if existing and (self.category is None or existing[0].id != self.category.id):
            self.error_label.setText(f"⚠  Category \"{name}\" already exists.")
            self.error_label.show()
            return

        self.error_label.hide()

        if self.category:
            self.category.name = name
            self.category.color = self._color
            self.store.update_category(self.category)
        else:
            from core.models import Category
            self.store.add_category(Category(id="", name=name, color=self._color))

        self.accept()

    # ── Stylesheet ────────────────────────────────────────────────────

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }
            QLabel { color: #a6adc8; }
            QLineEdit {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                padding: 4px 8px; min-height: 28px;
            }
            QLineEdit:focus { border-color: #89b4fa; }
            QPushButton {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                padding: 4px 12px; min-height: 28px;
            }
            QPushButton:hover { background-color: #45475a; }
            QDialogButtonBox QPushButton[text="Save"] {
                background-color: #89b4fa; color: #1e1e2e;
                border: none; font-weight: bold;
            }
            QDialogButtonBox QPushButton[text="Save"]:hover {
                background-color: #b4befe;
            }
            QLabel#ErrorLabel {
                color: #f38ba8; background-color: #302030;
                border-radius: 6px; padding: 6px 10px;
            }
        """)

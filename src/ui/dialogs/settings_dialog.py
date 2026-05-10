"""
Settings dialog — app-wide preferences.
Edits: show_in_tray, start_minimized, sort_order.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QCheckBox, QComboBox, QFrame,
)
from PySide6.QtCore import Qt

from core.data_store import DataStore
from core.models import Settings

SORT_OPTIONS = [
    ("Manual order",  "manual"),
    ("Alphabetical",  "alphabetical"),
    ("Recently used", "by_last_used"),
]

DIALOG_STYLE = """
    QDialog {
        background-color: #1e1e2e;
    }
    QLabel {
        color: #cdd6f4;
    }
    QLabel#SectionLabel {
        color: #6c7086;
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    QFrame#Separator {
        background-color: #313244;
    }
    QCheckBox {
        color: #cdd6f4;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid #45475a;
        background-color: #313244;
    }
    QCheckBox::indicator:checked {
        background-color: #89b4fa;
        border-color: #89b4fa;
    }
    QCheckBox::indicator:hover {
        border-color: #89b4fa;
    }
    QComboBox {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 6px;
        padding: 0 10px;
        min-height: 30px;
    }
    QComboBox:hover {
        border-color: #89b4fa;
    }
    QComboBox::drop-down {
        border: none;
        width: 20px;
    }
    QComboBox QAbstractItemView {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        selection-background-color: #45475a;
        outline: none;
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


class SettingsDialog(QDialog):
    def __init__(self, store: DataStore, parent=None) -> None:
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("Settings")
        self.setMinimumWidth(360)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui()
        self._load_current()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Behaviour section ────────────────────────────────────────
        layout.addWidget(self._section_label("BEHAVIOUR"))

        self.chk_show_in_tray = QCheckBox("Show in system tray")
        self.chk_show_in_tray.setToolTip(
            "Keep the app running in the system tray when the window is closed."
        )
        layout.addWidget(self.chk_show_in_tray)

        self.chk_start_minimized = QCheckBox("Start minimized to tray")
        self.chk_start_minimized.setToolTip(
            "Launch the app without showing the window — only the tray icon appears."
        )
        layout.addWidget(self.chk_start_minimized)

        # Disable start_minimized when tray is off — it would have no effect
        self.chk_show_in_tray.toggled.connect(self._on_tray_toggled)

        layout.addWidget(self._separator())

        # ── Display section ──────────────────────────────────────────
        layout.addWidget(self._section_label("DISPLAY"))

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft)

        self.sort_combo = QComboBox()
        for label, _ in SORT_OPTIONS:
            self.sort_combo.addItem(label)
        form.addRow(QLabel("Default sort order:"), self.sort_combo)
        layout.addLayout(form)

        layout.addStretch()
        layout.addWidget(self._separator())

        # ── Buttons ──────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self._on_save)
        btn_layout.addWidget(cancel)
        btn_layout.addWidget(save)
        layout.addLayout(btn_layout)

    def _load_current(self) -> None:
        s = self.store.data.settings
        self.chk_show_in_tray.setChecked(s.show_in_tray)
        self.chk_start_minimized.setChecked(s.start_minimized)
        self.chk_start_minimized.setEnabled(s.show_in_tray)

        for i, (_, value) in enumerate(SORT_OPTIONS):
            if value == s.sort_order:
                self.sort_combo.setCurrentIndex(i)
                break

    def _on_tray_toggled(self, enabled: bool) -> None:
        self.chk_start_minimized.setEnabled(enabled)
        if not enabled:
            self.chk_start_minimized.setChecked(False)

    def _on_save(self) -> None:
        _, sort_value = SORT_OPTIONS[self.sort_combo.currentIndex()]
        new_settings = Settings(
            sort_order=sort_value,
            show_in_tray=self.chk_show_in_tray.isChecked(),
            start_minimized=self.chk_start_minimized.isChecked(),
        )
        self.store.save_settings(new_settings)
        self.accept()

    # ── Helpers ──────────────────────────────────────────────────────

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        return label

    def _separator(self) -> QFrame:
        line = QFrame()
        line.setObjectName("Separator")
        line.setFixedHeight(1)
        return line
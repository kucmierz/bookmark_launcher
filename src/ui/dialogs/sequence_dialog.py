"""
SequenceDialog: create and edit sequences.
Left side: available bookmarks and sub-sequences to add.
Right side: current items in this sequence (reorderable, removable).
Cycle detection runs before adding any sub-sequence.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QDialogButtonBox,
    QLabel, QListWidget, QListWidgetItem, QWidget,
    QSplitter, QAbstractItemView,
)
from PySide6.QtCore import Qt, QSize

from core.models import Sequence, SequenceItem
from core.data_store import DataStore


class SequenceDialog(QDialog):
    def __init__(
        self,
        store: DataStore,
        sequence: Sequence | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.store = store
        self.sequence = sequence          # None = new sequence
        self._seq_id = sequence.id if sequence else None  # for cycle checks

        self.setWindowTitle("Edit Sequence" if sequence else "Add Sequence")
        self.setMinimumSize(560, 460)
        self.setModal(True)

        self._build_ui()
        self._apply_stylesheet()
        self._populate_available()

        if sequence:
            self._populate_from(sequence)

    # ── UI construction ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Name + note ───────────────────────────────────────────────
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Work start")
        form.addRow("Name:", self.name_edit)

        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Short description (shown as tooltip)")
        form.addRow("Note:", self.note_edit)

        layout.addLayout(form)

        # ── Two-column item picker ─────────────────────────────────────
        cols = QHBoxLayout()
        cols.setSpacing(8)

        # Left: available items
        left = QVBoxLayout()
        left.addWidget(QLabel("Available:"))
        self.available_list = QListWidget()
        self.available_list.setStyleSheet(self._list_style())
        self.available_list.itemDoubleClicked.connect(self._add_selected)
        left.addWidget(self.available_list)

        add_btn = QPushButton("Add  ▶")
        add_btn.clicked.connect(self._add_selected)
        left.addWidget(add_btn)
        cols.addLayout(left)

        # Right: items in this sequence
        right = QVBoxLayout()
        right.addWidget(QLabel("In sequence (top = first):"))
        self.items_list = QListWidget()
        self.items_list.setStyleSheet(self._list_style())
        self.items_list.setDragDropMode(QAbstractItemView.InternalMove)
        right.addWidget(self.items_list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        up_btn = QPushButton("▲")
        up_btn.setFixedWidth(36)
        up_btn.clicked.connect(self._move_up)
        down_btn = QPushButton("▼")
        down_btn.setFixedWidth(36)
        down_btn.clicked.connect(self._move_down)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_selected)
        btn_row.addWidget(up_btn)
        btn_row.addWidget(down_btn)
        btn_row.addStretch()
        btn_row.addWidget(remove_btn)
        right.addLayout(btn_row)
        cols.addLayout(right)

        layout.addLayout(cols, stretch=1)

        # ── Error + buttons ───────────────────────────────────────────
        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ── Populate ──────────────────────────────────────────────────────

    def _populate_available(self) -> None:
        """Fill the left list with all bookmarks and other sequences."""
        self.available_list.clear()

        for bm in self.store.get_bookmarks():
            item = QListWidgetItem(f"📌  {bm.name}")
            item.setData(Qt.UserRole, ("bookmark", bm.id, bm.name))
            self.available_list.addItem(item)

        for seq in self.store.get_sequences():
            if seq.id == self._seq_id:
                continue   # can't add self
            item = QListWidgetItem(f"▶  {seq.name}")
            item.setData(Qt.UserRole, ("sequence", seq.id, seq.name))
            self.available_list.addItem(item)

    def _populate_from(self, seq: Sequence) -> None:
        """Fill form fields and items list from an existing sequence."""
        self.name_edit.setText(seq.name)
        self.note_edit.setText(seq.note)

        for si in seq.items:
            if si.type == "bookmark":
                bm = self.store.get_bookmark(si.ref_id)
                label = f"📌  {bm.name}" if bm else f"📌  (deleted {si.ref_id})"
            else:
                s = self.store.get_sequence(si.ref_id)
                label = f"▶  {s.name}" if s else f"▶  (deleted {si.ref_id})"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, (si.type, si.ref_id, label))
            self.items_list.addItem(item)

    # ── Item management ───────────────────────────────────────────────

    def _add_selected(self) -> None:
        item = self.available_list.currentItem()
        if item is None:
            return

        kind, ref_id, label = item.data(Qt.UserRole)

        # Cycle check for sub-sequences
        if kind == "sequence" and self._seq_id:
            if self.store.has_cycle(self._seq_id, ref_id):
                self.error_label.setText(
                    f"⚠  Cannot add \"{label}\" — it would create a cycle."
                )
                self.error_label.show()
                return

        # Duplicate check — same item can only appear once
        for i in range(self.items_list.count()):
            existing = self.items_list.item(i).data(Qt.UserRole)
            if existing[0] == kind and existing[1] == ref_id:
                self.error_label.setText(f"⚠  \"{label}\" is already in this sequence.")
                self.error_label.show()
                return

        self.error_label.hide()
        new_item = QListWidgetItem(item.text())
        new_item.setData(Qt.UserRole, (kind, ref_id, label))
        self.items_list.addItem(new_item)

    def _remove_selected(self) -> None:
        row = self.items_list.currentRow()
        if row >= 0:
            self.items_list.takeItem(row)

    def _move_up(self) -> None:
        row = self.items_list.currentRow()
        if row > 0:
            item = self.items_list.takeItem(row)
            self.items_list.insertItem(row - 1, item)
            self.items_list.setCurrentRow(row - 1)

    def _move_down(self) -> None:
        row = self.items_list.currentRow()
        if row >= 0 and row < self.items_list.count() - 1:
            item = self.items_list.takeItem(row)
            self.items_list.insertItem(row + 1, item)
            self.items_list.setCurrentRow(row + 1)

    # ── Save ──────────────────────────────────────────────────────────

    def _save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            self.error_label.setText("⚠  Sequence name cannot be empty.")
            self.error_label.show()
            return

        if self.items_list.count() == 0:
            self.error_label.setText("⚠  Add at least one item to the sequence.")
            self.error_label.show()
            return

        self.error_label.hide()

        items = []
        for i in range(self.items_list.count()):
            kind, ref_id, _label = self.items_list.item(i).data(Qt.UserRole)
            items.append(SequenceItem(type=kind, ref_id=ref_id))

        if self.sequence:
            self.sequence.name = name
            self.sequence.note = self.note_edit.text().strip()
            self.sequence.items = items
            self.store.update_sequence(self.sequence)
        else:
            new_seq = Sequence(id="", name=name,
                               note=self.note_edit.text().strip(), items=items)
            self.store.add_sequence(new_seq)

        self.accept()

    # ── Styles ────────────────────────────────────────────────────────

    def _list_style(self) -> str:
        return """
            QListWidget {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                color: #cdd6f4;
                outline: none;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 4px;
                margin: 1px 4px;
            }
            QListWidget::item:hover { background-color: #313244; }
            QListWidget::item:selected {
                background-color: #45475a;
                color: #cdd6f4;
            }
        """

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }
            QLabel  { color: #a6adc8; }
            QLineEdit, QTextEdit {
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

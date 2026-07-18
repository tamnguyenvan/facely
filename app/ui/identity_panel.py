"""Identity panel for registration and management using Qt."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QFrame, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from app.ui.theme import SPACING
from app.utils.validators import validate_name, validate_person_id


class IdentityPanel(QWidget):
    """Right sidebar for identity registration and management."""
    
    # Signals
    register_requested = Signal(str, str)  # name, person_id
    delete_requested = Signal(str)  # person_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(340)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build identity panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        layout.setSpacing(SPACING["md"])
        
        # Registration section
        reg_frame = QFrame()
        reg_frame.setObjectName("cardFrame")
        reg_layout = QVBoxLayout(reg_frame)
        reg_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        reg_layout.setSpacing(SPACING["sm"])
        
        title = QLabel("Register Face")
        title.setObjectName("titleLabel")
        reg_layout.addWidget(title)
        
        # Name entry
        name_label = QLabel("Name:")
        reg_layout.addWidget(name_label)
        
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("Enter name...")
        reg_layout.addWidget(self.name_entry)
        
        # Person ID entry
        id_label = QLabel("ID (optional):")
        reg_layout.addWidget(id_label)
        
        self.id_entry = QLineEdit()
        self.id_entry.setPlaceholderText("Auto-generated if empty")
        reg_layout.addWidget(self.id_entry)
        
        # Capture button
        self.capture_btn = QPushButton("● Capture")
        self.capture_btn.setObjectName("primaryButton")
        self.capture_btn.clicked.connect(self._on_capture)
        reg_layout.addWidget(self.capture_btn)
        
        layout.addWidget(reg_frame)
        
        # Known identities section
        identities_title = QLabel("Known Identities")
        identities_title.setObjectName("titleLabel")
        layout.addWidget(identities_title)
        
        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "ID"])
        self.tree.setColumnWidth(0, 180)
        self.tree.setColumnWidth(1, 100)
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)
        
        # Delete button
        self.delete_btn = QPushButton("🗑 Delete Selected")
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(self.delete_btn)
    
    def _on_capture(self) -> None:
        """Handle capture button click."""
        name = self.name_entry.text().strip()
        person_id = self.id_entry.text().strip() or None
        
        # Validate
        valid, msg = validate_name(name)
        if not valid:
            QMessageBox.critical(self, "Validation Error", msg)
            return
        
        if person_id:
            valid, msg = validate_person_id(person_id)
            if not valid:
                QMessageBox.critical(self, "Validation Error", msg)
                return
        
        # Emit signal
        self.register_requested.emit(name, person_id or "")
    
    def _on_delete(self) -> None:
        """Handle delete button click."""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "No Selection", "Please select an identity to delete"
            )
            return
        
        name = current_item.text(0)
        person_id = current_item.text(1)
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete identity '{name}' ({person_id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(person_id)
    
    def refresh_identities(self, identities: list[dict]) -> None:
        """Refresh the identities list."""
        self.tree.clear()
        for identity in identities:
            item = QTreeWidgetItem([identity["name"], identity["person_id"]])
            self.tree.addTopLevelItem(item)
    
    def clear_form(self) -> None:
        """Clear registration form."""
        self.name_entry.clear()
        self.id_entry.clear()

"""Control panel for camera and model controls using Qt."""
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QComboBox, QHBoxLayout
from PySide6.QtCore import Signal
from app.ui.theme import COLORS, SPACING


class ControlPanel(QWidget):
    """Bottom control bar with camera and model controls."""
    
    # Signals
    start_requested = Signal()
    stop_requested = Signal()
    model_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Build control panel UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
        layout.setSpacing(SPACING["md"])
        
        # Start/Stop button
        self.start_btn = QPushButton("▶ Start Camera")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.clicked.connect(self._toggle_camera)
        layout.addWidget(self.start_btn)
        
        # Model selector
        model_label = QLabel("Model:")
        layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["arcface", "deepface", "sface"])
        self.model_combo.setCurrentText("arcface")
        self.model_combo.currentTextChanged.connect(self._on_model_selected)
        layout.addWidget(self.model_combo)
        
        # Status indicator
        self.status_label = QLabel("● OFFLINE")
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(self.status_label)
        
        # Spacer
        layout.addStretch()
        
        # Latency
        self.latency_label = QLabel("Latency: --ms")
        self.latency_label.setObjectName("accentLabel")
        layout.addWidget(self.latency_label)
        
        # FPS counter
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setObjectName("accentLabel")
        layout.addWidget(self.fps_label)
    
    def _toggle_camera(self) -> None:
        """Toggle camera on/off."""
        if self._is_running:
            self.stop_requested.emit()
            self._is_running = False
            self.start_btn.setText("▶ Start Camera")
            self.status_label.setText("● OFFLINE")
            self.status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        else:
            self.start_requested.emit()
            self._is_running = True
            self.start_btn.setText("⏹ Stop Camera")
            self.status_label.setText("● ONLINE")
            self.status_label.setStyleSheet(f"color: {COLORS['success']};")
    
    def _on_model_selected(self, model_name: str) -> None:
        """Handle model selection."""
        self.status_label.setText("● SWITCHING")
        self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
        self.model_changed.emit(model_name)
        # Status will be updated back to ONLINE by the main window
    
    def set_online_status(self) -> None:
        """Set status to online."""
        if self._is_running:
            self.status_label.setText("● ONLINE")
            self.status_label.setStyleSheet(f"color: {COLORS['success']};")
    
    def update_stats(self, fps: int | None = None, latency: int | None = None) -> None:
        """Update FPS and latency display."""
        if fps is not None:
            self.fps_label.setText(f"FPS: {fps}")
        if latency is not None:
            self.latency_label.setText(f"Latency: {latency}ms")

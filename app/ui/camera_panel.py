"""Camera panel for displaying live feed using Qt."""
import cv2
import numpy as np
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont
from app.ui.theme import COLORS


class CameraPanel(QWidget):
    """Panel for displaying camera feed with overlays."""
    
    def __init__(self, parent=None, width: int = 960, height: int = 540):
        super().__init__(parent)
        self.width = width
        self.height = height
        
        # Setup UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(self)
        self.label.setFixedSize(width, height)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"background-color: {COLORS['bg_root']};")
        
        layout.addWidget(self.label)
        
        self._current_frame = None
        self._current_results = []
        self._show_placeholder()
    
    def _show_placeholder(self) -> None:
        """Show placeholder when no camera feed."""
        pixmap = QPixmap(self.width, self.height)
        pixmap.fill(QColor(COLORS['bg_root']))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(COLORS['text_muted']))
        painter.setFont(QFont('Segoe UI', 16))
        painter.drawText(
            pixmap.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Camera Inactive\nClick 'Start Camera' to begin"
        )
        painter.end()
        
        self.label.setPixmap(pixmap)
    
    def update_frame(self, frame: np.ndarray, results: list[dict]) -> None:
        """Update display with new frame and detection results."""
        # Resize frame to fit display
        frame_resized = cv2.resize(frame, (self.width, self.height))
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        
        # Calculate scaling factors
        orig_h, orig_w = frame.shape[:2]
        scale_x = self.width / orig_w
        scale_y = self.height / orig_h
        
        # Convert to QImage
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(
            rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
        )
        
        # Create pixmap and draw overlays
        pixmap = QPixmap.fromImage(qt_image)
        painter = QPainter(pixmap)
        
        # Draw face detection results
        for result in results:
            self._draw_face_result(painter, result, scale_x, scale_y)
        
        painter.end()
        
        self.label.setPixmap(pixmap)
    
    def _draw_face_result(
        self, painter: QPainter, result: dict, scale_x: float, scale_y: float
    ) -> None:
        """Draw face detection result on the frame."""
        x1, y1, x2, y2 = result["bbox"]
        x1, x2 = int(x1 * scale_x), int(x2 * scale_x)
        y1, y2 = int(y1 * scale_y), int(y2 * scale_y)
        
        name = result["name"]
        score = result["score"]
        
        # Choose color based on match status
        if name == "Unknown":
            color = QColor(COLORS["bbox_unknown"])
        else:
            color = QColor(COLORS["bbox_match"])
        
        # Draw bounding box
        pen = QPen(color, 2)
        painter.setPen(pen)
        painter.drawRect(x1, y1, x2 - x1, y2 - y1)
        
        # Draw label background
        label_text = f"{name} ({score:.2f})"
        label_y = y1 - 25 if y1 > 30 else y2 + 5
        
        painter.fillRect(x1, label_y, 200, 20, QColor(COLORS["label_bg"]))
        
        # Draw label text
        painter.setPen(QColor(COLORS["text_primary"]))
        painter.setFont(QFont('Consolas', 10))
        painter.drawText(x1 + 5, label_y + 15, label_text)
        
        # Draw confidence bar
        bar_width = int(180 * score)
        bar_color = self._get_confidence_color(score)
        painter.fillRect(x1 + 5, label_y + 15, bar_width, 3, QColor(bar_color))
    
    def _get_confidence_color(self, score: float) -> str:
        """Get color based on confidence score."""
        if score >= 0.80:
            return COLORS["success"]
        elif score >= 0.55:
            return COLORS["warning"]
        else:
            return COLORS["danger"]
    
    def clear(self) -> None:
        """Clear display and show placeholder."""
        self._show_placeholder()

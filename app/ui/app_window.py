"""Main application window using Qt."""
import sys
import queue
import threading
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox
from PySide6.QtCore import QTimer, Qt
from app.ui.theme import get_stylesheet
from app.ui.camera_panel import CameraPanel
from app.ui.control_panel import ControlPanel
from app.ui.identity_panel import IdentityPanel
from app.services.camera_service import CameraService
from app.services.recognition_service import RecognitionService
from app.services.registration_service import RegistrationService
from app.core.model_manager import ModelManager
from app.core.detector import FaceDetector
from app.core.matcher import EmbeddingMatcher
from app.db.database import Database
from app.db.identity_repo import IdentityRepository
from app.config import CONFIG
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AppWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Facely v1.0.0")
        self.setGeometry(100, 100, 1380, 820)
        
        # Initialize services
        self._init_services()
        
        # Build UI
        self._setup_ui()
        
        # Apply stylesheet
        self.setStyleSheet(get_stylesheet())
        
        # State
        self._running = False
        self._frame_count = 0
        self._capture_frames = []
        self._capturing = False
        self._capture_name = None
        self._capture_id = None
        
        # Setup timer for polling
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self._poll_frames)
        
        logger.info("Facely started")
    
    def _init_services(self) -> None:
        """Initialize all services."""
        # Database
        db = Database()
        try:
            db.initialize()
        except Exception as e:
            logger.warning(f"Database initialization: {e}")
        
        self.repo = IdentityRepository(db)
        
        # Core components
        self.model_manager = ModelManager()
        self.detector = FaceDetector(
            model_name="version-RFB-640.onnx", threshold=0.7
        )
        self.matcher = EmbeddingMatcher()
        
        # Services
        self.camera_service = CameraService()
        self.recognition_service = RecognitionService(
            self.model_manager, self.detector, self.matcher, self.repo
        )
        self.registration_service = RegistrationService(
            self.detector, self.model_manager, self.repo
        )
        
        # Load default model
        try:
            self.model_manager.load(CONFIG.default_model)
            self.recognition_service.reload_cache(CONFIG.default_model)
        except Exception as e:
            logger.error(f"Failed to load default model: {e}")
            QMessageBox.warning(
                self,
                "Model Load Error",
                f"Failed to load {CONFIG.default_model} model. "
                "Please ensure model files are in assets/models/"
            )
    
    def _setup_ui(self) -> None:
        """Build the UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Content area (camera + identity panel)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Camera panel
        self.camera_panel = CameraPanel(width=960, height=720)
        content_layout.addWidget(self.camera_panel)
        
        # Identity panel
        self.identity_panel = IdentityPanel()
        self.identity_panel.register_requested.connect(self._start_capture)
        self.identity_panel.delete_requested.connect(self._delete_identity)
        content_layout.addWidget(self.identity_panel)
        
        main_layout.addWidget(content_widget)
        
        # Control panel
        self.control_panel = ControlPanel()
        self.control_panel.start_requested.connect(self._start_camera)
        self.control_panel.stop_requested.connect(self._stop_camera)
        self.control_panel.model_changed.connect(self._change_model)
        main_layout.addWidget(self.control_panel)
        
        # Load identities
        self._refresh_identities()
    
    def _start_camera(self) -> None:
        """Start camera and recognition."""
        try:
            self.camera_service.start()
            self._running = True
            self.poll_timer.start(30)  # Poll every 30ms (~33 FPS)
            logger.info("Camera started")
        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            QMessageBox.critical(self, "Camera Error", f"Failed to start camera: {e}")
    
    def _stop_camera(self) -> None:
        """Stop camera and recognition."""
        self._running = False
        self.poll_timer.stop()
        self.camera_service.stop()
        self.camera_panel.clear()
        logger.info("Camera stopped")
    
    def _change_model(self, model_name: str) -> None:
        """Change recognition model."""
        def _load():
            try:
                self.recognition_service.set_model(model_name)
                logger.info(f"Model changed to {model_name}")
                # Update status back to online
                QTimer.singleShot(0, self.control_panel.set_online_status)
            except Exception as e:
                logger.error(f"Failed to change model: {e}")
                QTimer.singleShot(
                    0,
                    lambda: QMessageBox.critical(
                        self, "Model Error", f"Failed to load {model_name}: {e}"
                    ),
                )
        
        threading.Thread(target=_load, daemon=True).start()
    
    def _poll_frames(self) -> None:
        """Poll for new frames and results."""
        if not self._running:
            return
        
        # Get frame from camera
        try:
            frame, should_process = self.camera_service.frame_queue.get_nowait()
            
            # Handle capture mode
            if self._capturing:
                self._capture_frames.append(frame)
                if len(self._capture_frames) >= RegistrationService.CAPTURE_FRAMES:
                    self._finish_capture()
                    return
            
            # Process frame for recognition
            if should_process:
                self._frame_count += 1
                self.recognition_service.process_frame(frame, self._frame_count)
        except queue.Empty:
            pass
        
        # Get recognition results
        try:
            result = self.recognition_service.result_queue.get_nowait()
            self.camera_panel.update_frame(result["frame"], result["results"])
            self.control_panel.update_stats(latency=result["latency_ms"])
        except queue.Empty:
            pass
    
    def _start_capture(self, name: str, person_id: str) -> None:
        """Start capturing frames for registration."""
        self._capturing = True
        self._capture_frames = []
        self._capture_name = name
        self._capture_id = person_id if person_id else None
        logger.info(f"Starting capture for {name}")
    
    def _finish_capture(self) -> None:
        """Finish capture and register identity."""
        self._capturing = False
        
        try:
            person_id = self.registration_service.register(
                self._capture_name, self._capture_frames, self._capture_id
            )
            
            # Reload cache
            self.recognition_service.reload_cache(self.model_manager.active_name)
            
            # Refresh UI
            self._refresh_identities()
            self.identity_panel.clear_form()
            
            QMessageBox.information(
                self, "Success", f"Registered {self._capture_name} ({person_id})"
            )
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            QMessageBox.critical(self, "Registration Error", str(e))
        finally:
            self._capture_frames = []
    
    def _delete_identity(self, person_id: str) -> None:
        """Delete an identity."""
        try:
            self.repo.delete_identity(person_id)
            self.recognition_service.reload_cache(self.model_manager.active_name)
            self._refresh_identities()
            QMessageBox.information(self, "Success", f"Deleted identity {person_id}")
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            QMessageBox.critical(self, "Delete Error", str(e))
    
    def _refresh_identities(self) -> None:
        """Refresh identities list."""
        identities = self.repo.list_identities()
        self.identity_panel.refresh_identities(identities)
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self._running:
            self._stop_camera()
        logger.info("Facely closed")
        event.accept()


def run_app():
    """Run the Qt application."""
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())

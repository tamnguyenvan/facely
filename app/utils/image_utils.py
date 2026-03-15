"""Image processing utilities."""
import cv2
import numpy as np
from PIL import Image, ImageTk


def bgr_to_photo_image(frame: np.ndarray) -> ImageTk.PhotoImage:
    """Convert BGR frame to Tkinter PhotoImage."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    return ImageTk.PhotoImage(pil_img)


def align_face(frame: np.ndarray, bbox: tuple, target_size: tuple = (112, 112)) -> np.ndarray:
    """Crop and align face from frame."""
    x1, y1, x2, y2 = bbox
    h, w = frame.shape[:2]
    
    # Add padding
    padding = 0.1
    pad_x = int((x2 - x1) * padding)
    pad_y = int((y2 - y1) * padding)
    
    x1 = max(0, x1 - pad_x)
    y1 = max(0, y1 - pad_y)
    x2 = min(w, x2 + pad_x)
    y2 = min(h, y2 + pad_y)
    
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return np.zeros((*target_size, 3), dtype=np.uint8)
    
    resized = cv2.resize(crop, target_size)
    return cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

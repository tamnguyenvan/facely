"""Face detection using Ultra-Light-Fast-Generic-Face-Detector ONNX model."""
import cv2
import numpy as np
import onnxruntime as ort
from pathlib import Path
from app.utils.logger import get_logger
from app.config import CONFIG

logger = get_logger(__name__)


class FaceDetector:
    """Face detector using RFB-640 ONNX model."""
    
    def __init__(self, model_name: str = "version-RFB-640.onnx", threshold: float = 0.7):
        """
        Initialize face detector.
        
        Args:
            model_name: Name of the ONNX model file
            threshold: Detection confidence threshold
        """
        self.threshold = threshold
        self.input_size = (640, 480)  # RFB-640 input size
        
        # Load ONNX model
        model_path = CONFIG.model_dir / model_name
        if not model_path.exists():
            raise FileNotFoundError(
                f"Face detection model not found: {model_path}\n"
                f"Please place {model_name} in {CONFIG.model_dir}"
            )
        
        self.ort_session = ort.InferenceSession(
            str(model_path),
            providers=['CPUExecutionProvider']
        )
        self.input_name = self.ort_session.get_inputs()[0].name
        
        logger.info(f"Face detector initialized with {model_name}")
    
    def detect(self, frame: np.ndarray) -> list[dict]:
        """
        Detect faces in frame.
        
        Args:
            frame: BGR image from OpenCV
        
        Returns:
            List of dicts with 'bbox' (x1,y1,x2,y2) and 'confidence'
        """
        orig_height, orig_width = frame.shape[:2]
        
        # Preprocess image
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, self.input_size)
        
        # Normalize
        image_mean = np.array([127, 127, 127])
        image = (image - image_mean) / 128.0
        image = np.transpose(image, [2, 0, 1])
        image = np.expand_dims(image, axis=0)
        image = image.astype(np.float32)
        
        # Run inference
        confidences, boxes = self.ort_session.run(None, {self.input_name: image})
        
        # Post-process predictions
        detections = self._predict(
            orig_width, orig_height, confidences, boxes, self.threshold
        )
        
        return detections
    
    def _predict(
        self, width: int, height: int, confidences: np.ndarray, 
        boxes: np.ndarray, prob_threshold: float, iou_threshold: float = 0.3
    ) -> list[dict]:
        """
        Post-process model predictions.
        
        Args:
            width: Original image width
            height: Original image height
            confidences: Model confidence outputs
            boxes: Model box outputs
            prob_threshold: Confidence threshold
            iou_threshold: IoU threshold for NMS
        
        Returns:
            List of detection dicts
        """
        boxes = boxes[0]
        confidences = confidences[0]
        
        picked_box_probs = []
        picked_labels = []
        
        # Process each class (class 0 is background, class 1 is face)
        for class_index in range(1, confidences.shape[1]):
            probs = confidences[:, class_index]
            mask = probs > prob_threshold
            probs = probs[mask]
            
            if probs.shape[0] == 0:
                continue
            
            subset_boxes = boxes[mask, :]
            box_probs = np.concatenate([subset_boxes, probs.reshape(-1, 1)], axis=1)
            
            # Apply NMS
            box_probs = self._hard_nms(
                box_probs, iou_threshold=iou_threshold, top_k=-1
            )
            
            picked_box_probs.append(box_probs)
            picked_labels.extend([class_index] * box_probs.shape[0])
        
        if not picked_box_probs:
            return []
        
        picked_box_probs = np.concatenate(picked_box_probs)
        
        # Scale boxes to original image size
        picked_box_probs[:, 0] *= width
        picked_box_probs[:, 1] *= height
        picked_box_probs[:, 2] *= width
        picked_box_probs[:, 3] *= height
        
        # Convert to detection format
        detections = []
        for i in range(picked_box_probs.shape[0]):
            x1, y1, x2, y2, conf = picked_box_probs[i]
            detections.append({
                "bbox": (int(x1), int(y1), int(x2), int(y2)),
                "confidence": float(conf),
            })
        
        return detections
    
    def _hard_nms(
        self, box_scores: np.ndarray, iou_threshold: float, top_k: int = -1
    ) -> np.ndarray:
        """
        Perform hard non-maximum suppression.
        
        Args:
            box_scores: (N, 5) array of [x1, y1, x2, y2, score]
            iou_threshold: IoU threshold for suppression
            top_k: Keep top k detections (-1 for all)
        
        Returns:
            Filtered box_scores array
        """
        scores = box_scores[:, -1]
        boxes = box_scores[:, :-1]
        
        picked = []
        indexes = np.argsort(scores)[::-1]
        
        while len(indexes) > 0:
            current = indexes[0]
            picked.append(current)
            
            if 0 < top_k == len(picked) or len(indexes) == 1:
                break
            
            current_box = boxes[current, :]
            indexes = indexes[1:]
            rest_boxes = boxes[indexes, :]
            
            iou = self._iou_of(
                rest_boxes,
                np.expand_dims(current_box, axis=0),
            )
            
            indexes = indexes[iou <= iou_threshold]
        
        return box_scores[picked, :]
    
    def _iou_of(self, boxes0: np.ndarray, boxes1: np.ndarray, eps: float = 1e-5) -> np.ndarray:
        """
        Calculate IoU between two sets of boxes.
        
        Args:
            boxes0: (N, 4) array of boxes
            boxes1: (M, 4) array of boxes
            eps: Small value to avoid division by zero
        
        Returns:
            (N, M) array of IoU values
        """
        overlap_left_top = np.maximum(boxes0[..., :2], boxes1[..., :2])
        overlap_right_bottom = np.minimum(boxes0[..., 2:], boxes1[..., 2:])
        
        overlap_area = self._area_of(overlap_left_top, overlap_right_bottom)
        area0 = self._area_of(boxes0[..., :2], boxes0[..., 2:])
        area1 = self._area_of(boxes1[..., :2], boxes1[..., 2:])
        
        return overlap_area / (area0 + area1 - overlap_area + eps)
    
    def _area_of(self, left_top: np.ndarray, right_bottom: np.ndarray) -> np.ndarray:
        """
        Calculate area of boxes.
        
        Args:
            left_top: (N, 2) array of top-left coordinates
            right_bottom: (N, 2) array of bottom-right coordinates
        
        Returns:
            (N,) array of areas
        """
        hw = np.clip(right_bottom - left_top, 0.0, None)
        return hw[..., 0] * hw[..., 1]
    
    def crop_face(
        self, frame: np.ndarray, bbox: tuple, padding: float = 0.1
    ) -> np.ndarray:
        """Crop face from frame with padding."""
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        
        pad_x = int((x2 - x1) * padding)
        pad_y = int((y2 - y1) * padding)
        
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(w, x2 + pad_x)
        y2 = min(h, y2 + pad_y)
        
        crop = frame[y1:y2, x1:x2]
        return cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

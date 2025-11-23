"""Object detection mode implementation"""

import time
import logging
from ultralytics import YOLO
from .base_mode import BaseMode

logger = logging.getLogger(__name__)


class ObjectDetectionMode(BaseMode):
    """Mode 3: YOLO object detection"""
    
    def __init__(self, audio_queue, camera_handler, yolo_model_path='yolov8n.pt'):
        super().__init__(audio_queue, mode_id=3, mode_name="Object Detection Mode")
        self.camera_handler = camera_handler
        self.yolo_model = None
        self.yolo_model_path = yolo_model_path
        self.confidence_threshold = 0.5
        self.update_interval = 3  # Update every 3 seconds
        self._load_yolo()
    
    def _load_yolo(self):
        """Load YOLO model"""
        try:
            self.yolo_model = YOLO(self.yolo_model_path)
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.yolo_model = None
    
    def _run(self):
        """Object detection worker"""
        if not self.camera_handler.is_available() or not self.yolo_model:
            self.speak("Camera or YOLO model not available for object detection")
            return
        
        self.speak("Object detection mode activated")
        logger.info("Object detection worker started")
        
        while self.running:
            try:
                logger.info("Attempting to capture frame for object detection...")
                ret, frame = self.camera_handler.capture_frame()
                logger.info(f"Frame capture result: {ret}")
                
                if ret and frame is not None:
                    logger.info(f"Frame shape: {frame.shape}")
                    # Run YOLO detection
                    logger.info("Running YOLO detection...")
                    results = self.yolo_model(frame)
                    logger.info(f"YOLO results: {len(results)} detections")
                    
                    # Process results
                    detections = []
                    for result in results:
                        boxes = result.boxes
                        if boxes is not None:
                            logger.info(f"Processing {len(boxes)} boxes")
                            for box in boxes:
                                cls = int(box.cls[0])
                                conf = float(box.conf[0])
                                logger.info(f"Box: class={cls}, confidence={conf:.2f}")
                                if conf > self.confidence_threshold:
                                    class_name = result.names[cls]
                                    detections.append(class_name)
                                    logger.info(f"Detection: {class_name}")
                                    
                    if detections:
                        # Count objects
                        object_counts = {}
                        for obj in detections:
                            object_counts[obj] = object_counts.get(obj, 0) + 1
                            
                        # Create description
                        description = []
                        for obj, count in object_counts.items():
                            if count == 1:
                                description.append(f"one {obj}")
                            else:
                                description.append(f"{count} {obj}s")
                                
                        final_description = ", ".join(description)
                        self.speak(f"I can see {final_description}")
                        logger.info(f"Speaking detection: {final_description}")
                    else:
                        self.speak("No objects detected")
                        logger.info("No objects detected")
                        
                    time.sleep(self.update_interval)
                else:
                    logger.error("Failed to capture frame for object detection")
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Object detection error: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                time.sleep(self.update_interval)
                
        logger.info("Object detection worker stopped")


"""Text recognition mode implementation"""

import time
import cv2
import pytesseract
from PIL import Image
import logging
from .base_mode import BaseMode

logger = logging.getLogger(__name__)


class TextRecognitionMode(BaseMode):
    """Mode 2: OCR text recognition and reading"""
    
    def __init__(self, audio_queue, camera_handler):
        super().__init__(audio_queue, mode_id=2, mode_name="Text Recognition Mode")
        self.camera_handler = camera_handler
        self.update_interval = 5  # Check every 5 seconds
    
    def _run(self):
        """Text recognition worker"""
        if not self.camera_handler.is_available():
            self.speak("Camera not available for text recognition")
            return
        
        self.speak("Text recognition mode activated")
        logger.info("Text recognition worker started")
        
        while self.running:
            try:
                logger.info("Attempting to capture frame from Pi Camera...")
                ret, frame = self.camera_handler.capture_frame()
                logger.info(f"Frame capture result: {ret}")
                
                if ret and frame is not None:
                    logger.info(f"Frame shape: {frame.shape}")
                    # Convert to PIL Image for OCR
                    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    logger.info("PIL image created successfully")
                    
                    # Perform OCR
                    text = pytesseract.image_to_string(pil_image)
                    logger.info(f"OCR result: '{text.strip()}'")
                    
                    if text.strip():
                        # Clean up text
                        clean_text = ' '.join(text.strip().split())
                        self.speak(f"I can see the following text: {clean_text}")
                        logger.info(f"Speaking text: {clean_text}")
                    else:
                        logger.info("No text detected in image")
                        
                    time.sleep(self.update_interval)
                else:
                    logger.error("Failed to capture frame from Pi Camera")
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Text recognition error: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                time.sleep(self.update_interval)
                
        logger.info("Text recognition worker stopped")


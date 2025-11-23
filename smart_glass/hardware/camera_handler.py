"""Camera handler for Pi Camera operations"""

import cv2
import subprocess
import time
import logging

logger = logging.getLogger(__name__)


class CameraHandler:
    """Handles camera initialization and frame capture"""
    
    def __init__(self):
        """Initialize camera handler"""
        self.camera = None
        self.setup_camera()
        self.check_camera_status()
    
    def setup_camera(self):
        """Initialize Pi Camera using multiple detection methods"""
        try:
            logger.info("Attempting to initialize Pi Camera...")
            
            # Method 1: Try rpicam-still (newer Pi Camera tool)
            try:
                test_cmd = ["rpicam-still", "--timeout", "1000", "--output", "/tmp/test.jpg"]
                result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    logger.info("Pi Camera is accessible via rpicam-still")
                    self.camera = "rpicam_camera"
                    subprocess.run(["rm", "-f", "/tmp/test.jpg"])
                    return
                else:
                    logger.warning(f"rpicam-still failed: {result.stderr}")
            except Exception as e:
                logger.debug(f"rpicam-still not available: {e}")
            
            # Method 2: Try libcamera-still
            try:
                test_cmd = ["libcamera-still", "--timeout", "1000", "--output", "/tmp/test.jpg"]
                result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    logger.info("Pi Camera is accessible via libcamera-still")
                    self.camera = "libcamera_camera"
                    subprocess.run(["rm", "-f", "/tmp/test.jpg"])
                    return
                else:
                    logger.warning(f"libcamera-still failed: {result.stderr}")
            except Exception as e:
                logger.debug(f"libcamera-still not available: {e}")
            
            # Method 3: Try OpenCV with Pi Camera device
            logger.info("Trying OpenCV with Pi Camera device...")
            try:
                camera_devices = ["/dev/video0", "/dev/video1", "/dev/video2", "/dev/video3"]
                
                for device in camera_devices:
                    try:
                        cap = cv2.VideoCapture(device)
                        if cap.isOpened():
                            ret, frame = cap.read()
                            if ret:
                                logger.info(f"OpenCV camera opened successfully on {device}")
                                self.camera = f"opencv_{device}"
                                cap.release()
                                break
                            else:
                                cap.release()
                    except Exception as e:
                        logger.debug(f"Failed to open {device}: {e}")
                        continue
                
                if self.camera is None:
                    logger.error("No camera device accessible via any method")
                    
            except Exception as e:
                logger.error(f"OpenCV camera setup failed: {e}")
                
        except subprocess.TimeoutExpired:
            logger.error("Pi Camera test timed out")
            self.camera = None
        except Exception as e:
            logger.error(f"Failed to initialize Pi Camera: {e}")
            import traceback
            logger.error(f"Camera setup traceback: {traceback.format_exc()}")
            self.camera = None
    
    def check_camera_status(self):
        """Check and log current camera status"""
        logger.info(f"Current camera status: {self.camera}")
        
        if self.camera is None:
            logger.error("No camera detected!")
            return False
            
        if self.camera == "rpicam_camera":
            logger.info("Camera type: rpicam-still (modern Pi Camera)")
        elif self.camera == "libcamera_camera":
            logger.info("Camera type: libcamera-still")
        elif self.camera.startswith("opencv_"):
            logger.info(f"Camera type: OpenCV on {self.camera}")
        else:
            logger.info(f"Unknown camera type: {self.camera}")
            
        return True
    
    def capture_frame(self):
        """Capture a frame from Pi Camera using multiple methods"""
        try:
            if self.camera is None:
                return False, None
                
            # Method 1: rpicam-still
            if self.camera == "rpicam_camera":
                temp_file = f"/tmp/frame_{int(time.time())}.jpg"
                cmd = ["rpicam-still", "--timeout", "1000", "--output", temp_file, "--nopreview"]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    frame = cv2.imread(temp_file)
                    if frame is not None:
                        subprocess.run(["rm", "-f", temp_file])
                        return True, frame
                    else:
                        subprocess.run(["rm", "-f", temp_file])
                        return False, None
                else:
                    logger.error(f"rpicam-still failed: {result.stderr}")
                    return False, None
                    
            # Method 2: libcamera-still
            elif self.camera == "libcamera_camera":
                temp_file = f"/tmp/frame_{int(time.time())}.jpg"
                cmd = ["libcamera-still", "--timeout", "1000", "--output", temp_file, "--nopreview"]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    frame = cv2.imread(temp_file)
                    if frame is not None:
                        subprocess.run(["rm", "-f", temp_file])
                        return True, frame
                    else:
                        subprocess.run(["rm", "-f", temp_file])
                        return False, None
                else:
                    logger.error(f"libcamera-still failed: {result.stderr}")
                    return False, None
                    
            # Method 3: OpenCV with Pi Camera device
            elif self.camera.startswith("opencv_"):
                device = self.camera.replace("opencv_", "")
                cap = cv2.VideoCapture(device)
                if cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    if ret:
                        return True, frame
                    else:
                        return False, None
                else:
                    return False, None
                    
            return False, None
                
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return False, None
    
    def is_available(self):
        """Check if camera is available"""
        return self.camera is not None


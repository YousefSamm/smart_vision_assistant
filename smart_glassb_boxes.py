#!/usr/bin/env python3
"""
Smart Glass Project - Raspberry Pi 4B
Controls: 3 push buttons with external pull-down resistors
- Pin 36: Mode selection button (cycles through 4 modes)
- Pin 38: Confirm selection button
- Pin 40: Exit/Idle button
- Pin 7: Ultrasonic trigger
- Pin 11: Ultrasonic echo
"""

import RPi.GPIO as GPIO
import time
import threading
import cv2
from gtts import gTTS
import pygame
from ultralytics import YOLO
import pytesseract
from PIL import Image
import queue
import logging
import subprocess
import numpy as np
import os


# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SmartGlass:
    def __init__(self):
        # GPIO Pin definitions
        self.MODE_BUTTON_PIN = 36      # Button 1: Mode selection
        self.CONFIRM_BUTTON_PIN = 38   # Button 2: Confirm selection
        self.EXIT_BUTTON_PIN = 40      # Button 3: Exit/Idle
        self.TRIG_PIN = 7              # Ultrasonic trigger
        self.ECHO_PIN = 11             # Ultrasonic echo
        
        # Button debouncing - increased for better stability
        self.BUTTON_DEBOUNCE_TIME = 0.5
        self.last_button_press = {
            self.MODE_BUTTON_PIN: 0,
            self.CONFIRM_BUTTON_PIN: 0,
            self.EXIT_BUTTON_PIN: 0
        }

        # System state
        # 0 = idle, 1-4 = active modes
        self.current_mode = 0
        self.mode_names = {
            0: "idle mode",
            1: "time mode",
            2: "text recognition and reading mode",
            3: "object detection mode",
            4: "distance measurements mode"
        }
        
        # Camera and YOLO
        self.camera = None
        self.yolo_model = None
        self.camera_thread = None
        self.camera_running = False
        
        # OpenCV display
        self.display_window = None
        self.show_visualization = True
        

        
        # Audio
        self.audio_queue = queue.Queue()
        self.audio_thread = None
        self.audio_running = False
        
        # Button monitoring
        self.button_thread = None
        self.button_running = False
        
        # Ultrasonic
        self.ultrasonic_thread = None
        self.ultrasonic_running = False
        
        # Object detection tracking
        self.last_detections = set()
        self.detection_change_threshold = 0.3  # Speak if 30% of objects change
        
        # Initialize GPIO
        self.setup_gpio()
        
        # Initialize audio
        self.setup_audio()
        
        # Initialize camera
        self.setup_camera()
        
        # Check camera status
        self.check_camera_status()
        
        # Initialize YOLO
        self.setup_yolo()
        
        # Start audio thread
        self.start_audio_thread()
        
        # Start button monitoring thread
        self.start_button_thread()
        
        # Welcome message
        self.speak("Welcome to Smart Glass! Ready to assist you.")
        
    def setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BOARD)
        
        # Setup input pins with pull-down resistors
        GPIO.setup(self.MODE_BUTTON_PIN, GPIO.IN, 
                  pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.CONFIRM_BUTTON_PIN, GPIO.IN, 
                  pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.EXIT_BUTTON_PIN, GPIO.IN, 
                  pull_up_down=GPIO.PUD_DOWN)
        
        # Setup ultrasonic pins
        GPIO.setup(self.TRIG_PIN, GPIO.OUT)
        GPIO.setup(self.ECHO_PIN, GPIO.IN)
        
        # Set trigger to low initially
        GPIO.output(self.TRIG_PIN, GPIO.LOW)
        
        logger.info("GPIO setup completed")
        
    def setup_audio(self):
        """Initialize pygame audio"""
        pygame.mixer.init()
        logger.info("Audio system initialized")
        
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
                    
                    # Clean up test image
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
                    
                    # Clean up test image
                    subprocess.run(["rm", "-f", "/tmp/test.jpg"])
                    return
                else:
                    logger.warning(f"libcamera-still failed: {result.stderr}")
            except Exception as e:
                logger.debug(f"libcamera-still not available: {e}")
            
            # Method 3: Try vcgencmd detection
            try:
                cmd = ["vcgencmd", "get_camera"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"Camera detected via vcgencmd: {result.stdout.strip()}")
                    # Even if vcgencmd shows detected=0, try OpenCV
                    pass
                else:
                    logger.warning("vcgencmd camera detection failed")
            except Exception as e:
                logger.debug(f"vcgencmd failed: {e}")
            
            # Method 4: Try OpenCV with Pi Camera device
            logger.info("Trying OpenCV with Pi Camera device...")
            try:
                # Try different Pi Camera device paths
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
                logger.warning("No camera available")
                return False, None
                
            # Method 1: rpicam-still (newer Pi Camera tool)
            if self.camera == "rpicam_camera":
                temp_file = f"/tmp/frame_{int(time.time())}.jpg"
                # Increase timeout and add more parameters for better capture
                cmd = ["rpicam-still", "--timeout", "2000", "--output", temp_file, 
                       "--nopreview", "--width", "640", "--height", "480"]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    # Read the captured image
                    frame = cv2.imread(temp_file)
                    if frame is not None and frame.size > 0:
                        logger.info(f"rpicam-still captured frame: {frame.shape}")
                        # Clean up temp file
                        subprocess.run(["rm", "-f", temp_file])
                        return True, frame
                    else:
                        logger.warning("rpicam-still captured empty frame")
                        subprocess.run(["rm", "-f", temp_file])
                        return False, None
                else:
                    logger.error(f"rpicam-still failed: {result.stderr}")
                    return False, None
                    
            # Method 2: libcamera-still
            elif self.camera == "libcamera_camera":
                temp_file = f"/tmp/frame_{int(time.time())}.jpg"
                # Increase timeout and add parameters for better capture
                cmd = ["libcamera-still", "--timeout", "2000", "--output", temp_file, 
                       "--nopreview", "--width", "640", "--height", "480"]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    # Read the captured image
                    frame = cv2.imread(temp_file)
                    if frame is not None and frame.size > 0:
                        logger.info(f"libcamera-still captured frame: {frame.shape}")
                        # Clean up temp file
                        subprocess.run(["rm", "-f", temp_file])
                        return True, frame
                    else:
                        logger.warning("libcamera-still captured empty frame")
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
                    # Set camera properties for better capture
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    ret, frame = cap.read()
                    cap.release()
                    if ret and frame is not None and frame.size > 0:
                        logger.info(f"OpenCV captured frame: {frame.shape}")
                        return True, frame
                    else:
                        logger.warning("OpenCV captured empty frame")
                        return False, None
                else:
                    logger.warning(f"Could not open OpenCV device: {device}")
                    return False, None
                    
            return False, None
                
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return False, None
            
    def create_test_frame(self):
        """Create a test frame when camera fails"""
        try:
            # Create a test pattern frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add some test content
            cv2.putText(frame, "CAMERA NOT AVAILABLE", (50, 200), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(frame, "Test Pattern", (200, 250), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Camera: {self.camera}", (50, 300), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add some shapes
            cv2.rectangle(frame, (100, 100), (200, 200), (255, 0, 0), 2)
            cv2.circle(frame, (400, 150), 50, (0, 255, 255), 2)
            
            return True, frame
        except Exception as e:
            logger.error(f"Failed to create test frame: {e}")
            return False, None
            
    def setup_yolo(self):
        """Initialize YOLO model"""
        try:
            # Use a smaller model for Raspberry Pi
            self.yolo_model = YOLO('yolov8n.pt')
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.yolo_model = None
            
    def start_audio_thread(self):
        """Start audio processing thread"""
        self.audio_running = True
        self.audio_thread = threading.Thread(target=self.audio_worker, daemon=True)
        self.audio_thread.start()
        logger.info("Audio thread started")
        
    def start_button_thread(self):
        """Start button monitoring thread"""
        self.button_running = True
        self.button_thread = threading.Thread(target=self.button_worker, daemon=True)
        self.button_thread.start()
        logger.info("Button monitoring thread started")
        
    def button_worker(self):
        """Button monitoring worker thread"""
        while self.button_running:
            try:
                self.check_buttons()
                time.sleep(0.05)  # Check buttons every 50ms
            except Exception as e:
                logger.error(f"Button worker error: {e}")
                time.sleep(0.1)
        
    def audio_worker(self):
        """Audio processing worker thread"""
        while self.audio_running:
            try:
                if not self.audio_queue.empty():
                    text = self.audio_queue.get()
                    self.generateAndPlayAudio(text)
                    
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Audio worker error: {e}")
                
    def speak(self, text):
        """Add text to audio queue for speech"""
        try:
            self.audio_queue.put(text)
            logger.info(f"Added to speech queue: {text}")
        except Exception as e:
            logger.error(f"Failed to add text to speech queue: {e}")
            
    def generateAndPlayAudio(self, text):
        """Generate and play audio from text"""
        try:
            # Create temporary audio file
            tts = gTTS(text=text, lang='en', slow=False)
            temp_file = f"/tmp/smart_glass_{int(time.time())}.mp3"
            tts.save(temp_file)
            
            # Play audio and wait for completion
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            # Clean up
            pygame.mixer.music.unload()
            os.remove(temp_file)
            
        except Exception as e:
            logger.error(f"Audio generation/playback failed: {e}")
            
    def interrupt_audio(self):
        """Interrupt any currently playing audio"""
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            logger.error(f"Failed to stop audio: {e}")
        
        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except Exception:
                pass
            
    def mode_button_callback(self, channel):
        """Handle mode button press"""
        # Interrupt any playing audio
        self.interrupt_audio()
        
        if self.current_mode == 0:  # Currently idle
            self.current_mode = 1
        else:
            self.current_mode = (self.current_mode % 4) + 1
            
        mode_name = self.mode_names[self.current_mode]
        self.speak(f"Switched to {mode_name}")
            
    def confirm_button_callback(self, channel):
        """Handle confirm button press"""
        # Interrupt any playing audio
        self.interrupt_audio()
        
        if self.current_mode > 0:
            mode_name = self.mode_names[self.current_mode]
            self.speak(f"{mode_name} selected")
            
            # Start the selected mode
            self.start_mode(self.current_mode)
                
    def exit_button_callback(self, channel):
        """Handle exit button press"""
        # Stop current mode first
        self.stop_current_mode()
        
        # Interrupt any playing audio
        self.interrupt_audio()
        
        self.current_mode = 0
        self.speak("Glass is now in idle mode")
            
    def start_mode(self, mode):
        """Start the specified mode"""
        self.stop_current_mode()  # Stop any running mode
        
        if mode == 1:
            self.start_time_mode()
        elif mode == 2:
            self.start_text_recognition_mode()
        elif mode == 3:
            self.start_object_detection_mode()
        elif mode == 4:
            self.start_distance_measurement_mode()
            
    def stop_current_mode(self):
        """Stop all running modes"""
        self.camera_running = False
        self.ultrasonic_running = False
        
        # Reset object detection tracking
        self.last_detections = set()
        
        # Close display
        self.close_display_window()
        
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=1)
            
        if self.ultrasonic_thread and self.ultrasonic_thread.is_alive():
            self.ultrasonic_thread.join(timeout=1)
            
    def start_time_mode(self):
        """Mode 1: Tell the time"""
        def time_worker():
            while self.current_mode == 1:
                current_time = time.strftime("%I:%M %p")
                self.speak(f"The current time is {current_time}")
                time.sleep(60)  # Update every minute
                
        self.speak("Time mode activated")
        threading.Thread(target=time_worker, daemon=True).start()
        
    def start_text_recognition_mode(self):
        """Mode 2: OCR text recognition and reading - simplified"""
        if not self.camera:
            self.speak("Camera not available for text recognition")
            return
            
        # Setup display window
        self.setup_display_window("Text Recognition")
        self.camera_running = True
        
    def start_object_detection_mode(self):
        """Mode 3: YOLO object detection - simplified"""
        if not self.camera or not self.yolo_model:
            self.speak("Camera or YOLO model not available for object detection")
            return
            
        # Setup display window
        self.setup_display_window("Object Detection")
        self.camera_running = True
        
        # Reset detection tracking for new session
        self.last_detections = set()
        
    def start_distance_measurement_mode(self):
        """Mode 4: Ultrasonic distance measurement"""
        def distance_worker():
            self.ultrasonic_running = True
            
            # First reading
            first_distance = self.measure_distance()
            self.speak(f"Initial distance reading: "
                      f"{first_distance:.1f} centimeters")
            
            while self.current_mode == 4 and self.ultrasonic_running:
                try:
                    distance = self.measure_distance()
                    
                    # Only speak warning if distance is less than 100 cm
                    if distance < 100:
                        self.speak(f"Warning! Distance is "
                                  f"{distance:.1f} centimeters")
                        
                    time.sleep(1)  # Update every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Distance measurement error: {e}")
                    time.sleep(1)
                    
        self.speak("Distance measurement mode activated")
        self.ultrasonic_thread = threading.Thread(target=distance_worker, 
                                                daemon=True)
        self.ultrasonic_thread.start()
        
    def measure_distance(self):
        """Measure distance using ultrasonic sensor"""
        try:
            # Send trigger signal
            GPIO.output(self.TRIG_PIN, GPIO.HIGH)
            time.sleep(0.00001)  # 10 microseconds
            GPIO.output(self.TRIG_PIN, GPIO.LOW)
            
            # Wait for echo
            start_time = time.time()
            while GPIO.input(self.ECHO_PIN) == GPIO.LOW:
                start_time = time.time()
                if time.time() - start_time > 0.1:  # Timeout
                    return 999.0
                    
            # Measure echo duration
            end_time = time.time()
            while GPIO.input(self.ECHO_PIN) == GPIO.HIGH:
                end_time = time.time()
                if time.time() - start_time > 0.1:  # Timeout
                    return 999.0
                    
            # Calculate distance
            duration = end_time - start_time
            distance = (duration * 34300) / 2  # Speed of sound = 343 m/s
            
            return max(0, distance)
            
        except Exception as e:
            logger.error(f"Distance measurement failed: {e}")
            return 999.0
            
    def setup_display_window(self, window_name="Smart Glass"):
        """Setup display - now just logs (saving screenshots)"""
        logger.info(f"Display mode: {window_name} (saving screenshots)")
        self.show_visualization = True
            
    def close_display_window(self):
        """Close display - no longer needed"""
        logger.info("Display closed (screenshot mode)")
            
    def save_frame_with_analysis(self, frame, mode_name):
        """Save frame with bounding boxes to file"""
        try:
            if frame is not None and frame.size > 0:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"smart_glass_{mode_name}_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                logger.info(f"📸 Screenshot saved: {filename}")
                return filename
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
        return None
    
    def has_detection_changed(self, current_detections):
        """Check if detections have changed significantly"""
        try:
            if not self.last_detections:
                # First detection - always speak
                return True
            
            # Convert to sets for comparison
            current_set = set(current_detections)
            last_set = self.last_detections
            
            # Calculate change percentage
            if not last_set:
                return True
            
            # Count new objects
            new_objects = current_set - last_set
            removed_objects = last_set - current_set
            
            # Calculate change ratio
            total_objects = len(current_set | last_set)
            changed_objects = len(new_objects | removed_objects)
            
            if total_objects == 0:
                return False
            
            change_ratio = changed_objects / total_objects
            
            # Speak if significant change
            if change_ratio >= self.detection_change_threshold:
                logger.info(f"Detection change: {change_ratio:.2f} "
                          f"(new: {new_objects}, removed: {removed_objects})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Detection change check error: {e}")
            return True  # Default to speaking on error
            
    def draw_text_bounding_boxes(self, frame, text_data):
        """Draw bounding boxes around detected text"""
        try:
            if not text_data or frame is None:
                return frame
                
            # Convert PIL image to OpenCV format if needed
            if hasattr(text_data, 'getbbox'):
                # text_data is a PIL Image
                bbox = text_data.getbbox()
                if bbox:
                    x1, y1, x2, y2 = bbox
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, "Text Detected", (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            elif isinstance(text_data, list):
                # text_data is a list of bounding boxes
                for bbox in text_data:
                    if len(bbox) >= 4:
                        x1, y1, x2, y2 = bbox[:4]
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                        cv2.putText(frame, "Text", (int(x1), int(y1)-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            return frame
        except Exception as e:
            logger.error(f"Failed to draw text bounding boxes: {e}")
            return frame
            
    def draw_yolo_bounding_boxes(self, frame, results):
        """Draw YOLO detection bounding boxes and labels"""
        try:
            if not results or frame is None:
                return frame
                
            annotated_frame = frame.copy()
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        # Only draw if confidence is above threshold
                        if conf > 0.5:
                            # Get class name
                            class_name = result.names[cls]
                            
                            # Draw bounding box
                            cv2.rectangle(annotated_frame, (int(x1), int(y1)), 
                                        (int(x2), int(y2)), (0, 0, 255), 2)
                            
                            # Draw label with confidence
                            label = f"{class_name}: {conf:.2f}"
                            label_size = cv2.getTextSize(label, 
                                                       cv2.FONT_HERSHEY_SIMPLEX, 
                                                       0.6, 2)[0]
                            
                            # Draw label background
                            cv2.rectangle(annotated_frame, 
                                        (int(x1), int(y1) - label_size[1] - 10), 
                                        (int(x1) + label_size[0], int(y1)), 
                                        (0, 0, 255), -1)
                            
                            # Draw label text
                            cv2.putText(annotated_frame, label, 
                                      (int(x1), int(y1) - 5), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                                      (255, 255, 255), 2)
            
            return annotated_frame
        except Exception as e:
            logger.error(f"Failed to draw YOLO bounding boxes: {e}")
            return frame
            

            
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up Smart Glass...")
        
        # Stop all threads
        self.audio_running = False
        self.button_running = False
        self.camera_running = False
        self.ultrasonic_running = False
        
        # Close display
        self.close_display_window()
        
        # Wait for threads to finish
        if self.button_thread and self.button_thread.is_alive():
            self.button_thread.join(timeout=1)
            
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1)
            
        # Stop camera
        if self.camera:
            self.camera.release()
            
        # Clean up GPIO
        GPIO.cleanup()
        
        # Stop pygame
        pygame.mixer.quit()
        
        logger.info("Cleanup completed")
        
    def check_buttons(self):
        """Check button states using polling"""
        current_time = time.time()
        
        # Get current button states
        mode_state = GPIO.input(self.MODE_BUTTON_PIN)
        confirm_state = GPIO.input(self.CONFIRM_BUTTON_PIN)
        exit_state = GPIO.input(self.EXIT_BUTTON_PIN)
        
        # Only log button presses, not continuous states
        if mode_state == GPIO.HIGH:
            if (current_time - self.last_button_press[self.MODE_BUTTON_PIN] > 
                self.BUTTON_DEBOUNCE_TIME):
                self.last_button_press[self.MODE_BUTTON_PIN] = current_time
                logger.info("Mode button pressed - calling callback")
                self.mode_button_callback(self.MODE_BUTTON_PIN)
                
        if confirm_state == GPIO.HIGH:
            if (current_time - self.last_button_press[self.CONFIRM_BUTTON_PIN] > 
                self.BUTTON_DEBOUNCE_TIME):
                self.last_button_press[self.CONFIRM_BUTTON_PIN] = current_time
                logger.info("Confirm button pressed - calling callback")
                self.confirm_button_callback(self.CONFIRM_BUTTON_PIN)
                
        if exit_state == GPIO.HIGH:
            if (current_time - self.last_button_press[self.EXIT_BUTTON_PIN] > 
                self.BUTTON_DEBOUNCE_TIME):
                self.last_button_press[self.EXIT_BUTTON_PIN] = current_time
                logger.info("Exit button pressed - calling callback")
                self.exit_button_callback(self.EXIT_BUTTON_PIN)

    def run(self):
        """Main run loop"""
        try:
            logger.info("Smart Glass started. Press Ctrl+C to exit.")
            self.speak("Smart Glass is running and ready")
            
            # Main thread handles everything including OpenCV display
            while True:
                # Handle text recognition on main thread
                if self.current_mode == 2 and self.camera_running:
                    try:
                        ret, frame = self.capture_frame()
                        if ret and frame is not None:
                            # Convert to PIL Image for OCR
                            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                            
                            # Perform OCR
                            try:
                                ocr_data = pytesseract.image_to_data(pil_image, 
                                                                   lang='eng',
                                                                   output_type=pytesseract.Output.DICT)
                                
                                # Draw bounding boxes
                                display_frame = self.draw_text_bounding_boxes(frame, ocr_data)
                                
                                # Get simple text for speech
                                simple_text = pytesseract.image_to_string(pil_image)
                                
                                if simple_text.strip():
                                    clean_text = ' '.join(simple_text.strip().split())
                                    self.speak(f"I can see the following text: {clean_text}")
                                else:
                                    self.speak("No text detected")
                                
                                # Save screenshot with bounding boxes
                                self.save_frame_with_analysis(display_frame, "text")
                                
                            except Exception as ocr_error:
                                logger.error(f"OCR error: {ocr_error}")
                                self.save_frame_with_analysis(frame, "text_error")
                        
                        time.sleep(5)  # Check every 5 seconds
                        
                    except Exception as e:
                        logger.error(f"Text recognition error: {e}")
                        time.sleep(5)
                
                # Handle object detection on main thread
                elif self.current_mode == 3 and self.camera_running:
                    try:
                        ret, frame = self.capture_frame()
                        if ret and frame is not None:
                            # Run YOLO detection
                            results = self.yolo_model(frame)
                            
                            # Draw bounding boxes
                            annotated_frame = self.draw_yolo_bounding_boxes(frame, results)
                            
                            # Process detections for speech
                            detections = []
                            for result in results:
                                if result.boxes is not None:
                                    for box in result.boxes:
                                        if float(box.conf[0]) > 0.5:
                                            class_name = result.names[int(box.cls[0])]
                                            detections.append(class_name)
                            
                            # Check if detections have changed significantly
                            if self.has_detection_changed(detections):
                                if detections:
                                    object_counts = {}
                                    for obj in detections:
                                        object_counts[obj] = object_counts.get(obj, 0) + 1
                                    
                                    description = []
                                    for obj, count in object_counts.items():
                                        if count == 1:
                                            description.append(f"one {obj}")
                                        else:
                                            description.append(f"{count} {obj}s")
                                    
                                    final_description = ", ".join(description)
                                    self.speak(f"I can see {final_description}")
                                else:
                                    self.speak("No objects detected")
                                
                                # Update last detections
                                self.last_detections = set(detections)
                            
                            # Save screenshot with bounding boxes
                            self.save_frame_with_analysis(annotated_frame, "object")
                            
                        time.sleep(5)  # Update every 3 seconds
                        
                    except Exception as e:
                        logger.error(f"Object detection error: {e}")
                        time.sleep(5)
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            self.cleanup()

if __name__ == "__main__":
    try:
        smart_glass = SmartGlass()
        smart_glass.run()
    except Exception as e:
        logger.error(f"Smart Glass failed to start: {e}")
        GPIO.cleanup()

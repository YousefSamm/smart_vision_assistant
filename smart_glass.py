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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
        GPIO.setup(self.MODE_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.CONFIRM_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.EXIT_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        # Setup ultrasonic pins
        GPIO.setup(self.TRIG_PIN, GPIO.OUT)
        GPIO.setup(self.ECHO_PIN, GPIO.IN)
        
        # Set trigger to low initially
        GPIO.output(self.TRIG_PIN, GPIO.LOW)
        
        # Note: Using polling instead of edge detection for better compatibility
        logger.info("GPIO setup completed - using polling method")
        
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
                return False, None
                
            # Method 1: rpicam-still (newer Pi Camera tool)
            if self.camera == "rpicam_camera":
                temp_file = f"/tmp/frame_{int(time.time())}.jpg"
                cmd = ["rpicam-still", "--timeout", "1000", "--output", temp_file, "--nopreview"]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # Read the captured image
                    frame = cv2.imread(temp_file)
                    if frame is not None:
                        # Clean up temp file
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
                    # Read the captured image
                    frame = cv2.imread(temp_file)
                    if frame is not None:
                        # Clean up temp file
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
            
    def interrupt_audio(self):
        """Interrupt any currently playing audio and clear the queue"""
        try:
            # Stop any playing audio
            pygame.mixer.music.stop()
            logger.info("Audio interrupted")
        except Exception as e:
            logger.error(f"Failed to stop audio: {e}")
        
        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except Exception:
                pass
        logger.info("Audio queue cleared")
        
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
            import os
            os.remove(temp_file)
            
            logger.info(f"Audio completed: {text}")
            
        except Exception as e:
            logger.error(f"Audio generation/playback failed: {e}")
            
    def mode_button_callback(self, channel):
        """Handle mode button press"""
        logger.info(f"Mode callback called - current mode: {self.current_mode}")
        
        # Interrupt any playing audio first
        self.interrupt_audio()
        
        if self.current_mode == 0:  # Currently idle
            self.current_mode = 1
        else:
            self.current_mode = (self.current_mode % 4) + 1
            
        mode_name = self.mode_names[self.current_mode]
        logger.info(f"Mode changed to: {self.current_mode} - {mode_name}")
        self.speak(f"Switched to {mode_name}")
            
    def confirm_button_callback(self, channel):
        """Handle confirm button press"""
        logger.info(f"Confirm callback called - current mode: {self.current_mode}")
        
        if self.current_mode > 0:
            mode_name = self.mode_names[self.current_mode]
            self.speak(f"{mode_name} selected")
            logger.info(f"Mode {self.current_mode} confirmed: {mode_name}")
            
            # Start the selected mode
            self.start_mode(self.current_mode)
        else:
            logger.info("No mode selected to confirm")
                
    def exit_button_callback(self, channel):
        """Handle exit button press"""
        logger.info(f"Exit callback called - current mode: {self.current_mode}")
        
        # Stop current mode first
        self.stop_current_mode()
        
        # Interrupt any playing audio
        self.interrupt_audio()
        
        self.current_mode = 0
        self.speak("Glass is now in idle mode")
        logger.info("Returned to idle mode")
            
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
        """Mode 2: OCR text recognition and reading"""
        if not self.camera:
            self.speak("Camera not available for text recognition")
            return
            
        def text_recognition_worker():
            self.camera_running = True
            logger.info("Text recognition worker started")
            
            while self.current_mode == 2 and self.camera_running:
                try:
                    logger.info("Attempting to capture frame from Pi Camera...")
                    ret, frame = self.capture_frame()
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
                            
                        time.sleep(5)  # Check every 5 seconds
                    else:
                        logger.error("Failed to capture frame from Pi Camera")
                        time.sleep(2)
                        
                except Exception as e:
                    logger.error(f"Text recognition error: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    time.sleep(5)
                    
            logger.info("Text recognition worker stopped")
                    
        self.speak("Text recognition mode activated")
        self.camera_thread = threading.Thread(target=text_recognition_worker, daemon=True)
        self.camera_thread.start()
        logger.info("Text recognition thread started")
        
    def start_object_detection_mode(self):
        """Mode 3: YOLO object detection"""
        if not self.camera or not self.yolo_model:
            self.speak("Camera or YOLO model not available for object detection")
            return
            
        def object_detection_worker():
            self.camera_running = True
            logger.info("Object detection worker started")
            
            while self.current_mode == 3 and self.camera_running:
                try:
                    logger.info("Attempting to capture frame for object detection...")
                    ret, frame = self.capture_frame()
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
                                    if conf > 0.5:  # Confidence threshold
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
                            
                        time.sleep(3)  # Update every 3 seconds
                    else:
                        logger.error("Failed to capture frame for object detection")
                        time.sleep(2)
                        
                except Exception as e:
                    logger.error(f"Object detection error: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    time.sleep(3)
                    
            logger.info("Object detection worker stopped")
                    
        self.speak("Object detection mode activated")
        self.camera_thread = threading.Thread(target=object_detection_worker, daemon=True)
        self.camera_thread.start()
        logger.info("Object detection thread started")
        
    def start_distance_measurement_mode(self):
        """Mode 4: Ultrasonic distance measurement"""
        def distance_worker():
            self.ultrasonic_running = True
            
            # First reading
            first_distance = self.measure_distance()
            self.speak(f"Initial distance reading: {first_distance:.1f} centimeters")
            
            while self.current_mode == 4 and self.ultrasonic_running:
                try:
                    distance = self.measure_distance()
                    
                    # Only speak warning if distance is less than 100 cm
                    if distance < 100:
                        self.speak(f"Warning! Distance is {distance:.1f} centimeters")
                        
                    time.sleep(1)  # Update every 1 second
                    
                except Exception as e:
                    logger.error(f"Distance measurement error: {e}")
                    time.sleep(1)
                    
        self.speak("Distance measurement mode activated")
        self.ultrasonic_thread = threading.Thread(target=distance_worker, daemon=True)
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
            
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up Smart Glass...")
        
        # Stop all threads
        self.audio_running = False
        self.button_running = False
        self.camera_running = False
        self.ultrasonic_running = False
        
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
            if current_time - self.last_button_press[self.MODE_BUTTON_PIN] > self.BUTTON_DEBOUNCE_TIME:
                self.last_button_press[self.MODE_BUTTON_PIN] = current_time
                logger.info("Mode button pressed - calling callback")
                self.mode_button_callback(self.MODE_BUTTON_PIN)
                
        if confirm_state == GPIO.HIGH:
            if current_time - self.last_button_press[self.CONFIRM_BUTTON_PIN] > self.BUTTON_DEBOUNCE_TIME:
                self.last_button_press[self.CONFIRM_BUTTON_PIN] = current_time
                logger.info("Confirm button pressed - calling callback")
                self.confirm_button_callback(self.CONFIRM_BUTTON_PIN)
                
        if exit_state == GPIO.HIGH:
            if current_time - self.last_button_press[self.EXIT_BUTTON_PIN] > self.BUTTON_DEBOUNCE_TIME:
                self.last_button_press[self.EXIT_BUTTON_PIN] = current_time
                logger.info("Exit button pressed - calling callback")
                self.exit_button_callback(self.EXIT_BUTTON_PIN)

    def run(self):
        """Main run loop"""
        try:
            logger.info("Smart Glass started. Press Ctrl+C to exit.")
            self.speak("Smart Glass is running and ready")
            
            # Main thread just keeps the application alive
            # Button monitoring is handled in separate thread
            while True:
                time.sleep(0.1)  # Small delay
                
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

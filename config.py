"""
Configuration file for Smart Glass Project
Modify these settings as needed for your setup
"""

# GPIO Pin Configuration
GPIO_CONFIG = {
    'MODE_BUTTON_PIN': 36,      # Button 1: Mode selection
    'CONFIRM_BUTTON_PIN': 38,   # Button 2: Confirm selection  
    'EXIT_BUTTON_PIN': 40,      # Button 3: Exit/Idle
    'TRIG_PIN': 7,              # Ultrasonic trigger
    'ECHO_PIN': 11,             # Ultrasonic echo
}

# Button Configuration
BUTTON_CONFIG = {
    'DEBOUNCE_TIME': 0.2,       # Seconds
    'BOUNCE_TIME': 200,         # Milliseconds for GPIO events
}

# Audio Configuration
AUDIO_CONFIG = {
    'LANGUAGE': 'en',           # Language for text-to-speech
    'SLOW_SPEECH': False,       # Slow speech for better clarity
    'VOLUME': 1.0,              # Audio volume (0.0 to 1.0)
}

# Camera Configuration
CAMERA_CONFIG = {
    'DEVICE_ID': 0,             # Camera device ID
    'FRAME_WIDTH': 640,         # Frame width
    'FRAME_HEIGHT': 480,        # Frame height
    'FPS': 30,                  # Frames per second
}

# YOLO Configuration
YOLO_CONFIG = {
    'MODEL_PATH': 'yolov8n.pt',  # YOLO model file
    'CONFIDENCE_THRESHOLD': 0.5,  # Detection confidence threshold
    'UPDATE_INTERVAL': 3,        # Seconds between detections
}

# OCR Configuration
OCR_CONFIG = {
    'UPDATE_INTERVAL': 5,       # Seconds between text recognition
    'LANGUAGE': 'eng',          # OCR language
}

# Ultrasonic Configuration
ULTRASONIC_CONFIG = {
    'WARNING_DISTANCE': 100,    # Distance in cm for warnings
    'UPDATE_INTERVAL': 5,       # Seconds between measurements
    'TIMEOUT': 0.1,             # Timeout for echo detection
    'SPEED_OF_SOUND': 343,      # Speed of sound in m/s
}

# Time Mode Configuration
TIME_CONFIG = {
    'UPDATE_INTERVAL': 60,      # Seconds between time announcements
    'TIME_FORMAT': '%I:%M %p',  # Time format string
}

# Logging Configuration
LOGGING_CONFIG = {
    'LEVEL': 'INFO',            # Log level (DEBUG, INFO, WARNING, ERROR)
    'FORMAT': '%(asctime)s - %(levelname)s - %(message)s',
    'FILE': 'smart_glass.log',  # Log file name (optional)
}

# System Configuration
SYSTEM_CONFIG = {
    'AUDIO_THREAD_SLEEP': 0.1,  # Audio thread sleep time
    'MAIN_THREAD_SLEEP': 0.1,   # Main thread sleep time
    'THREAD_TIMEOUT': 1,        # Thread join timeout
}

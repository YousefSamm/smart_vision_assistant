"""GPIO Handler for button and sensor management"""

import RPi.GPIO as GPIO
import logging

logger = logging.getLogger(__name__)


class GPIOHandler:
    """Handles all GPIO operations including buttons and sensors"""
    
    def __init__(self, config=None):
        """
        Initialize GPIO handler
        
        Args:
            config: Configuration dictionary with pin definitions
        """
        self.config = config or {}
        self.MODE_BUTTON_PIN = self.config.get('MODE_BUTTON_PIN', 36)
        self.CONFIRM_BUTTON_PIN = self.config.get('CONFIRM_BUTTON_PIN', 38)
        self.EXIT_BUTTON_PIN = self.config.get('EXIT_BUTTON_PIN', 40)
        self.TRIG_PIN = self.config.get('TRIG_PIN', 7)
        self.ECHO_PIN = self.config.get('ECHO_PIN', 11)
        
        self.setup_gpio()
    
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
        
        logger.info("GPIO setup completed - using polling method")
    
    def read_button(self, pin):
        """Read button state"""
        return GPIO.input(pin)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        GPIO.cleanup()
        logger.info("GPIO cleanup completed")


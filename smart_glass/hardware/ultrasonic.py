"""Ultrasonic sensor handler"""

import RPi.GPIO as GPIO
import time
import logging

logger = logging.getLogger(__name__)


class UltrasonicSensor:
    """Handles ultrasonic distance measurement"""
    
    def __init__(self, trig_pin=7, echo_pin=11, speed_of_sound=343):
        """
        Initialize ultrasonic sensor
        
        Args:
            trig_pin: GPIO pin for trigger
            echo_pin: GPIO pin for echo
            speed_of_sound: Speed of sound in m/s (default 343)
        """
        self.TRIG_PIN = trig_pin
        self.ECHO_PIN = echo_pin
        self.SPEED_OF_SOUND = speed_of_sound
        
        # Ensure GPIO is set up (should be done by GPIOHandler)
        GPIO.setup(self.TRIG_PIN, GPIO.OUT)
        GPIO.setup(self.ECHO_PIN, GPIO.IN)
        GPIO.output(self.TRIG_PIN, GPIO.LOW)
    
    def measure_distance(self):
        """
        Measure distance using ultrasonic sensor
        
        Returns:
            float: Distance in centimeters, or 999.0 on error
        """
        try:
            # Send trigger signal
            GPIO.output(self.TRIG_PIN, GPIO.HIGH)
            time.sleep(0.00001)  # 10 microseconds
            GPIO.output(self.TRIG_PIN, GPIO.LOW)
            
            # Wait for echo
            start_time = time.time()
            timeout_start = time.time()
            while GPIO.input(self.ECHO_PIN) == GPIO.LOW:
                start_time = time.time()
                if time.time() - timeout_start > 0.1:  # Timeout
                    return 999.0
                    
            # Measure echo duration
            end_time = time.time()
            while GPIO.input(self.ECHO_PIN) == GPIO.HIGH:
                end_time = time.time()
                if time.time() - start_time > 0.1:  # Timeout
                    return 999.0
                    
            # Calculate distance
            duration = end_time - start_time
            distance = (duration * self.SPEED_OF_SOUND * 100) / 2  # Convert to cm
            
            return max(0, distance)
            
        except Exception as e:
            logger.error(f"Distance measurement failed: {e}")
            return 999.0


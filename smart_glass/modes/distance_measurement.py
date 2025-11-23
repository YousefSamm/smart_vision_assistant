"""Distance measurement mode implementation"""

import time
import logging
from .base_mode import BaseMode

logger = logging.getLogger(__name__)


class DistanceMeasurementMode(BaseMode):
    """Mode 4: Ultrasonic distance measurement"""
    
    def __init__(self, audio_queue, ultrasonic_sensor):
        super().__init__(audio_queue, mode_id=4, mode_name="Distance Measurement Mode")
        self.ultrasonic_sensor = ultrasonic_sensor
        self.warning_distance = 100  # cm
        self.update_interval = 1  # Update every 1 second
    
    def _run(self):
        """Distance measurement worker"""
        self.speak("Distance measurement mode activated")
        
        # First reading
        first_distance = self.ultrasonic_sensor.measure_distance()
        self.speak(f"Initial distance reading: {first_distance:.1f} centimeters")
        
        while self.running:
            try:
                distance = self.ultrasonic_sensor.measure_distance()
                
                # Only speak warning if distance is less than warning distance
                if distance < self.warning_distance:
                    self.speak(f"Warning! Distance is {distance:.1f} centimeters")
                    
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Distance measurement error: {e}")
                time.sleep(self.update_interval)


"""Time mode implementation"""

import time
import logging
from .base_mode import BaseMode

logger = logging.getLogger(__name__)


class TimeMode(BaseMode):
    """Mode 1: Tell the time"""
    
    def __init__(self, audio_queue):
        super().__init__(audio_queue, mode_id=1, mode_name="Time Mode")
        self.update_interval = 60  # Update every minute
    
    def _run(self):
        """Time mode worker"""
        self.speak("Time mode activated")
        
        while self.running:
            current_time = time.strftime("%I:%M %p")
            self.speak(f"The current time is {current_time}")
            time.sleep(self.update_interval)


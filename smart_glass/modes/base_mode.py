"""Base class for all modes"""

import threading
import logging

logger = logging.getLogger(__name__)


class BaseMode:
    """Base class for all operational modes"""
    
    def __init__(self, audio_queue, mode_id, mode_name):
        """
        Initialize base mode
        
        Args:
            audio_queue: AudioQueue instance for speaking
            mode_id: Unique mode identifier
            mode_name: Human-readable mode name
        """
        self.audio_queue = audio_queue
        self.mode_id = mode_id
        self.mode_name = mode_name
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the mode"""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"{self.mode_name} started")
    
    def stop(self):
        """Stop the mode"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        logger.info(f"{self.mode_name} stopped")
    
    def _run(self):
        """Override this method in subclasses"""
        raise NotImplementedError("Subclasses must implement _run method")
    
    def speak(self, text):
        """Convenience method to add text to audio queue"""
        self.audio_queue.speak(text)


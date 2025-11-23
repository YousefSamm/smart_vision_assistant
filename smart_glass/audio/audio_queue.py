"""Audio queue management"""

import queue
import threading
import logging

logger = logging.getLogger(__name__)


class AudioQueue:
    """Manages audio queue and playback thread"""
    
    def __init__(self, tts_engine):
        """
        Initialize audio queue
        
        Args:
            tts_engine: TTSEngine instance for generating audio
        """
        self.audio_queue = queue.Queue()
        self.audio_thread = None
        self.audio_running = False
        self.tts_engine = tts_engine
    
    def start(self):
        """Start audio processing thread"""
        self.audio_running = True
        self.audio_thread = threading.Thread(target=self._audio_worker, daemon=True)
        self.audio_thread.start()
        logger.info("Audio thread started")
    
    def stop(self):
        """Stop audio processing thread"""
        self.audio_running = False
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1)
    
    def speak(self, text):
        """Add text to audio queue for speech"""
        try:
            self.audio_queue.put(text)
            logger.info(f"Added to speech queue: {text}")
        except Exception as e:
            logger.error(f"Failed to add text to speech queue: {e}")
    
    def interrupt(self):
        """Interrupt any currently playing audio and clear the queue"""
        try:
            self.tts_engine.stop()
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
    
    def _audio_worker(self):
        """Audio processing worker thread"""
        import time
        while self.audio_running:
            try:
                if not self.audio_queue.empty():
                    text = self.audio_queue.get()
                    self.tts_engine.speak(text)
                    
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Audio worker error: {e}")


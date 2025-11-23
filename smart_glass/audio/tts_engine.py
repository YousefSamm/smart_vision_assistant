"""Text-to-Speech engine"""

import pygame
import os
import time
from gtts import gTTS
import logging

logger = logging.getLogger(__name__)


class TTSEngine:
    """Handles text-to-speech conversion and playback"""
    
    def __init__(self, language='en', slow=False):
        """
        Initialize TTS engine
        
        Args:
            language: Language code for TTS (default: 'en')
            slow: Whether to use slow speech (default: False)
        """
        self.language = language
        self.slow = slow
        self.setup_audio()
    
    def setup_audio(self):
        """Initialize pygame audio"""
        pygame.mixer.init()
        logger.info("Audio system initialized")
    
    def speak(self, text):
        """Generate and play audio from text"""
        try:
            # Create temporary audio file
            tts = gTTS(text=text, lang=self.language, slow=self.slow)
            temp_file = f"/tmp/smart_glass_{int(time.time())}.mp3"
            tts.save(temp_file)
            
            # Play audio and wait for completion
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
            # Clean up
            pygame.mixer.music.unload()
            os.remove(temp_file)
            
            logger.info(f"Audio completed: {text}")
            
        except Exception as e:
            logger.error(f"Audio generation/playback failed: {e}")
    
    def stop(self):
        """Stop any currently playing audio"""
        try:
            pygame.mixer.music.stop()
            logger.info("Audio stopped")
        except Exception as e:
            logger.error(f"Failed to stop audio: {e}")
    
    def cleanup(self):
        """Clean up audio resources"""
        pygame.mixer.quit()
        logger.info("Audio cleanup completed")


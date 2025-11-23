#!/usr/bin/env python3
"""
Smart Glass Project - Raspberry Pi 4B
Main entry point for the Smart Vision Assistant
"""

import time
import threading
import logging

from .hardware import GPIOHandler, CameraHandler, UltrasonicSensor
from .audio import TTSEngine, AudioQueue
from .modes import (
    TimeMode,
    TextRecognitionMode,
    ObjectDetectionMode,
    DistanceMeasurementMode
)
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class SmartGlass:
    """Main Smart Glass controller"""
    
    def __init__(self, config=None):
        """
        Initialize Smart Glass system
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
        
        # System state
        self.current_mode = 0  # 0 = idle, 1-4 = active modes
        self.mode_names = {
            0: "idle mode",
            1: "time mode",
            2: "text recognition and reading mode",
            3: "object detection mode",
            4: "distance measurements mode"
        }
        
        # Button debouncing
        self.BUTTON_DEBOUNCE_TIME = 0.5
        self.last_button_press = {}
        
        # Initialize hardware
        self.gpio_handler = GPIOHandler(self.config)
        self.camera_handler = CameraHandler()
        self.ultrasonic_sensor = UltrasonicSensor(
            trig_pin=self.gpio_handler.TRIG_PIN,
            echo_pin=self.gpio_handler.ECHO_PIN
        )
        
        # Initialize audio
        self.tts_engine = TTSEngine()
        self.audio_queue = AudioQueue(self.tts_engine)
        self.audio_queue.start()
        
        # Initialize button tracking
        self.last_button_press = {
            self.gpio_handler.MODE_BUTTON_PIN: 0,
            self.gpio_handler.CONFIRM_BUTTON_PIN: 0,
            self.gpio_handler.EXIT_BUTTON_PIN: 0
        }
        
        # Mode instances
        self.current_mode_instance = None
        self.mode_instances = {
            1: TimeMode(self.audio_queue),
            2: TextRecognitionMode(self.audio_queue, self.camera_handler),
            3: ObjectDetectionMode(self.audio_queue, self.camera_handler),
            4: DistanceMeasurementMode(self.audio_queue, self.ultrasonic_sensor)
        }
        
        # Button monitoring thread
        self.button_thread = None
        self.button_running = False
        self.start_button_thread()
        
        # Welcome message
        self.audio_queue.speak("Welcome to Smart Glass! Ready to assist you.")
    
    def start_button_thread(self):
        """Start button monitoring thread"""
        self.button_running = True
        self.button_thread = threading.Thread(target=self._button_worker, daemon=True)
        self.button_thread.start()
        logger.info("Button monitoring thread started")
    
    def _button_worker(self):
        """Button monitoring worker thread"""
        while self.button_running:
            try:
                self._check_buttons()
                time.sleep(0.05)  # Check buttons every 50ms
            except Exception as e:
                logger.error(f"Button worker error: {e}")
                time.sleep(0.1)
    
    def _check_buttons(self):
        """Check button states using polling"""
        current_time = time.time()
        
        # Get current button states
        mode_state = self.gpio_handler.read_button(self.gpio_handler.MODE_BUTTON_PIN)
        confirm_state = self.gpio_handler.read_button(self.gpio_handler.CONFIRM_BUTTON_PIN)
        exit_state = self.gpio_handler.read_button(self.gpio_handler.EXIT_BUTTON_PIN)
        
        # Mode button
        if mode_state:
            if (current_time - self.last_button_press[self.gpio_handler.MODE_BUTTON_PIN] > 
                self.BUTTON_DEBOUNCE_TIME):
                self.last_button_press[self.gpio_handler.MODE_BUTTON_PIN] = current_time
                logger.info("Mode button pressed")
                self._handle_mode_button()
        
        # Confirm button
        if confirm_state:
            if (current_time - self.last_button_press[self.gpio_handler.CONFIRM_BUTTON_PIN] > 
                self.BUTTON_DEBOUNCE_TIME):
                self.last_button_press[self.gpio_handler.CONFIRM_BUTTON_PIN] = current_time
                logger.info("Confirm button pressed")
                self._handle_confirm_button()
        
        # Exit button
        if exit_state:
            if (current_time - self.last_button_press[self.gpio_handler.EXIT_BUTTON_PIN] > 
                self.BUTTON_DEBOUNCE_TIME):
                self.last_button_press[self.gpio_handler.EXIT_BUTTON_PIN] = current_time
                logger.info("Exit button pressed")
                self._handle_exit_button()
    
    def _handle_mode_button(self):
        """Handle mode button press"""
        logger.info(f"Mode callback called - current mode: {self.current_mode}")
        
        # Interrupt any playing audio first
        self.audio_queue.interrupt()
        
        if self.current_mode == 0:  # Currently idle
            self.current_mode = 1
        else:
            self.current_mode = (self.current_mode % 4) + 1
        
        mode_name = self.mode_names[self.current_mode]
        logger.info(f"Mode changed to: {self.current_mode} - {mode_name}")
        self.audio_queue.speak(f"Switched to {mode_name}")
    
    def _handle_confirm_button(self):
        """Handle confirm button press"""
        logger.info(f"Confirm callback called - current mode: {self.current_mode}")
        
        # Interrupt any playing audio first
        self.audio_queue.interrupt()
        
        if self.current_mode > 0:
            mode_name = self.mode_names[self.current_mode]
            self.audio_queue.speak(f"{mode_name} selected")
            logger.info(f"Mode {self.current_mode} confirmed: {mode_name}")
            
            # Start the selected mode
            self._start_mode(self.current_mode)
        else:
            logger.info("No mode selected to confirm")
    
    def _handle_exit_button(self):
        """Handle exit button press"""
        logger.info(f"Exit callback called - current mode: {self.current_mode}")
        
        # Stop current mode first
        self._stop_current_mode()
        
        # Interrupt any playing audio
        self.audio_queue.interrupt()
        
        self.current_mode = 0
        self.audio_queue.speak("Glass is now in idle mode")
        logger.info("Returned to idle mode")
    
    def _start_mode(self, mode):
        """Start the specified mode"""
        self._stop_current_mode()  # Stop any running mode
        
        if mode in self.mode_instances:
            self.current_mode_instance = self.mode_instances[mode]
            self.current_mode_instance.start()
            logger.info(f"Mode {mode} started")
        else:
            logger.error(f"Invalid mode: {mode}")
    
    def _stop_current_mode(self):
        """Stop all running modes"""
        if self.current_mode_instance:
            self.current_mode_instance.stop()
            self.current_mode_instance = None
            logger.info("Current mode stopped")
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up Smart Glass...")
        
        # Stop all threads
        self.button_running = False
        self.audio_queue.stop()
        
        # Stop current mode
        self._stop_current_mode()
        
        # Wait for threads to finish
        if self.button_thread and self.button_thread.is_alive():
            self.button_thread.join(timeout=1)
        
        # Clean up hardware
        self.tts_engine.cleanup()
        self.gpio_handler.cleanup()
        
        logger.info("Cleanup completed")
    
    def run(self):
        """Main run loop"""
        try:
            logger.info("Smart Glass started. Press Ctrl+C to exit.")
            self.audio_queue.speak("Smart Glass is running and ready")
            
            # Main thread just keeps the application alive
            # Button monitoring is handled in separate thread
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    try:
        # Try to load config if available
        try:
            import sys
            import os
            # Add parent directory to path to import config
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            import config
            config_dict = {
                'MODE_BUTTON_PIN': getattr(config, 'MODE_BUTTON_PIN', 36),
                'CONFIRM_BUTTON_PIN': getattr(config, 'CONFIRM_BUTTON_PIN', 38),
                'EXIT_BUTTON_PIN': getattr(config, 'EXIT_BUTTON_PIN', 40),
                'TRIG_PIN': getattr(config, 'TRIG_PIN', 7),
                'ECHO_PIN': getattr(config, 'ECHO_PIN', 11),
            }
        except ImportError:
            config_dict = None
        
        smart_glass = SmartGlass(config=config_dict)
        smart_glass.run()
    except Exception as e:
        logger.error(f"Smart Glass failed to start: {e}")
        import traceback
        logger.error(traceback.format_exc())
        import RPi.GPIO as GPIO
        GPIO.cleanup()


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Button Testing Utility for Smart Glass Project
Use this to test button connections before running the main application
"""

import RPi.GPIO as GPIO
import time
import sys

# GPIO Pin definitions (same as main application)
MODE_BUTTON_PIN = 36      # Button 1: Mode selection
CONFIRM_BUTTON_PIN = 38   # Button 2: Confirm selection
EXIT_BUTTON_PIN = 40      # Button 3: Exit/Idle

def setup_gpio():
    """Initialize GPIO pins for testing"""
    GPIO.setmode(GPIO.BOARD)
    
    # Setup input pins with pull-down resistors
    GPIO.setup(MODE_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(CONFIRM_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(EXIT_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    print("GPIO setup completed")
    print(f"Mode Button: Pin {MODE_BUTTON_PIN}")
    print(f"Confirm Button: Pin {CONFIRM_BUTTON_PIN}")
    print(f"Exit Button: Pin {EXIT_BUTTON_PIN}")
    print("Press buttons to test. Press Ctrl+C to exit.\n")

def test_buttons():
    """Test button functionality"""
    try:
        setup_gpio()
        
        print("Button Test Started!")
        print("Press each button to verify connections...")
        
        while True:
            # Check Mode Button
            if GPIO.input(MODE_BUTTON_PIN) == GPIO.HIGH:
                print("✓ Mode Button (Pin 36) - PRESSED")
                time.sleep(0.5)  # Debounce
                
            # Check Confirm Button
            if GPIO.input(CONFIRM_BUTTON_PIN) == GPIO.HIGH:
                print("✓ Confirm Button (Pin 38) - PRESSED")
                time.sleep(0.5)  # Debounce
                
            # Check Exit Button
            if GPIO.input(EXIT_BUTTON_PIN) == GPIO.HIGH:
                print("✓ Exit Button (Pin 40) - PRESSED")
                time.sleep(0.5)  # Debounce
                
            time.sleep(0.1)  # Small delay to prevent high CPU usage
            
    except KeyboardInterrupt:
        print("\nButton test stopped by user")
    except Exception as e:
        print(f"Error during button test: {e}")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup completed")

if __name__ == "__main__":
    try:
        test_buttons()
    except Exception as e:
        print(f"Failed to start button test: {e}")
        GPIO.cleanup()
        sys.exit(1)

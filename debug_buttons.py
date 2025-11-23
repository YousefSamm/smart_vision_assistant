#!/usr/bin/env python3
"""
Debug version to test button detection logic
"""

import RPi.GPIO as GPIO
import time

class ButtonDebug:
    def __init__(self):
        # GPIO Pin definitions
        self.MODE_BUTTON_PIN = 36      # Button 1: Mode selection
        self.CONFIRM_BUTTON_PIN = 38   # Button 2: Confirm selection
        self.EXIT_BUTTON_PIN = 40      # Button 3: Exit/Idle
        
        # Button debouncing
        self.BUTTON_DEBOUNCE_TIME = 0.2
        self.last_button_press = {
            self.MODE_BUTTON_PIN: 0,
            self.CONFIRM_BUTTON_PIN: 0,
            self.EXIT_BUTTON_PIN: 0
        }
        
        # System state
        self.current_mode = 0  # 0 = idle, 1-4 = active modes
        self.mode_names = {
            0: "idle mode",
            1: "time mode",
            2: "text recognition and reading mode",
            3: "object detection mode",
            4: "distance measurements mode"
        }
        
        # Initialize GPIO
        self.setup_gpio()
        
    def setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BOARD)
        
        # Setup input pins with pull-down resistors
        GPIO.setup(self.MODE_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.CONFIRM_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.EXIT_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        print("GPIO setup completed")
        
    def check_buttons(self):
        """Check button states using polling"""
        current_time = time.time()
        
        # Check Mode Button
        mode_pressed = (GPIO.input(self.MODE_BUTTON_PIN) == GPIO.HIGH and 
                       current_time - self.last_button_press[self.MODE_BUTTON_PIN] > self.BUTTON_DEBOUNCE_TIME)
        
        # Check Confirm Button
        confirm_pressed = (GPIO.input(self.CONFIRM_BUTTON_PIN) == GPIO.HIGH and 
                          current_time - self.last_button_press[self.CONFIRM_BUTTON_PIN] > self.BUTTON_DEBOUNCE_TIME)
        
        # Check Exit Button
        exit_pressed = (GPIO.input(self.EXIT_BUTTON_PIN) == GPIO.HIGH and 
                       current_time - self.last_button_press[self.EXIT_BUTTON_PIN] > self.BUTTON_DEBOUNCE_TIME)
        
        # Print debug info
        print(f"\rMode: {GPIO.input(self.MODE_BUTTON_PIN)} | Confirm: {GPIO.input(self.CONFIRM_BUTTON_PIN)} | Exit: {GPIO.input(self.EXIT_BUTTON_PIN)} | Mode: {self.current_mode}", end="")
        
        # Handle Mode Button
        if mode_pressed:
            self.last_button_press[self.MODE_BUTTON_PIN] = current_time
            print(f"\n✓ MODE BUTTON PRESSED! Current mode: {self.current_mode}")
            if self.current_mode == 0:  # Currently idle
                self.current_mode = 1
            else:
                self.current_mode = (self.current_mode % 4) + 1
            mode_name = self.mode_names[self.current_mode]
            print(f"  → Switched to: {mode_name}")
            
        # Handle Confirm Button
        if confirm_pressed:
            self.last_button_press[self.CONFIRM_BUTTON_PIN] = current_time
            print(f"\n✓ CONFIRM BUTTON PRESSED! Mode {self.current_mode}")
            if self.current_mode > 0:
                mode_name = self.mode_names[self.current_mode]
                print(f"  → {mode_name} selected")
            else:
                print("  → No mode selected")
                
        # Handle Exit Button
        if exit_pressed:
            self.last_button_press[self.EXIT_BUTTON_PIN] = current_time
            print(f"\n✓ EXIT BUTTON PRESSED!")
            self.current_mode = 0
            print(f"  → Returned to idle mode")
            
    def run(self):
        """Main debug loop"""
        try:
            print("Button Debug Started!")
            print("Press buttons to test. Press Ctrl+C to exit.")
            print("Format: Mode | Confirm | Exit | Current Mode")
            print("-" * 50)
            
            while True:
                self.check_buttons()
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nStopping debug...")
        finally:
            GPIO.cleanup()
            print("GPIO cleanup completed")

if __name__ == "__main__":
    try:
        debug = ButtonDebug()
        debug.run()
    except Exception as e:
        print(f"Debug failed to start: {e}")
        GPIO.cleanup()

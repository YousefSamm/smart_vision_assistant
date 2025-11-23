# Smart Glass Project - Raspberry Pi 4B

A smart glass system with 4 operational modes controlled by 3 push buttons.

## Hardware Requirements

- Raspberry Pi 4B
- Pi Camera Module
- 3 Push Buttons with external pull-down resistors
- HC-SR04 Ultrasonic Sensor
- Audio output (speakers/headphones)

## Pin Connections

### Buttons (with external pull-down resistors)
- **Button 1 (Mode Selection)**: GPIO 36 (BOARD pin 36)
- **Button 2 (Confirm)**: GPIO 38 (BOARD pin 38)  
- **Button 3 (Exit/Idle)**: GPIO 40 (BOARD pin 40)

### Ultrasonic Sensor
- **TRIG**: GPIO 7 (BOARD pin 7)
- **ECHO**: GPIO 11 (BOARD pin 11)

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install system packages:**
   ```bash
   sudo apt update
   sudo apt install tesseract-ocr
   sudo apt install python3-pygame
   ```

3. **Enable camera and I2C in raspi-config:**
   ```bash
   sudo raspi-config
   ```

## Usage

### Starting the System
```bash
python3 smart_glass.py
```

### Button Operations

1. **Button 1**: Cycle through 4 modes
2. **Button 2**: Confirm and activate selected mode
3. **Button 3**: Exit current mode and return to idle

### Modes

1. **Time Mode**: Announces current time every minute
2. **Text Recognition**: Uses OCR to read text from camera
3. **Object Detection**: YOLOv8 object detection with audio description
4. **Distance Measurement**: Ultrasonic distance monitoring with warnings

## Features

- Button debouncing (200ms)
- Multi-threaded operation
- Audio feedback for all operations
- Automatic mode switching
- Distance warnings below 100cm
- Comprehensive logging

## Troubleshooting

- **Camera issues**: Check camera connections and enable in raspi-config
- **Audio issues**: Ensure audio output is configured
- **GPIO errors**: Verify button connections and pull-down resistors
- **YOLO slow**: Consider using TensorFlow Lite for better performance

## File Structure

- `smart_glass.py` - Main application
- `requirements.txt` - Python dependencies
- `config.py` - Configuration settings
- `test_buttons.py` - Button testing utility
- `README.md` - This file

# Smart Vision Assistant - Raspberry Pi 4B

A professional smart glass system with 4 operational modes controlled by 3 push buttons.

## 🎯 Features

- **Time Mode**: Announces current time every minute
- **Text Recognition**: Uses OCR to read text from camera feed
- **Object Detection**: YOLOv8 object detection with audio description
- **Distance Measurement**: Ultrasonic distance monitoring with warnings
- **Audio Feedback**: Text-to-speech for all operations
- **Button Control**: 3-button interface for mode selection
- **Multi-threaded**: Efficient concurrent operation
- **Professional Architecture**: Modular, maintainable codebase

## 📋 Hardware Requirements

- Raspberry Pi 4B
- Pi Camera Module
- 3 Push Buttons with external pull-down resistors
- HC-SR04 Ultrasonic Sensor
- Audio output (speakers/headphones)

## 🔌 Pin Connections

### Buttons (with external pull-down resistors)
- **Button 1 (Mode Selection)**: GPIO 36 (BOARD pin 36)
- **Button 2 (Confirm)**: GPIO 38 (BOARD pin 38)  
- **Button 3 (Exit/Idle)**: GPIO 40 (BOARD pin 40)

### Ultrasonic Sensor
- **TRIG**: GPIO 7 (BOARD pin 7)
- **ECHO**: GPIO 11 (BOARD pin 11)

See `docs/wiring_diagram.md` for detailed wiring information.

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YousefSamm/smart_vision_assistant.git
cd smart_vision_assistant
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Or install as a package:
```bash
pip install -e .
```

### 3. Install System Packages
```bash
sudo apt update
sudo apt install tesseract-ocr python3-pygame libcamera-tools
```

### 4. Enable Camera
```bash
sudo raspi-config
```
Navigate to Interface Options → Camera → Enable

### 5. Run Installation Script (Optional)
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

## 💻 Usage

### Starting the System

**Option 1: Using the run script**
```bash
python3 run.py
```

**Option 2: Using the module directly**
```bash
python3 -m smart_glass.main
```

**Option 3: Using the installed command (after pip install -e .)**
```bash
smart-glass
```

### Button Operations

1. **Button 1 (Mode)**: Cycle through 4 modes
   - Press to switch: Idle → Time → Text Recognition → Object Detection → Distance Measurement → Idle
   - Interrupts current audio and announces new mode

2. **Button 2 (Confirm)**: Confirm and activate selected mode
   - Activates the currently selected mode
   - Interrupts any playing audio

3. **Button 3 (Exit)**: Exit current mode and return to idle
   - Stops current mode operation
   - Returns to idle state

### Modes

#### 1. Time Mode
- Announces current time every minute
- Format: "The current time is HH:MM AM/PM"

#### 2. Text Recognition Mode
- Captures frames from camera every 5 seconds
- Performs OCR using Tesseract
- Speaks detected text: "I can see the following text: [text]"

#### 3. Object Detection Mode
- Uses YOLOv8 for real-time object detection
- Updates every 3 seconds
- Speaks detected objects: "I can see one person, two chairs"

#### 4. Distance Measurement Mode
- Takes initial distance reading when activated
- Continuously monitors distance every 1 second
- Warns when distance < 100cm: "Warning! Distance is X.X centimeters"

## 📁 Project Structure

```
smart_vision_assistant/
├── smart_glass/              # Main package
│   ├── __init__.py
│   ├── main.py               # Main entry point
│   ├── config.py             # Configuration (optional)
│   │
│   ├── hardware/             # Hardware interfaces
│   │   ├── __init__.py
│   │   ├── gpio_handler.py  # GPIO button handling
│   │   ├── camera_handler.py # Camera operations
│   │   └── ultrasonic.py     # Ultrasonic sensor
│   │
│   ├── modes/                # Mode implementations
│   │   ├── __init__.py
│   │   ├── base_mode.py      # Base class for modes
│   │   ├── time_mode.py
│   │   ├── text_recognition.py
│   │   ├── object_detection.py
│   │   └── distance_measurement.py
│   │
│   ├── audio/                # Audio handling
│   │   ├── __init__.py
│   │   ├── tts_engine.py     # Text-to-speech
│   │   └── audio_queue.py    # Audio queue management
│   │
│   └── utils/                # Utilities
│       ├── __init__.py
│       └── logger.py         # Logging utilities
│
├── tests/                    # Test files
│   ├── __init__.py
│   ├── test_buttons.py
│   ├── test_camera.py
│   └── test_display.py
│
├── scripts/                  # Utility scripts
│   └── install.sh
│
├── docs/                     # Documentation
│   └── wiring_diagram.md
│
├── .gitignore
├── LICENSE
├── README.md                 # This file
├── requirements.txt
├── setup.py                  # Package installation
└── run.py                    # Entry point script
```

## ⚙️ Configuration

You can customize the system by creating a `config.py` file in the root directory:

```python
# GPIO Pin Configuration
MODE_BUTTON_PIN = 36
CONFIRM_BUTTON_PIN = 38
EXIT_BUTTON_PIN = 40
TRIG_PIN = 7
ECHO_PIN = 11

# Button Configuration
BUTTON_DEBOUNCE_TIME = 0.5  # seconds
```

See `config.py` (if exists) for more configuration options.

## 🐛 Troubleshooting

### Camera Issues
- **No camera detected**: Check camera connections and enable in raspi-config
- **Camera access denied**: Run with `sudo` or add user to video group: `sudo usermod -a -G video $USER`
- **OpenCV errors**: Install libcamera-tools: `sudo apt install libcamera-tools`

### Audio Issues
- **No audio output**: Check audio output configuration: `sudo raspi-config` → Advanced Options → Audio
- **TTS not working**: Ensure internet connection for gTTS (or use offline TTS)

### GPIO Errors
- **Permission denied**: Run with `sudo` or add user to gpio group: `sudo usermod -a -G gpio $USER`
- **Button not responding**: Verify button connections and pull-down resistors

### Performance Issues
- **YOLO slow**: Consider using TensorFlow Lite or smaller YOLO model
- **High CPU usage**: Reduce update intervals in mode configurations

## 🧪 Testing

Run individual test scripts:
```bash
python3 tests/test_buttons.py
python3 tests/test_camera.py
python3 tests/test_display.py
```

## 📝 Development

### Adding a New Mode

1. Create a new file in `smart_glass/modes/`
2. Inherit from `BaseMode`
3. Implement the `_run()` method
4. Add to `smart_glass/modes/__init__.py`
5. Register in `smart_glass/main.py`

### Code Style

- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings to all classes and methods
- Keep functions focused and modular

## 📄 License

See LICENSE file for details.

## 👤 Author

**Yousef Samm**

- GitHub: [@YousefSamm](https://github.com/YousefSamm)

## 🙏 Acknowledgments

- YOLOv8 by Ultralytics
- Tesseract OCR
- Raspberry Pi Foundation
- OpenCV community

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Note**: This project requires Raspberry Pi 4B with proper hardware setup. Ensure all connections are secure before running the system.

#!/bin/bash

# Smart Glass Project Installation Script
# For Raspberry Pi 4B

echo "=== Smart Glass Project Installation ==="
echo "This script will install all required dependencies"
echo ""

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3-pip python3-venv
sudo apt install -y tesseract-ocr tesseract-ocr-eng
sudo apt install -y python3-pygame
sudo apt install -y libatlas-base-dev  # For numpy optimization
sudo apt install -y libhdf5-dev libhdf5-serial-dev
sudo apt install -y libjasper-dev libqtcore4 libqtgui4 libqt4-test

# Enable camera and I2C
echo "Enabling camera and I2C interfaces..."
sudo raspi-config nonint do_camera 0
sudo raspi-config nonint do_i2c 0

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv smart_glass_env
source smart_glass_env/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install TensorFlow for ARM
echo "Installing TensorFlow for ARM..."
pip install tensorflow==2.10.0

# Download YOLOv8 model
echo "Downloading YOLOv8 model..."
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Set permissions
echo "Setting permissions..."
chmod +x smart_glass.py
chmod +x test_buttons.py

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "To activate the environment:"
echo "source smart_glass_env/bin/activate"
echo ""
echo "To test buttons:"
echo "python3 test_buttons.py"
echo ""
echo "To run the main application:"
echo "python3 smart_glass.py"
echo ""
echo "Note: You may need to reboot for camera/I2C changes to take effect"

#!/usr/bin/env python3
"""
Camera Test Script for Raspberry Pi Camera
Run this to diagnose camera issues
"""

import subprocess
import os
import sys

def test_libcamera():
    """Test libcamera-still"""
    print("=== Testing libcamera-still ===")
    try:
        # Check if libcamera-still is available
        result = subprocess.run(["which", "libcamera-still"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ libcamera-still found at: {result.stdout.strip()}")
            
            # Test camera capture
            print("Testing camera capture...")
            test_cmd = ["libcamera-still", "--timeout", "1000", "--output", "/tmp/test_camera.jpg"]
            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print("✓ Camera capture successful!")
                if os.path.exists("/tmp/test_camera.jpg"):
                    size = os.path.getsize("/tmp/test_camera.jpg")
                    print(f"✓ Image saved: /tmp/test_camera.jpg ({size} bytes)")
                    # Clean up
                    os.remove("/tmp/test_camera.jpg")
                else:
                    print("✗ Image file not found")
            else:
                print(f"✗ Camera capture failed: {result.stderr}")
        else:
            print("✗ libcamera-still not found")
            
    except subprocess.TimeoutExpired:
        print("✗ Camera test timed out")
    except Exception as e:
        print(f"✗ libcamera test error: {e}")

def test_vcgencmd():
    """Test vcgencmd camera detection"""
    print("\n=== Testing vcgencmd camera detection ===")
    try:
        result = subprocess.run(["vcgencmd", "get_camera"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ vcgencmd result: {result.stdout.strip()}")
        else:
            print(f"✗ vcgencmd failed: {result.stderr}")
    except Exception as e:
        print(f"✗ vcgencmd error: {e}")

def test_video_devices():
    """Test video device files"""
    print("\n=== Testing video devices ===")
    video_devices = []
    for i in range(10):
        device = f"/dev/video{i}"
        if os.path.exists(device):
            video_devices.append(device)
            print(f"✓ Found video device: {device}")
    
    if not video_devices:
        print("✗ No video devices found")
    else:
        print(f"✓ Total video devices: {len(video_devices)}")

def test_opencv():
    """Test OpenCV camera access"""
    print("\n=== Testing OpenCV camera access ===")
    try:
        import cv2
        print(f"✓ OpenCV version: {cv2.__version__}")
        
        # Test each video device
        for i in range(4):
            device = f"/dev/video{i}"
            if os.path.exists(device):
                print(f"Testing {device}...")
                cap = cv2.VideoCapture(device)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        print(f"✓ {device} working - Frame shape: {frame.shape}")
                    else:
                        print(f"✗ {device} opened but cannot read frames")
                    cap.release()
                else:
                    print(f"✗ {device} cannot be opened")
            else:
                print(f"✗ {device} does not exist")
                
    except ImportError:
        print("✗ OpenCV not installed")
    except Exception as e:
        print(f"✗ OpenCV test error: {e}")

def test_camera_config():
    """Test camera configuration"""
    print("\n=== Testing camera configuration ===")
    try:
        # Check if camera is enabled in config
        result = subprocess.run(["raspi-config", "nonint", "get_camera"], capture_output=True, text=True)
        if result.returncode == 0:
            camera_enabled = result.stdout.strip() == "0"
            if camera_enabled:
                print("✓ Camera is enabled in raspi-config")
            else:
                print("✗ Camera is disabled in raspi-config")
                print("  Run: sudo raspi-config")
                print("  Interface Options → Camera → Enable")
        else:
            print("✗ Could not check camera config")
            
    except Exception as e:
        print(f"✗ Config check error: {e}")

def main():
    """Run all camera tests"""
    print("Raspberry Pi Camera Diagnostic Tool")
    print("=" * 40)
    
    test_libcamera()
    test_vcgencmd()
    test_video_devices()
    test_opencv()
    test_camera_config()
    
    print("\n=== Summary ===")
    print("If camera tests failed, try:")
    print("1. Enable camera in raspi-config")
    print("2. Install libcamera-tools: sudo apt install libcamera-tools")
    print("3. Reboot the system")
    print("4. Check camera cable connection")

if __name__ == "__main__":
    main()

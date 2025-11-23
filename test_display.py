#!/usr/bin/env python3
"""
Display Test Script for Smart Glass
Tests OpenCV display functionality with different backends
"""

import cv2
import numpy as np
import os

def test_display_backends():
    """Test different OpenCV display backends"""
    print("=== Testing OpenCV Display Backends ===")
    
    # Set environment variables
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    os.environ['DISPLAY'] = ':0'
    
    # Create test frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, "DISPLAY TEST", (200, 200), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, "If you see this, display works!", (150, 250), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "Press any key to continue...", (180, 300), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    # Test 1: Normal window
    print("\n1. Testing WINDOW_NORMAL...")
    try:
        cv2.namedWindow("Test Normal", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Test Normal", 800, 600)
        cv2.imshow("Test Normal", frame)
        print("✓ WINDOW_NORMAL created successfully")
        print("Press any key in the window to continue...")
        cv2.waitKey(0)
        cv2.destroyWindow("Test Normal")
    except Exception as e:
        print(f"✗ WINDOW_NORMAL failed: {e}")
    
    # Test 2: Autosize window
    print("\n2. Testing WINDOW_AUTOSIZE...")
    try:
        cv2.namedWindow("Test Autosize", cv2.WINDOW_AUTOSIZE)
        cv2.imshow("Test Autosize", frame)
        print("✓ WINDOW_AUTOSIZE created successfully")
        print("Press any key in the window to continue...")
        cv2.waitKey(0)
        cv2.destroyWindow("Test Autosize")
    except Exception as e:
        print(f"✗ WINDOW_AUTOSIZE failed: {e}")
    
    # Test 3: Default window
    print("\n3. Testing default window...")
    try:
        cv2.namedWindow("Test Default")
        cv2.imshow("Test Default", frame)
        print("✓ Default window created successfully")
        print("Press any key in the window to continue...")
        cv2.waitKey(0)
        cv2.destroyWindow("Test Default")
    except Exception as e:
        print(f"✗ Default window failed: {e}")
    
    cv2.destroyAllWindows()
    print("\n✓ Display tests completed")

def test_camera_display():
    """Test camera with display"""
    print("\n=== Testing Camera with Display ===")
    
    # Try to open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("✗ Could not open camera")
        return
    
    print("✓ Camera opened successfully")
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Create display window
    cv2.namedWindow("Camera Test", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera Test", 800, 600)
    
    print("Camera test window opened. Press 'q' to quit...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("✗ Failed to read frame from camera")
            break
        
        # Add text overlay
        cv2.putText(frame, "CAMERA TEST - Press 'q' to quit", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {frame.shape}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("Camera Test", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("✓ Camera test completed")

def main():
    """Run all display tests"""
    print("Smart Glass Display Test Tool")
    print("=" * 40)
    
    test_display_backends()
    test_camera_display()
    
    print("\n=== Summary ===")
    print("If display tests failed:")
    print("1. Install Qt5: sudo apt install qt5-default")
    print("2. Check display: echo $DISPLAY")
    print("3. Make sure you're running on the Pi directly (not SSH)")
    print("4. Try: export QT_QPA_PLATFORM=xcb")

if __name__ == "__main__":
    main()

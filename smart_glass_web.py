#!/usr/bin/env python3
"""
Simple Web Interface for Smart Glass
No OpenCV display issues - everything in browser!
"""

import cv2
import numpy as np
import base64
import threading
import time
import os
from flask import Flask, render_template_string, Response, jsonify
import subprocess
from PIL import Image
import pytesseract
from ultralytics import YOLO
import RPi.GPIO as GPIO
import pygame
from gtts import gTTS
import io

app = Flask(__name__)

# Global variables
camera = None
yolo_model = None
current_frame = None
frame_lock = threading.Lock()
audio_queue = []
audio_thread = None
current_mode = 0
camera_running = False

# GPIO pins
MODE_PIN = 18
CONFIRM_PIN = 16
EXIT_PIN = 12
TRIG_PIN = 23
ECHO_PIN = 24

def init_camera():
    """Initialize camera"""
    global camera
    try:
        # Try rpicam-still first
        result = subprocess.run(['rpicam-still', '--help'], 
                              capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✅ rpicam-still available")
            return True
    except:
        pass
    
    # Try OpenCV camera
    for device in [0, 1, 2]:
        cap = cv2.VideoCapture(device)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✅ OpenCV camera on device {device}")
                camera = cap
                return True
            cap.release()
    
    print("❌ No camera found")
    return False

def init_yolo():
    """Initialize YOLO model"""
    global yolo_model
    try:
        yolo_model = YOLO('yolov8n.pt')
        print("✅ YOLO model loaded")
        return True
    except Exception as e:
        print(f"❌ YOLO failed: {e}")
        return False

def init_gpio():
    """Initialize GPIO"""
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MODE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(CONFIRM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(EXIT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(TRIG_PIN, GPIO.OUT)
        GPIO.setup(ECHO_PIN, GPIO.IN)
        print("✅ GPIO initialized")
        return True
    except Exception as e:
        print(f"❌ GPIO failed: {e}")
        return False

def init_audio():
    """Initialize audio"""
    try:
        pygame.mixer.init()
        print("✅ Audio initialized")
        return True
    except Exception as e:
        print(f"❌ Audio failed: {e}")
        return False

def capture_frame():
    """Capture frame from camera"""
    global camera
    try:
        if camera:
            ret, frame = camera.read()
            if ret:
                return True, frame
        
        # Try rpicam-still
        result = subprocess.run(['rpicam-still', '-o', '/tmp/frame.jpg', 
                               '--width', '640', '--height', '480'], 
                              timeout=5)
        if result.returncode == 0:
            frame = cv2.imread('/tmp/frame.jpg')
            if frame is not None:
                return True, frame
        
        return False, None
    except Exception as e:
        print(f"Capture error: {e}")
        return False, None

def audio_worker():
    """Audio worker thread"""
    global audio_queue
    while True:
        if audio_queue:
            text = audio_queue.pop(0)
            try:
                tts = gTTS(text=text, lang='en')
                tts.save('/tmp/speech.mp3')
                pygame.mixer.music.load('/tmp/speech.mp3')
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except Exception as e:
                print(f"Audio error: {e}")
        time.sleep(0.1)

def speak(text):
    """Add text to speech queue"""
    global audio_queue
    audio_queue.append(text)

def button_monitor():
    """Monitor buttons"""
    global current_mode, camera_running
    last_mode_time = 0
    last_confirm_time = 0
    last_exit_time = 0
    
    while True:
        try:
            current_time = time.time()
            
            # Mode button
            if not GPIO.input(MODE_PIN) and current_time - last_mode_time > 0.5:
                current_mode = (current_mode + 1) % 5
                modes = ["idle", "time", "text", "object", "distance"]
                speak(f"Mode {current_mode}: {modes[current_mode]}")
                last_mode_time = current_time
                print(f"Mode: {modes[current_mode]}")
            
            # Confirm button
            if not GPIO.input(CONFIRM_PIN) and current_time - last_confirm_time > 0.5:
                if current_mode == 2:  # Text recognition
                    camera_running = True
                    speak("Text recognition started")
                elif current_mode == 3:  # Object detection
                    camera_running = True
                    speak("Object detection started")
                elif current_mode == 4:  # Distance
                    speak("Distance measurement started")
                last_confirm_time = current_time
                print(f"Confirmed mode: {current_mode}")
            
            # Exit button
            if not GPIO.input(EXIT_PIN) and current_time - last_exit_time > 0.5:
                camera_running = False
                current_mode = 0
                speak("Returned to idle")
                last_exit_time = current_time
                print("Exit pressed")
            
            time.sleep(0.1)
        except Exception as e:
            print(f"Button error: {e}")
            time.sleep(1)

def draw_text_bounding_boxes(frame, ocr_data):
    """Draw bounding boxes around detected text"""
    try:
        if not ocr_data or frame is None:
            return frame
        
        display_frame = frame.copy()
        
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            conf = int(ocr_data['conf'][i])
            
            if text and conf > 30:  # Confidence threshold
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                
                # Draw green bounding box
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(display_frame, text, (x, y-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return display_frame
    except Exception as e:
        print(f"Text bounding box error: {e}")
        return frame

def draw_yolo_bounding_boxes(frame, results):
    """Draw bounding boxes around detected objects"""
    try:
        if not results or frame is None:
            return frame
        
        display_frame = frame.copy()
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    if float(box.conf[0]) > 0.5:  # Confidence threshold
                        # Get box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        # Get class name and confidence
                        class_id = int(box.cls[0])
                        class_name = result.names[class_id]
                        confidence = float(box.conf[0])
                        
                        # Draw red bounding box
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        
                        # Draw label
                        label = f"{class_name}: {confidence:.2f}"
                        cv2.putText(display_frame, label, (x1, y1-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        return display_frame
    except Exception as e:
        print(f"YOLO bounding box error: {e}")
        return frame

def take_screenshot_with_analysis():
    """Take screenshot and save with bounding boxes"""
    global current_mode
    
    try:
        ret, frame = capture_frame()
        if not ret or frame is None:
            print("❌ Failed to capture frame")
            return None
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        annotated_frame = frame.copy()
        
        if current_mode == 2:  # Text recognition
            # OCR with bounding boxes
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            try:
                ocr_data = pytesseract.image_to_data(pil_image, 
                                                   lang='eng',
                                                   output_type=pytesseract.Output.DICT)
                annotated_frame = draw_text_bounding_boxes(frame, ocr_data)
                
                # Get text for speech
                text = pytesseract.image_to_string(pil_image)
                if text.strip():
                    speak(f"I see text: {text.strip()[:50]}")
                    print(f"📝 Text detected: {text.strip()[:50]}")
                else:
                    speak("No text detected")
                    print("📝 No text detected")
                    
            except Exception as e:
                print(f"OCR error: {e}")
                speak("Text recognition failed")
        
        elif current_mode == 3:  # Object detection
            # YOLO with bounding boxes
            if yolo_model:
                try:
                    results = yolo_model(frame)
                    annotated_frame = draw_yolo_bounding_boxes(frame, results)
                    
                    # Get detections for speech
                    detections = []
                    for result in results:
                        if result.boxes is not None:
                            for box in result.boxes:
                                if float(box.conf[0]) > 0.5:
                                    class_name = result.names[int(box.cls[0])]
                                    detections.append(class_name)
                    
                    if detections:
                        object_counts = {}
                        for obj in detections:
                            object_counts[obj] = object_counts.get(obj, 0) + 1
                        
                        description = []
                        for obj, count in object_counts.items():
                            if count == 1:
                                description.append(f"one {obj}")
                            else:
                                description.append(f"{count} {obj}s")
                        
                        final_description = ", ".join(description)
                        speak(f"I see: {final_description}")
                        print(f"🎯 Objects detected: {final_description}")
                    else:
                        speak("No objects detected")
                        print("🎯 No objects detected")
                        
                except Exception as e:
                    print(f"YOLO error: {e}")
                    speak("Object detection failed")
            else:
                speak("Object detection not available")
                print("🎯 YOLO model not available")
        
        # Save screenshot
        mode_names = ["idle", "time", "text", "object", "distance"]
        filename = f"smart_glass_{mode_names[current_mode]}_{timestamp}.jpg"
        cv2.imwrite(filename, annotated_frame)
        print(f"📸 Screenshot saved: {filename}")
        
        return filename
        
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None

def camera_worker():
    """Camera worker thread - takes screenshots instead of live feed"""
    global current_frame, current_mode, camera_running
    
    while True:
        if camera_running and current_mode in [2, 3]:
            try:
                # Take screenshot with analysis
                filename = take_screenshot_with_analysis()
                
                if filename:
                    # Update frame for web display (simple frame without analysis)
                    ret, frame = capture_frame()
                    if ret and frame is not None:
                        with frame_lock:
                            current_frame = frame.copy()
                
                time.sleep(5)  # Take screenshot every 5 seconds
            except Exception as e:
                print(f"Camera worker error: {e}")
                time.sleep(1)
        else:
            time.sleep(0.5)

# Flask routes
@app.route('/')
def index():
    """Main page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart Glass Web Interface</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                background: #f0f0f0;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            img { 
                max-width: 100%; 
                height: auto; 
                border: 3px solid #333; 
                border-radius: 5px;
                margin: 10px 0;
            }
            .controls {
                margin: 20px 0;
                padding: 15px;
                background: #e8f4f8;
                border-radius: 5px;
            }
            button {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                margin: 5px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover { background: #45a049; }
            .status {
                margin: 10px 0;
                padding: 10px;
                background: #f9f9f9;
                border-radius: 5px;
            }
            .mode {
                font-weight: bold;
                color: #2196F3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Smart Glass Web Interface</h1>
            
            <div class="status">
                <p><strong>Status:</strong> <span id="status">Ready</span></p>
                <p><strong>Mode:</strong> <span id="mode" class="mode">Idle</span></p>
                <p><strong>Camera:</strong> <span id="camera">Active</span></p>
            </div>
            
            <div class="controls">
                <h3>Manual Controls</h3>
                <button onclick="setMode(0)">Idle</button>
                <button onclick="setMode(1)">Time</button>
                <button onclick="setMode(2)">Text Recognition</button>
                <button onclick="setMode(3)">Object Detection</button>
                <button onclick="setMode(4)">Distance</button>
                <br><br>
                <button onclick="confirmMode()">Confirm Mode</button>
                <button onclick="exitMode()">Exit Mode</button>
                <br><br>
                <button onclick="takeScreenshot()" style="background: #FF9800;">📸 Take Screenshot</button>
                <button onclick="listScreenshots()" style="background: #9C27B0;">📁 View Screenshots</button>
            </div>
            
            <div id="screenshots" class="controls" style="display: none;">
                <h3>📸 Screenshots</h3>
                <div id="screenshotList"></div>
            </div>
            
            <h3>Live Camera Feed</h3>
            <img id="cameraFeed" src="/video_feed" alt="Camera Feed">
            
            <div class="status">
                <p><em>Auto-refreshes every 2 seconds</em></p>
                <p><em>Use buttons on device or web controls above</em></p>
            </div>
        </div>
        
        <script>
            let currentMode = 0;
            const modes = ['Idle', 'Time', 'Text Recognition', 'Object Detection', 'Distance'];
            
            function setMode(mode) {
                currentMode = mode;
                document.getElementById('mode').textContent = modes[mode];
                fetch('/set_mode/' + mode);
            }
            
            function confirmMode() {
                fetch('/confirm_mode');
                document.getElementById('status').textContent = 'Mode confirmed';
            }
            
            function exitMode() {
                fetch('/exit_mode');
                document.getElementById('status').textContent = 'Returned to idle';
                document.getElementById('mode').textContent = 'Idle';
                currentMode = 0;
            }
            
            function takeScreenshot() {
                document.getElementById('status').textContent = 'Taking screenshot...';
                fetch('/take_screenshot')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            document.getElementById('status').textContent = 'Screenshot saved: ' + data.filename;
                        } else {
                            document.getElementById('status').textContent = 'Screenshot failed: ' + data.message;
                        }
                    });
            }
            
            function listScreenshots() {
                fetch('/list_screenshots')
                    .then(response => response.json())
                    .then(data => {
                        const screenshotDiv = document.getElementById('screenshots');
                        const listDiv = document.getElementById('screenshotList');
                        
                        if (data.screenshots.length > 0) {
                            listDiv.innerHTML = '<p><strong>Recent Screenshots:</strong></p>';
                            data.screenshots.slice(0, 10).forEach(filename => {
                                listDiv.innerHTML += '<p>📸 ' + filename + '</p>';
                            });
                            screenshotDiv.style.display = 'block';
                        } else {
                            listDiv.innerHTML = '<p>No screenshots found</p>';
                            screenshotDiv.style.display = 'block';
                        }
                    });
            }
            
            // Auto-refresh camera feed
            setInterval(function() {
                const img = document.getElementById('cameraFeed');
                img.src = '/video_feed?' + new Date().getTime();
            }, 2000);
            
            // Update status
            setInterval(function() {
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('mode').textContent = modes[data.mode];
                        document.getElementById('status').textContent = data.status;
                    });
            }, 1000);
        </script>
    </body>
    </html>
    """
    return html

@app.route('/video_feed')
def video_feed():
    """Video feed endpoint"""
    global current_frame
    with frame_lock:
        if current_frame is not None:
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', current_frame)
            frame_bytes = buffer.tobytes()
            return Response(frame_bytes, mimetype='image/jpeg')
        else:
            # Return placeholder
            placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
            placeholder[:] = (100, 100, 100)
            cv2.putText(placeholder, "No Camera Feed", (200, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            _, buffer = cv2.imencode('.jpg', placeholder)
            frame_bytes = buffer.tobytes()
            return Response(frame_bytes, mimetype='image/jpeg')

@app.route('/set_mode/<int:mode>')
def set_mode(mode):
    """Set mode via web"""
    global current_mode
    current_mode = mode
    return jsonify({'status': 'ok', 'mode': mode})

@app.route('/confirm_mode')
def confirm_mode():
    """Confirm mode via web"""
    global camera_running, current_mode
    if current_mode in [2, 3]:
        camera_running = True
    return jsonify({'status': 'ok'})

@app.route('/exit_mode')
def exit_mode():
    """Exit mode via web"""
    global camera_running, current_mode
    camera_running = False
    current_mode = 0
    return jsonify({'status': 'ok'})

@app.route('/status')
def status():
    """Get current status"""
    global current_mode, camera_running
    status_text = "Running" if camera_running else "Idle"
    return jsonify({'mode': current_mode, 'status': status_text})

@app.route('/take_screenshot')
def take_screenshot():
    """Manually take a screenshot"""
    filename = take_screenshot_with_analysis()
    if filename:
        return jsonify({'status': 'success', 'filename': filename})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to take screenshot'})

@app.route('/list_screenshots')
def list_screenshots():
    """List all screenshots"""
    import glob
    screenshots = glob.glob("smart_glass_*.jpg")
    screenshots.sort(reverse=True)  # Most recent first
    return jsonify({'screenshots': screenshots})

if __name__ == "__main__":
    print("🚀 Starting Smart Glass Web Interface...")
    
    # Initialize components
    if not init_camera():
        print("❌ Camera initialization failed")
        exit(1)
    
    if not init_yolo():
        print("⚠️  YOLO not available, object detection disabled")
    
    if not init_gpio():
        print("⚠️  GPIO not available, button controls disabled")
    
    if not init_audio():
        print("⚠️  Audio not available, speech disabled")
    
    # Start worker threads
    if audio_queue is not None:
        audio_thread = threading.Thread(target=audio_worker, daemon=True)
        audio_thread.start()
        print("✅ Audio thread started")
    
    button_thread = threading.Thread(target=button_monitor, daemon=True)
    button_thread.start()
    print("✅ Button thread started")
    
    camera_thread = threading.Thread(target=camera_worker, daemon=True)
    camera_thread.start()
    print("✅ Camera thread started")
    
    print("🌐 Web server starting on http://0.0.0.0:5000")
    print("📱 Open your browser and go to http://localhost:5000")
    print("🎮 Use the web interface or physical buttons")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        GPIO.cleanup()

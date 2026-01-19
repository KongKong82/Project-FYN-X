# Camera & Face Recognition Setup Guide

## 🎯 Goal
Add camera support with face detection and recognition to FYN-X for local testing.

## 📦 Installation

### Basic (Face Detection Only)

```bash
# Install OpenCV
pip install opencv-python --break-system-packages
```

**This gives you:**
- ✅ Camera access
- ✅ Face detection (boxes around faces)
- ❌ Face recognition (identifying people)

### Advanced (Face Recognition)

```bash
# Install face_recognition library
pip install face-recognition --break-system-packages
```

**⚠️ Note for Windows users:**
- Requires Visual C++ Build Tools
- If installation fails, see troubleshooting below

**This gives you:**
- ✅ Camera access
- ✅ Face detection
- ✅ Face recognition (identify specific people)

## 🚀 Quick Start

### Test Your Camera

```bash
python src/camera.py
```

This will:
1. Connect to your webcam
2. Show a 5-second preview
3. Display face detection boxes if faces are detected

### Add Face Recognition

```python
from src.camera import Camera

# Initialize camera with recognition
camera = Camera(
    source='local',           # Use local webcam
    camera_id=0,             # Default camera
    enable_face_detection=True,
    enable_face_recognition=True
)

# Connect
camera.connect()

# Add yourself to the database
print("Look at the camera...")
camera.add_face("Riley")  # Your name

# Now test recognition
frame = camera.capture_frame()
name = camera.recognize_face(frame)
print(f"Recognized: {name}")  # Should print "Riley"

camera.disconnect()
```

## 🎭 Face Recognition Workflow

### Step 1: Add Faces to Database

```python
from src.camera import Camera

camera = Camera(source='local', enable_face_recognition=True)
camera.connect()

# Method 1: Capture from camera
camera.add_face("Riley")

# Method 2: From saved image
import cv2
frame = cv2.imread("photo.jpg")
camera.add_face("Alex", frame)

camera.disconnect()
```

Faces are saved to: `data/faces/Riley.npy`

### Step 2: Use Recognition

```python
camera = Camera(source='local', enable_face_recognition=True)
camera.connect()

# Camera automatically loads known faces
print(f"Known faces: {camera.list_known_faces()}")

# Recognize in real-time
while True:
    frame = camera.capture_frame()
    name = camera.recognize_face(frame)
    
    if name:
        print(f"Hello, {name}!")
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.disconnect()
```

## 🔧 Integration with FYN-X

### Option 1: Face Recognition at Startup

Add to `FYNX_run.py`:

```python
from src.camera import Camera

# In FynxRunner.__init__
self.camera = None
if use_camera:
    self.camera = Camera(source='local', enable_face_recognition=True)
    if self.camera.connect():
        print("[CAMERA] Connected")

# In start_conversation
if self.camera:
    frame = self.camera.capture_frame()
    name = self.camera.recognize_face(frame)
    if name:
        self.current_speaker_name = name
        print(f"[CAMERA] Recognized: {name}")
```

### Option 2: Continuous Monitoring

```python
def monitor_camera(camera, callback):
    """Monitor camera for face changes."""
    import time
    last_name = None
    
    while True:
        frame = camera.capture_frame()
        name = camera.recognize_face(frame)
        
        if name and name != last_name:
            callback(name)  # New person detected
            last_name = name
        
        time.sleep(1)  # Check every second

# Start in background thread
import threading
thread = threading.Thread(
    target=monitor_camera, 
    args=(camera, on_person_changed),
    daemon=True
)
thread.start()
```

## 🎨 Camera Sources

### Local Webcam (Default)

```python
camera = Camera(
    source='local',
    camera_id=0  # 0 = default, 1 = external webcam, etc.
)
```

### Edge Device (Future)

```python
camera = Camera(
    source='edge',
    # Will use RTSP/HTTP stream from Raspberry Pi
)
```

**Note**: Edge camera not yet implemented. Use `source='local'` for now.

## 🐛 Troubleshooting

### "No module named 'cv2'"

```bash
pip install opencv-python --break-system-packages
```

### "face_recognition installation failed" (Windows)

**Option 1: Install Build Tools**
1. Download Visual Studio Build Tools:
   https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
2. Install "Desktop development with C++"
3. Retry: `pip install face-recognition --break-system-packages`

**Option 2: Use pre-compiled wheel**
1. Download from: https://github.com/z-mahmud22/Dlib_Windows_Python3.x
2. Install: `pip install dlib-19.22.99-cp311-cp311-win_amd64.whl`
3. Then: `pip install face-recognition --break-system-packages`

**Option 3: Skip face recognition**
Just use face detection (no recognition):
```python
camera = Camera(enable_face_recognition=False)
```

### "Camera not found" / "Could not open camera"

**Check available cameras:**
```python
import cv2

for i in range(5):  # Test camera IDs 0-4
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i}: ✓ Available")
        cap.release()
    else:
        print(f"Camera {i}: ✗ Not found")
```

**Common fixes:**
- Make sure webcam is connected
- Close other apps using camera (Zoom, Teams, etc.)
- Try different `camera_id` values
- Check webcam permissions (Windows Settings → Privacy → Camera)

### "Face not recognized" (even though it's in database)

**Tips for better recognition:**
- Good lighting (face camera, avoid backlighting)
- Face camera directly (not at an angle)
- Remove glasses/hats if possible
- Re-add face with multiple angles:
  ```python
  camera.add_face("Riley")  # Front view
  # Turn slightly left
  camera.add_face("Riley")  # Overwrites with better encoding
  ```

### Low frame rate / laggy preview

**Reduce resolution:**
```python
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
```

**Skip face recognition on every frame:**
```python
frame_count = 0
name = None

while True:
    frame = camera.capture_frame()
    
    # Only recognize every 30 frames (1 second at 30fps)
    if frame_count % 30 == 0:
        name = camera.recognize_face(frame)
    
    frame_count += 1
```

## 📊 Performance

### Face Detection (OpenCV)
- Speed: **Fast** (30-60 FPS)
- Accuracy: Good for frontal faces
- CPU usage: Low

### Face Recognition (face_recognition)
- Speed: **Slower** (5-15 FPS)
- Accuracy: Excellent
- CPU usage: High (GPU not used)

**Recommendation**: 
- Use detection for real-time preview
- Use recognition only when needed (e.g., on new face detected)

## 🎯 Example: Add Yourself to FYN-X

Complete workflow:

```bash
# 1. Install
pip install opencv-python face-recognition --break-system-packages

# 2. Test camera
python src/camera.py

# 3. Add yourself
python -c "
from src.camera import Camera
import time

camera = Camera(source='local', enable_face_recognition=True)
camera.connect()

print('Look at the camera...')
time.sleep(2)  # Give you time to look

camera.add_face('Riley')
print('Face added!')

camera.disconnect()
"

# 4. Test recognition
python -c "
from src.camera import Camera

camera = Camera(source='local', enable_face_recognition=True)
camera.connect()

print('Known faces:', camera.list_known_faces())

frame = camera.capture_frame()
name = camera.recognize_face(frame)
print(f'Recognized: {name}')

camera.disconnect()
"
```

## 🚀 Next Steps

1. **Test camera**: `python src/camera.py`
2. **Add yourself**: Use script above
3. **Integrate with FYN-X**: See integration examples
4. **Test edge device**: (When hardware arrives)

For voice integration, see [MICROPHONE_SETUP.md](MICROPHONE_SETUP.md)

# Quick Start - Test FYN-X Locally in 10 Minutes

## 🎯 Goal
Get camera, microphone, and TTS working with FYN-X on your computer.

## ⚡ 10-Minute Setup

### 1. Activate Environment (30 seconds)
```bash
cd C:\Users\riley\fynx
.\env\Scripts\Activate.ps1
```

### 2. Install Packages (3 minutes)
```bash
# Camera (required)
pip install opencv-python --break-system-packages

# Voice input (required)
pip install SpeechRecognition pyaudio --break-system-packages

# TTS (required - pick one)
pip install edge-tts --break-system-packages
```

**Note**: If PyAudio fails on Windows, see `MICROPHONE_SETUP.md` for wheel installation.

### 3. Test Everything (2 minutes)
```bash
python test_components.py
```

Follow prompts to test each component.

### 4. Add Your Face (1 minute)
```python
# Save as add_face.py
from src.camera import Camera
import time

camera = Camera(source='local', enable_face_recognition=True)
camera.connect()

name = input('Your name: ')
print('Look at camera in 3 seconds...')
for i in range(3, 0, -1):
    print(i)
    time.sleep(1)

camera.add_face(name)
print(f'✓ Face added: {name}')
camera.disconnect()
```

Run:
```bash
python add_face.py
```

### 5. Test FYN-X (1 minute)
```bash
# Basic test
python FYNX_run.py
```

## 🎯 What Works Now

✅ **Text conversation** - Type and chat
✅ **Memory system** - Remembers conversations
✅ **Name detection** - Auto-learns your name
✅ **Benchmarking** - Track performance

**Ready to integrate:**
- Camera (face recognition)
- Microphone (voice input)
- TTS (voice output)

## 🔧 Quick Integration

To add camera to FYN-X, add this to `FYNX_run.py`:

```python
# At top
from src.camera import Camera

# In __init__
def __init__(self, ..., enable_camera=False):
    # ... existing code ...
    
    if enable_camera:
        self.camera = Camera(source='local', enable_face_recognition=True)
        self.camera.connect()

# In start_conversation
def start_conversation(self):
    if hasattr(self, 'camera') and self.camera:
        frame = self.camera.capture_frame()
        name = self.camera.recognize_face(frame)
        if name:
            current_speaker_name = name
            print(f"[CAMERA] Recognized: {name}")
    # ... existing code ...
```

Then run: `python FYNX_run.py --camera`

## 📚 Full Guides

For detailed setup and troubleshooting:

| Guide | Purpose |
|-------|---------|
| `LOCAL_TESTING_GUIDE.md` | Complete testing workflow |
| `CAMERA_SETUP.md` | Camera & face recognition |
| `MICROPHONE_SETUP.md` | Voice input |
| `TTS_INTEGRATION.md` | Text-to-speech |
| `IMPLEMENTATION_SUMMARY.md` | Everything that was created |

## 🐛 Quick Troubleshooting

**Camera not found?**
```python
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i}: ✓")
```

**Microphone not working?**
```bash
python src/stt.py
```
Check which microphones are listed.

**PyAudio won't install?**
Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

## ✅ Checklist

- [ ] Virtual environment activated
- [ ] Packages installed (opencv, SpeechRecognition, pyaudio, edge-tts)
- [ ] Components tested (`python test_components.py`)
- [ ] Face added to database
- [ ] FYN-X runs (`python FYNX_run.py`)

## 🚀 Next Steps

1. ✅ **Test components** - Make sure everything works
2. ⭐ **Integrate camera** - Add face recognition to FYNX_run.py
3. ⭐ **Integrate voice** - Add voice input to FYNX_run.py
4. ⭐ **Integrate TTS** - Add voice output to FYNX_run.py
5. ⭐ **Test full system** - Camera + Voice + TTS together

See `LOCAL_TESTING_GUIDE.md` for complete integration examples!

## 💡 Pro Tips

1. **Test individually first** - Camera, then voice, then TTS
2. **Add yourself to face DB** - Makes testing easier
3. **Adjust thresholds** - For your lighting/audio environment
4. **Start with text-only** - Get familiar with FYN-X first
5. **Read the guides** - They have detailed troubleshooting

**You can now test 95% of FYN-X features on your computer!** 🎉

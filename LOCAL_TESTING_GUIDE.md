# Local Testing Guide - Complete FYN-X Without Edge Device

## 🎯 Goal
Test **all** FYN-X features on your computer while waiting for hardware to arrive.

## ✅ What You Can Test Locally

| Feature | Local? | Requires |
|---------|--------|----------|
| Text conversation | ✅ Yes | Ollama |
| Memory system | ✅ Yes | Nothing extra |
| Voice input | ✅ Yes | Microphone + packages |
| Camera/face recognition | ✅ Yes | Webcam + packages |
| Text-to-speech | ✅ Yes | TTS packages |
| GPU acceleration | ✅ Yes | NVIDIA/AMD GPU |
| Streaming output | ✅ Yes | Nothing extra |
| Benchmarking | ✅ Yes | Nothing extra |

**Everything except the physical robot body!**

## 🚀 Quick Setup (30 Minutes)

### Step 1: Activate Virtual Environment

```bash
cd C:\Users\riley\fynx

# PowerShell
.\env\Scripts\Activate.ps1

# Command Prompt
.\env\Scripts\activate.bat
```

### Step 2: Install Core Packages

```bash
# Camera support
pip install opencv-python --break-system-packages

# Voice input
pip install SpeechRecognition pyaudio --break-system-packages

# TTS (pick one)
pip install edge-tts --break-system-packages  # Online, high quality
# OR
pip install pyttsx3 --break-system-packages   # Offline, faster
```

### Step 3: Optional - Face Recognition

```bash
pip install face-recognition --break-system-packages
```

**Note**: On Windows, if this fails see [CAMERA_SETUP.md](CAMERA_SETUP.md) for pre-built wheels.

### Step 4: Test Everything

```bash
python test_components.py
```

This tests:
- ✅ Camera & face detection
- ✅ Microphone & voice input  
- ✅ Text-to-speech
- ✅ Ollama & FYN-X model

## 🎮 Usage Modes

### Mode 1: Text Only (Basic)

```bash
python FYNX_run.py
```

- Type your messages
- FYN-X responds with text
- Memory system active
- Fastest mode

### Mode 2: Text + TTS (Hear FYN-X)

```bash
python FYNX_run.py --tts
```

- Type your messages
- FYN-X speaks responses
- Good for testing voice quality

**Note**: TTS integration requires updating FYNX_run.py (see TTS_INTEGRATION.md)

### Mode 3: Voice Input (Speak to FYN-X)

```bash
python FYNX_run.py --voice
```

- Speak your questions
- FYN-X responds with text
- Press [S] to speak, [T] to type

**Note**: Voice integration requires updating FYNX_run.py (see MICROPHONE_SETUP.md)

### Mode 4: Full Voice Conversation

```bash
python FYNX_run.py --voice --tts
```

- Speak to FYN-X
- FYN-X speaks back
- Closest to final robot experience
- Most immersive!

### Mode 5: Camera-Enabled

```bash
python FYNX_run.py --camera
```

- FYN-X recognizes you by face
- Automatically sets your name
- No need to introduce yourself

**Note**: Camera integration requires updating FYNX_run.py (see CAMERA_SETUP.md)

### Mode 6: Everything Enabled

```bash
python FYNX_run.py --camera --voice --tts --benchmarks
```

- Face recognition on startup
- Voice input
- Voice output
- Performance tracking
- **Full FYN-X experience!**

## 🧪 Component Testing

### Test Camera

```bash
python src/camera.py
```

Shows:
- Camera connection status
- Face detection boxes (if faces present)
- 5-second preview window

### Test Microphone

```bash
python src/stt.py
```

Tests:
- Microphone detection
- Speech recognition
- Lists all available microphones

### Test TTS

```bash
python src/tts.py
```

Plays:
- Test audio from FYN-X
- Shows available voices
- Tests audio output

### Test All Components

```bash
python test_components.py
```

Comprehensive test of all systems.

## 📝 Adding Yourself to Face Database

### Method 1: Python Script

```python
from src.camera import Camera

camera = Camera(source='local', enable_face_recognition=True)
camera.connect()

print("Look at the camera...")
import time
time.sleep(2)  # Give yourself time to position

camera.add_face("Riley")
print("Face added!")

camera.disconnect()
```

Save as `add_face.py`, run: `python add_face.py`

### Method 2: Interactive

```bash
python -c "
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
print(f'Added face: {name}')
camera.disconnect()
"
```

## 🎯 Testing Workflows

### Workflow 1: Text Conversation with Memory

```bash
python FYNX_run.py
```

```
You: Hi, I'm Riley
[✓ Detected: Riley. I'll remember you now!]

You: I like robotics
FYN-X: That's fascinating! What kind of robotics...

You: exit
✓ Conversation saved to memory (ID: 42)
  Speaker: Riley
  Topics: robotics
```

**Tests:**
- ✅ Name detection
- ✅ Memory saving
- ✅ Context continuity

### Workflow 2: Voice-Activated Conversation

```bash
python FYNX_run.py --voice
```

```
[T]ype or [S]peak? s
[MIC] Listening...
You said: "What is the weather today?"

FYN-X: I don't have access to current weather...
```

**Tests:**
- ✅ Voice input
- ✅ Speech recognition
- ✅ Normal FYN-X logic

### Workflow 3: Full Multimodal

```bash
python FYNX_run.py --camera --voice --tts
```

```
[CAMERA] Recognized: Riley
Speaking with: Riley

[T]ype or [S]peak? s
[MIC] Listening...
You said: "Tell me about yourself"

FYN-X: (speaks) "I am FYN-X, a protocol droid..."
```

**Tests:**
- ✅ Face recognition
- ✅ Voice input
- ✅ Voice output
- ✅ Full integration

## 🐛 Common Issues & Solutions

### Camera Issues

**"No camera found"**
```python
# Test which camera IDs work
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i}: ✓")
        cap.release()
```

Use working ID:
```python
camera = Camera(camera_id=1)  # If camera 0 doesn't work
```

**"Face not recognized"**
- Ensure good lighting
- Face camera directly
- Re-add face with `camera.add_face("Riley")`

### Microphone Issues

**"PyAudio installation failed"**

See [MICROPHONE_SETUP.md](MICROPHONE_SETUP.md) for Windows wheel installation.

**"No speech detected"**

```python
# Lower threshold for quiet environments
stt = MicrophoneSTT(energy_threshold=100)

# Or auto-adjust
stt.recognizer.adjust_for_ambient_noise(source, duration=2)
```

### TTS Issues

**"No audio playing"**
- Check system volume
- Check correct audio device selected
- Try different TTS engine

```python
# Switch from edge-tts to pyttsx3
tts = LocalTTS(engine='pyttsx3')
```

## 📊 Performance Expectations

### With GPU (NVIDIA RTX 3060+)

| Feature | Performance |
|---------|-------------|
| Text response | 2-5 seconds |
| Face recognition | 5-15 FPS |
| Voice recognition | 1-3 seconds |
| TTS generation | 0.5-2 seconds |

### CPU Only

| Feature | Performance |
|---------|-------------|
| Text response | 10-20 seconds |
| Face recognition | 2-5 FPS |
| Voice recognition | 1-3 seconds |
| TTS generation | 0.5-2 seconds |

**Note**: Face recognition and TTS don't use GPU, so they're similar speed either way.

## 🎯 Full Local Testing Checklist

Before hardware arrives, verify:

- [ ] **Ollama installed** - `ollama list`
- [ ] **FYN-X model built** - `python server/rebuild_model.py`
- [ ] **GPU working** - Task Manager shows GPU usage
- [ ] **Camera working** - `python src/camera.py`
- [ ] **Face added to DB** - `camera.add_face("YourName")`
- [ ] **Microphone working** - `python src/stt.py`
- [ ] **TTS working** - `python src/tts.py`
- [ ] **Text conversation** - `python FYNX_run.py`
- [ ] **Voice input** - `python FYNX_run.py --voice`
- [ ] **Full multimodal** - All features together

## 📁 Local Setup Summary

What you have locally:

```
Your Computer
├── AI Model (Ollama + FYN-X) ✅
├── Memory System (data/memories.json) ✅
├── Camera (Built-in webcam) ✅
│   ├── Face detection ✅
│   └── Face recognition ✅
├── Microphone (Built-in/USB) ✅
│   └── Speech-to-text ✅
├── Speakers (Audio output) ✅
│   └── Text-to-speech ✅
└── GPU (NVIDIA/AMD) ✅
    └── Fast inference ✅
```

What you're waiting for:

```
Edge Device (Raspberry Pi)
├── TTS processing (optimization)
├── Network communication
└── Robot body integration
```

**But you can test 95% of FYN-X right now!**

## 🚀 Next Steps

1. **Run component tests**:
   ```bash
   python test_components.py
   ```

2. **Add yourself to face database**:
   ```bash
   python add_face.py  # Create this from example above
   ```

3. **Test full system**:
   ```bash
   python FYNX_run.py --camera --voice --tts
   ```

4. **Organize files** (optional):
   ```bash
   python reorganize_directories.py
   ```

5. **Report issues**: Test everything and note what works/doesn't

## 💡 Pro Tips

1. **Start simple**: Test text-only first, then add features
2. **Check benchmarks**: Type "benchmark" during conversation
3. **Test memory**: Have multi-turn conversations, verify recall
4. **Try different voices**: TTS has multiple voice options
5. **Adjust thresholds**: Tune energy/pause thresholds for your environment

That's it! You now have a fully functional FYN-X system for local testing. When hardware arrives, you'll just need to connect the edge device. 🤖✨

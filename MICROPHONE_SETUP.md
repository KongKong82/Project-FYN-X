# Microphone & Voice Input Setup Guide

## 🎯 Goal
Add voice input to FYN-X for hands-free conversation using your computer's microphone.

## 📦 Installation

### Required Packages

```bash
# Speech recognition library
pip install SpeechRecognition --break-system-packages

# Microphone access
pip install pyaudio --break-system-packages
```

### Optional (Better Quality)

```bash
# Whisper for offline, high-quality recognition
pip install openai-whisper --break-system-packages
```

## ⚠️ Windows PyAudio Installation

If `pip install pyaudio` fails on Windows:

**Method 1: Pre-built wheel**
1. Download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Choose file matching your Python version (e.g., `PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl` for Python 3.11)
3. Install: `pip install PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl`

**Method 2: Microsoft C++ Build Tools**
1. Install from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Select "Desktop development with C++"
3. Retry: `pip install pyaudio --break-system-packages`

## 🚀 Quick Start

### Test Your Microphone

```bash
python src/stt.py
```

This will:
1. List available microphones
2. Test single-phrase recognition
3. Optionally test continuous listening

### Basic Usage

```python
from src.stt import MicrophoneSTT

# Initialize STT
stt = MicrophoneSTT(
    engine='auto',        # 'auto', 'google', 'whisper', or 'sphinx'
    language='en-US',
    energy_threshold=300  # Adjust for noise level
)

# Listen for a single phrase
print("Say something...")
text = stt.listen_once(timeout=5)
print(f"You said: {text}")
```

## 🎙️ STT Engines

### Google (Default - Online)
- **Quality**: ⭐⭐⭐⭐
- **Speed**: Fast
- **Requires**: Internet connection
- **Best for**: General use

```python
stt = MicrophoneSTT(engine='google')
```

### Whisper (Offline - High Quality)
- **Quality**: ⭐⭐⭐⭐⭐
- **Speed**: Slower
- **Requires**: Install openai-whisper
- **Best for**: Offline use, accuracy

```python
stt = MicrophoneSTT(engine='whisper')
```

### Sphinx (Offline - Basic)
- **Quality**: ⭐⭐
- **Speed**: Fast
- **Requires**: Nothing extra
- **Best for**: Offline basic recognition

```python
stt = MicrophoneSTT(engine='sphinx')
```

## 🔧 Integration with FYN-X

### Mode 1: Push-to-Talk

```python
from src.stt import MicrophoneSTT

# In FynxRunner class
self.stt = MicrophoneSTT(engine='google')

# Add command
if user_input.lower() == "listen":
    print("[MIC] Listening (5 seconds)...")
    text = self.stt.listen_once(timeout=5, phrase_time_limit=10)
    if text:
        # Process as normal user input
        self.process_turn(text)
```

### Mode 2: Voice-Activated

```python
# Continuous listening with wake word
def on_speech(text):
    print(f"[VOICE] {text}")
    # Process with FYN-X
    response = runner.process_turn(text)

stt.listen_continuous(
    callback=on_speech,
    wake_word="hey phoenix"  # Say this to activate
)
```

### Mode 3: Always Listening

```python
# Continuous listening (no wake word)
def on_speech(text):
    if text.lower() == "stop listening":
        stt.stop_listening()
    else:
        runner.process_turn(text)

stt.listen_continuous(callback=on_speech)
```

## 🎯 Complete Voice-Enabled FYN-X

### Simple Integration

Add to `FYNX_run.py`:

```python
from src.stt import MicrophoneSTT

class FynxRunner:
    def __init__(self, ..., enable_voice: bool = False):
        # ... existing code ...
        
        self.stt = None
        if enable_voice:
            try:
                self.stt = MicrophoneSTT(engine='auto')
                print("(Voice Input Enabled)")
            except Exception as e:
                print(f"[WARNING] Voice input failed: {e}")
    
    def run_interactive(self):
        # ... existing code ...
        
        while True:
            # Option 1: Type or speak
            if self.stt:
                choice = input("\n[T]ype or [S]peak? (t/s): ").lower()
                
                if choice == 's':
                    print("[MIC] Listening...")
                    user_input = self.stt.listen_once(timeout=5)
                    if not user_input:
                        print("[MIC] No speech detected")
                        continue
                    print(f"You said: {user_input}")
                else:
                    user_input = input("\nYou: ").strip()
            else:
                user_input = input("\nYou: ").strip()
            
            # ... process as normal ...
```

Then run:
```bash
python FYNX_run.py --voice
```

## 🎨 Advanced Features

### Adjust for Background Noise

```python
stt = MicrophoneSTT(energy_threshold=4000)  # Higher = less sensitive

# Or auto-adjust
import speech_recognition as sr
with sr.Microphone() as source:
    stt.recognizer.adjust_for_ambient_noise(source, duration=2)
    print(f"Adjusted threshold: {stt.recognizer.energy_threshold}")
```

### Multiple Microphones

```python
# List all microphones
stt.list_microphones()

# Use specific microphone
import speech_recognition as sr
mic = sr.Microphone(device_index=1)  # Use microphone #1
```

### Voice Activity Detection

```python
# Detect when user starts/stops speaking
stt.recognizer.pause_threshold = 0.8  # Seconds of silence = end of phrase
stt.recognizer.phrase_threshold = 0.3  # Min seconds of speech

text = stt.listen_once(phrase_time_limit=None)  # No time limit
```

## 🐛 Troubleshooting

### "No module named 'pyaudio'"

See installation section above for Windows-specific fixes.

### "No microphone detected"

```bash
# Test with:
python -c "
import speech_recognition as sr
print('Microphones:', sr.Microphone.list_microphone_names())
"
```

**Fixes:**
- Check microphone is plugged in
- Check Windows sound settings (Settings → System → Sound → Input)
- Try different `device_index` values
- Restart computer

### "Speech not recognized" / Poor accuracy

**Improve recognition:**
1. **Reduce background noise**
   - Close windows
   - Turn off fans/AC
   - Use headset mic instead of laptop mic

2. **Adjust energy threshold**
   ```python
   # Lower = more sensitive (picks up quiet speech)
   # Higher = less sensitive (ignores background noise)
   stt = MicrophoneSTT(energy_threshold=300)
   ```

3. **Speak clearly**
   - Speak at normal volume
   - Don't speak too fast
   - Pause briefly between sentences

4. **Use better engine**
   ```python
   # Whisper is more accurate
   stt = MicrophoneSTT(engine='whisper')
   ```

### "Request failed" / API errors (Google engine)

**Google STT requires internet.** If offline:
```python
# Use offline engines
stt = MicrophoneSTT(engine='whisper')  # or 'sphinx'
```

### High latency / slow recognition

**Google**: Usually fast (~1 second)
**Whisper**: Slower (~3-5 seconds) but more accurate

**To reduce latency:**
```python
# Shorter phrase limit
text = stt.listen_once(phrase_time_limit=5)  # Max 5 seconds

# Or use faster engine
stt = MicrophoneSTT(engine='google')
```

## 📊 Performance Comparison

| Engine | Speed | Quality | Offline | Best For |
|--------|-------|---------|---------|----------|
| Google | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | General use |
| Whisper | ⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | Accuracy |
| Sphinx | ⭐⭐⭐⭐ | ⭐⭐ | ✅ | Basic offline |

**Recommendation**: Start with **Google** for testing, switch to **Whisper** if you need offline.

## 🎯 Example Workflows

### Workflow 1: Voice Commands Only

```python
from src.stt import MicrophoneSTT

stt = MicrophoneSTT(engine='google')

print("Voice commands enabled. Say 'quit' to exit.")
print("Speak your command...")

while True:
    text = stt.listen_once(timeout=10)
    
    if not text:
        continue
    
    if 'quit' in text.lower() or 'exit' in text.lower():
        print("Goodbye!")
        break
    
    # Process command
    print(f"Processing: {text}")
    # ... send to FYN-X ...
```

### Workflow 2: Hybrid (Type or Speak)

```python
import sys
from src.stt import MicrophoneSTT

try:
    stt = MicrophoneSTT(engine='auto')
    voice_available = True
except:
    voice_available = False
    print("Voice not available, keyboard only")

while True:
    if voice_available:
        mode = input("[T]ype or [V]oice? ").lower()
        
        if mode == 'v':
            print("Listening...")
            user_input = stt.listen_once(timeout=5)
        else:
            user_input = input("You: ")
    else:
        user_input = input("You: ")
    
    # Process normally...
```

### Workflow 3: Wake Word Activation

```python
from src.stt import MicrophoneSTT

stt = MicrophoneSTT(engine='google')

def on_voice_input(text):
    print(f">> {text}")
    # Send to FYN-X for processing
    # ...

print("Say 'Hey Phoenix' to activate...")
stt.listen_continuous(
    callback=on_voice_input,
    wake_word="hey phoenix"
)

# Runs in background, press Enter to stop
input("Press Enter to stop listening...")
stt.stop_listening()
```

## 🚀 Complete Test Script

Save as `test_voice.py`:

```python
from src.stt import MicrophoneSTT

print("="*60)
print("FYN-X VOICE INPUT TEST")
print("="*60)

# Initialize
try:
    stt = MicrophoneSTT(engine='google')
    print("\n✓ Microphone initialized")
except Exception as e:
    print(f"\n✗ Failed: {e}")
    exit(1)

# List microphones
print("\nAvailable microphones:")
stt.list_microphones()

# Test 1: Single phrase
print("\n" + "="*60)
print("TEST 1: Say something (5 seconds)")
print("="*60)
text = stt.listen_once(timeout=5)
if text:
    print(f"✓ Recognized: '{text}'")
else:
    print("✗ No speech detected")

# Test 2: Continuous (optional)
choice = input("\nTest continuous listening? (y/n): ")
if choice.lower() == 'y':
    print("\nSpeak continuously. Press Enter to stop.")
    
    def callback(text):
        print(f"  >> {text}")
    
    stt.listen_continuous(callback)
    input()
    stt.stop_listening()

print("\n✓ Voice test complete!")
```

Run: `python test_voice.py`

## 🎯 Next Steps

1. **Install packages**: See installation section
2. **Test microphone**: `python src/stt.py`
3. **Test with FYN-X**: Add voice input to your workflow
4. **Combine with camera**: See integration examples

For camera integration, see [CAMERA_SETUP.md](CAMERA_SETUP.md)

## 💡 Pro Tips

1. **Use headset microphone** for better quality (less background noise)
2. **Adjust energy threshold** if recognition is inconsistent
3. **Use Whisper offline** if you have privacy concerns
4. **Combine with wake word** for hands-free operation
5. **Add timeout** to prevent hanging on silence

That's it! You now have full voice input capabilities for local testing. 🎙️🤖

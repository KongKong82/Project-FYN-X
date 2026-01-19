# Local TTS Integration Guide

## 🎯 Goal
Add local text-to-speech to FYN-X for testing without edge device.

## ⚡ Quick Setup

### Step 1: Install TTS Engine

```bash
# Best quality (requires internet)
pip install edge-tts --break-system-packages

# OR offline alternative
pip install pyttsx3 --break-system-packages
```

### Step 2: Test TTS Module

```bash
python src/tts.py
```

You should hear: "Greetings! I am FYN-X, a protocol droid. My vocal processors are functioning nominally."

### Step 3: Add TTS to FYNX_run.py

**Option A: Simple Integration (Manual)**

Add at the top of `FYNX_run.py`:
```python
# Add after other imports
try:
    from src.tts import LocalTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("[WARNING] Local TTS not available")
```

Add to `__init__` method in `FynxRunner` class:
```python
# Add after other initialization
self.local_tts = None
if enable_local_tts and TTS_AVAILABLE:
    try:
        self.local_tts = LocalTTS(engine='auto')
        print("(Local TTS Enabled)")
    except Exception as e:
        print(f"[WARNING] Local TTS failed to initialize: {e}")
```

Add TTS callback in `_create_output_callback` method:
```python
# Add local TTS if enabled
if self.local_tts:
    def tts_callback(chunk: str):
        try:
            self.local_tts.speak(chunk)
        except Exception as e:
            print(f"\n[TTS ERROR]: {e}")
    callbacks.append(tts_callback)
```

**Option B: Quick Test (Temporary)**

Create a test file `test_tts_integration.py`:
```python
from src.tts import LocalTTS

# Initialize TTS
tts = LocalTTS(engine='auto')

# Test it
test_sentences = [
    "Greetings! I am FYN-X.",
    "How may I assist you today?",
    "I possess extensive archival knowledge of galactic history.",
]

for sentence in test_sentences:
    print(f"Speaking: {sentence}")
    tts.speak(sentence)
    print()

print("TTS test complete!")
```

Run: `python test_tts_integration.py`

## 🎨 Customization

### Change Voice (edge-tts)

```python
from src.tts import LocalTTS

tts = LocalTTS(engine='edge_tts')

# List recommended voices
tts.list_voices()

# Set voice
tts.set_voice('en-GB-RyanNeural')  # British male (recommended for FYN-X)
# tts.set_voice('en-US-GuyNeural')  # American male
# tts.set_voice('en-AU-WilliamNeural')  # Australian male
```

### Change Voice (pyttsx3 - offline)

```python
from src.tts import LocalTTS

tts = LocalTTS(engine='pyttsx3')

# List all available voices
tts.list_voices()

# Set by index (from list above)
voices = tts.engine.getProperty('voices')
tts.set_voice(voices[1].id)  # Usually index 0=female, 1=male

# Adjust speed
tts.set_rate(175)  # Default is 175 words/minute
```

## 🔊 Voice Recommendations for FYN-X

### Best Options (edge-tts):
1. **en-GB-RyanNeural** - British male, formal (BEST for protocol droid)
2. **en-US-GuyNeural** - American male, clear
3. **en-AU-WilliamNeural** - Australian male, friendly

### Testing Different Voices:

```python
from src.tts import LocalTTS

voices = [
    'en-GB-RyanNeural',
    'en-US-GuyNeural',
    'en-AU-WilliamNeural',
]

test_text = "Greetings! I am FYN-X, a protocol droid."

for voice in voices:
    print(f"\nTesting: {voice}")
    tts = LocalTTS(engine='edge_tts', voice=voice)
    tts.speak(test_text)
```

## 🎯 Full Integration Example

If you want to fully integrate TTS into FYN-X with a command-line flag:

**Add to `main()` function in FYNX_run.py:**
```python
def main():
    """Entry point."""
    # Parse command line arguments
    enable_network = "--network" in sys.argv
    enable_ros2 = "--ros2" in sys.argv
    disable_streaming = "--no-streaming" in sys.argv
    disable_benchmarks = "--no-benchmarks" in sys.argv
    enable_local_tts = "--tts" in sys.argv  # ADD THIS
    
    # ... existing code ...
    
    # Initialize and run
    runner = FynxRunner(
        use_face_recognition=False,
        enable_streaming=not disable_streaming,
        enable_network=enable_network,
        enable_ros2=enable_ros2,
        enable_benchmarks=not disable_benchmarks,
        enable_local_tts=enable_local_tts  # ADD THIS
    )
    runner.run_interactive()
```

**Then run:**
```bash
python FYNX_run.py --tts
```

## ⚠️ Important Notes

### 1. **TTS with Streaming**
- Local TTS works best with sentence-chunked streaming
- Each chunk will be spoken as it arrives
- This creates more natural-sounding speech

### 2. **Network vs Local TTS**
- **Network TTS** (edge device): Real-time, low latency
- **Local TTS** (this module): Good for testing, slightly higher latency

### 3. **Performance Impact**
- **edge-tts**: Requires internet, slight delay for audio generation
- **pyttsx3**: No internet needed, instant but lower quality
- **gTTS**: Requires internet, simplest but most robotic

## 🐛 Troubleshooting

### "No TTS engine available"
```bash
# Install at least one engine
pip install edge-tts --break-system-packages
```

### "Module not found: pyttsx3/edge_tts/gtts"
```bash
# Make sure you installed with --break-system-packages
pip install edge-tts --break-system-packages
```

### "TTS is speaking but no sound"
- Check system volume
- Check audio output device
- Try different TTS engine

### "TTS is too slow"
```python
# Use pyttsx3 for faster (offline) TTS
tts = LocalTTS(engine='pyttsx3')
tts.set_rate(200)  # Increase speed
```

### "TTS voice sounds wrong"
```python
# List and test voices
tts = LocalTTS(engine='edge_tts')
tts.list_voices()
tts.set_voice('en-GB-RyanNeural')
```

## 📊 Comparison

| Engine | Quality | Speed | Offline | Internet | Best For |
|--------|---------|-------|---------|----------|----------|
| edge-tts | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | ✅ | Production |
| pyttsx3 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | ❌ | Testing/Offline |
| gTTS | ⭐⭐⭐ | ⭐⭐⭐ | ❌ | ✅ | Simple use |

**Recommendation**: Use **edge-tts** with **en-GB-RyanNeural** voice for best FYN-X experience.

## 🚀 Quick Test

```bash
# Install
pip install edge-tts --break-system-packages

# Test TTS module
python src/tts.py

# Test with FYN-X (if integrated)
python FYNX_run.py --tts

# Or create simple test
python -c "from src.tts import LocalTTS; tts = LocalTTS(); tts.speak('Hello from FYN-X')"
```

That's it! You now have local TTS for testing FYN-X. 🎙️🤖

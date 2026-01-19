"""
Local Text-to-Speech module for FYN-X testing and debugging.
Provides fallback TTS when edge compute device is not available.
"""

import sys
from pathlib import Path
from typing import Optional

# Try to import TTS libraries
TTS_AVAILABLE = {
    'pyttsx3': False,
    'edge_tts': False,
    'gtts': False
}

try:
    import pyttsx3
    TTS_AVAILABLE['pyttsx3'] = True
except ImportError:
    pass

try:
    import edge_tts
    import asyncio
    TTS_AVAILABLE['edge_tts'] = True
except ImportError:
    pass

try:
    from gtts import gTTS
    import os
    TTS_AVAILABLE['gtts'] = True
except ImportError:
    pass


class LocalTTS:
    """
    Local TTS engine for testing FYN-X without edge device.
    Tries multiple TTS backends in order of quality.
    """
    
    def __init__(self, engine: str = 'auto', voice: Optional[str] = None, rate: int = 175):
        """
        Initialize local TTS.
        
        Args:
            engine: 'auto', 'pyttsx3', 'edge_tts', or 'gtts'
            voice: Optional voice name (engine-specific)
            rate: Speech rate (words per minute, for pyttsx3)
        """
        self.engine_name = engine
        self.engine = None
        self.voice = voice
        self.rate = rate
        
        if engine == 'auto':
            # Try engines in order of quality
            if TTS_AVAILABLE['edge_tts']:
                self.engine_name = 'edge_tts'
            elif TTS_AVAILABLE['pyttsx3']:
                self.engine_name = 'pyttsx3'
            elif TTS_AVAILABLE['gtts']:
                self.engine_name = 'gtts'
            else:
                raise RuntimeError(
                    "No TTS engine available. Install one with:\n"
                    "  pip install pyttsx3 --break-system-packages\n"
                    "  pip install edge-tts --break-system-packages\n"
                    "  pip install gtts --break-system-packages"
                )
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the selected TTS engine."""
        if self.engine_name == 'pyttsx3':
            self.engine = pyttsx3.init()
            
            # Set voice (optional)
            if self.voice:
                self.engine.setProperty('voice', self.voice)
            else:
                # Try to find a good voice
                voices = self.engine.getProperty('voices')
                # Prefer male voices for droid character
                for v in voices:
                    if 'male' in v.name.lower() and 'female' not in v.name.lower():
                        self.engine.setProperty('voice', v.id)
                        break
            
            # Set rate
            self.engine.setProperty('rate', self.rate)
            
        elif self.engine_name == 'edge_tts':
            # Edge TTS is async, no initialization needed
            # We'll use: en-GB-RyanNeural (British male, good for protocol droid)
            if not self.voice:
                self.voice = 'en-GB-RyanNeural'
                
        elif self.engine_name == 'gtts':
            # gTTS is simple, no initialization needed
            pass
    
    def speak(self, text: str):
        """
        Speak the text using the selected engine.
        
        Args:
            text: Text to speak
        """
        if not text or not text.strip():
            return
        
        if self.engine_name == 'pyttsx3':
            self._speak_pyttsx3(text)
        elif self.engine_name == 'edge_tts':
            self._speak_edge_tts(text)
        elif self.engine_name == 'gtts':
            self._speak_gtts(text)
    
    def _speak_pyttsx3(self, text: str):
        """Speak using pyttsx3 (offline, fast)."""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"[TTS ERROR] pyttsx3: {e}")
    
    def _speak_edge_tts(self, text: str):
        """Speak using edge-tts (online, high quality)."""
        try:
            import asyncio
            import edge_tts
            
            async def _speak():
                communicate = edge_tts.Communicate(text, self.voice)
                await communicate.save("temp_tts.mp3")
                
                # Play the audio
                if sys.platform == 'win32':
                    import winsound
                    winsound.PlaySound("temp_tts.mp3", winsound.SND_FILENAME)
                elif sys.platform == 'darwin':
                    import os
                    os.system(f"afplay temp_tts.mp3")
                else:  # Linux
                    import os
                    os.system(f"mpg123 temp_tts.mp3")
            
            asyncio.run(_speak())
            
            # Cleanup
            Path("temp_tts.mp3").unlink(missing_ok=True)
            
        except Exception as e:
            print(f"[TTS ERROR] edge-tts: {e}")
    
    def _speak_gtts(self, text: str):
        """Speak using gTTS (online, simple)."""
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save("temp_tts.mp3")
            
            # Play the audio
            if sys.platform == 'win32':
                import winsound
                winsound.PlaySound("temp_tts.mp3", winsound.SND_FILENAME)
            elif sys.platform == 'darwin':
                import os
                os.system(f"afplay temp_tts.mp3")
            else:  # Linux
                import os
                os.system(f"mpg123 temp_tts.mp3")
            
            # Cleanup
            Path("temp_tts.mp3").unlink(missing_ok=True)
            
        except Exception as e:
            print(f"[TTS ERROR] gTTS: {e}")
    
    def list_voices(self):
        """List available voices for the current engine."""
        if self.engine_name == 'pyttsx3':
            voices = self.engine.getProperty('voices')
            print("\nAvailable pyttsx3 voices:")
            for i, voice in enumerate(voices):
                print(f"  {i}: {voice.name} ({voice.id})")
        elif self.engine_name == 'edge_tts':
            print("\nRecommended edge-tts voices for FYN-X:")
            print("  en-GB-RyanNeural (British male, formal)")
            print("  en-US-GuyNeural (American male)")
            print("  en-AU-WilliamNeural (Australian male)")
            print("  en-GB-LibbyNeural (British female)")
            print("\nFor full list, run: edge-tts --list-voices")
        elif self.engine_name == 'gtts':
            print("gTTS uses Google's default voice (no customization)")
    
    def set_voice(self, voice: str):
        """Change the voice for the current engine."""
        self.voice = voice
        if self.engine_name == 'pyttsx3':
            self.engine.setProperty('voice', voice)
    
    def set_rate(self, rate: int):
        """Change speech rate (pyttsx3 only)."""
        self.rate = rate
        if self.engine_name == 'pyttsx3':
            self.engine.setProperty('rate', rate)


def get_available_engines() -> list:
    """Get list of available TTS engines."""
    return [name for name, available in TTS_AVAILABLE.items() if available]


def print_setup_instructions():
    """Print setup instructions for TTS engines."""
    print("\n" + "=" * 60)
    print("LOCAL TTS SETUP")
    print("=" * 60)
    
    if not any(TTS_AVAILABLE.values()):
        print("No TTS engines found. Install one or more:")
        print()
        print("Option 1 - pyttsx3 (offline, fast, lower quality):")
        print("  pip install pyttsx3 --break-system-packages")
        print()
        print("Option 2 - edge-tts (online, high quality, Microsoft):")
        print("  pip install edge-tts --break-system-packages")
        print()
        print("Option 3 - gTTS (online, simple, Google):")
        print("  pip install gtts --break-system-packages")
    else:
        print("Available TTS engines:")
        for engine, available in TTS_AVAILABLE.items():
            status = "✓ Installed" if available else "✗ Not installed"
            print(f"  {engine}: {status}")
    
    print("=" * 60 + "\n")


# Example usage and testing
if __name__ == "__main__":
    print_setup_instructions()
    
    available = get_available_engines()
    if not available:
        print("Please install a TTS engine first.")
        sys.exit(1)
    
    print(f"Testing with: {available[0]}")
    tts = LocalTTS(engine=available[0])
    
    # List available voices
    tts.list_voices()
    
    # Test speech
    print("\nTesting speech...")
    tts.speak("Greetings! I am FYN-X, a protocol droid. My vocal processors are functioning nominally.")
    
    print("\nTTS test complete!")

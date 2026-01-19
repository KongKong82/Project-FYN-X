"""
Speech-to-Text (STT) module for FYN-X.
Supports local microphone input and multiple STT engines.
"""

import sys
from pathlib import Path
from typing import Optional, Callable
import queue
import threading

# Try to import audio libraries
AUDIO_AVAILABLE = {
    'pyaudio': False,
    'speech_recognition': False,
    'whisper': False
}

try:
    import pyaudio
    AUDIO_AVAILABLE['pyaudio'] = True
except ImportError:
    pass

try:
    import speech_recognition as sr
    AUDIO_AVAILABLE['speech_recognition'] = True
except ImportError:
    pass

try:
    import whisper
    AUDIO_AVAILABLE['whisper'] = True
except ImportError:
    pass


class MicrophoneSTT:
    """
    Speech-to-Text using microphone input.
    Supports multiple STT engines with automatic fallback.
    """
    
    def __init__(self, engine: str = 'auto', language: str = 'en-US',
                 energy_threshold: int = 300, pause_threshold: float = 0.8):
        """
        Initialize STT engine.
        
        Args:
            engine: 'auto', 'google', 'whisper', or 'sphinx'
            language: Language code (e.g., 'en-US')
            energy_threshold: Minimum audio energy to consider as speech
            pause_threshold: Seconds of silence to consider end of phrase
        """
        self.engine_name = engine
        self.language = language
        self.energy_threshold = energy_threshold
        self.pause_threshold = pause_threshold
        
        self.recognizer = None
        self.microphone = None
        self.is_listening = False
        self.listen_thread = None
        
        # Auto-select engine
        if engine == 'auto':
            if AUDIO_AVAILABLE['speech_recognition']:
                self.engine_name = 'google'  # Default to Google
            else:
                raise RuntimeError(
                    "No STT engine available. Install with:\n"
                    "  pip install SpeechRecognition pyaudio --break-system-packages\n"
                    "  pip install openai-whisper --break-system-packages  # Optional, better quality"
                )
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the STT engine."""
        if not AUDIO_AVAILABLE['speech_recognition']:
            raise RuntimeError(
                "SpeechRecognition library required. Install with:\n"
                "  pip install SpeechRecognition pyaudio --break-system-packages"
            )
        
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = self.energy_threshold
        self.recognizer.pause_threshold = self.pause_threshold
        
        # Initialize microphone
        try:
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                print("[MIC] Adjusting for ambient noise... Please wait.")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print(f"[MIC] Ready! Energy threshold: {self.recognizer.energy_threshold}")
        
        except Exception as e:
            print(f"[MIC ERROR] Could not initialize microphone: {e}")
            print("Make sure you have a microphone connected")
            raise
    
    def listen_once(self, timeout: Optional[float] = None, 
                    phrase_time_limit: Optional[float] = None) -> Optional[str]:
        """
        Listen for a single phrase and convert to text.
        
        Args:
            timeout: Seconds to wait for speech to start (None = no timeout)
            phrase_time_limit: Max seconds for phrase (None = no limit)
            
        Returns:
            Recognized text, or None if failed
        """
        if not self.microphone:
            print("[MIC ERROR] Microphone not initialized")
            return None
        
        try:
            print("[MIC] Listening...")
            
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            print("[MIC] Processing...")
            
            # Recognize speech
            text = self._recognize_audio(audio)
            
            if text:
                print(f"[MIC] Recognized: {text}")
            else:
                print("[MIC] Could not understand audio")
            
            return text
            
        except sr.WaitTimeoutError:
            print("[MIC] Listening timed out")
            return None
        except Exception as e:
            print(f"[MIC ERROR] {e}")
            return None
    
    def _recognize_audio(self, audio) -> Optional[str]:
        """
        Recognize audio using selected engine.
        
        Args:
            audio: AudioData object
            
        Returns:
            Recognized text or None
        """
        try:
            if self.engine_name == 'google':
                return self.recognizer.recognize_google(audio, language=self.language)
            
            elif self.engine_name == 'whisper':
                if not AUDIO_AVAILABLE['whisper']:
                    print("[MIC WARNING] Whisper not available, falling back to Google")
                    return self.recognizer.recognize_google(audio, language=self.language)
                return self.recognizer.recognize_whisper(audio, language=self.language.split('-')[0])
            
            elif self.engine_name == 'sphinx':
                return self.recognizer.recognize_sphinx(audio)
            
            else:
                print(f"[MIC ERROR] Unknown engine: {self.engine_name}")
                return None
                
        except sr.UnknownValueError:
            # Could not understand audio
            return None
        except sr.RequestError as e:
            print(f"[MIC ERROR] API request failed: {e}")
            return None
        except Exception as e:
            print(f"[MIC ERROR] Recognition failed: {e}")
            return None
    
    def listen_continuous(self, callback: Callable[[str], None], 
                         wake_word: Optional[str] = None):
        """
        Listen continuously and call callback with recognized text.
        
        Args:
            callback: Function to call with recognized text
            wake_word: Optional wake word to activate (e.g., "hey phoenix")
        """
        if self.is_listening:
            print("[MIC WARNING] Already listening")
            return
        
        self.is_listening = True
        wake_word_active = wake_word is None  # If no wake word, always active
        
        def listen_worker():
            print("[MIC] Continuous listening started")
            if wake_word:
                print(f"[MIC] Say '{wake_word}' to activate")
            
            with self.microphone as source:
                while self.is_listening:
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                        text = self._recognize_audio(audio)
                        
                        if text:
                            text_lower = text.lower()
                            
                            # Check for wake word
                            if wake_word and not wake_word_active:
                                if wake_word.lower() in text_lower:
                                    print(f"[MIC] Wake word detected!")
                                    wake_word_active = True
                                    # Remove wake word from text
                                    text = text_lower.replace(wake_word.lower(), '').strip()
                                    if text:
                                        callback(text)
                                continue
                            
                            # Process recognized text
                            if wake_word_active:
                                callback(text)
                    
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        print(f"[MIC ERROR] {e}")
                        continue
        
        self.listen_thread = threading.Thread(target=listen_worker, daemon=True)
        self.listen_thread.start()
    
    def stop_listening(self):
        """Stop continuous listening."""
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        print("[MIC] Stopped listening")
    
    def list_microphones(self):
        """List available microphone devices."""
        if not AUDIO_AVAILABLE['pyaudio']:
            print("PyAudio not available")
            return
        
        print("\nAvailable microphones:")
        print("-" * 60)
        
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"  {index}: {name}")
        
        print("-" * 60)


def get_available_engines() -> list:
    """Get list of available STT engines."""
    engines = []
    
    if AUDIO_AVAILABLE['speech_recognition']:
        engines.extend(['google', 'sphinx'])
    
    if AUDIO_AVAILABLE['whisper']:
        engines.append('whisper')
    
    return engines


def print_setup_instructions():
    """Print setup instructions for STT."""
    print("\n" + "=" * 60)
    print("MICROPHONE / STT SETUP")
    print("=" * 60)
    
    print("\nRequired (basic STT with Google):")
    print("  pip install SpeechRecognition pyaudio --break-system-packages")
    
    print("\nOptional (better quality, offline):")
    print("  pip install openai-whisper --break-system-packages")
    
    print("\nNote for Windows:")
    print("  If PyAudio fails to install, download wheel from:")
    print("  https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
    print("  Then: pip install PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl")
    
    available = []
    for engine, avail in AUDIO_AVAILABLE.items():
        status = "✓ Installed" if avail else "✗ Not installed"
        available.append(f"  {engine}: {status}")
    
    print("\nCurrently available:")
    for item in available:
        print(item)
    
    print("=" * 60 + "\n")


# Example usage and testing
if __name__ == "__main__":
    print_setup_instructions()
    
    engines = get_available_engines()
    if not engines:
        print("Please install required packages first.")
        sys.exit(1)
    
    print(f"Available engines: {', '.join(engines)}")
    
    # Test microphone
    try:
        stt = MicrophoneSTT(engine='auto')
        
        # List microphones
        stt.list_microphones()
        
        # Test single listen
        print("\n" + "=" * 60)
        print("TEST: Single phrase recognition")
        print("=" * 60)
        print("Say something (you have 5 seconds)...")
        
        text = stt.listen_once(timeout=5, phrase_time_limit=10)
        
        if text:
            print(f"\n✓ SUCCESS! Recognized: \"{text}\"")
        else:
            print("\n✗ No speech detected or recognition failed")
        
        # Test continuous (optional)
        response = input("\nTest continuous listening? (y/n): ")
        if response.lower() == 'y':
            print("\n" + "=" * 60)
            print("TEST: Continuous recognition")
            print("=" * 60)
            print("Speak continuously. Press Enter to stop.")
            
            def callback(text):
                print(f"  >> {text}")
            
            stt.listen_continuous(callback)
            input()
            stt.stop_listening()
        
        print("\nSTT test complete!")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)

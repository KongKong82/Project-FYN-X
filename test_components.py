"""
Complete component testing script for FYN-X.
Tests camera, microphone, TTS, and all local capabilities.
"""

import sys
from pathlib import Path


def test_imports():
    """Test if required libraries are installed."""
    print("\n" + "="*70)
    print("CHECKING INSTALLED PACKAGES")
    print("="*70)
    
    packages = {
        'opencv-python': False,
        'face-recognition': False,
        'SpeechRecognition': False,
        'pyaudio': False,
        'edge-tts': False,
        'pyttsx3': False,
    }
    
    # Test OpenCV
    try:
        import cv2
        packages['opencv-python'] = True
    except ImportError:
        pass
    
    # Test face_recognition
    try:
        import face_recognition
        packages['face-recognition'] = True
    except ImportError:
        pass
    
    # Test SpeechRecognition
    try:
        import speech_recognition
        packages['SpeechRecognition'] = True
    except ImportError:
        pass
    
    # Test PyAudio
    try:
        import pyaudio
        packages['pyaudio'] = True
    except ImportError:
        pass
    
    # Test edge-tts
    try:
        import edge_tts
        packages['edge-tts'] = True
    except ImportError:
        pass
    
    # Test pyttsx3
    try:
        import pyttsx3
        packages['pyttsx3'] = True
    except ImportError:
        pass
    
    # Print results
    for package, installed in packages.items():
        status = "✓ Installed" if installed else "✗ Not installed"
        print(f"  {package}: {status}")
    
    # Check what features are available
    print("\n" + "="*70)
    print("AVAILABLE FEATURES")
    print("="*70)
    
    features = {
        'Camera (basic)': packages['opencv-python'],
        'Face Recognition': packages['face-recognition'],
        'Voice Input': packages['SpeechRecognition'] and packages['pyaudio'],
        'TTS (online)': packages['edge-tts'],
        'TTS (offline)': packages['pyttsx3'],
    }
    
    for feature, available in features.items():
        status = "✓ Ready" if available else "✗ Missing packages"
        print(f"  {feature}: {status}")
    
    return packages


def test_camera(skip_recognition=False):
    """Test camera functionality."""
    print("\n" + "="*70)
    print("CAMERA TEST")
    print("="*70)
    
    try:
        from src.camera import Camera
        
        # Initialize camera
        camera = Camera(
            source='local',
            enable_face_detection=True,
            enable_face_recognition=not skip_recognition
        )
        
        # Connect
        if not camera.connect():
            print("✗ Failed to connect to camera")
            return False
        
        print("✓ Camera connected")
        
        # Capture test frame
        frame = camera.capture_frame()
        if frame is None:
            print("✗ Could not capture frame")
            camera.disconnect()
            return False
        
        print(f"✓ Captured frame: {frame.shape}")
        
        # Test face detection
        faces = camera.detect_faces(frame)
        print(f"✓ Face detection working (detected {len(faces)} faces)")
        
        # Test face recognition
        if not skip_recognition and camera.enable_face_recognition:
            known = camera.list_known_faces()
            print(f"✓ Face recognition available (known: {known})")
        
        # Show preview
        print("\nShowing camera preview for 3 seconds...")
        camera.show_preview(duration=3, show_detection=True)
        
        camera.disconnect()
        print("\n✓ Camera test passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Camera test failed: {e}")
        return False


def test_microphone():
    """Test microphone functionality."""
    print("\n" + "="*70)
    print("MICROPHONE TEST")
    print("="*70)
    
    try:
        from src.stt import MicrophoneSTT
        
        # Initialize
        stt = MicrophoneSTT(engine='google')
        print("✓ Microphone initialized")
        
        # List microphones
        print("\nAvailable microphones:")
        stt.list_microphones()
        
        # Test recognition
        print("\n" + "="*70)
        print("Say something (you have 5 seconds)...")
        print("="*70)
        
        text = stt.listen_once(timeout=5, phrase_time_limit=10)
        
        if text:
            print(f"\n✓ Microphone test passed!")
            print(f"  Recognized: \"{text}\"")
            return True
        else:
            print("\n⚠ No speech detected (mic might be working but no speech)")
            return True  # Still pass if mic initialized
        
    except Exception as e:
        print(f"\n✗ Microphone test failed: {e}")
        return False


def test_tts():
    """Test text-to-speech."""
    print("\n" + "="*70)
    print("TTS TEST")
    print("="*70)
    
    try:
        from src.tts import LocalTTS
        
        # Initialize
        tts = LocalTTS(engine='auto')
        print(f"✓ TTS initialized (engine: {tts.engine_name})")
        
        # Test speech
        print("\nSpeaking test phrase...")
        tts.speak("FYN-X text to speech is working!")
        
        print("\n✓ TTS test passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ TTS test failed: {e}")
        return False


def test_ollama():
    """Test Ollama and FYN-X model."""
    print("\n" + "="*70)
    print("OLLAMA / MODEL TEST")
    print("="*70)
    
    import subprocess
    
    try:
        # Check if Ollama is running
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✓ Ollama is running")
        
        # Check if FYN-X model exists
        if "FYN-X" in result.stdout:
            print("✓ FYN-X model found")
            
            # Get model info
            for line in result.stdout.split('\n'):
                if 'FYN-X' in line:
                    print(f"  {line}")
            
            return True
        else:
            print("⚠ FYN-X model not found")
            print("  Run: python server/rebuild_model.py")
            return False
        
    except FileNotFoundError:
        print("✗ Ollama not installed")
        print("  Download from: https://ollama.ai/download")
        return False
    except subprocess.CalledProcessError:
        print("✗ Ollama not responding")
        print("  Try: ollama serve")
        return False


def print_installation_guide(missing_packages):
    """Print installation instructions for missing packages."""
    print("\n" + "="*70)
    print("INSTALLATION GUIDE")
    print("="*70)
    
    install_commands = {
        'opencv-python': 'pip install opencv-python --break-system-packages',
        'face-recognition': 'pip install face-recognition --break-system-packages',
        'SpeechRecognition': 'pip install SpeechRecognition --break-system-packages',
        'pyaudio': 'pip install pyaudio --break-system-packages',
        'edge-tts': 'pip install edge-tts --break-system-packages',
        'pyttsx3': 'pip install pyttsx3 --break-system-packages',
    }
    
    print("\nTo install missing packages:\n")
    
    for package in missing_packages:
        if package in install_commands:
            print(f"# {package}")
            print(f"{install_commands[package]}\n")
    
    print("For detailed setup guides, see:")
    print("  - CAMERA_SETUP.md (camera & face recognition)")
    print("  - MICROPHONE_SETUP.md (voice input)")
    print("  - TTS_INTEGRATION.md (text-to-speech)")


def print_summary(results):
    """Print test summary."""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test}: {status}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED!")
        print("="*70)
        print("\nYou're ready to run FYN-X with full capabilities!")
        print("  python FYNX_run.py --voice --camera")
    else:
        print("\n" + "="*70)
        print("⚠ SOME TESTS FAILED")
        print("="*70)
        print("\nSee installation guide above to fix missing components.")


def main():
    """Main test routine."""
    print("\n" + "="*70)
    print(" " * 25 + "FYN-X COMPONENT TEST")
    print("="*70)
    
    print("\nThis will test all FYN-X components:")
    print("  1. Required packages")
    print("  2. Camera (with face detection)")
    print("  3. Microphone (voice input)")
    print("  4. TTS (text-to-speech)")
    print("  5. Ollama / FYN-X model")
    
    response = input("\nProceed with tests? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Test 1: Check packages
    packages = test_imports()
    
    missing = [pkg for pkg, installed in packages.items() if not installed]
    
    # Test 2-5: Run component tests
    results = {}
    
    # Camera test
    if packages['opencv-python']:
        skip_recognition = not packages['face-recognition']
        results['Camera'] = test_camera(skip_recognition=skip_recognition)
    else:
        print("\n⚠ Skipping camera test (opencv not installed)")
        results['Camera'] = False
    
    # Microphone test
    if packages['SpeechRecognition'] and packages['pyaudio']:
        test_mic = input("\nTest microphone? (will listen for speech) (y/n): ")
        if test_mic.lower() == 'y':
            results['Microphone'] = test_microphone()
        else:
            print("Skipping microphone test")
            results['Microphone'] = None
    else:
        print("\n⚠ Skipping microphone test (packages not installed)")
        results['Microphone'] = False
    
    # TTS test
    if packages['edge-tts'] or packages['pyttsx3']:
        test_audio = input("\nTest TTS? (will play audio) (y/n): ")
        if test_audio.lower() == 'y':
            results['TTS'] = test_tts()
        else:
            print("Skipping TTS test")
            results['TTS'] = None
    else:
        print("\n⚠ Skipping TTS test (packages not installed)")
        results['TTS'] = False
    
    # Ollama test
    results['Ollama'] = test_ollama()
    
    # Print installation guide for missing packages
    if missing:
        print_installation_guide(missing)
    
    # Print summary
    filtered_results = {k: v for k, v in results.items() if v is not None}
    print_summary(filtered_results)


if __name__ == "__main__":
    main()

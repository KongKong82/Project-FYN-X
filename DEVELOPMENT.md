# FYN-X Development Roadmap

This document outlines planned features and implementation details for FYN-X development.

## Phase 1: Core Memory System ✅ (COMPLETED)

- [x] Personal conversation memory storage
- [x] Tag-based memory retrieval
- [x] Conversation session management
- [x] JSON-based persistence
- [x] Memory search functionality
- [x] Automatic conversation summarization

## Phase 2: Voice Integration (NEXT)

### Speech-to-Text (STT)

**Goal**: Convert user speech to text for processing

**Options**:

1. **Whisper (OpenAI)** - Recommended
   - Highly accurate
   - Runs locally
   - Good for real-time transcription
   ```bash
   pip install openai-whisper
   ```

2. **Google Speech Recognition**
   - Cloud-based
   - Requires internet
   ```bash
   pip install SpeechRecognition pyaudio
   ```

3. **Vosk** - Lightweight alternative
   - Fully offline
   - Lower accuracy but fast
   ```bash
   pip install vosk
   ```

**Implementation Plan**:

```python
# src/voice_input.py

import whisper
import pyaudio
import numpy as np

class SpeechToText:
    def __init__(self, model_size="base"):
        self.model = whisper.load_model(model_size)
        self.audio = pyaudio.PyAudio()
        
    def listen(self, duration=5):
        """Record audio and transcribe."""
        # Record audio
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        frames = []
        for _ in range(0, int(16000 / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Convert to numpy array
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
        audio_data = audio_data.astype(np.float32) / 32768.0
        
        # Transcribe
        result = self.model.transcribe(audio_data)
        return result["text"]
```

### Text-to-Speech (TTS)

**Goal**: Convert FYN-X's responses to speech

**Options**:

1. **Piper TTS** - Recommended for character voices
   - High quality neural TTS
   - Can train custom voices
   - Perfect for droid personality
   ```bash
   pip install piper-tts
   ```

2. **Coqui TTS**
   - Voice cloning capabilities
   - Multiple voice options
   ```bash
   pip install TTS
   ```

3. **gTTS (Google)** - Simplest
   - Easy to use
   - Limited voice options
   ```bash
   pip install gtts
   ```

**Implementation Plan**:

```python
# src/voice_output.py

from TTS.api import TTS

class TextToSpeech:
    def __init__(self, voice_model="tts_models/en/ljspeech/tacotron2-DDC"):
        self.tts = TTS(voice_model)
        
    def speak(self, text):
        """Convert text to speech and play."""
        # Generate audio
        self.tts.tts_to_file(
            text=text,
            file_path="temp_speech.wav"
        )
        
        # Play audio
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load("temp_speech.wav")
        pygame.mixer.music.play()
        
        # Wait for completion
        while pygame.mixer.music.get_busy():
            continue
```

**Voice Assistant Mode**:

```python
# FYNX_run.py modifications

from src.voice_input import SpeechToText
from src.voice_output import TextToSpeech

class FynxRunner:
    def __init__(self, voice_mode=False):
        # ... existing init ...
        
        if voice_mode:
            self.stt = SpeechToText()
            self.tts = TextToSpeech()
            self.voice_mode = True
        else:
            self.voice_mode = False
    
    def voice_interactive_loop(self):
        """Voice-based interaction loop."""
        self.start_conversation()
        self.tts.speak("FYN-X online. How may I assist you?")
        
        while True:
            print("\n[Listening...]")
            user_input = self.stt.listen(duration=5)
            print(f"You said: {user_input}")
            
            if "goodbye" in user_input.lower():
                self.tts.speak("Until we meet again.")
                self.end_conversation()
                break
            
            response = self.process_turn(user_input)
            print(f"FYN-X: {response}")
            self.tts.speak(response)
```

## Phase 3: Face Recognition

### Implementation Approach

**Libraries**:
- OpenCV for camera access and face detection
- face_recognition (dlib-based) for face encoding and matching

```bash
pip install opencv-python
pip install face-recognition
pip install dlib
```

### Core Components

#### 1. Face Detection

```python
# src/face_recognition_module.py (expand existing stub)

import cv2
import face_recognition
import numpy as np

class FaceRecognizer:
    def initialize_camera(self, camera_id=0):
        self.camera = cv2.VideoCapture(camera_id)
        return self.camera.isOpened()
    
    def detect_face(self):
        """Capture and detect face from camera."""
        ret, frame = self.camera.read()
        if not ret:
            return None
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if not face_locations:
            return None
        
        # Get encoding for first face
        face_encodings = face_recognition.face_encodings(
            rgb_frame, 
            face_locations
        )
        
        if face_encodings:
            return {
                'encoding': face_encodings[0],
                'location': face_locations[0],
                'frame': frame
            }
        
        return None
```

#### 2. Face Recognition

```python
def recognize_face(self, face_encoding):
    """Match face against known faces."""
    if not self.known_faces:
        return None
    
    # Get all known encodings
    known_encodings = [
        np.array(person['encodings'][0]) 
        for person in self.known_faces.values()
    ]
    known_names = list(self.known_faces.keys())
    
    # Compare faces
    matches = face_recognition.compare_faces(
        known_encodings, 
        face_encoding,
        tolerance=0.6  # Adjust for accuracy
    )
    
    face_distances = face_recognition.face_distance(
        known_encodings, 
        face_encoding
    )
    
    if len(face_distances) > 0:
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            return known_names[best_match_index]
    
    return None
```

#### 3. Face Learning

```python
def learn_face(self, name, face_encoding):
    """Add new face to database."""
    if name not in self.known_faces:
        self.known_faces[name] = {
            'name': name,
            'encodings': [],
            'added_date': datetime.now().isoformat()
        }
    
    # Convert numpy array to list for JSON serialization
    encoding_list = face_encoding.tolist()
    self.known_faces[name]['encodings'].append(encoding_list)
    
    self._save_face_database()
    return True
```

### Face Recognition Workflow

```
┌─────────────────────────────────────────────┐
│  1. User approaches FYN-X                   │
│  2. Camera activates                        │
│  3. Face detected in frame                  │
│  4. Generate face encoding (128-d vector)   │
│  5. Compare to known faces database         │
│     ├─ Match found → "Welcome back, Riley!" │
│     └─ No match → "Hello! I don't believe   │
│                    we've met. May I learn   │
│                    your name?"              │
│  6. If new: capture multiple angles         │
│  7. Store encoding with identity            │
│  8. Use identity for conversation session   │
└─────────────────────────────────────────────┘
```

### Integration with Conversation

```python
class FynxRunner:
    def start_conversation_with_recognition(self):
        """Start conversation with face recognition."""
        print("Initializing camera...")
        self.face_recognizer.initialize_camera()
        
        print("Detecting face...")
        face_data = self.face_recognizer.detect_face()
        
        if face_data:
            identity = self.face_recognizer.recognize_face(
                face_data['encoding']
            )
            
            if identity:
                print(f"Recognized: {identity}")
                greeting = f"Ah, {identity}! Welcome back."
            else:
                print("Unknown person detected")
                greeting = "Hello! I don't believe we've met."
                
                # Offer to learn face
                response = input("Would you like me to learn your face? (yes/no): ")
                if response.lower() == 'yes':
                    name = input("What is your name? ")
                    self.face_recognizer.learn_face(
                        name, 
                        face_data['encoding']
                    )
                    identity = name
                    greeting = f"A pleasure to meet you, {name}!"
        else:
            identity = "unknown"
            greeting = "Hello there!"
        
        self.current_session = ConversationSession(identity)
        print(f"\n{greeting}\n")
```

## Phase 4: Enhanced Retrieval (Vector Embeddings)

### Current: Keyword Matching
- Tags: ["sarah", "project", "work"]
- Matches: Exact tag overlap

### Future: Semantic Similarity
- Query: "What work stuff did I discuss with Sarah?"
- Semantic understanding finds relevant memories even without exact tag matches

**Implementation**:

```python
# Add to src/memory.py

from sentence_transformers import SentenceTransformer

class EnhancedMemoryManager(MemoryManager):
    def __init__(self, memory_file):
        super().__init__(memory_file)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self._generate_embeddings()
    
    def _generate_embeddings(self):
        """Generate embeddings for all memories."""
        for memory in self.memories:
            if 'embedding' not in memory:
                text = memory.get('summary', '')
                embedding = self.embedding_model.encode(text)
                memory['embedding'] = embedding.tolist()
        
        self._save_memories()
    
    def semantic_search(self, query, limit=5):
        """Search using semantic similarity."""
        query_embedding = self.embedding_model.encode(query)
        
        # Calculate cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        
        scores = []
        for memory in self.memories:
            memory_emb = np.array(memory['embedding'])
            similarity = cosine_similarity(
                [query_embedding], 
                [memory_emb]
            )[0][0]
            scores.append((memory, similarity))
        
        # Sort by similarity
        scores.sort(key=lambda x: x[1], reverse=True)
        return [mem for mem, score in scores[:limit]]
```

## Phase 5: Multi-Modal Memory

### Vision Memory
- Store images from camera during conversations
- Associate images with conversation context
- "Show me the photo from when I talked about the birthday party"

### Location Memory
- GPS integration for location tracking
- "Where was I when I talked about the restaurant?"
- "Remind me to discuss X next time I'm at the office"

### Temporal Patterns
- Learn when certain topics are discussed
- "You usually ask about work projects on Monday mornings"
- Proactive reminders based on patterns

## Phase 6: Advanced Features

### Natural Language Understanding
- Intent detection beyond tag matching
- Entity relationship extraction
- Sentiment analysis for context

### Proactive Assistance
- "Master Riley, you mentioned wanting to finish that project today"
- "It's been two weeks since you spoke with Sarah"
- "You asked me to remind you about..."

### Privacy & Security
- Encrypted memory storage
- Per-user access controls
- Memory deletion/editing capabilities
- GDPR-compliant data handling

### Multi-Device Sync
- Cloud backup of memories
- Sync across multiple FYN-X instances
- Mobile app integration

## Technical Debt & Improvements

### Short Term
- [ ] Add error handling for Ollama connection failures
- [ ] Implement memory pruning (delete old/irrelevant memories)
- [ ] Add confidence scores to tag extraction
- [ ] Better duplicate conversation detection

### Medium Term
- [ ] Web interface for memory browsing
- [ ] Export memories to various formats
- [ ] Import conversations from chat logs
- [ ] Performance optimization for large memory databases

### Long Term
- [ ] Distributed memory across multiple droids
- [ ] Learning from corrections (active learning)
- [ ] Multi-language support
- [ ] Custom personality training

## Development Timeline (Estimated)

```
Month 1-2: Voice Integration
  - Week 1-2: STT implementation
  - Week 3-4: TTS implementation
  - Testing and refinement

Month 3: Face Recognition
  - Week 1: Camera integration
  - Week 2: Face detection/encoding
  - Week 3: Recognition and learning
  - Week 4: Integration with conversation system

Month 4: Vector Embeddings
  - Week 1-2: Embedding generation
  - Week 3: Semantic search implementation
  - Week 4: Testing and comparison with tag-based

Month 5-6: Advanced Features
  - Multi-modal memory
  - Proactive assistance
  - Privacy features
  - Polish and optimization
```

## Getting Started on Next Phase

To begin Phase 2 (Voice Integration), run:

```bash
# Install dependencies
pip install openai-whisper
pip install TTS
pip install pyaudio

# Test voice components
python -c "import whisper; print('Whisper installed successfully')"
python -c "from TTS.api import TTS; print('TTS installed successfully')"
```

Then implement `src/voice_input.py` and `src/voice_output.py` following the templates above.

---

*Remember: The goal is a seamless, personal companion that remembers your life, not just Star Wars trivia.*

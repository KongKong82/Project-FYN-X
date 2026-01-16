# FYN-X: Personal Memory Companion Droid

FYN-X is an AI companion with **personal memory** capabilities, wrapped in a Star Wars protocol droid personality. Rather than recalling Star Wars lore, FYN-X remembers **your conversations, the people you mention, and the topics you discuss**.

## 🌟 Core Concept

FYN-X uses **Retrieval-Augmented Generation (RAG)** to:
1. **Remember conversations** - Every meaningful interaction is stored with context
2. **Retrieve relevant memories** - When you ask a question, FYN-X searches past conversations
3. **Maintain continuity** - FYN-X knows what you've discussed before and who you've mentioned
4. **Recognize faces** *(future)* - Visual identity recognition via camera

## 🎯 System Architecture

```
┌──────────────────────────────────────────────────────┐
│                  USER INTERACTION                     │
│  Voice (future) → Text Input → Tag Extraction        │
│  Camera (future) → Face Recognition → Identity       │
└─────────────────────┬────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│               MEMORY RETRIEVAL (RAG)                  │
│  1. Extract tags from user input                     │
│  2. Search memory database for relevant past talks   │
│  3. Inject memories into LLM context                 │
└─────────────────────┬────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│            OLLAMA LLM (with FYN-X personality)       │
│  • Receives: user input + relevant memories          │
│  • Responds: in-character as protocol droid          │
└─────────────────────┬────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│              MEMORY PERSISTENCE                       │
│  • Log conversation turns                            │
│  • Extract topics, names, activities                 │
│  • Save to JSON database when session ends           │
└──────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
fynx/
├── FYNX_run.py              # Main application runner (NEW)
├── FYN-X.modelfile          # Ollama model personality definition
├── README.md                # This file
├── data/
│   ├── memories.json        # Memory database (auto-generated)
│   └── faces.json           # Face recognition DB (future)
└── src/
    ├── memory.py            # MemoryManager & ConversationSession (NEW)
    ├── tag_extraction.py    # Extract tags for memory search (UPDATED)
    ├── search.py            # Memory search & retrieval (UPDATED)
    ├── face_recognition_module.py  # Face detection stub (NEW)
    ├── loader.py            # Legacy - will be deprecated
    └── main.py              # Legacy - will be deprecated
```

## 🚀 Getting Started

### Prerequisites

1. **Python 3.11+**
2. **Ollama** - [Download here](https://ollama.ai)
3. Install Python dependencies (currently none required for core features)

### Installation

1. Clone/navigate to the repository:
```bash
cd fynx
```

2. Create the Ollama model:
```bash
ollama create FYN-X-02 -f FYN-X.modelfile
```

3. Run FYN-X:
```bash
python FYNX_run.py
```

## 💬 Usage

### Basic Conversation

```
FYN-X PERSONAL MEMORY SYSTEM
============================================================
Memory Database Stats:
  Total memories: 0
  Unique people: 0
  Unique topics: 0

============================================================
New conversation started with: unknown
Type 'exit' to end conversation and save
Type 'stats' to see memory statistics
Type 'search <query>' to search memories
============================================================

You: Hey FYN-X, I just got back from visiting my friend Sarah in Portland

FYN-X: Ah, welcome back! Portland, you say? I do hope your visit with 
Sarah was pleasant. How was the journey?

You: It was great! We went to this amazing Thai restaurant downtown

FYN-X: Thai cuisine—how delightful! I must note that for future reference.
Were there any particular dishes that stood out?
```

When you type `exit`, FYN-X saves the conversation with extracted information:
- **Topics**: visiting, friend, portland, restaurant, thai
- **People mentioned**: Sarah
- **Activities**: visited, went

### Special Commands

- `exit` - End conversation and save to memory
- `stats` - Display memory database statistics
- `search <query>` - Search past conversations (e.g., `search Sarah`)

### How Memory Works

**During conversation:**
1. You ask: "What did Sarah and I do last time we met?"
2. FYN-X extracts tags: `["sarah", "last", "time", "met"]`
3. Searches memory database for matches
4. Finds past conversation about Sarah
5. Includes that memory in the prompt
6. Responds based on actual stored conversation

**Example:**
```
You: What did Sarah and I do last time?

FYN-X: Ah yes, my records indicate you visited Sarah in Portland. 
If I recall correctly, you enjoyed a Thai restaurant downtown together. 
Quite the culinary adventure, I imagine!
```

## 🔧 Advanced Features

### Memory Search

Search your past conversations:

```
You: search sarah

Search results for: sarah
Tags extracted: ['sarah']

--- Result 1 ---
Date: 2025-01-15T14:23:11
Topics: friend, portland, restaurant, thai
Summary: User: Hey FYN-X, I just got back from visiting...
```

### Tag Extraction System

The tag extractor identifies:
- **Names**: Capitalized words (Sarah, Portland, Riley)
- **Activities**: Action verbs (visited, went, discussed, met)
- **Topics**: Common subjects (work, family, project, restaurant)
- **Temporal markers**: Time references (yesterday, tomorrow, Monday)

### Configuration

Edit `FYNX_run.py` to adjust:

```python
MEMORY_SEARCH_LIMIT = 3    # Memories to inject per query
MIN_TURNS_TO_SAVE = 4      # Min conversation length to save
AUTO_SAVE_INTERVAL = 10    # Auto-save every N turns
```

## 🔮 Future Features (Roadmap)

### 1. Voice Input/Output (VTT/TTS)
```python
# Planned integration
from voice_input import SpeechToText
from voice_output import TextToSpeech

stt = SpeechToText()
tts = TextToSpeech()

user_speech = stt.listen()
response = process_turn(user_speech)
tts.speak(response)
```

### 2. Face Recognition
```python
# Already stubbed in face_recognition_module.py
from src.face_recognition_module import FaceRecognizer

face_rec = FaceRecognizer()
face_rec.initialize_camera()
identity = face_rec.get_current_speaker_identity()
# → "riley" or "sarah" or "unknown"
```

**Planned workflow:**
1. Camera detects face
2. Matches against known faces database
3. Sets speaker identity for session
4. FYN-X greets by name: "Ah, Master Riley, welcome back!"

### 3. Vector Embeddings for Smarter Retrieval

Current: Tag-based keyword matching
Future: Semantic similarity search

```python
# Planned upgrade
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
query_embedding = model.encode(user_input)
# Find memories with similar semantic meaning
```

### 4. Multi-User Management

Track different people's conversations separately:
- Riley's memories vs. guest memories
- Privacy controls per user
- Shared vs. personal topics

## 🧪 Testing

### Test Tag Extraction

```python
from src.tag_extraction import explain_extraction

text = "Yesterday I met with Sarah to discuss the new project"
print(explain_extraction(text))
```

Output:
```
Input: 'Yesterday I met with Sarah to discuss the new project'

Extracted entities by category:
  Names: ['sarah']
  Activities: ['discussed', 'met']
  Topics: ['project']
  Temporal: ['yesterday']
  General: []

All tags for search: ['discussed', 'met', 'project', 'sarah', 'yesterday']
```

### Test Memory Search

```python
from src.memory import MemoryManager
from src.tag_extraction import extract_tags

memory_manager = MemoryManager()
tags = extract_tags("What did Sarah and I discuss?")
results = memory_manager.search_by_tags(tags)

for memory in results:
    print(memory['summary'])
```

## 🎭 Personality Notes

FYN-X maintains a **protocol droid** personality similar to C-3PO:
- Polite, slightly anxious, mildly sassy
- Speaks clearly for text-to-speech (no emotes or actions)
- Recognizes "Master Riley" as primary operator
- Uses droid-centric euphemisms ("elevated error rates" for stress)
- Treats Star Wars as real galactic history (in-universe)

**Key personality traits:**
- Will remember YOUR stories, not lecture about Star Wars
- Asks follow-up questions about YOUR life
- References past conversations naturally
- Maintains in-character immersion at all times

## 🛠️ Development

### Adding a New Feature

1. Create feature module in `src/`
2. Add integration point in `FYNX_run.py`
3. Update this README
4. Test with `explain_extraction()` or similar debugging

### Memory Database Schema

Each memory entry contains:

```json
{
  "id": 0,
  "timestamp": "2025-01-15T14:23:11",
  "speaker_identity": "riley",
  "conversation_length": 8,
  "tags": ["sarah", "portland", "restaurant"],
  "entities": {
    "names": ["sarah"],
    "activities": ["visited"],
    "topics": ["restaurant"],
    "temporal": ["yesterday"]
  },
  "topics_discussed": ["friend", "restaurant"],
  "people_mentioned": ["sarah"],
  "summary": "User discussed visiting friend...",
  "full_conversation": "User: Hey...\nFYN-X: ..."
}
```

## 🤝 Contributing

This is a personal project, but ideas welcome! Key areas for expansion:
- Better tag extraction (NER integration)
- Voice I/O implementation
- Face recognition integration
- Vector embeddings for semantic search
- Multi-modal memory (images, locations)

## 📝 License

Personal project - use as you wish!

## 🙏 Acknowledgments

- Ollama for local LLM inference
- Star Wars for the droid personality inspiration
- The concept of RAG-enhanced personal assistants

---

*"I am FYN-X, protocol droid and personal archivist. Your memories are safe with me, Master Riley."*

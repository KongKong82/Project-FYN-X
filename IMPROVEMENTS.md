# FYN-X Improvements: Memory System and Benchmarking

## Overview
This update addresses several key issues to make FYN-X more efficient and intelligent:

1. **No Identity Assumptions** - FYN-X no longer assumes who it's talking to
2. **Stricter Memory Storage** - Only important sentences are saved, not full conversations
3. **Name-Based Filtering** - Added `speaker_name` field for efficient memory filtering
4. **Performance Benchmarking** - Track execution time of each module

---

## 🆕 New Features

### 1. Speaker Name Handling

**Before:** FYN-X would assume a speaker identity (default "unknown")

**Now:** 
- FYN-X asks for your name when starting a conversation
- You can skip providing a name (it remains `None`)
- Use `setname <your name>` during conversation to set/update your name
- Memories are tagged with `speaker_name` for filtering

**Example:**
```
[FYN-X] I don't know who I'm speaking with.
[FYN-X] What is your name? (or press Enter to skip): Riley
[FYN-X] Nice to meet you, Riley! I'll remember you!
```

Or during conversation:
```
You: setname Riley
✓ Name set to: Riley
```

### 2. Smarter Memory Storage

**Before:** Full conversations stored in JSON, making files huge

**Now:**
- Only the most important/memorable sentences are extracted and saved
- Each sentence is scored based on:
  - Names mentioned (15 points per name)
  - Activities/actions (10 points per activity)
  - Topics discussed (8 points per topic)
  - Temporal markers (5 points per time reference)
  - Importance indicators (12 points per indicator)
- Only sentences scoring 25+ are saved
- Maximum of 5 important sentences per conversation

**Memory Structure:**
```json
{
  "speaker_name": "Riley",
  "timestamp": "2025-01-17T...",
  "important_sentences": [
    {"text": "I'm working on FYN-X robot project", "score": 45.2},
    {"text": "Planning to add voice recognition next week", "score": 38.5}
  ],
  "summary": "I'm working on FYN-X robot project | Planning to add voice...",
  "tags": ["working", "fynx", "robot", "project", "planning", "voice", "recognition", "week"],
  "people_mentioned": ["Riley"],
  "topics_discussed": ["work", "project"]
}
```

### 3. Performance Benchmarking

**New Module:** `src/benchmarks.py`

Track performance of each module to identify optimization opportunities.

**Usage:**

View live performance summary after each conversation:
```
You: exit
✓ Conversation saved to memory

============================================================
PERFORMANCE SUMMARY
============================================================
Total Time: 15234.45ms
Modules Called: 8

Module Breakdown:
------------------------------------------------------------
ollama_inference              12500.23ms (82.1%) [3 calls, avg: 4166.74ms]
memory_search                  1234.56ms ( 8.1%) [3 calls, avg: 411.52ms]
tag_extraction                  456.78ms ( 3.0%) [3 calls, avg: 152.26ms]
prompt_building                 234.56ms ( 1.5%) [3 calls, avg: 78.19ms]
save_memory                     123.45ms ( 0.8%) [1 calls, avg: 123.45ms]
============================================================
```

View historical stats:
```
You: benchmark

================================================================================
MODULE STATISTICS (last 10 sessions)
================================================================================
ollama_inference               Avg: 4250.12ms  Min: 3800.00ms  Max: 5200.00ms  (30 calls)
memory_search                  Avg:  425.34ms  Min:  320.00ms  Max:  550.00ms  (30 calls)
tag_extraction                 Avg:  155.23ms  Min:  120.00ms  Max:  200.00ms  (30 calls)
...
================================================================================
```

**Programmatic Usage:**
```python
from src import benchmarks

# Option 1: Context manager
with benchmarks.track_time("my_module", {"size": 100}):
    # Your code here
    result = process_data()

# Option 2: Decorator
@benchmarks.timed("my_function")
def my_function():
    return compute_something()
```

### 4. Name-Based Memory Filtering

**All search functions now support speaker filtering:**

```python
# Search only Riley's memories
memories = memory_manager.search_by_tags(
    tags=["robotics", "project"],
    speaker_name="Riley"
)

# Get Riley's recent memories
recent = memory_manager.get_recent_memories(
    limit=5,
    speaker_name="Riley"
)

# Search memories about a specific person
about_alex = memory_manager.search_by_person("Alex")

# Search memories FROM a specific speaker
from_riley = memory_manager.search_by_speaker_name("Riley")
```

---

## 🔧 New Commands

| Command | Description |
|---------|-------------|
| `setname <name>` | Set or update your name during conversation |
| `benchmark` | Show performance statistics (if benchmarking enabled) |
| `stats` | Show memory database statistics |
| `search <query>` | Search memories (now shows speaker names) |
| `exit` | End conversation and show performance summary |

---

## 📊 Updated Memory Stats

```
Memory Database Stats:
  Total memories: 42
  Unique speakers: 3          ← NEW!
  Unique people: 15
  Unique topics: 28
  Known speakers: Riley, Alex, Sam    ← NEW!
```

---

## 🚀 Command Line Arguments

```bash
# Run with benchmarking (default)
python FYNX_run.py

# Disable benchmarking
python FYNX_run.py --no-benchmarks

# Enable network publishing
python FYNX_run.py --network

# Enable ROS2 publishing
python FYNX_run.py --ros2

# Disable streaming
python FYNX_run.py --no-streaming

# Combine flags
python FYNX_run.py --network --no-benchmarks
```

---

## 🔍 What Gets Saved Now?

**Example Conversation:**

```
You: Hi, I'm Riley. I'm working on a robotics project called FYN-X. 
     I'm planning to add voice recognition next week.
FYN-X: That sounds exciting! What kind of voice recognition?
You: I want it to recognize different speakers.
FYN-X: Great idea! That would make interactions more personal.
```

**What's Saved:**
```json
{
  "speaker_name": "Riley",
  "important_sentences": [
    {
      "text": "I'm working on a robotics project called FYN-X",
      "score": 48.5
    },
    {
      "text": "I'm planning to add voice recognition next week",
      "score": 42.0
    },
    {
      "text": "I want it to recognize different speakers",
      "score": 35.5
    }
  ],
  "tags": ["riley", "working", "robotics", "project", "fynx", "planning", "voice", "recognition", "week", "speakers"],
  "people_mentioned": ["Riley"],
  "topics_discussed": ["work", "project", "plan"]
}
```

**What's NOT Saved:**
- Generic responses like "That sounds exciting!"
- Low-value sentences with no specific information
- Full conversation logs (unless very short, <4 turns)

---

## 📈 Performance Optimization Workflow

1. **Run conversations normally** - benchmarking happens automatically
2. **Type `benchmark`** to see which modules are slowest
3. **Focus optimization efforts** on the highest time consumers
4. **Compare before/after** using historical stats

**Example Analysis:**
```
If you see:
  ollama_inference: 85% of total time
  memory_search: 10% of total time
  tag_extraction: 3% of total time

→ Focus on optimizing Ollama inference first
  (e.g., use smaller model, optimize prompt length)
```

---

## 🧪 Testing the Changes

### Test 1: Name Handling
```bash
python FYNX_run.py
# Don't provide name when asked
# Later in conversation: "setname TestUser"
# Type "stats" to verify speaker is saved
```

### Test 2: Memory Efficiency
```bash
# Have a conversation with multiple topics
# Exit and check data/memories.json
# Verify only important sentences are saved
```

### Test 3: Benchmarking
```bash
python FYNX_run.py
# Have a few conversations
# Type "benchmark" to see stats
# Exit to see session summary
```

### Test 4: Name Filtering
```bash
# Create memories as "Riley"
# Exit and restart
# Create memories as "Alex"
# Search should show filtered results
```

---

## 📝 Files Modified

| File | Changes |
|------|---------|
| `src/benchmarks.py` | **NEW** - Performance tracking module |
| `src/tag_extraction.py` | Added sentence importance scoring |
| `src/memory.py` | Added `speaker_name` field and filtering |
| `FYNX_run.py` | Integrated benchmarking, name handling |

---

## 🎯 Benefits

1. **Smaller Memory Files** - Only ~5 sentences per conversation vs entire logs
2. **Better Recall** - FYN-X remembers important info, not filler
3. **Faster Search** - Name filtering reduces search space
4. **Actionable Performance Data** - Know exactly where to optimize
5. **Better Privacy** - Less unnecessary conversation data stored
6. **Personalization** - Different people can have separate memory spaces

---

## 🔮 Next Steps

Based on these improvements, you can now:

1. **Profile your system** - See where bottlenecks are
2. **Optimize strategically** - Focus on high-impact modules
3. **Track improvements** - Compare benchmark stats over time
4. **Scale to multiple users** - Name-based filtering supports multi-user
5. **Reduce storage** - Memory files stay manageable long-term

Enjoy your upgraded FYN-X! 🤖

# FYN-X Quick Reference Guide

## 🚀 Getting Started

```bash
# Test the improvements
python test_improvements.py

# Run FYN-X normally
python FYNX_run.py

# Run with specific options
python FYNX_run.py --network          # Enable network publishing
python FYNX_run.py --no-benchmarks    # Disable benchmarking
python FYNX_run.py --no-streaming     # Disable streaming
```

## 💬 In-Conversation Commands

| Command | What It Does |
|---------|--------------|
| `setname <name>` | Set/update your name |
| `stats` | Show memory database stats |
| `search <query>` | Search past memories |
| `benchmark` | Show performance statistics |
| `exit` | End conversation, save & show summary |

## 🧠 Memory Structure (New)

```python
{
  "speaker_name": "Riley",              # WHO spoke (can be None)
  "important_sentences": [              # WHAT matters (max 5)
    {
      "text": "Working on FYN-X project",
      "score": 45.2
    }
  ],
  "summary": "Brief summary",           # Quick overview
  "tags": [...],                        # For searching
  "people_mentioned": ["Alex"],         # WHO was mentioned
  "topics_discussed": ["robotics"]      # WHAT was discussed
}
```

## 📊 Understanding Sentence Scores

| Score Range | Meaning | Example |
|-------------|---------|---------|
| 0-20 | Generic/filler | "That's interesting" |
| 20-40 | Somewhat important | "I like robotics" |
| 40-60 | Important | "Working on FYN-X project" |
| 60-80 | Very important | "Meeting Sarah tomorrow about project deadline" |
| 80+ | Critical | "I'm planning to launch FYN-X next Friday with Alex" |

**Score Components:**
- Names: +15 each
- Activities: +10 each  
- Topics: +8 each
- Importance words: +12 each
- Temporal markers: +5 each

## 🔍 Searching Memories

### From Command Line
```bash
# During conversation
You: search robotics
You: search meeting Alex
```

### Programmatically
```python
from src.memory import MemoryManager

manager = MemoryManager()

# Search by tags (auto-filtered by current speaker)
results = manager.search_by_tags(
    tags=["robotics", "project"],
    speaker_name="Riley"  # Optional
)

# Search by person mentioned
memories = manager.search_by_person("Alex")

# Search by speaker
memories = manager.search_by_speaker_name("Riley")

# Get recent memories
recent = manager.get_recent_memories(
    limit=5,
    speaker_name="Riley"  # Optional
)
```

## 📈 Benchmarking

### View Live Stats
```bash
You: benchmark
```

### Get Historical Data
```python
from src import benchmarks

# View specific module stats
stats = benchmarks.get_module_stats("ollama_inference", last_n=10)
print(stats)  # {'avg_ms': 4250.12, 'min_ms': 3800, ...}

# Print all module stats
benchmarks.print_all_module_stats(last_n=10)
```

### Add Custom Benchmarks
```python
from src.benchmarks import track_time, timed

# Option 1: Context manager
with track_time("my_module"):
    expensive_operation()

# Option 2: Decorator
@timed("my_function")
def my_function():
    return compute()
```

## 🎯 Optimization Workflow

1. **Identify bottleneck**: Type `benchmark` to see slowest modules
2. **Focus effort**: Optimize the highest % first
3. **Measure impact**: Compare before/after stats
4. **Iterate**: Repeat for next bottleneck

Example:
```
Before optimization:
  ollama_inference: 85% (4250ms avg)
  memory_search: 10% (500ms avg)
  
After optimizing prompt length:
  ollama_inference: 78% (3100ms avg)  ← 1150ms saved!
  memory_search: 15% (500ms avg)
```

## 🗂️ Memory File Sizes

**Before improvements:**
```
Typical memory file after 10 conversations:
- Full conversation logs: ~50-100KB
- Redundant information stored
- Difficult to search
```

**After improvements:**
```
Same 10 conversations:
- Important sentences only: ~5-10KB
- 90% reduction in file size
- Faster searches
- More targeted recall
```

## 🔧 Troubleshooting

### "I don't see my name in stats"
```bash
# During conversation:
You: setname YourName
You: stats    # Should now show your name
```

### "Benchmarks not showing"
```bash
# Make sure you didn't disable them:
python FYNX_run.py  # benchmarks ON by default
```

### "Memory file too large"
```bash
# Old memories might still have full conversations
# Delete old memories or migrate:
rm data/memories.json  # Start fresh
```

### "Sentence scores seem wrong"
```python
# Test scoring on your own sentences:
from src.tag_extraction import explain_extraction

text = "Your test sentence here"
print(explain_extraction(text))
```

## 📁 File Structure

```
fynx/
├── FYNX_run.py              # Main entry point
├── test_improvements.py     # Test suite for new features
├── IMPROVEMENTS.md          # Detailed change documentation
├── QUICKREFERENCE.md        # This file
├── src/
│   ├── memory.py           # ✨ Updated: speaker_name support
│   ├── tag_extraction.py   # ✨ Updated: sentence scoring
│   ├── search.py           # ✨ Updated: speaker filtering
│   ├── benchmarks.py       # ⭐ NEW: performance tracking
│   ├── streaming.py
│   ├── network.py
│   └── face_recognition_module.py
└── data/
    ├── memories.json        # Your memories (lighter now!)
    └── performance_log.json # Benchmark data
```

## 🎓 Best Practices

1. **Set your name early**: Helps FYN-X remember context better
2. **Review benchmark stats**: After 5-10 conversations
3. **Clear old memories**: If switching to multi-user mode
4. **Use search**: Before asking FYN-X to remember something
5. **Check important sentences**: Use `search` to verify what's saved

## 🚀 Next Steps

After testing the improvements:

1. ✅ Run test suite: `python test_improvements.py`
2. ✅ Have a conversation: `python FYNX_run.py`
3. ✅ Set your name: `setname Riley`
4. ✅ Check stats: `stats`
5. ✅ View benchmarks: `benchmark`
6. ✅ Search memories: `search robotics`
7. ✅ Review memory file: `data/memories.json`

Enjoy your upgraded FYN-X! 🤖✨

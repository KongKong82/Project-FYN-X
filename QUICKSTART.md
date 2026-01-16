# Quick Start Guide

Get FYN-X running in 5 minutes!

## Step 1: Install Ollama

Download and install Ollama:
- **Windows/Mac**: https://ollama.ai/download
- **Linux**: `curl https://ollama.ai/install.sh | sh`

Verify installation:
```bash
ollama --version
```

## Step 2: Create the FYN-X Model

From the `fynx` directory:

```bash
ollama create FYN-X-02 -f FYN-X.modelfile
```

You should see output like:
```
transferring model data
using existing layer sha256:...
creating new layer sha256:...
writing manifest
success
```

Verify the model was created:
```bash
ollama list
```

You should see `FYN-X-02` in the list.

## Step 3: Test the Components

Run the test suite to verify everything works:

```bash
python test_components.py
```

Expected output:
```
============================================================
FYN-X COMPONENT TEST SUITE
============================================================
TAG EXTRACTION TESTS
...
MEMORY SYSTEM TESTS
...
ALL TESTS COMPLETED
```

## Step 4: Run FYN-X!

```bash
python FYNX_run.py
```

You'll see:
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
```

## Example Conversation

```
You: Hey FYN-X, I just got back from lunch with my friend Maria

FYN-X: Ah, welcome back! I do hope your lunch with Maria was pleasant. 
How was the experience?

You: It was great! We went to that new Thai place downtown

FYN-X: Thai cuisine—how delightful! I trust it met your expectations?

You: Yes, the pad thai was amazing

FYN-X: Splendid! I shall make note of this recommendation for future 
reference. Thai restaurants with quality pad thai are worth remembering.

You: exit

✓ Conversation saved to memory (ID: 0)
  Topics: lunch, friend, restaurant, thai
  People: maria
```

## Test Memory Retrieval

Start a new conversation:

```bash
python FYNX_run.py
```

Then ask:
```
You: What restaurant did I go to with Maria?

FYN-X: Ah yes, my records indicate you enjoyed lunch with Maria at a 
Thai restaurant downtown. If I recall correctly, you were quite pleased 
with the pad thai. A successful culinary venture, it would seem!
```

## Using Special Commands

### Check Statistics
```
You: stats

Memory Database Stats:
  Total memories: 1
  Unique people: 1
  Unique topics: 4
  Known people: maria
```

### Search Memories
```
You: search maria

Search results for: maria
Tags extracted: ['maria']

--- Result 1 ---
Date: 2025-01-15T14:23:11
Topics: lunch, friend, restaurant, thai
Summary: User: Hey FYN-X, I just got back from lunch...
```

## Troubleshooting

### "Ollama not found"
- Make sure Ollama is installed and in your PATH
- Try running `ollama list` in a new terminal
- On Windows, you may need to restart your terminal after installation

### "Model FYN-X-02 not found"
- Run `ollama create FYN-X-02 -f FYN-X.modelfile` again
- Check that you're in the `fynx` directory
- Verify the `FYN-X.modelfile` exists

### Response takes too long
- First response is slower (model loading)
- Subsequent responses should be faster
- Check CPU usage - Ollama is computationally intensive
- Consider using a smaller base model (edit FYN-X.modelfile to use `llama3.2` instead of `llama3`)

### Memory not saving
- Check that `data/` directory exists
- Verify write permissions
- Look for `data/memories.json` after ending a conversation
- Conversations need at least 4 turns to auto-save

## Next Steps

1. **Have multiple conversations** - Build up your memory database
2. **Test memory retrieval** - Ask about past topics/people
3. **Read DEVELOPMENT.md** - Learn about upcoming features
4. **Customize the personality** - Edit `FYN-X.modelfile`

## Tips for Better Conversations

**Good prompts:**
- "I met with John yesterday to discuss the quarterly report"
- "Remind me what Sarah and I talked about last time"
- "I need to plan my daughter's birthday party next month"

**FYN-X remembers:**
- People you mention
- Topics you discuss  
- Activities you do
- Time references

**FYN-X won't remember:**
- Things from before you started using it
- Conversations from other FYN-X instances (unless you copy the memories.json file)
- Star Wars lore (the model knows this already!)

## Advanced Usage

### View Raw Memory
```bash
cat data/memories.json
```

### Backup Memories
```bash
cp data/memories.json data/memories_backup.json
```

### Import Old Conversations
Edit `data/memories.json` and add entries manually (advanced users only!)

### Change Models
Edit `FYNX_run.py` and change:
```python
MODEL_NAME = "FYN-X-02"  # Change to your model name
```

---

Enjoy your personal memory-enhanced droid companion!

*"I shall remember this conversation most faithfully, Master."* - FYN-X

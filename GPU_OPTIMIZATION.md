# GPU Optimization Guide for FYN-X

## 🎯 Goal
Ensure Ollama uses your GPU for maximum performance and reduce response times.

## ⚡ Quick GPU Check

```bash
# Check if Ollama is using GPU
ollama ps

# Check GPU usage (Windows)
# Open Task Manager → Performance → GPU

# Check GPU usage (Linux)
nvidia-smi
```

## 🔧 Step 1: Verify GPU Drivers

### NVIDIA GPU
```bash
# Check NVIDIA driver
nvidia-smi

# Should show your GPU and driver version
# If not, install/update NVIDIA drivers from:
# https://www.nvidia.com/download/index.aspx
```

### AMD GPU
```bash
# Check ROCm (Linux only)
rocm-smi

# Windows: AMD GPUs use DirectML (should work automatically)
```

### Apple Silicon (M1/M2/M3)
```bash
# Metal is built-in, should work automatically
# Check with:
system_profiler SPDisplaysDataType
```

## 🔧 Step 2: Rebuild FYN-X Model with GPU Settings

The updated `FYN-X.modelfile` now includes:
```
PARAMETER num_gpu 999    # Use all available GPU layers
PARAMETER num_thread 8   # CPU threads for non-GPU work
PARAMETER num_ctx 8192   # Context window size
```

**Rebuild the model:**
```bash
cd C:\Users\riley\fynx

# Remove old model
ollama rm FYN-X

# Create new model with GPU settings
ollama create FYN-X -f FYN-X.modelfile
```

## 🔧 Step 3: Verify GPU Usage

After rebuilding, run FYN-X and check GPU usage:

### Windows (Task Manager)
1. Run: `python FYNX_run.py`
2. Open Task Manager (Ctrl+Shift+Esc)
3. Go to Performance → GPU
4. You should see GPU usage spike when FYN-X responds

### NVIDIA GPUs (nvidia-smi)
```bash
# In another terminal while FYN-X is running:
watch -n 1 nvidia-smi

# Look for:
# - GPU Utilization should be high (60-100%)
# - Memory usage should increase
# - Process "ollama" should appear
```

### Check Ollama Logs
```bash
# View Ollama logs to see GPU detection
# Windows:
ollama serve

# Look for lines like:
# "GPU detected: NVIDIA GeForce RTX 3080"
# "Loaded model to GPU"
```

## 🔧 Step 4: Optimize Model Size

If you have limited GPU VRAM, use a smaller model:

```bash
# Check available models
ollama list

# Current: llama3 (4.7GB)
# Alternative options:

# Smaller, faster (2.3GB) - RECOMMENDED for testing
ollama pull llama3.2

# Then update FYN-X.modelfile:
# Change first line from "FROM llama3" to "FROM llama3.2"

# Rebuild
ollama create FYN-X -f FYN-X.modelfile
```

## 🔧 Step 5: Environment Variables (Advanced)

Set these before running Ollama:

### Force GPU Usage
```bash
# Windows (PowerShell)
$env:OLLAMA_NUM_GPU="999"

# Linux/Mac
export OLLAMA_NUM_GPU=999
```

### Increase Parallel Requests (if you have lots of VRAM)
```bash
# Windows (PowerShell)
$env:OLLAMA_NUM_PARALLEL="4"

# Linux/Mac
export OLLAMA_NUM_PARALLEL=4
```

### Set GPU Device (if you have multiple GPUs)
```bash
# Windows (PowerShell)
$env:CUDA_VISIBLE_DEVICES="0"  # Use first GPU

# Linux/Mac
export CUDA_VISIBLE_DEVICES=0
```

## 📊 Performance Benchmarks

### Expected Performance (with GPU)

| GPU | Response Time | Tokens/sec |
|-----|---------------|------------|
| RTX 3060 (12GB) | 2-4s | 30-50 |
| RTX 3080 (10GB) | 1-3s | 50-80 |
| RTX 4090 (24GB) | 1-2s | 80-120 |
| M1 Max | 2-4s | 30-50 |
| M2 Ultra | 1-2s | 60-100 |

### Expected Performance (CPU only)
| CPU | Response Time | Tokens/sec |
|-----|---------------|------------|
| Modern i7/Ryzen 7 | 10-20s | 5-10 |
| Modern i5/Ryzen 5 | 15-30s | 3-8 |

**If your response times match CPU performance, GPU isn't being used!**

## 🐛 Troubleshooting

### Problem: GPU not being used

**Check 1: Model loaded to GPU?**
```bash
ollama ps
# Should show model loaded with GPU info
```

**Check 2: VRAM sufficient?**
```bash
# llama3 needs ~4-5GB VRAM
# Check available VRAM:
nvidia-smi  # Look at "Memory-Usage"

# If insufficient, use smaller model:
ollama pull llama3.2  # Only needs ~2-3GB
```

**Check 3: Ollama service using GPU?**
```bash
# Restart Ollama service
# Windows:
taskkill /F /IM ollama.exe
ollama serve

# Linux:
sudo systemctl restart ollama
```

### Problem: "CUDA out of memory"

**Solution 1: Reduce context window**
Edit `FYN-X.modelfile`:
```
PARAMETER num_ctx 4096  # Reduce from 8192
```

**Solution 2: Reduce GPU layers**
```
PARAMETER num_gpu 32  # Reduce from 999
```

**Solution 3: Use smaller model**
```
FROM llama3.2  # Instead of llama3
```

### Problem: Slow despite GPU usage

**Check 1: Thermal throttling**
```bash
nvidia-smi
# Check GPU temperature
# If >80°C, GPU may be throttling
```

**Check 2: Power limit**
```bash
nvidia-smi -q -d POWER
# Ensure GPU is not power-limited
```

**Solution: Increase power limit (NVIDIA)**
```bash
# Linux (requires root)
sudo nvidia-smi -pl 300  # Set to 300W (adjust for your GPU)
```

## 🎯 Optimal Configuration

For **RTX 3060/3070/3080** (8-12GB VRAM):
```modelfile
FROM llama3
PARAMETER num_gpu 999
PARAMETER num_ctx 8192
PARAMETER num_thread 8
```

For **RTX 3050/GTX 1660** (4-6GB VRAM):
```modelfile
FROM llama3.2
PARAMETER num_gpu 999
PARAMETER num_ctx 4096
PARAMETER num_thread 8
```

For **M1/M2 Mac** (Unified memory):
```modelfile
FROM llama3
PARAMETER num_gpu 999
PARAMETER num_ctx 8192
PARAMETER num_thread 8
```

## 🚀 Quick Start Checklist

- [ ] GPU drivers installed and updated
- [ ] Ollama can detect GPU (`ollama ps`)
- [ ] Updated FYN-X.modelfile with GPU parameters
- [ ] Rebuilt model: `ollama create FYN-X -f FYN-X.modelfile`
- [ ] Verified GPU usage during inference
- [ ] Response times < 5 seconds for typical queries

## 📈 Monitoring Performance

Add this to your workflow:

```bash
# Terminal 1: Run FYN-X
python FYNX_run.py --enable-benchmarks

# Terminal 2: Monitor GPU
watch -n 1 nvidia-smi

# At end of conversation, type "benchmark"
# Compare inference times with GPU targets above
```

## 💡 Pro Tips

1. **Warm up the model**: First response is always slower (model loading)
2. **Batch testing**: GPU is most efficient with consistent load
3. **Monitor VRAM**: Don't run other GPU-intensive apps simultaneously
4. **Update Ollama**: Newer versions have better GPU support
   ```bash
   ollama --version  # Check version
   # Update from: https://ollama.ai/download
   ```

That's it! Your FYN-X should now be running on GPU with optimal performance. 🚀

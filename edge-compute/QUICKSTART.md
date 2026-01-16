# FYN-X Edge Compute - Quick Reference

Scripts for running FYN-X TTS on Raspberry Pi or other edge devices.

## Quick Start (Network Mode)

### On Raspberry Pi:
```bash
# 1. Copy files
scp edge-compute/*.py pi@raspberrypi.local:~/

# 2. Run setup script
chmod +x setup_raspberry_pi.sh
./setup_raspberry_pi.sh

# 3. Start receiver
python3 network_tts_receiver.py
```

### On Main Computer:
```bash
# 1. Edit FYNX_run.py configuration:
ENABLE_NETWORK = True
NETWORK_HOST = "raspberrypi.local"  # or IP like "192.168.1.100"

# 2. Run FYN-X with network mode
python FYNX_run.py --network
```

## Available Scripts

| Script | Description |
|--------|-------------|
| `network_tts_receiver.py` | TCP socket receiver (no ROS2 required) |
| `ros2_tts_node.py` | ROS2 subscriber node (for robotics) |
| `setup_raspberry_pi.sh` | Automated setup script for Pi |

## Command Line Options

### Main System (FYNX_run.py)
```bash
python FYNX_run.py                    # Standard mode
python FYNX_run.py --network          # Enable network publishing
python FYNX_run.py --ros2             # Enable ROS2 publishing
python FYNX_run.py --no-streaming     # Disable streaming (legacy mode)
```

### Raspberry Pi (network_tts_receiver.py)
```bash
python3 network_tts_receiver.py                    # Default (espeak, port 5555)
python3 network_tts_receiver.py --port 6000        # Custom port
python3 network_tts_receiver.py --tts festival     # Different TTS engine
```

## TTS Engine Options

- **espeak** - Lightweight, robotic (perfect for droids!) ⭐ Recommended
- **festival** - More natural voice
- **piper** - High quality neural TTS (requires setup)

## Troubleshooting

**Can't connect?**
```bash
# Find Pi IP:
hostname -I

# Test connectivity:
ping raspberrypi.local

# Check if receiver is running:
netstat -tulpn | grep 5555
```

**No audio?**
```bash
# Test audio:
speaker-test -t wav -c 2

# Adjust volume:
alsamixer

# Test TTS:
espeak "test"
```

**High latency?**
- Use wired ethernet instead of WiFi
- Check network with: `ping -c 10 <pi-ip>`
- Reduce memory search limit in FYNX_run.py

## See Full Documentation

For complete setup instructions, ROS2 integration, and advanced features, see:
- `edge-compute/README.md` - Full setup guide
- Main project `README.md` - Overall system architecture

---

*Streaming TTS for real-time droid conversations!*

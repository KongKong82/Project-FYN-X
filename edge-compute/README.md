# FYN-X Edge Compute Setup Guide

This directory contains scripts for running FYN-X TTS on a Raspberry Pi or other edge device.

## Overview

FYN-X can stream responses to a Raspberry Pi in real-time, allowing for:
- **Lower latency** - Text chunks are spoken as they're generated
- **Edge processing** - TTS runs on the Pi, reducing main system load
- **Hardware flexibility** - Use Pi-specific audio hardware

## Two Approaches

### 1. Network Socket (Simpler)
- No dependencies except Python stdlib
- Direct TCP socket communication
- Easier to set up

### 2. ROS2 (More Robust)
- Industry-standard robotics middleware
- Better for complex robot integration
- More scalable for multiple nodes

---

## Setup Instructions

### Prerequisites

**On Raspberry Pi:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3 (usually pre-installed)
sudo apt install python3 python3-pip -y

# Install TTS engine (choose one)
# Option 1: espeak (lightweight, robotic voice - PERFECT for droids!)
sudo apt install espeak -y

# Option 2: Festival (more natural voice)
sudo apt install festival -y

# Option 3: Piper (best quality, neural TTS)
# See: https://github.com/rhasspy/piper
```

**On Main System (where FYN-X runs):**
```bash
# No additional dependencies for network mode
# For ROS2 mode, install rclpy
pip install rclpy std_msgs
```

---

## Method 1: Network Socket (Recommended for Beginners)

### On Raspberry Pi

1. **Copy the receiver script:**
```bash
scp edge-compute/network_tts_receiver.py pi@raspberrypi.local:~/
```

2. **Make it executable:**
```bash
chmod +x network_tts_receiver.py
```

3. **Run the receiver:**
```bash
# Basic usage (espeak)
python3 network_tts_receiver.py

# With custom port
python3 network_tts_receiver.py --port 6000

# With different TTS engine
python3 network_tts_receiver.py --tts festival
```

You should see:
```
Starting FYN-X TTS Receiver on 0.0.0.0:5555
TTS Engine: espeak
✓ Server listening on 0.0.0.0:5555
Waiting for FYN-X connection...
```

### On Main System

1. **Configure network settings in FYNX_run.py:**
```python
# Edit these lines at the top of FYNX_run.py
ENABLE_NETWORK = True
NETWORK_HOST = "raspberrypi.local"  # or "192.168.1.100"
NETWORK_PORT = 5555
```

2. **Run FYN-X:**
```bash
python FYNX_run.py --network
```

You should see:
```
FYN-X PERSONAL MEMORY SYSTEM
(Streaming Mode Enabled)
(Network: raspberrypi.local:5555)
```

3. **Test it:**
```
You: Hello FYN-X!

FYN-X: [Text streams to Pi and is spoken]
```

---

## Method 2: ROS2 (For Robotics Integration)

### On Raspberry Pi

1. **Install ROS2 (Humble or later):**
```bash
# Follow official ROS2 installation for Raspberry Pi:
# https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html

# Quick install (Ubuntu 22.04):
sudo apt install ros-humble-desktop
```

2. **Install Python ROS2 packages:**
```bash
sudo apt install python3-rclpy python3-std-msgs
```

3. **Copy the ROS2 node:**
```bash
scp edge-compute/ros2_tts_node.py pi@raspberrypi.local:~/
chmod +x ros2_tts_node.py
```

4. **Source ROS2 and run the node:**
```bash
source /opt/ros/humble/setup.bash
python3 ros2_tts_node.py
```

### On Main System

1. **Install ROS2 Python client:**
```bash
pip install rclpy std_msgs
```

2. **Configure in FYNX_run.py:**
```python
ENABLE_ROS2 = True
ROS2_TOPIC = "/fynx/tts_input"
```

3. **Run FYN-X:**
```bash
python FYNX_run.py --ros2
```

---

## Testing the Connection

### Network Mode Test
```bash
# On Pi:
python3 network_tts_receiver.py

# On main system:
python3 -c "
from src.network import NetworkPublisher
pub = NetworkPublisher('raspberrypi.local', 5555)
pub.connect()
pub.publish_chunk('Hello from FYN-X!')
pub.disconnect()
"
```

### ROS2 Mode Test
```bash
# On Pi:
python3 ros2_tts_node.py

# On main system (in another terminal):
ros2 topic pub /fynx/tts_input std_msgs/msg/String "data: 'Hello from ROS2'"
```

---

## TTS Engine Comparison

| Engine | Quality | Speed | CPU Usage | Robotic? | Setup |
|--------|---------|-------|-----------|----------|-------|
| **espeak** | Low | Fast | Low | ✅ Very | Easy |
| **festival** | Medium | Medium | Medium | Somewhat | Easy |
| **piper** | High | Medium | High | Configurable | Complex |

**Recommendation for droids: espeak!**
- Sounds authentically robotic
- Very lightweight
- Perfect for protocol droid personality
- Instant installation

---

## Troubleshooting

### "Connection refused"
- Check Pi is on same network
- Verify IP address: `ping raspberrypi.local`
- Check firewall: `sudo ufw status`
- Try IP instead of hostname

### "No sound output"
- Test audio: `speaker-test -t wav -c 2`
- Check volume: `alsamixer`
- Verify TTS works: `espeak "test"`

### "ROS2 not found"
- Source ROS2: `source /opt/ros/humble/setup.bash`
- Add to `.bashrc` to auto-source

### "High latency"
- Check network connection speed
- Use wired ethernet instead of WiFi
- Reduce sentence chunking threshold

---

## Running as a Service

### Systemd Service (Network Mode)

Create `/etc/systemd/system/fynx-tts.service`:

```ini
[Unit]
Description=FYN-X TTS Receiver
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/network_tts_receiver.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable fynx-tts.service
sudo systemctl start fynx-tts.service
sudo systemctl status fynx-tts.service
```

---

## Advanced Configuration

### Custom Piper Voice

1. Download Piper voice model:
```bash
wget https://github.com/rhasspy/piper/releases/download/v1.0.0/voice-en-us-lessac-medium.tar.gz
tar -xzf voice-en-us-lessac-medium.tar.gz
```

2. Edit `ros2_tts_node.py` or `network_tts_receiver.py`:
```python
VOICE_MODEL = "/home/pi/piper/models/en_US-lessac-medium.onnx"
```

### Adjust Speech Rate

**espeak:**
```python
# In _speak_espeak() method:
['espeak', '-v', 'en', '-s', '160', '-p', '40', text]
#                         ^^^^       ^^^^
#                         speed      pitch
```

### Network Security

**Use SSH tunnel for secure connection:**
```bash
# On main system:
ssh -L 5555:localhost:5555 pi@raspberrypi.local

# Then configure:
NETWORK_HOST = "localhost"
```

---

## Performance Tips

1. **Use wired ethernet** for lowest latency
2. **Overclock Pi** for faster TTS processing
3. **Use espeak** for minimal resource usage
4. **Sentence chunking** balances latency vs. natural speech
5. **Close unused services** on Pi for more resources

---

## Integration with Physical Robot

### GPIO Control Example

Add to `ros2_tts_node.py`:

```python
import RPi.GPIO as GPIO

class FynxTTSNode(Node):
    def __init__(self):
        super().__init__('fynx_tts_node')
        
        # Setup GPIO for mouth LED
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(18, GPIO.OUT)
        self.mouth_led = GPIO.PWM(18, 100)  # Pin 18, 100Hz
        
    def _speak(self, text: str):
        # Turn on mouth LED
        self.mouth_led.start(50)
        
        # Speak
        super()._speak(text)
        
        # Turn off mouth LED
        self.mouth_led.stop()
```

### Servo Control for Head Movement

```python
from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)

def nod_head():
    kit.servo[0].angle = 30
    time.sleep(0.2)
    kit.servo[0].angle = 0
```

---

## Next Steps

- [ ] Test basic connection
- [ ] Verify audio output
- [ ] Tune speech parameters
- [ ] Set up as system service
- [ ] Add physical robot integration (LEDs, servos)
- [ ] Configure face recognition camera
- [ ] Test full conversation loop

---

**Need help?** Check the main DEVELOPMENT.md for the complete roadmap.

*"I shall speak your words most faithfully, Master."* - FYN-X

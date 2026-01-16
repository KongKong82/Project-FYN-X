#!/bin/bash
# FYN-X Raspberry Pi Quick Setup Script
# Run this on your Raspberry Pi to set up TTS receiver

set -e

echo "=================================="
echo "FYN-X Raspberry Pi Setup"
echo "=================================="
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "[1/4] Updating system packages..."
sudo apt update

# Install TTS engine
echo ""
echo "[2/4] Installing TTS engines..."
echo "Which TTS engine(s) would you like to install?"
echo "  1) espeak (recommended - lightweight, robotic voice)"
echo "  2) festival (more natural voice)"
echo "  3) Both"
read -p "Choice (1-3): " tts_choice

case $tts_choice in
    1)
        sudo apt install -y espeak
        TTS_ENGINE="espeak"
        ;;
    2)
        sudo apt install -y festival
        TTS_ENGINE="festival"
        ;;
    3)
        sudo apt install -y espeak festival
        TTS_ENGINE="espeak"
        ;;
    *)
        echo "Invalid choice, installing espeak"
        sudo apt install -y espeak
        TTS_ENGINE="espeak"
        ;;
esac

# Test audio
echo ""
echo "[3/4] Testing audio output..."
if command -v speaker-test &> /dev/null; then
    echo "Playing test sound (5 seconds)..."
    timeout 5s speaker-test -t wav -c 2 2>/dev/null || true
fi

# Test TTS
if [ "$TTS_ENGINE" = "espeak" ]; then
    echo "Testing espeak..."
    espeak "Hello, I am FYN-X" 2>/dev/null || echo "Warning: espeak test failed"
fi

# Create run script
echo ""
echo "[4/4] Creating launch scripts..."

cat > ~/start_fynx_receiver.sh << 'EOF'
#!/bin/bash
# FYN-X TTS Receiver Launcher

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Configuration
PORT=5555
TTS_ENGINE="espeak"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --tts)
            TTS_ENGINE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Starting FYN-X TTS Receiver..."
echo "Port: $PORT"
echo "TTS Engine: $TTS_ENGINE"
echo ""

python3 network_tts_receiver.py --port "$PORT" --tts "$TTS_ENGINE"
EOF

chmod +x ~/start_fynx_receiver.sh

# Create systemd service file template
cat > ~/fynx-tts.service << EOF
[Unit]
Description=FYN-X TTS Receiver
After=network.target sound.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME
ExecStart=/usr/bin/python3 $HOME/network_tts_receiver.py --tts $TTS_ENGINE
Restart=always
RestartSec=10
Environment="HOME=$HOME"

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "TTS Engine: $TTS_ENGINE"
echo ""
echo "To run the receiver manually:"
echo "  ./start_fynx_receiver.sh"
echo ""
echo "To install as a system service:"
echo "  sudo cp ~/fynx-tts.service /etc/systemd/system/"
echo "  sudo systemctl enable fynx-tts"
echo "  sudo systemctl start fynx-tts"
echo ""
echo "To test from another computer:"
echo "  python FYNX_run.py --network"
echo ""
echo "Find your Pi's IP address:"
echo "  hostname -I"
echo ""

# Show IP address
IP_ADDR=$(hostname -I | awk '{print $1}')
if [ -n "$IP_ADDR" ]; then
    echo "This Pi's IP address: $IP_ADDR"
    echo ""
    echo "On your main computer, edit FYNX_run.py:"
    echo "  NETWORK_HOST = \"$IP_ADDR\""
    echo ""
fi

echo "Ready for FYN-X!"

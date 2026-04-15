#!/bin/bash
# =============================================================================
# FYN-X Edge — Raspberry Pi Setup Script
# =============================================================================
# Installs Docker, pulls the FYN-X Edge camera publisher image, and sets it
# up to run automatically on boot.
#
# Supports: Raspberry Pi 3B, Pi Zero 2W (arm64)
# Requires: Debian/Raspberry Pi OS (Bookworm or Trixie), internet connection
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/KongKong82/Project-FYN-X/refs/heads/main/FYN-X_Edge_Setup.sh | bash
#   — or —
#   bash FYN-X_Edge_Setup.sh
# =============================================================================

set -e  # exit on any error

# ── Config ────────────────────────────────────────────────────────────────────
DOCKERHUB_IMAGE="kongkong82/fyn-x_edge:latest"
PROJECT_DIR="$HOME/fynx-edge"
ROS_DOMAIN_ID=0
# ─────────────────────────────────────────────────────────────────────────────

# ── Colours for output ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}    $1"; }
warning() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         FYN-X Edge Installer             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── Check we're on a supported platform ──────────────────────────────────────
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" ]]; then
    error "This script is for arm64 Raspberry Pi only (detected: $ARCH)"
fi
info "Architecture: $ARCH ✓"

# Detect Pi model for any model-specific tuning
PI_MODEL=$(cat /proc/device-tree/model 2>/dev/null | tr -d '\0' || echo "Unknown")
info "Detected: $PI_MODEL"

# Flag if this is a Zero 2W (512MB RAM) so we use lighter settings
IS_ZERO2W=false
if echo "$PI_MODEL" | grep -qi "zero 2"; then
    IS_ZERO2W=true
    warning "Pi Zero 2W detected — will apply low-memory camera settings"
fi

# ── Step 1: System update ─────────────────────────────────────────────────────
info "Updating package lists..."
sudo apt-get update -qq

# ── Step 2: Install dependencies ─────────────────────────────────────────────
# usbutils gives us lsusb for camera detection
PKGS_TO_INSTALL=""
for pkg in dphys-swapfile usbutils; do
    if ! command -v "${pkg/dphys-swapfile/dphys-swapfile}" &>/dev/null && \
       ! dpkg -l "$pkg" 2>/dev/null | grep -q "^ii"; then
        PKGS_TO_INSTALL="$PKGS_TO_INSTALL $pkg"
    fi
done
if [[ -n "$PKGS_TO_INSTALL" ]]; then
    info "Installing dependencies:$PKGS_TO_INSTALL..."
    sudo apt-get install -y -qq $PKGS_TO_INSTALL
    success "Dependencies installed"
else
    success "Dependencies already installed"
fi

# ── Step 3: Configure swap ────────────────────────────────────────────────────
SWAP_SIZE=1024
if [[ "$IS_ZERO2W" == true ]]; then
    SWAP_SIZE=512
fi

CURRENT_SWAP=$(grep CONF_SWAPSIZE /etc/dphys-swapfile 2>/dev/null | cut -d= -f2 || echo "0")
if [[ "$CURRENT_SWAP" -ge "$SWAP_SIZE" ]] 2>/dev/null; then
    success "Swap already configured (${CURRENT_SWAP}MB)"
else
    info "Configuring ${SWAP_SIZE}MB swap..."
    sudo sed -i "s/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=${SWAP_SIZE}/" /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    success "Swap configured (${SWAP_SIZE}MB)"
fi

# ── Step 4: Install Docker ────────────────────────────────────────────────────
if command -v docker &>/dev/null; then
    success "Docker already installed ($(docker --version | cut -d' ' -f3 | tr -d ','))"
else
    info "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    success "Docker installed"
fi

# ── Step 5: Add user to required groups ──────────────────────────────────────
info "Configuring user groups..."
for group in docker video audio; do
    if groups "$USER" | grep -q "\b$group\b"; then
        success "Already in group: $group"
    else
        sudo usermod -aG "$group" "$USER"
        success "Added $USER to group: $group"
    fi
done

# ── Step 6: Fix Docker socket permissions ────────────────────────────────────
if [[ -S /var/run/docker.sock ]]; then
    sudo chmod 666 /var/run/docker.sock
    success "Docker socket permissions OK"
fi

# ── Step 7: Enable Docker on boot ────────────────────────────────────────────
info "Enabling Docker service on boot..."
sudo systemctl enable docker
sudo systemctl start docker
success "Docker service enabled"

# ── Step 8: Detect USB camera ────────────────────────────────────────────────
#
# Known camera database — add new cameras here.
# Format per entry:
#   VENDOR_ID:PRODUCT_ID  (lowercase, as shown by lsusb)
#
# Config values set per camera:
#   CAM_NAME     — human-readable name shown in output
#   CAM_WIDTH    — default capture width
#   CAM_HEIGHT   — default capture height
#   CAM_FPS      — default capture framerate
#   CAM_AUDIO    — true if camera has a built-in microphone
#   CAM_KNOWN    — always true for matched cameras
#
# Zero 2W overrides width/height/fps to lighter values automatically.
#
# To add a new camera:
#   1. Run `lsusb` and find the idVendor and idProduct for your camera
#   2. Add a new block below following the same pattern
#   3. Update the script in the GitHub repo
# ─────────────────────────────────────────────────────────────────────────────

info "Detecting USB camera..."

# Install usbutils if lsusb not available
if ! command -v lsusb &>/dev/null; then
    sudo apt-get install -y -qq usbutils
fi

LSUSB_OUTPUT=$(lsusb)

CAM_KNOWN=false
CAM_NAME="Unknown"
CAM_WIDTH=640
CAM_HEIGHT=480
CAM_FPS=15
CAM_AUDIO=false
UNKNOWN_CAM_ID=""

# ── Camera: ARC International HD Web Camera (05a3:9331) ──────────────────────
if echo "$LSUSB_OUTPUT" | grep -qi "05a3:9331"; then
    CAM_KNOWN=true
    CAM_NAME="ARC International HD Web Camera (05a3:9331)"
    CAM_AUDIO=true
    if [[ "$IS_ZERO2W" == true ]]; then
        CAM_WIDTH=640; CAM_HEIGHT=480; CAM_FPS=15
    else
        CAM_WIDTH=1280; CAM_HEIGHT=720; CAM_FPS=30
    fi

# ── Camera: openaicam (32e6:9251) ────────────────────────────────────────────
elif echo "$LSUSB_OUTPUT" | grep -qi "32e6:9251"; then
    CAM_KNOWN=true
    CAM_NAME="openaicam (32e6:9251)"
    CAM_AUDIO=false
    if [[ "$IS_ZERO2W" == true ]]; then
        CAM_WIDTH=640; CAM_HEIGHT=480; CAM_FPS=12
    else
        CAM_WIDTH=1280; CAM_HEIGHT=720; CAM_FPS=12
    fi

# ── Unknown camera — try to identify anything UVC-looking ────────────────────
else
    # Grab the first non-hub, non-root USB device as a best guess
    UNKNOWN_CAM_ID=$(lsusb | grep -iv "hub\|root\|linux foundation" | head -1 | awk '{print $6}')
    if [[ -n "$UNKNOWN_CAM_ID" ]]; then
        CAM_NAME="Unknown camera ($UNKNOWN_CAM_ID)"
        warning "Unrecognised camera detected: $UNKNOWN_CAM_ID — using safe fallback settings"
    else
        CAM_NAME="No camera detected"
        warning "No USB camera found — using fallback settings. Plug in your camera and restart."
    fi
    # Safe fallback values that work on most UVC cameras
    CAM_WIDTH=640; CAM_HEIGHT=480; CAM_FPS=15
fi

if [[ "$CAM_KNOWN" == true ]]; then
    success "Camera recognised: $CAM_NAME"
    info "  Resolution : ${CAM_WIDTH}x${CAM_HEIGHT} @ ${CAM_FPS}fps"
    info "  Microphone : $([ "$CAM_AUDIO" == true ] && echo 'Yes' || echo 'No')"
else
    warning "Camera not in known list — fallback config applied (640x480 @ 15fps)"
fi

# ── Step 9: Create project directory and write config ────────────────────────
info "Creating project directory at $PROJECT_DIR..."
mkdir -p "$PROJECT_DIR/config"

AUDIO_DEVICE=-1
if [[ "$CAM_AUDIO" == false ]]; then
    AUDIO_DEVICE=-2   # -2 = skip audio entirely (handled in node)
fi

cat > "$PROJECT_DIR/config/camera_params.yaml" <<EOF
camera_audio_publisher:
  ros__parameters:
    device_index: 0
    width: ${CAM_WIDTH}
    height: ${CAM_HEIGHT}
    fps: ${CAM_FPS}
    frame_id: camera_optical_frame
    publish_compressed: true
    audio_device: ${AUDIO_DEVICE}
EOF
success "Camera config written (${CAM_WIDTH}x${CAM_HEIGHT} @ ${CAM_FPS}fps)"

# Write docker-compose.yml
cat > "$PROJECT_DIR/docker-compose.yml" <<EOF
services:
  fynx_edge:
    image: ${DOCKERHUB_IMAGE}
    network_mode: host
    devices:
      - /dev/video0:/dev/video0
      - /dev/snd:/dev/snd
    cap_add:
      - SYS_NICE
    group_add:
      - video
      - audio
    environment:
      - ROS_DOMAIN_ID=${ROS_DOMAIN_ID}
      - PYTHONUNBUFFERED=1
    volumes:
      - ./config:/ros2_ws/install/camera_publisher/share/camera_publisher/config:ro
    restart: unless-stopped
EOF
success "docker-compose.yml written"

# ── Step 10: Pull the Docker image ───────────────────────────────────────────
info "Pulling Docker image: $DOCKERHUB_IMAGE"
info "This may take a few minutes on first run (~600MB)..."

if docker info &>/dev/null 2>&1; then
    docker pull "$DOCKERHUB_IMAGE"
else
    sg docker -c "docker pull $DOCKERHUB_IMAGE"
fi
success "Image pulled"

# ── Step 11: Install systemd service ─────────────────────────────────────────
info "Installing systemd service..."
sudo tee /etc/systemd/system/fynx-edge.service > /dev/null <<EOF
[Unit]
Description=FYN-X Edge Camera Publisher
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${PROJECT_DIR}
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=120
User=${USER}

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable fynx-edge.service
success "systemd service installed and enabled"

# ── Step 12: Verify camera device ────────────────────────────────────────────
echo ""
info "Checking for camera devices..."
if ls /dev/video* &>/dev/null; then
    success "Camera device(s) found:"
    ls /dev/video* | while read dev; do echo "    $dev"; done
else
    warning "No /dev/video* devices found. Plug in your camera and run: cd $PROJECT_DIR && docker compose up"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        FYN-X Edge Setup Complete!        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Pi model       : ${CYAN}$PI_MODEL${NC}"
echo -e "  Camera         : ${CYAN}$CAM_NAME${NC}"
echo -e "  Resolution     : ${CYAN}${CAM_WIDTH}x${CAM_HEIGHT} @ ${CAM_FPS}fps${NC}"
echo -e "  Project folder : ${BLUE}$PROJECT_DIR${NC}"
echo -e "  Docker image   : ${BLUE}$DOCKERHUB_IMAGE${NC}"
echo -e "  ROS Domain ID  : ${BLUE}$ROS_DOMAIN_ID${NC}"
echo ""
echo -e "  ${YELLOW}To start FYN-X Edge now:${NC}"
echo -e "    cd $PROJECT_DIR && docker compose up"
echo ""
echo -e "  ${YELLOW}It will also start automatically on next boot.${NC}"
echo ""

# ── Unknown camera warning ────────────────────────────────────────────────────
if [[ "$CAM_KNOWN" == false ]]; then
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ⚠  ACTION REQUIRED: CAMERA NOT RECOGNISED                  ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    if [[ -n "$UNKNOWN_CAM_ID" ]]; then
        echo -e "  Your camera (${YELLOW}$UNKNOWN_CAM_ID${NC}) is not in the FYN-X known camera list."
    else
        echo -e "  ${YELLOW}No USB camera was detected during installation.${NC}"
    fi
    echo ""
    echo -e "  A fallback config (640x480 @ 15fps) has been applied and"
    echo -e "  ${YELLOW}may or may not work${NC} with your camera."
    echo ""
    echo -e "  To get proper support for your camera:"
    echo -e "    1. Run ${CYAN}lsusb${NC} and find your camera's Vendor:Product ID"
    echo -e "    2. Run ${CYAN}lsusb -v${NC} and note the supported resolutions and FPS"
    echo -e "    3. Open an issue or PR at:"
    echo -e "       ${BLUE}https://github.com/KongKong82/Project-FYN-X${NC}"
    echo -e "       with your camera ID and descriptor output"
    echo ""
    echo -e "  You can manually tune your config now at:"
    echo -e "    ${CYAN}$PROJECT_DIR/config/camera_params.yaml${NC}"
    echo -e "  then restart with: ${CYAN}cd $PROJECT_DIR && docker compose restart${NC}"
    echo ""
fi

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
#   curl -fsSL https://raw.githubusercontent.com/YOUR_GITHUB/FYN-X/main/FYN-X_Edge_Setup.sh | bash
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
PI_MODEL=$(cat /proc/device-tree/model 2>/dev/null || echo "Unknown")
info "Detected: $PI_MODEL"

# Flag if this is a Zero 2W (512MB RAM) so we use lighter settings
IS_ZERO2W=false
if echo "$PI_MODEL" | grep -qi "zero 2"; then
    IS_ZERO2W=true
    warning "Pi Zero 2W detected — will apply low-memory camera settings (640x480 @ 15fps)"
fi

# ── Step 1: System update ─────────────────────────────────────────────────────
info "Updating package lists..."
sudo apt-get update -qq

# ── Step 2: Install Docker ────────────────────────────────────────────────────
if command -v docker &>/dev/null; then
    success "Docker already installed ($(docker --version | cut -d' ' -f3 | tr -d ','))"
else
    info "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    success "Docker installed"
fi

# ── Step 3: Add user to required groups ──────────────────────────────────────
info "Configuring user groups..."
for group in docker video audio; do
    if groups "$USER" | grep -q "\b$group\b"; then
        success "Already in group: $group"
    else
        sudo usermod -aG "$group" "$USER"
        success "Added $USER to group: $group"
    fi
done

# ── Step 4: Enable Docker on boot ────────────────────────────────────────────
info "Enabling Docker service on boot..."
sudo systemctl enable docker
sudo systemctl start docker
success "Docker service enabled"

# ── Step 5: Enable swap ───────────────────────────────────────────────────────
SWAP_SIZE=1024
if [[ "$IS_ZERO2W" == true ]]; then
    SWAP_SIZE=512
fi

if [[ -f /etc/dphys-swapfile ]]; then
    CURRENT_SWAP=$(grep CONF_SWAPSIZE /etc/dphys-swapfile | cut -d= -f2)
    if [[ "$CURRENT_SWAP" -ge "$SWAP_SIZE" ]] 2>/dev/null; then
        success "Swap already configured (${CURRENT_SWAP}MB)"
    else
        info "Configuring ${SWAP_SIZE}MB swap..."
        sudo sed -i "s/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=${SWAP_SIZE}/" /etc/dphys-swapfile
        sudo dphys-swapfile setup
        sudo dphys-swapfile swapon
        success "Swap configured (${SWAP_SIZE}MB)"
    fi
else
    warning "dphys-swapfile not found — skipping swap configuration"
fi

# ── Step 6: Create project directory and config files ────────────────────────
info "Creating project directory at $PROJECT_DIR..."
mkdir -p "$PROJECT_DIR/config"

# Write camera_params.yaml — lighter settings for Zero 2W
if [[ "$IS_ZERO2W" == true ]]; then
    cat > "$PROJECT_DIR/config/camera_params.yaml" <<'EOF'
camera_audio_publisher:
  ros__parameters:
    device_index: 0
    width: 640
    height: 480
    fps: 15
    frame_id: camera_optical_frame
    publish_compressed: true
    audio_device: -1
EOF
else
    cat > "$PROJECT_DIR/config/camera_params.yaml" <<'EOF'
camera_audio_publisher:
  ros__parameters:
    device_index: 0
    width: 1280
    height: 720
    fps: 30
    frame_id: camera_optical_frame
    publish_compressed: true
    audio_device: -1
EOF
fi
success "Camera config written"

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

# ── Step 7: Pull the Docker image ─────────────────────────────────────────────
info "Pulling Docker image: $DOCKERHUB_IMAGE"
info "This may take a few minutes on first run (~600MB)..."

if groups "$USER" | grep -q "\bdocker\b"; then
    docker pull "$DOCKERHUB_IMAGE"
else
    # User was just added to docker group this session — use sg to activate it
    sg docker -c "docker pull $DOCKERHUB_IMAGE"
fi
success "Image pulled"

# ── Step 8: Install systemd service for auto-start on boot ───────────────────
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

# ── Step 9: Verify camera device ─────────────────────────────────────────────
echo ""
info "Checking for camera devices..."
if ls /dev/video* &>/dev/null; then
    success "Camera device(s) found:"
    ls /dev/video* | while read dev; do
        echo "    $dev"
    done
else
    warning "No /dev/video* devices found. Make sure the camera is plugged in before starting."
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        FYN-X Edge Setup Complete!        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Project folder : ${BLUE}$PROJECT_DIR${NC}"
echo -e "  Docker image   : ${BLUE}$DOCKERHUB_IMAGE${NC}"
echo -e "  ROS Domain ID  : ${BLUE}$ROS_DOMAIN_ID${NC}"
echo ""
echo -e "  ${YELLOW}To start FYN-X Edge now:${NC}"
echo -e "    cd $PROJECT_DIR && docker compose up"
echo ""
echo -e "  ${YELLOW}It will also start automatically on next boot.${NC}"
echo ""

if ! groups "$USER" | grep -q "\bdocker\b" 2>/dev/null; then
    echo -e "  ${YELLOW}NOTE: Log out and back in (or reboot) for group changes to take effect.${NC}"
    echo -e "  ${YELLOW}Or run: newgrp docker${NC}"
    echo ""
fi

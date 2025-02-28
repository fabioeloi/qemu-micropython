#!/bin/bash
# Set up development environment for STM32 QEMU and MicroPython
set -e

echo "Setting up development environment for STM32 QEMU and MicroPython..."

# Define variables
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$PROJECT_DIR/tools"
QEMU_DIR="$TOOLS_DIR/qemu"
MICROPYTHON_DIR="$TOOLS_DIR/micropython"

# Install prerequisites
echo "Installing prerequisites..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    brew update
    brew install wget git python3 cmake pkg-config glib libffi gettext pixman ninja
    brew install --cask gcc-arm-embedded
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo apt-get update
    sudo apt-get install -y build-essential libglib2.0-dev libpixman-1-dev git python3 python3-pip wget
    sudo apt-get install -y gcc-arm-none-eabi libnewlib-arm-none-eabi
fi

# Create directories
mkdir -p "$TOOLS_DIR"

# Clone and build QEMU with STM32 support
if [ ! -d "$QEMU_DIR" ]; then
    echo "Cloning QEMU..."
    git clone https://github.com/qemu/qemu "$QEMU_DIR"
    cd "$QEMU_DIR"
    echo "Configuring QEMU..."
    ./configure --target-list=arm-softmmu --enable-debug
    echo "Building QEMU..."
    make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu)
    echo "QEMU build complete."
else
    echo "QEMU directory already exists, skipping clone."
fi

# Clone and prepare MicroPython
if [ ! -d "$MICROPYTHON_DIR" ]; then
    echo "Cloning MicroPython..."
    git clone https://github.com/micropython/micropython "$MICROPYTHON_DIR"
    cd "$MICROPYTHON_DIR"
    git submodule update --init
    cd ports/stm32
    echo "Building MicroPython for STM32..."
    make BOARD=DISCOVERY_F4 MICROPY_PY_WIZNET5K=5200 MICROPY_PY_LWIP=1
    echo "MicroPython build complete."
else
    echo "MicroPython directory already exists, skipping clone."
fi

# Create symlinks to the project
mkdir -p "$PROJECT_DIR/firmware/build"
ln -sf "$MICROPYTHON_DIR/ports/stm32/build-DISCOVERY_F4/firmware.bin" "$PROJECT_DIR/firmware/build/firmware.bin"

echo "Environment setup complete."
echo "You can now use the build.sh and run_qemu.sh scripts."
# STM32 IoT Virtual Development Environment

This project provides a virtual development environment for STM32 microcontrollers running MicroPython, using QEMU for hardware emulation. It allows developers to build and test IoT applications without physical hardware.

## Features

- QEMU-based emulation of STM32F4 microcontrollers
- MicroPython firmware with STM32 support
- Sensor simulation and peripheral emulation
- IoT connectivity for device telemetry
- Development workflow from virtual testing to physical deployment

## Directory Structure

```
qemu-micropython/
├── bin/                     # Compiled binaries and firmware
├── config/                  # QEMU and environment configurations
│   ├── boards/              # Board-specific configurations
│   ├── micropython/         # MicroPython build configuration
│   └── qemu/                # QEMU machine definitions
├── docs/                    # Documentation
├── firmware/                # MicroPython firmware builds
├── scripts/                 # Utility scripts for the environment
│   ├── build.sh             # Build the firmware
│   ├── run_qemu.sh          # Start QEMU with proper parameters
│   └── flash.sh             # Flash firmware to QEMU or physical device
├── src/                     # Project source code
│   ├── lib/                 # Libraries and modules
│   └── main.py              # Main application code
├── tests/                   # Test suite
└── tools/                   # Additional development tools
```

## Getting Started

### Prerequisites

- Git
- Python 3.x
- QEMU (version 7.0+ recommended)
- ARM GCC Toolchain
- ST-Link utilities (for physical device deployment)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/qemu-micropython.git
   cd qemu-micropython
   ```

2. Run the environment setup script:
   ```bash
   chmod +x scripts/setup_env.sh
   ./scripts/setup_env.sh
   ```

   This will:
   - Install required dependencies
   - Clone and build QEMU with STM32 support
   - Clone and prepare MicroPython for STM32

### Building the Firmware

To build the MicroPython firmware with your application:

```bash
./scripts/build.sh
```

By default, this builds for the STM32F4-Discovery board. You can specify a different board:

```bash
./scripts/build.sh NUCLEO_F446RE
```

### Running in QEMU

To run your application in the QEMU emulator:

```bash
./scripts/run_qemu.sh
```

This will start QEMU with the appropriate configuration for your target board and load your firmware.

### Deploying to Physical Hardware

When you're ready to deploy to a physical STM32 device:

```bash
./scripts/flash.sh /dev/ttyACM0
```

Replace `/dev/ttyACM0` with the appropriate device path for your board.

## Development Workflow

1. Write your MicroPython application in `src/main.py`
2. Add supporting modules in `src/lib/`
3. Build the firmware with `./scripts/build.sh`
4. Test in QEMU with `./scripts/run_qemu.sh`
5. Debug and refine your code
6. Deploy to physical hardware with `./scripts/flash.sh`

## Sample Applications

The repository includes a sample IoT application that demonstrates:

- GPIO control (LED blinking)
- I2C sensor reading (temperature, humidity)
- MQTT-based IoT connectivity

## Debugging

When running in QEMU, you can attach GDB for debugging:

```bash
arm-none-eabi-gdb firmware/build/firmware.elf
(gdb) target remote localhost:1234
(gdb) continue
```

## Limitations

- Not all STM32 peripherals are fully emulated in QEMU
- Timing may differ between emulated and physical environments
- Some hardware-specific features may require adjustment for accurate simulation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- MicroPython project: https://micropython.org/
- QEMU project: https://www.qemu.org/
- STM32 community: https://www.st.com/
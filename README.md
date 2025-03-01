# STM32 IoT Virtual Development Environment

[![GitHub Stars](https://img.shields.io/github/stars/fabioeloi/qemu-micropython?style=flat-square)](https://github.com/fabioeloi/qemu-micropython/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/fabioeloi/qemu-micropython?style=flat-square)](https://github.com/fabioeloi/qemu-micropython/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/fabioeloi/qemu-micropython?style=flat-square)](https://github.com/fabioeloi/qemu-micropython/issues)
[![GitHub License](https://img.shields.io/github/license/fabioeloi/qemu-micropython?style=flat-square)](https://github.com/fabioeloi/qemu-micropython/blob/main/LICENSE)
[![CI Status](https://img.shields.io/github/actions/workflow/status/fabioeloi/qemu-micropython/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/fabioeloi/qemu-micropython/actions)

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
- ARM GCC Toolchain (arm-none-eabi-gcc)
- Make

Note: QEMU will be automatically downloaded and built by the setup script.

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
   - Set up board configurations

### Building the Firmware

To build the MicroPython firmware with your application:

```bash
./scripts/build.sh
```

The script is currently configured to build for the STM32F4DISC board. The build process creates firmware files (which may include firmware0.bin and firmware1.bin for split firmware boards).

### Running in QEMU

To run your application in the QEMU emulator:

```bash
./scripts/run_qemu.sh
```

This will:
- Check for firmware files in the build directory
- Handle split firmware files if necessary (combining them for QEMU)
- Start QEMU with the appropriate configuration for the target board
- Load your firmware and start execution

Note: We're currently using the olimex-stm32-h405 machine type in QEMU as it has a Cortex-M4 processor similar to the STM32F4 Discovery board.

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

## Troubleshooting

### Common Issues

1. **QEMU machine type errors**: If you encounter errors about unsupported machine types, check the `config/qemu/stm32f4.cfg` file. You may need to modify it to use a different machine type supported by your QEMU build.

2. **Firmware not found**: The build process generates different firmware files depending on the board. For STM32F4DISC, it creates split firmware files (firmware0.bin and firmware1.bin). The run script automatically handles this.

3. **Build failures**: Ensure you have the ARM toolchain (arm-none-eabi-gcc) installed and in your PATH.

## Limitations

- Not all STM32 peripherals are fully emulated in QEMU
- We're using olimex-stm32-h405 as a substitute for STM32F4-Discovery in QEMU
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
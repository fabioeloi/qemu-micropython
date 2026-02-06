# STM32F4DISC_QEMU Board Configuration

This is a custom board configuration for running MicroPython on STM32F4 Discovery in QEMU.

## Purpose

This board configuration is optimized for QEMU emulation, with features that are not well-supported in QEMU disabled to ensure stable operation.

## Board Features

### Enabled Features
- **UART2**: Used for REPL console (TX: PA2, RX: PA3)
- **USB**: USB FS support for device mode
- **GPIO**: Basic GPIO support
- **LED**: Green LED on PD12

### Disabled Features (not well-supported in QEMU)
- RTC (Real-Time Clock)
- ADC/DAC (Analog peripherals)
- SPI
- I2C
- CAN
- SD Card
- Timers
- Internal flash storage

## Files

- **mpconfigboard.h**: Board-specific C configuration
- **mpconfigboard.mk**: Build configuration and compiler flags
- **stm32f4xx_hal_conf.h**: STM32 HAL configuration
- **pins.csv**: Pin definitions for the board
- **manifest.py**: Python module freeze configuration

## Usage

This board configuration is automatically copied to the MicroPython build tree during the CI build process:

```bash
cp -r config/boards/STM32F4DISC_QEMU/* tools/micropython/ports/stm32/boards/STM32F4DISC_QEMU/
```

Then the firmware can be built with:

```bash
./scripts/build.sh STM32F4DISC_QEMU
```

## QEMU Compatibility

This configuration is designed to work with QEMU's `olimex-stm32-h405` machine type, which is the closest match to the STM32F4 Discovery board available in QEMU.

## References

- [MicroPython STM32 Port](https://github.com/micropython/micropython/tree/master/ports/stm32)
- [QEMU STM32 Support](https://www.qemu.org/docs/master/system/arm/stm32.html)

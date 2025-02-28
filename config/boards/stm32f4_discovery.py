# STM32F4 Discovery Board Configuration for MicroPython

# MCU specifications
MCU = "STM32F407VG"
MCUDEF = "STM32F407xx"
CPU = "cortex-m4"
FPU = "fpv4-sp-d16"
FLOAT_ABI = "hard"

# Board configuration
BOARD = "DISCOVERY_F4"
CROSS_COMPILE = "arm-none-eabi-"

# Memory layout
LD_FILES = ["stm32f407vg.ld", "common_basic.ld"]
TEXT0_ADDR = 0x08000000
TEXT1_ADDR = 0x08020000
FLASH_SIZE = 1024  # KB
RAM_SIZE = 192  # KB

# Enable modules
MICROPY_PY_USSL = 1
MICROPY_SSL_MBEDTLS = 1
MICROPY_PY_BTREE = 1
MICROPY_PY_THREAD = 1

# Network configuration
MICROPY_PY_LWIP = 1
MICROPY_PY_NETWORK = 1
MICROPY_PY_NETWORK_WIZNET5K = 5200

# Enable specific peripherals
MICROPY_HW_ENABLE_RTC = 1
MICROPY_HW_ENABLE_SPI = 1
MICROPY_HW_ENABLE_I2C = 1
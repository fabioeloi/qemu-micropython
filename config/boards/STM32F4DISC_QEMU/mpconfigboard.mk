MCU_SERIES = f4
CMSIS_MCU = STM32F407xx
AF_FILE = boards/stm32f407_af.csv
LD_FILES = boards/stm32f407.ld boards/common_basic.ld

# MicroPython settings
MICROPY_PY_LWIP = 0
MICROPY_PY_USSL = 0
MICROPY_SSL_MBEDTLS = 0
MICROPY_PY_BTREE = 0
MICROPY_PY_THREAD = 0

# Disable unnecessary features for QEMU
MICROPY_PY_NETWORK = 0
MICROPY_HW_ENABLE_SDCARD = 0

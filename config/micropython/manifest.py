# MicroPython configuration manifest
# This file defines which modules should be included in the firmware build

# Include our custom libraries from src/lib
freeze_namespace(ns=None, path="src/lib", prefix="")  # noqa: F821

# Include the standard STM32 port modules
include("$(MPY_DIR)/ports/stm32/manifest.py")  # noqa: F821

# Include sensor drivers
include("$(MPY_DIR)/drivers/sensors/manifest.py")  # noqa: F821

# Add additional specific modules as needed
freeze("$(PORT_DIR)/modules")  # noqa: F821
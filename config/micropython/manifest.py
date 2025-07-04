# MicroPython configuration manifest
# This file defines which modules should be included in the firmware build

# Include our custom libraries from src/lib
freeze_namespace(ns=None, path="src/lib", prefix="")

# Include the microCoAPy library (as a package)
freeze("src/lib/microcoapy/")

# Include the standard STM32 port modules
include("$(MPY_DIR)/ports/stm32/manifest.py")

# Include sensor drivers
include("$(MPY_DIR)/drivers/sensors/manifest.py")

# Add additional specific modules as needed
freeze("$(PORT_DIR)/modules")
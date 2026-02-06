# MicroPython manifest for STM32F4DISC_QEMU board
# This file defines which modules should be frozen into the firmware

# Include our custom libraries from the project src directory
freeze_namespace(ns=None, path="$(PROJECT_DIR)/src/lib", prefix="")

# Include main.py from src directory
freeze("$(PROJECT_DIR)/src", ("main.py",))

# Include the standard STM32 port modules
include("$(PORT_DIR)/boards/manifest.py")

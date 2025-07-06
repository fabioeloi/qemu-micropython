# Project Documentation Overview

This directory contains detailed documentation for various aspects of the `qemu-micropython` project.

## Key Documents

Below is a list of primary documentation pages to help you get started and understand specific features:

**Getting Started & Setup:**
*   **[../README.md](../README.md)**: The main project README with overview, setup, quick start, and links to all major documents.
*   **[IDE Integration](IDE_INTEGRATION.md)**: Notes on integrating with IDEs like VSCode.

**Core Functionality & Emulation:**
*   **[QEMU for STM32F4 Development and Testing](QEMU_GUIDE_STM32F4.md)**: Comprehensive guide covering QEMU setup, machine choices, core features utilized (serial, semihosting, GDB stub), known limitations, and best practices. This consolidates information from previous QEMU notes and exploration reports.
*   **[Semihosting with `usemihosting`](SEMIHOSTING.md)**: Guide to using the `usemihosting` MicroPython module for host interaction.

**Development & Testing:**
*   **[GDB Debugging Guide](GDB_DEBUGGING.md)**: Comprehensive guide to debugging MicroPython in QEMU using GDB and the project's custom helper scripts.
*   **Unit Testing:**
    *   **[Host-Based C Unit Testing](UNIT_TESTING_C_HOST.md)**: How to write and run C unit tests on your host machine.
    *   **[On-Target C Unit Testing in QEMU](UNIT_TESTING_C_QEMU.md)**: How to run C unit tests in the emulated QEMU environment.
    *   **[Python Unit Testing](UNIT_TESTING_PYTHON.md)**: Guide for testing Python scripts and tools.
*   **[Continuous Integration (CI)](CONTINUOUS_INTEGRATION.md)**: Overview of the project's CI setup using GitHub Actions.

**Hardware & Drivers (Examples/Guides):**
*   **[UART Integration Guide](UART_INTEGRATION_GUIDE.md)**: Information on UART usage and integration.
*   **[UART Driver Testing](UART_DRIVER_TESTING.md)**: Notes on testing UART drivers.

**Project Management & Planning:**
*   **[../ROADMAP_STATUS.md](../ROADMAP_STATUS.md)**: Current project roadmap and status of milestones.
*   **[Project Management Notes](project_management.md)**: General notes on project tracking.
*   **[Release Notes Directory](release_notes/)**: Directory containing notes for each release.

**Simulations (Examples/Guides):**
*   **[CoAP Simulation](COAP_SIMULATION.md)**
*   **[MQTT Simulation](MQTT_SIMULATION.md)**

**Historical / To Be Reviewed:**
*   **[NEXT_STEPS.md](NEXT_STEPS.md)**: Historical planning document, largely superseded by GitHub Issues and current roadmap. Consider for archival.
*   The content from `qemu_stm32f4_machine_exploration.md` and `QEMU-STM32-NOTES.md` has been integrated into the new `QEMU_GUIDE_STM32F4.md`. These older files can be archived or removed.


Please refer to the main project [../README.md](../README.md) for the primary entry point and overall structure.

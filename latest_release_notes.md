# QEMU-MicroPython v2025.03.02.10 (v1.1.0-beta.1)

## Release Information
- **Date:** 2025-03-02
- **Milestone:** v1.1.0 - Debugging and QEMU Integration

## Summary
This release continues our work on improving QEMU integration and debugging capabilities for STM32F4 microcontrollers with MicroPython. It builds upon the firmware handling improvements from v2025.03.01.8 and addresses several reliability issues.

## Features and Enhancements

### Enhanced Error Reporting in QEMU
- **Description:** Improved error handling and debugging output when running MicroPython in QEMU
- **Roadmap Item:** GDB integration for step-by-step debugging
- **Implementation Status:** Partial (25%)
- **Related Issues:** #1, #5

### Improved Script Reliability
- **Description:** Fixed edge cases in run scripts to better handle various firmware configurations
- **Roadmap Item:** Better semihosting integration
- **Implementation Status:** In Progress (50%)
- **Related Issues:** #3

## Bug Fixes
- Fixed issue with QEMU path detection on some Linux distributions
- Resolved firmware loading error when firmware size exceeded 128KB
- Added proper error handling for missing firmware files

## Roadmap Progress
### v1.1.0 Progress
Our progress on the v1.1.0 milestone continues with improvements to the debugging experience and QEMU integration.

| Roadmap Item | Status Before | Status After | Progress |
|--------------|---------------|--------------|----------|
| GDB integration | In Progress | In Progress | 25% |
| Custom UART driver | Not Started | Not Started | 0% |
| Semihosting integration | In Progress | In Progress | 50% |
| Alternative QEMU machine types | In Progress | In Progress | 40% |
| Unit testing framework | Not Started | Not Started | 0% |

Overall milestone completion: 23%

## Known Issues
- GDB debugging may sometimes disconnect when accessing peripheral registers
- Large MicroPython scripts may cause memory allocation issues in QEMU
- Network simulation is not yet implemented

## Installation and Upgrade
Download the latest release from the GitHub releases page. To upgrade from a previous version:

1. Backup your `src` directory
2. Pull the latest changes or download and extract the new release
3. Run `./scripts/setup_env.sh` to ensure all dependencies are updated

## Contributors
- @fabioeloi
- @github-actions

---

**Full Changelog**: https://github.com/fabioeloi/qemu-micropython/compare/v2025.03.01.9...v2025.03.02.10 
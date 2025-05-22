# Version Mapping Guide

This document provides mapping between date-based release versions and semantic versioning aligned with our project roadmap.

## Version Mapping

| Date-based Version | Semantic Version | Notes |
|-------------------|------------------|-------|
| v2025.02.28.5-6   | Pre-v1.0.0       | Initial Setup: Environment setup and testing |
| v1.0.0            | v1.0.0           | Initial Release: Foundation release |
| v2025.03.01.7-9   | v1.1.0-alpha     | v1.1.0: Debugging and QEMU integration (early work) |
| v2025.03.02.10    | v1.1.0-beta.1    | v1.1.0: Debugging and QEMU integration (continued) |
| v2025.03.03.11    | v1.1.0-beta.2    | v1.1.0: Custom UART driver implementation |
| v2025.03.04.12    | v1.1.0-beta.3    | v1.1.0: Enhanced UART testing capabilities |
| v2025.03.04.13    | v1.1.0-beta.4    | v1.1.0: GDB integration and Python debugging |
| v2025.03.04.17    | v1.1.0-beta.5    | v1.1.0: Enhanced exception handling documentation and testing |
| v2025.03.05.1     | v1.1.0           | Final release of the Debugging and QEMU Integration milestone. |
| TBD               | v1.2.0           | v1.2.0: IoT and Simulation Capabilities |
| TBD               | v1.3.0           | v1.3.0: Development Infrastructure |

## Versioning Policy

Going forward, we will use the following versioning approach:

1. **Date-based versions** (vYYYY.MM.DD.build) will continue to be used for automated builds and incremental releases
2. **Semantic versions** (v1.x.y) will be used for major milestone completions
3. When a date-based version completes a significant portion of a roadmap milestone, it will also receive a semantic version tag

## Using This Guide

Developers and users should reference this guide to understand how incremental releases relate to the project roadmap. Each semantic version represents a significant milestone in the project development.
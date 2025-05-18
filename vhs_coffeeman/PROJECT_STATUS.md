# VHS Coffeeman Project Status

## Project Overview

VHS Coffeeman is an interactive art installation that dispenses cocktails through a modified VHS player. When a participant inserts a VHS tape with an embedded RFID tag, the system plays curated film clips while mixing a drink through a series of peristaltic pumps.

## Migration Status

We are migrating the project from an RP2040 microcontroller to a Raspberry Pi platform. This document tracks the current state of the port and outlines what remains to be completed.

### Current Architecture

**Original System (RP2040):**
- VCR housing contains an RFID reader, RP2040 microcontroller, and ATmega328 running GRBL
- VHS tapes have RFID tags that trigger hardcoded drink recipes
- System controls up to 10 peristaltic pumps driven by stepper motors
- The RP2040 automatically controls the VCR's play and eject buttons through optoisolators

**New System (Raspberry Pi):**
- Raspberry Pi handles all functionality (GPIO, RFID reading, recipe storage, video playback)
- Communicates directly with GRBL controller for stepper motor control
- Stores drink recipes in JSON format for easy editing
- Plays curated film clips that match each VHS tape's theme
- Controls the VCR's physical buttons via GPIO

## Completed Tasks

- [x] **Project Structure**
  - Set up standard Python project directory structure
  - Created package organization (core, hardware, utils, recipes, media, maintenance)
  - Created README and dependency management files

- [x] **Development Environment**
  - Set up Python virtual environment
  - Installed required dependencies
  - Created activation script for easy environment setup

- [x] **Core Modules**
  - Ported configuration settings (pins, constants, states, commands)
  - Created logging utility for consistent logging across modules
  - Started porting state machine logic

- [x] **Hardware Interfaces**
  - Ported GRBL interface for stepper motor control
  - Ported pump controller for managing multiple peristaltic pumps
  - Ported VCR controller for play/eject button control
  - Ported RFID reader interface

- [x] **Test Scripts**
  - Created GPIO test script for testing VCR buttons and pump control pins
  - Created RFID test script for reading/writing tags
  - Created GRBL test script for testing communication and movement
  - Created pump test script for testing pump control functions

## In Progress

- [ ] **Recipe Management**
  - Created recipe data structure and file-based storage
  - Need to complete integration with main application

- [ ] **Media Playback**
  - Created video player module
  - Need to test with actual media files

- [ ] **State Machine**
  - Basic implementation started
  - Need to complete all state transitions and handlers

## Remaining Tasks

- [ ] **Main Application**
  - Create main application entry point
  - Implement event loop
  - Integrate all components

- [ ] **Maintenance Utilities**
  - Create command-line maintenance tools
  - Implement pump priming, cleaning, and manual control

- [ ] **Full Integration**
  - Connect RFID reading to recipe lookup
  - Connect recipe execution to pump control
  - Synchronize video playback with drink dispensing

- [ ] **Testing and Calibration**
  - Test all components together
  - Calibrate pump dispensing accuracy
  - Tune timing for synchronization

- [ ] **Documentation**
  - Create installation instructions
  - Create maintenance manual
  - Create operation guide

## Design Improvements

The new Raspberry Pi implementation offers several improvements over the original RP2040 design:

1. **Modular Architecture**: Clear separation of concerns with well-defined interfaces between components
2. **Improved Error Handling**: Comprehensive logging and error recovery
3. **Maintainability**: Standard Python project structure with proper dependency management
4. **Extended Features**: Media playback capabilities for a more immersive experience
5. **Flexibility**: Dynamic recipe loading and easier configuration

## Testing Approach

We're following a component-first testing approach:

1. Test individual hardware interfaces using dedicated test scripts
2. Test integration between related components (e.g., GRBL + pumps)
3. Test the full system with all components working together

## Next Steps

1. Validate hardware interfaces with actual hardware
2. Complete the main application entry point
3. Implement the event loop and state transitions
4. Test full integration with a complete drink dispensing cycle

## Timeline

- **Phase 1 (Current)**: Set up project structure and port core modules
- **Phase 2**: Complete individual component implementation and testing
- **Phase 3**: Implement main application and integration
- **Phase 4**: Testing, calibration, and refinement
- **Phase 5**: Documentation and final deployment
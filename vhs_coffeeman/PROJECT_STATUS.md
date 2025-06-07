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
  - Need to implement full drink dispensing workflow

- [ ] **Cup Sensor Integration**
  - VCNL4010 proximity sensor module created
  - Hardware testing completed
  - Need integration with main state machine

## Testing Progress

- [x] **GRBL Interface Testing**
  - GRBL controller communication verified on /dev/ttyUSB0
  - GRBL v1.1h responding correctly to commands
  - Connection and basic command functionality confirmed
  - Motor movement commands tested and working

- [x] **GPIO Testing**
  - VCR button control pins tested and working
  - Pump control pins verified and working

- [x] **RFID Testing**
  - RFID reader initialization and communication verified
  - Tag reading functionality tested and working
  - Fixed initialization issues with SimpleMFRC522

- [x] **Pump Control Testing**
  - Individual pump control tested and working
  - Motor control integration verified
  - Pump sequencing functionality confirmed

- [x] **VCR Control Testing**
  - Play and eject button control tested and working
  - GPIO control for VCR buttons verified

- [x] **Cup Sensor Testing**
  - VCNL4010 proximity sensor integrated and tested
  - Cup detection at 15-30mm range working
  - Calibration functionality implemented

## Remaining Tasks

- [ ] **LED Control System**
  - Design and implement LED strip control for visual feedback
  - Add LED configuration to hardware setup
  - Create test scripts for LED functionality

- [ ] **Main Application**
  - Create main application entry point
  - Implement event loop
  - Integrate all components

- [ ] **State Machine Implementation**
  - Complete state machine with full drink dispensing workflow:
    1. Wait for RFID tag detection
    2. Match tag ID with drink recipe
    3. Check cup sensor for safe pour condition
    4. Load and validate drink recipe
    5. Send movement commands to GRBL controller
    6. Monitor pour completion
    7. Trigger VCR eject button
    8. Return to waiting state

- [ ] **Dry Pour Testing**
  - Test complete drink dispensing sequence without liquids
  - Validate timing and coordination between components
  - Test error handling and recovery scenarios

- [ ] **Maintenance Utilities**
  - Create command-line maintenance tools
  - Implement pump priming, cleaning, and manual control

- [ ] **Full Integration**
  - Connect RFID reading to recipe lookup
  - Connect recipe execution to pump control
  - Synchronize video playback with drink dispensing
  - Integrate cup sensor safety checks

- [ ] **Testing and Calibration**
  - Test all components together
  - Calibrate pump dispensing accuracy
  - Tune timing for synchronization
  - Test complete user workflow

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

1. **Implement LED Control System**
   - Add LED strip control for visual feedback during operation
   - Create configuration and test scripts

2. **Complete State Machine Implementation**
   - Implement the full drink dispensing workflow
   - Add proper error handling and state transitions
   - Integrate all tested hardware components

3. **Dry Pour Testing**
   - Test complete sequence: RFID → recipe lookup → cup detection → recipe execution → VCR eject → reset
   - Validate timing and component coordination
   - Test error scenarios and recovery

4. **Integration and Refinement**
   - Connect all components into unified system
   - Calibrate dispensing accuracy
   - Optimize user experience flow

## Timeline

- **Phase 1 (Current)**: Set up project structure and port core modules
- **Phase 2**: Complete individual component implementation and testing
- **Phase 3**: Implement main application and integration
- **Phase 4**: Testing, calibration, and refinement
- **Phase 5**: Documentation and final deployment
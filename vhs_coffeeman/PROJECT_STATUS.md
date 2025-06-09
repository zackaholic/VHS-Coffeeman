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
  - Implemented complete event-driven state machine with hardware abstraction
  - Created hardware manager for unified component control

- [x] **Hardware Interfaces**
  - Ported GRBL interface for stepper motor control
  - Ported pump controller for managing multiple peristaltic pumps
  - Ported VCR controller for play/eject button control
  - Ported RFID reader interface
  - Integrated cup sensor with safety logic

- [x] **Test Scripts**
  - Created GPIO test script for testing VCR buttons and pump control pins
  - Created RFID test script for reading/writing tags
  - Created GRBL test script for testing communication and movement
  - Created pump test script for testing pump control functions

- [x] **State Machine Implementation**
  - Complete event-driven state machine with full drink dispensing workflow
  - Implemented states: IDLE → RECIPE_LOADED → WAITING_FOR_CUP → POURING → POURING_COMPLETE → DRINK_READY
  - Integrated cup sensor safety logic (emergency stop on cup removal during pour)
  - Coordinated video playback timing with drink dispensing
  - Added LED placeholder functions for status indication
  - Hardware abstraction layer for clean component integration

- [x] **Main Application**
  - Created main application entry point with command-line options
  - Implemented graceful shutdown handling and signal management
  - Added debug mode and system requirements checking
  - Comprehensive logging setup

- [x] **Recipe Management**
  - Implemented three-file JSON recipe system for human-friendly management
  - Created tapes.json (RFID → movie), ingredients.json (ingredient → pump), recipes.json (movie → recipe)
  - Added recipe validation and translation pipeline
  - Backward compatibility with existing hardware interfaces
  - Sample recipes created for testing (Taxi Driver, Blade Runner, The Big Lebowski, Casablanca)

- [x] **Media Playback**
  - Complete video player module with folder-based random clip selection
  - Support for multiple video formats and players (mpv/VLC/omxplayer with automatic fallback)
  - Video playback starts when pouring begins for dramatic timing
  - Video stops on tape eject to maintain VHS illusion
  - Independent video operation (failures don't stop drink making)
  - End-to-end RFID tag to video integration working perfectly

- [x] **Cup Sensor Integration**
  - VCNL4010 proximity sensor module created
  - Hardware testing completed
  - Full integration with main state machine and safety logic

- [x] **RFID Tape Registration System**
  - Complete interactive tape registration tool (scripts/register_tape.py)
  - Automatic VCR eject after successful registration with 3-second delay
  - Movie title sanitization and duplicate detection
  - Command-line options: --list, --no-eject, --help
  - Clean user interface without console logging spam
  - GPIO mode conflict resolution between RFID reader and VCR controller

## Recently Completed (Current Session)

- [x] **🎯 DRY RUN TESTING COMPLETE**
  - Full workflow tested and validated through multiple cycles
  - RFID detection → recipe loading → cup placement → dispensing → tape eject → reset
  - All state transitions working correctly
  - Pump dispensing calibrated and operational

- [x] **Hardware Optimizations**
  - Cup sensor stability improvements (VCNL4010 timeout fixes)
  - Conditional polling system (only monitor when needed)
  - Error tolerance (10 consecutive failures before error)
  - Graceful degradation with mock sensor fallback
  - I2C communication improvements

- [x] **System Debugging and Fixes**
  - Fixed RFID reader method name inconsistency
  - Fixed missing VCR eject/play methods
  - Fixed PumpController disable_all method naming
  - GRBL timeout optimization for pump operations
  - Double logging issue resolution

## In Progress

- [ ] **LED Control System**
  - Placeholder functions created in hardware manager
  - Need to implement actual LED hardware control
  - LED states: Attractor pattern → Red (no cup) → Green (cup ready) → White (pouring/ready) → Attractor

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
  - Added missing execute_recipe() method for complete recipe dispensing

- [x] **VCR Control Testing**
  - Play and eject button control tested and working
  - GPIO control for VCR buttons verified

- [x] **Cup Sensor Testing**
  - VCNL4010 proximity sensor integrated and tested
  - Cup detection at 15-30mm range working
  - Calibration functionality implemented

## Remaining Tasks

- [ ] **LED Control System Implementation**
  - Implement actual LED hardware control (placeholder functions exist)
  - Add LED configuration to hardware setup
  - Create test scripts for LED functionality

- [ ] **System Polish and Optimization**
  - Fine-tune video and hardware coordination timing
  - Optimize performance for smooth user experience
  - Test edge cases and error recovery scenarios

- [ ] **Maintenance Utilities**
  - Create command-line maintenance tools
  - Implement pump priming, cleaning, and manual control

- [ ] **System Integration Testing**
  - Test all components together in complete workflow
  - Calibrate pump dispensing accuracy
  - Tune timing for synchronization
  - Test complete user experience flow

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

1. **Define Recipe Format**
   - Finalize recipe JSON schema and data structure
   - Remove fallback recipe system and implement real recipe files
   - Create recipe files for VHS tape collection

2. **Implement LED Control System**
   - Add actual LED hardware control (placeholder functions exist)
   - Create LED configuration and test scripts
   - Implement status indication patterns

3. **System Integration Testing**
   - Test complete workflow with all components integrated
   - Perform dry pour testing without liquids
   - Validate timing, coordination, and error handling

4. **Calibration and Refinement**
   - Calibrate pump dispensing accuracy
   - Tune timing for optimal user experience
   - Test and refine error recovery scenarios

## Timeline

- **Phase 1 (Completed)**: Set up project structure and port core modules
- **Phase 2 (Completed)**: Complete individual component implementation and testing  
- **Phase 3 (Completed)**: Implement main application and integration
- **Phase 4 (Completed)**: Recipe system and tape registration tools
- **Phase 5 (Current)**: System integration testing and dry runs
- **Phase 6**: Video playback integration and final calibration
- **Phase 7**: Documentation and deployment

## Major Milestone: Production-Ready Recipe System

The VHS Coffeeman system now has a complete, production-ready implementation:

- ✅ **Full state machine** with event-driven workflow
- ✅ **Hardware abstraction** for all components  
- ✅ **Three-file recipe system** with human-friendly management
- ✅ **RFID tape registration tool** with automatic VCR eject
- ✅ **Media coordination** with video playback framework
- ✅ **Safety systems** including cup sensor monitoring
- ✅ **GPIO conflict resolution** between RFID and VCR hardware
- ✅ **Complete recipe pipeline** from tag detection to pump control

## ✅ Major Milestone Complete: Dry Run Testing SUCCESS

**COMPLETED**: Comprehensive dry run testing has been **successfully completed**! The system now performs the complete workflow flawlessly:

- ✅ **Complete workflow testing**: RFID detection → recipe loading → cup detection → pump sequencing → VCR eject → cycle reset
- ✅ **Timing validation**: All components coordinate properly with optimized timeouts
- ✅ **Error handling**: Robust safety systems with graceful degradation
- ✅ **User experience**: Smooth interaction flow tested through multiple cycles
- ✅ **Hardware optimization**: Cup sensor stability improvements and conditional polling
- ✅ **Pump calibration**: Working dispensing with adjustable oz/mm ratios

## ✅ Major Milestone Complete: Video Playback Integration SUCCESS

**COMPLETED**: Video playback integration has been **successfully implemented and tested**! The system now provides a complete VHS experience:

- ✅ **Folder-based random clip selection**: Multiple clips per movie with random selection for varied experiences
- ✅ **Complete RFID-to-video pipeline**: Tag ID → Movie name → Random clip selection working flawlessly
- ✅ **Multi-player support**: Automatic fallback mpv → VLC → omxplayer with optimal player selection
- ✅ **VHS illusion maintained**: Video stops on tape eject for authentic VHS experience
- ✅ **Error handling**: Graceful fallbacks with default video support
- ✅ **End-to-end integration**: Video timing perfectly coordinated with drink dispensing workflow

## 🎯 Next Major Milestone: System Refinement and LED Control

With both the core dispensing system and video playback proven, the focus now shifts to **final system polish**:

- **LED Control Implementation**: Complete the visual feedback system with proper LED patterns
- **System calibration**: Fine-tune pump timing and user experience
- **Performance optimization**: Optimize video and hardware coordination
- **Production preparation**: Final testing and deployment readiness
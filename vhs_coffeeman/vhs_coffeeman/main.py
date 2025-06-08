#!/usr/bin/env python3
"""
main.py - Main Application Entry Point for VHS Coffeeman

This is the main entry point for the VHS Coffeeman system running on Raspberry Pi.
It initializes all components and starts the state machine for interactive operation.

The VHS Coffeeman is an interactive art installation that dispenses cocktails through
a modified VHS player. When a participant inserts a VHS tape with an embedded RFID tag,
the system plays curated film clips while mixing a drink through peristaltic pumps.

Usage:
    python3 main.py [options]
    
Options:
    --debug         Enable debug logging
    --test-mode     Run in test mode (no hardware initialization)
    --config FILE   Use custom configuration file

The application coordinates:
    - RFID tag detection for recipe triggering
    - Cup sensor monitoring for safety
    - Video playback synchronized with drink dispensing
    - Stepper motor control via GRBL for pump operations
    - VCR button control for tape ejection
    - LED status indication throughout the process

Signal handling is implemented for graceful shutdown on SIGINT/SIGTERM.
"""

import sys
import signal
import argparse
import time
from typing import Optional
from utils.logger import get_logger, setup_logging
from core.hardware_manager import HardwareManager
from core.state_machine import StateMachine

# Global references for signal handling
hardware_manager: Optional[HardwareManager] = None
state_machine: Optional[StateMachine] = None
logger = get_logger(__name__)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    signal_name = signal.Signals(signum).name
    logger.info(f"Received {signal_name} signal, shutting down gracefully...")
    
    # Cleanup state machine
    if state_machine:
        try:
            state_machine.cleanup()
        except Exception as e:
            logger.error(f"Error during state machine cleanup: {e}")
    
    # Cleanup hardware
    if hardware_manager:
        try:
            hardware_manager.cleanup()
        except Exception as e:
            logger.error(f"Error during hardware cleanup: {e}")
    
    logger.info("Shutdown complete")
    sys.exit(0)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="VHS Coffeeman - Interactive Cocktail Dispensing System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 main.py                    # Normal operation
    python3 main.py --debug            # Enable debug logging
    python3 main.py --test-mode        # Test mode (no hardware)
    
For more information, see the project documentation.
        """
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging for detailed operation information'
    )
    
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='Run in test mode without hardware initialization (for development)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        metavar='FILE',
        help='Path to custom configuration file (not yet implemented)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        metavar='FILE',
        help='Path to log file (default: logs to console and /var/log/vhs_coffeeman.log)'
    )
    
    return parser.parse_args()


def check_system_requirements():
    """Check that system requirements are met."""
    import os
    import platform
    
    logger.info("Checking system requirements...")
    
    # Check if running on Linux (Raspberry Pi)
    if platform.system() != 'Linux':
        logger.warning(f"Running on {platform.system()}, not Linux - some features may not work")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 7):
        logger.error(f"Python 3.7+ required, running {python_version.major}.{python_version.minor}")
        return False
    
    logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if running as root (needed for GPIO access)
    if os.geteuid() != 0:
        logger.warning("Not running as root - GPIO access may fail")
        logger.info("Consider running with 'sudo python3 main.py' for full hardware access")
    
    return True


def initialize_hardware(test_mode: bool = False) -> Optional[HardwareManager]:
    """
    Initialize the hardware manager.
    
    Args:
        test_mode: If True, skip actual hardware initialization
        
    Returns:
        HardwareManager instance or None if initialization failed
    """
    try:
        if test_mode:
            logger.info("Initializing in TEST MODE - no hardware will be accessed")
            # TODO: Implement mock hardware manager for testing
            logger.warning("Test mode not fully implemented - using real hardware manager")
        
        logger.info("Initializing hardware manager...")
        hardware = HardwareManager()
        
        logger.info("Hardware manager initialized successfully")
        return hardware
        
    except Exception as e:
        logger.error(f"Failed to initialize hardware manager: {e}")
        logger.error("Make sure you're running with appropriate permissions and hardware is connected")
        return None


def initialize_state_machine(hardware: HardwareManager, debug: bool = False) -> Optional[StateMachine]:
    """
    Initialize the state machine.
    
    Args:
        hardware: HardwareManager instance
        debug: Enable debug logging
        
    Returns:
        StateMachine instance or None if initialization failed
    """
    try:
        logger.info("Initializing state machine...")
        state_machine = StateMachine(hardware, debug=debug)
        
        logger.info("State machine initialized successfully")
        return state_machine
        
    except Exception as e:
        logger.error(f"Failed to initialize state machine: {e}")
        return None


def main():
    """Main application entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(debug=args.debug, log_file=args.log_file)
    
    logger.info("=" * 60)
    logger.info("VHS Coffeeman - Interactive Cocktail Dispensing System")
    logger.info("=" * 60)
    logger.info("Starting application...")
    
    # Check system requirements
    if not check_system_requirements():
        logger.error("System requirements not met, exiting")
        sys.exit(1)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    global hardware_manager, state_machine
    
    try:
        # Initialize hardware manager
        hardware_manager = initialize_hardware(test_mode=args.test_mode)
        if not hardware_manager:
            logger.error("Hardware initialization failed, exiting")
            sys.exit(1)
        
        # Initialize state machine
        state_machine = initialize_state_machine(hardware_manager, debug=args.debug)
        if not state_machine:
            logger.error("State machine initialization failed, exiting")
            sys.exit(1)
        
        # Start the state machine
        logger.info("Starting state machine...")
        state_machine.start()
        
        logger.info("VHS Coffeeman system is now running!")
        logger.info("System ready - waiting for RFID tag insertion")
        
        if args.debug:
            logger.info("Debug mode enabled - detailed logging active")
        
        # Main application loop
        try:
            while True:
                # The state machine runs in its own thread via hardware monitoring
                # This main loop just keeps the application alive and can be used
                # for periodic maintenance tasks if needed
                
                time.sleep(1.0)
                
                # Optional: Log periodic status in debug mode
                if args.debug and int(time.time()) % 30 == 0:  # Every 30 seconds
                    status = state_machine.get_status()
                    logger.debug(f"System status: {status}")
        
        except KeyboardInterrupt:
            # This will be handled by the signal handler
            pass
            
    except Exception as e:
        logger.error(f"Unexpected error in main application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
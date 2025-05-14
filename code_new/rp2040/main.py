"""
main.py - Main Program for VHS Coffeeman

This is the main entry point for the VHS Coffeeman system, running on a Raspberry Pi Pico
(RP2040) with CircuitPython. It initializes all system components and implements the main
event loop.

The system dispenses drinks through a modified VHS player, receiving recipes from a
Raspberry Pi over serial communication and controlling peristaltic pumps via a GRBL controller.

System Components:
    - Configuration (config.py): Central settings and constants
    - Pump Controller (pump_controller.py): Manages pump operations
    - VCR Controller (vcr_controller.py): Controls VCR play/eject buttons
    - GRBL Interface (grbl_interface.py): Communicates with GRBL controller
    - Serial Communication (serial_comm.py): Handles communication with Raspberry Pi
    - State Machine (state_machine.py): Manages system state and transitions
    - Recipe (recipe.py): Stores and executes drink recipes
    - Maintenance (maintenance.py): Handles maintenance operations

Main Program Flow:
    1. Import all necessary modules and CircuitPython libraries
    2. Initialize all system components
    3. Enter the main event loop, which:
       - Checks for incoming serial commands
       - Processes commands through the state machine
       - Handles any system events or timeouts
       - Implements watchdog functionality for safety

Serial Protocol:
    Commands from Raspberry Pi:
        - RECIPE:ID,PUMP:AMOUNT,PUMP:AMOUNT,...
        - START_POUR
        - STOP
        - MAINTENANCE:ACTION
    
    Responses to Raspberry Pi:
        - READY
        - POURING
        - COMPLETE
        - ERROR:message

The main loop is non-blocking and handles all operations in an event-driven manner.
It checks for incoming commands, processes them through the state machine, and sends
status updates back to the Raspberry Pi as appropriate.
"""

import time
import supervisor
import gc

# Import system components
from config import constants
from grbl_interface import GRBLInterface
from pump_controller import PumpController
from vcr_controller import VCRController
from serial_comm import SerialCommunication
from maintenance import Maintenance
from state_machine import StateMachine

# Track initialization status
initialized = False

def initialize_system():
    """
    Initialize all system components.
    
    Returns:
        tuple: (grbl, pump_controller, vcr_controller, serial, maintenance, state_machine)
    """
    print("Initializing VHS Coffeeman system...")
    
    # Initialize GRBL interface
    print("Initializing GRBL interface...")
    grbl = GRBLInterface()
    
    # Initialize pump controller
    print("Initializing pump controller...")
    pump_controller = PumpController(grbl)
    
    # Initialize VCR controller
    print("Initializing VCR controller...")
    vcr_controller = VCRController()
    
    # Initialize serial communication
    print("Initializing serial communication...")
    serial = SerialCommunication()
    
    # Initialize maintenance module
    print("Initializing maintenance module...")
    maintenance = Maintenance(pump_controller)
    
    # Initialize state machine
    print("Initializing state machine...")
    state_machine = StateMachine(
        pump_controller=pump_controller,
        vcr_controller=vcr_controller,
        serial=serial,
        maintenance=maintenance
    )
    
    print("System initialization complete")
    return (grbl, pump_controller, vcr_controller, serial, maintenance, state_machine)

def main():
    """Main program entry point."""
    global initialized
    
    # Initialize the system
    if not initialized:
        try:
            # Initialize all system components
            components = initialize_system()
            grbl, pump_controller, vcr_controller, serial, maintenance, state_machine = components
            
            # Set initialization flag
            initialized = True
            
            # Output memory usage after initialization
            gc.collect()
            print(f"Free memory after initialization: {gc.mem_free()} bytes")
            
        except Exception as e:
            print(f"Error during initialization: {e}")
            # If initialization fails, try to reboot
            supervisor.reload()
            return
    
    try:
        # Main event loop
        print("Entering main event loop")
        last_memory_check = time.monotonic()
        
        while True:
            # Check for incoming commands
            command = serial.check_for_command()
            if command:
                # Process the command through the state machine
                state_machine.handle_command(command)
            
            # Perform periodic tasks
            current_time = time.monotonic()
            
            # Check memory usage every 60 seconds
            if current_time - last_memory_check >= 60:
                gc.collect()
                print(f"Free memory: {gc.mem_free()} bytes")
                last_memory_check = current_time
            
            # Short delay to prevent CPU hogging
            time.sleep_ms(constants.EVENT_LOOP_DELAY_MS)
            
    except Exception as e:
        print(f"Error in main loop: {e}")
        
        # Try to clean up
        try:
            pump_controller.disable_all()
            serial.send_status("ERROR", str(e))
        except:
            pass
        
        # Reboot the system
        supervisor.reload()

# Execute main function
if __name__ == "__main__":
    main()
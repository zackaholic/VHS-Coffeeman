"""
maintenance.py - Maintenance Module for VHS Coffeeman

This module handles maintenance operations for the VHS Coffeeman system.
It provides a class for performing maintenance tasks such as priming, cleaning,
and direct pump control.

Classes:
    Maintenance: Manages maintenance operations

The Maintenance class is responsible for:
    - Executing maintenance commands
    - Priming all pumps (running forward to fill lines)
    - Cleaning all pumps (running backward to empty lines)
    - Controlling individual pumps directly
    - Parsing maintenance commands

Maintenance Commands:
    - PRIME_ALL: Run all pumps forward to prime lines
    - CLEAN_ALL: Run all pumps backward to empty lines
    - PUMP:NUM:DIRECTION:AMOUNT: Control a specific pump
      (e.g., PUMP:3:FORWARD:100 runs pump 3 forward 100mm)

Usage:
    from maintenance import Maintenance
    from pump_controller import PumpController
    
    # Initialize the pump controller
    pump_controller = PumpController()
    
    # Initialize the maintenance controller
    maintenance = Maintenance(pump_controller)
    
    # Execute maintenance commands
    maintenance.prime_all()
    maintenance.clean_all()
    maintenance.control_pump(pump_index=3, direction="FORWARD", amount_mm=100)
    
    # Execute a command from serial
    maintenance.execute_command("PRIME_ALL")
    maintenance.execute_command("PUMP:3:FORWARD:100")

The maintenance operations include safety checks and proper sequencing to prevent
damage to the pumps or other components.

This module depends on:
    - config.py for maintenance settings
    - pump_controller.py for pump control
    - grbl_interface.py for stepper motor control
"""

from config import constants, commands

class Maintenance:
    """Manages maintenance operations."""
    
    def __init__(self, pump_controller):
        """
        Initialize the maintenance controller.
        
        Args:
            pump_controller: A PumpController instance for controlling pumps.
        """
        self.pump_controller = pump_controller
    
    def prime_all(self):
        """
        Prime all pumps by running them forward to fill lines.
        
        Returns:
            bool: True if all pumps were primed successfully, False otherwise.
        """
        print("Priming all pumps")
        
        # Track overall success
        success = True
        
        # Run each pump forward to prime lines
        for pump_index in range(constants.NUM_PUMPS):
            print(f"Priming pump {pump_index}")
            
            # Run the pump forward by the prime amount
            if not self.pump_controller.run_pump(
                pump_index, 
                commands.FORWARD, 
                constants.PRIME_AMOUNT_MM
            ):
                print(f"Failed to prime pump {pump_index}")
                success = False
        
        return success
    
    def clean_all(self):
        """
        Clean all pumps by running them backward to empty lines.
        
        Returns:
            bool: True if all pumps were cleaned successfully, False otherwise.
        """
        print("Cleaning all pumps")
        
        # Track overall success
        success = True
        
        # Run each pump backward to empty lines
        for pump_index in range(constants.NUM_PUMPS):
            print(f"Cleaning pump {pump_index}")
            
            # Run the pump backward by the clean amount
            if not self.pump_controller.run_pump(
                pump_index, 
                commands.BACKWARD, 
                constants.CLEAN_AMOUNT_MM
            ):
                print(f"Failed to clean pump {pump_index}")
                success = False
        
        return success
    
    def control_pump(self, pump_index, direction, amount_mm):
        """
        Control a specific pump directly.
        
        Args:
            pump_index: The index of the pump to control.
            direction: The direction to run the pump (FORWARD or BACKWARD).
            amount_mm: The distance to move in millimeters.
            
        Returns:
            bool: True if the pump was controlled successfully, False otherwise.
        """
        print(f"Controlling pump {pump_index}: {direction} {amount_mm}mm")
        
        # Validate direction
        if direction not in [commands.FORWARD, commands.BACKWARD]:
            print(f"Invalid direction: {direction}")
            return False
        
        # Validate amount (must be positive)
        if amount_mm <= 0:
            print(f"Invalid amount: {amount_mm}mm (must be positive)")
            return False
        
        # Run the pump in the specified direction
        return self.pump_controller.run_pump(pump_index, direction, amount_mm)
    
    def execute_command(self, command):
        """
        Execute a maintenance command.
        
        Args:
            command: A parsed command object or a string command.
            
        Returns:
            bool: True if the command was executed successfully, False otherwise.
        """
        try:
            # If the command is a string, handle simple commands
            if isinstance(command, str):
                if command == commands.PRIME_ALL:
                    return self.prime_all()
                elif command == commands.CLEAN_ALL:
                    return self.clean_all()
                else:
                    print(f"Unknown maintenance command: {command}")
                    return False
            
            # If the command is a dictionary (parsed command object)
            elif isinstance(command, dict):
                action = command.get('action')
                
                if action == commands.PRIME_ALL:
                    return self.prime_all()
                    
                elif action == commands.CLEAN_ALL:
                    return self.clean_all()
                    
                elif action == commands.PUMP:
                    # Extract pump control parameters
                    pump_index = command.get('pump_index')
                    direction = command.get('direction')
                    amount = command.get('amount')
                    
                    # Convert amount from oz to mm if needed
                    if amount <= 10:  # Assume it's in oz if small number
                        amount_mm = amount * constants.MM_PER_OZ
                    else:
                        amount_mm = amount
                    
                    # Control the pump
                    return self.control_pump(pump_index, direction, amount_mm)
                
                else:
                    print(f"Unknown maintenance action: {action}")
                    return False
            
            else:
                print(f"Invalid command type: {type(command)}")
                return False
                
        except Exception as e:
            print(f"Error executing maintenance command: {e}")
            return False
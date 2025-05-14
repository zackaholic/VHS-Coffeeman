"""
pump_controller.py - Pump Control Module for VHS Coffeeman

This module manages all pump-related functionality for the VHS Coffeeman system.
It provides classes for controlling individual pumps and coordinating multiple pumps
during drink dispensing operations.

Classes:
    Pump: Controls a single peristaltic pump
    PumpController: Manages multiple pumps and coordinates dispensing operations

The PumpController class is the primary interface used by other modules. It handles:
    - Initializing all pump objects
    - Enabling/disabling specific pumps
    - Dispensing specific amounts through each pump
    - Coordinating with GRBL for stepper motor control
    - Error detection and recovery during dispensing

Usage:
    from pump_controller import PumpController
    from grbl_interface import GRBLInterface
    
    # Initialize the controller
    grbl = GRBLInterface()
    controller = PumpController(grbl)
    
    # Dispense a specific amount through a pump
    controller.dispense(pump_index=0, amount_oz=1.5)
    
    # Disable all pumps
    controller.disable_all()

The pumps are defined based on the pin configuration in config.py.
Each dispense operation handles the full sequence:
    1. Enable the specified pump
    2. Calculate mm movement based on oz amount
    3. Send command to GRBL
    4. Monitor GRBL_EN pin for completion
    5. Disable pump
    6. Reset GRBL position

This module depends on:
    - config.py for pin definitions and conversion factors
    - grbl_interface.py for stepper motor control
"""

import time
from machine import Pin
from config import pins, constants
from grbl_interface import GRBLInterface

class Pump:
    """Controls a single peristaltic pump."""
    
    def __init__(self, pin_num):
        """
        Initialize a pump with a specific pin.
        
        Args:
            pin_num: The GPIO pin number for the pump's enable control.
        """
        self.pin = Pin(pin_num, Pin.OUT)
        self.disable()  # Start with pump disabled
    
    def enable(self):
        """Enable the pump (set pin low)."""
        self.pin.value(0)
    
    def disable(self):
        """Disable the pump (set pin high)."""
        self.pin.value(1)
    
    def is_enabled(self):
        """Check if the pump is enabled."""
        return self.pin.value() == 0

class PumpController:
    """Manages multiple pumps and coordinates dispensing operations."""
    
    def __init__(self, grbl_interface):
        """
        Initialize the pump controller.
        
        Args:
            grbl_interface: An instance of GRBLInterface for stepper control.
        """
        self.grbl = grbl_interface
        self.pumps = []
        
        # Initialize all pumps based on config
        for pin_num in pins.PUMP_PINS:
            self.pumps.append(Pump(pin_num))
        
        # Make sure all pumps are disabled at startup
        self.disable_all()
    
    def disable_all(self):
        """Disable all pumps."""
        for pump in self.pumps:
            pump.disable()
    
    def validate_pump_index(self, pump_index):
        """
        Validate that a pump index is valid.
        
        Args:
            pump_index: The index of the pump to validate.
            
        Returns:
            bool: True if the pump index is valid, False otherwise.
            
        Raises:
            ValueError: If the pump index is invalid.
        """
        if pump_index < 0 or pump_index >= len(self.pumps):
            error_msg = f"Invalid pump index: {pump_index}. Must be between 0 and {len(self.pumps) - 1}"
            print(error_msg)
            raise ValueError(error_msg)
        return True
    
    def validate_amount(self, amount_oz):
        """
        Validate that an amount is within acceptable range.
        
        Args:
            amount_oz: The amount to dispense in fluid ounces.
            
        Returns:
            bool: True if the amount is valid, False otherwise.
            
        Raises:
            ValueError: If the amount is invalid.
        """
        if amount_oz < constants.MIN_PUMP_OZ or amount_oz > constants.MAX_PUMP_OZ:
            error_msg = f"Invalid amount: {amount_oz} oz. Must be between {constants.MIN_PUMP_OZ} and {constants.MAX_PUMP_OZ} oz"
            print(error_msg)
            raise ValueError(error_msg)
        return True
    
    def dispense(self, pump_index, amount_oz):
        """
        Dispense a specific amount through a pump.
        
        Args:
            pump_index: The index of the pump to use.
            amount_oz: The amount to dispense in fluid ounces.
            
        Returns:
            bool: True if dispensing was successful, False otherwise.
        """
        try:
            # Validate parameters
            self.validate_pump_index(pump_index)
            self.validate_amount(amount_oz)
            
            # Convert ounces to millimeters
            distance_mm = amount_oz * constants.MM_PER_OZ
            
            # 1. Enable the pump
            print(f"Enabling pump {pump_index}")
            self.pumps[pump_index].enable()
            
            # 2. Send movement command to GRBL
            print(f"Dispensing {amount_oz} oz ({distance_mm} mm) from pump {pump_index}")
            if not self.grbl.move(distance_mm):
                # If move command failed, disable pump and return False
                self.pumps[pump_index].disable()
                return False
            
            # 3. Wait for the move to complete
            if not self.grbl.wait_for_completion():
                # If move completion failed, disable pump and return False
                self.pumps[pump_index].disable()
                return False
            
            # 4. Disable the pump
            self.pumps[pump_index].disable()
            
            # 5. Reset GRBL position
            self.grbl.reset_position()
            
            return True
            
        except Exception as e:
            print(f"Error dispensing from pump {pump_index}: {e}")
            # Make sure pump is disabled in case of error
            if pump_index >= 0 and pump_index < len(self.pumps):
                self.pumps[pump_index].disable()
            return False
    
    def run_pump(self, pump_index, direction, distance_mm):
        """
        Run a pump in a specific direction for a specific distance.
        
        Args:
            pump_index: The index of the pump to use.
            direction: The direction to run the pump ("FORWARD" or "BACKWARD").
            distance_mm: The distance to move in millimeters.
            
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            # Validate pump index
            self.validate_pump_index(pump_index)
            
            # Validate distance
            if distance_mm <= 0:
                raise ValueError(f"Invalid distance: {distance_mm} mm. Must be positive")
            
            # Enable the pump
            self.pumps[pump_index].enable()
            
            # Move in the appropriate direction
            success = False
            if direction == "FORWARD":
                success = self.grbl.move(distance_mm)
            elif direction == "BACKWARD":
                success = self.grbl.move_backward(distance_mm)
            else:
                raise ValueError(f"Invalid direction: {direction}. Must be FORWARD or BACKWARD")
            
            if not success:
                self.pumps[pump_index].disable()
                return False
            
            # Wait for the move to complete
            if not self.grbl.wait_for_completion():
                self.pumps[pump_index].disable()
                return False
            
            # Disable the pump
            self.pumps[pump_index].disable()
            
            # Reset GRBL position
            self.grbl.reset_position()
            
            return True
            
        except Exception as e:
            print(f"Error running pump {pump_index}: {e}")
            # Make sure pump is disabled in case of error
            if pump_index >= 0 and pump_index < len(self.pumps):
                self.pumps[pump_index].disable()
            return False
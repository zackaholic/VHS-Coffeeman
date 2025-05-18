"""Controller for managing pumps."""

import time
from typing import List, Dict, Tuple, Optional
import RPi.GPIO as GPIO

from vhs_coffeeman.core.config import Pins, Constants
from vhs_coffeeman.hardware.grbl_interface import GrblInterface
from vhs_coffeeman.utils.logger import setup_logger

logger = setup_logger(__name__)

class PumpController:
    """Controls multiple peristaltic pumps for ingredient dispensing."""
    
    def __init__(self, grbl_interface: GrblInterface):
        """Initialize the pump controller.
        
        Args:
            grbl_interface: Interface to the GRBL controller
        """
        self.grbl = grbl_interface
        self.num_pumps = len(Pins.PUMP_ENABLE)
        self.current_pump = None
        
        # Initialize GPIO pins
        GPIO.setmode(GPIO.BCM)
        for pin in Pins.PUMP_ENABLE:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)  # Disable all pumps initially
            
        logger.info(f"Initialized {self.num_pumps} pump controllers")
    
    def enable_pump(self, pump_index: int) -> bool:
        """Enable a specific pump.
        
        Args:
            pump_index: Index of the pump to enable (0-9)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._validate_pump_index(pump_index):
            return False
        
        # Disable any currently active pump
        self.disable_all_pumps()
        
        # Enable the specified pump
        GPIO.output(Pins.PUMP_ENABLE[pump_index], GPIO.HIGH)
        self.current_pump = pump_index
        logger.debug(f"Enabled pump {pump_index}")
        return True
    
    def disable_pump(self, pump_index: int) -> bool:
        """Disable a specific pump.
        
        Args:
            pump_index: Index of the pump to disable (0-9)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._validate_pump_index(pump_index):
            return False
        
        GPIO.output(Pins.PUMP_ENABLE[pump_index], GPIO.LOW)
        if self.current_pump == pump_index:
            self.current_pump = None
        logger.debug(f"Disabled pump {pump_index}")
        return True
    
    def disable_all_pumps(self):
        """Disable all pumps."""
        for i in range(self.num_pumps):
            GPIO.output(Pins.PUMP_ENABLE[i], GPIO.LOW)
        self.current_pump = None
        logger.debug("Disabled all pumps")
    
    def dispense(self, pump_index: int, amount_oz: float) -> bool:
        """Dispense a specified amount from a pump.
        
        Args:
            pump_index: Index of the pump (0-9)
            amount_oz: Amount to dispense in fluid ounces
            
        Returns:
            bool: True if dispensing completed successfully
        """
        if not self._validate_pump_index(pump_index) or not self._validate_amount(amount_oz):
            return False
        
        # Convert ounces to millimeters
        distance_mm = amount_oz * Constants.MM_PER_OZ
        
        # Enable the pump
        if not self.enable_pump(pump_index):
            logger.error(f"Failed to enable pump {pump_index}")
            return False
        
        # Reset position and move the specified distance
        self.grbl.reset_position()
        result = self.grbl.move_distance(distance_mm)
        
        # Disable the pump after dispensing
        self.disable_pump(pump_index)
        
        if result:
            logger.info(f"Dispensed {amount_oz}oz from pump {pump_index}")
        else:
            logger.error(f"Failed to dispense from pump {pump_index}")
        
        return result
    
    def run_pump(self, pump_index: int, direction: str, distance_mm: float) -> bool:
        """Run a pump manually in a specific direction.
        
        Args:
            pump_index: Index of the pump (0-9)
            direction: 'forward' or 'backward'
            distance_mm: Distance to run in millimeters
            
        Returns:
            bool: True if operation completed successfully
        """
        if not self._validate_pump_index(pump_index):
            return False
        
        if direction not in ["forward", "backward"]:
            logger.error(f"Invalid direction: {direction}")
            return False
        
        # Convert to negative for backward movement
        actual_distance = distance_mm if direction == "forward" else -distance_mm
        
        # Enable the pump
        if not self.enable_pump(pump_index):
            logger.error(f"Failed to enable pump {pump_index}")
            return False
        
        # Reset position and move the specified distance
        self.grbl.reset_position()
        result = self.grbl.move_distance(actual_distance)
        
        # Disable the pump after operation
        self.disable_pump(pump_index)
        
        if result:
            logger.info(f"Ran pump {pump_index} {direction} for {distance_mm}mm")
        else:
            logger.error(f"Failed to run pump {pump_index}")
        
        return result
    
    def _validate_pump_index(self, pump_index: int) -> bool:
        """Validate that the pump index is within range."""
        if not (0 <= pump_index < self.num_pumps):
            logger.error(f"Invalid pump index: {pump_index}. Must be 0-{self.num_pumps-1}")
            return False
        return True
    
    def _validate_amount(self, amount_oz: float) -> bool:
        """Validate that the amount is positive."""
        if amount_oz <= 0:
            logger.error(f"Invalid amount: {amount_oz}. Must be positive")
            return False
        return True
    
    def __del__(self):
        """Clean up resources when deleted."""
        self.disable_all_pumps()
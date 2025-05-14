"""
pump_test.py - Pump Controller Testing Module for VHS Coffeeman

This module provides focused testing for the pump controller system, verifying
the complete cycle of pump operation including:
- Selecting and enabling a specific pump
- Controlling dispensing through GRBL movement
- Detecting movement completion
- Disabling the pump

Usage:
    import time
    from pump_test import PumpTester
    
    # Initialize the tester
    tester = PumpTester()
    
    # Test a specific pump forward
    tester.test_pump(pump_index=0, amount_oz=0.5)
    
    # Test a specific pump backward
    tester.test_pump_backward(pump_index=0, amount_oz=0.5)
"""

import time
from machine import Pin
from config import pins, constants
from grbl_interface import GRBLInterface

class PumpTester:
    """Provides focused testing for the pump controller system."""
    
    def __init__(self):
        """Initialize the pump tester with GRBL and pump setup."""
        # Initialize GRBL interface
        self.grbl = GRBLInterface()
        
        # Initialize pump pins
        self.pumps = []
        for pin_num in pins.PUMP_PINS:
            self.pumps.append(Pin(pin_num, Pin.OUT, value=1))  # Start disabled (high)
        
        print(f"Pump Tester initialized with {len(self.pumps)} pumps")
    
    def validate_pump_index(self, pump_index):
        """
        Validate that a pump index is valid.
        
        Args:
            pump_index: The index of the pump to validate.
            
        Returns:
            bool: True if the pump index is valid, False otherwise.
        """
        if pump_index < 0 or pump_index >= len(self.pumps):
            print(f"Invalid pump index: {pump_index}. Must be between 0 and {len(self.pumps) - 1}")
            return False
        return True
    
    def validate_amount(self, amount_oz):
        """
        Validate that an amount is within acceptable range.
        
        Args:
            amount_oz: The amount to dispense in fluid ounces.
            
        Returns:
            bool: True if the amount is valid, False otherwise.
        """
        if amount_oz < constants.MIN_PUMP_OZ or amount_oz > constants.MAX_PUMP_OZ:
            print(f"Invalid amount: {amount_oz} oz. Must be between {constants.MIN_PUMP_OZ} and {constants.MAX_PUMP_OZ} oz")
            return False
        return True
    
    def test_pump(self, pump_index, amount_oz):
        """
        Test a pump by dispensing a specific amount forward.
        
        Args:
            pump_index: The index of the pump to test.
            amount_oz: The amount to dispense in fluid ounces.
            
        Returns:
            bool: True if the test was successful, False otherwise.
        """
        print(f"\n--- Testing Pump {pump_index} Forward ({amount_oz} oz) ---")
        
        # Validate parameters
        if not self.validate_pump_index(pump_index) or not self.validate_amount(amount_oz):
            return False
        
        try:
            # Convert ounces to millimeters
            distance_mm = amount_oz * constants.MM_PER_OZ
            
            # 1. Reset GRBL position
            print("Resetting GRBL position")
            self.grbl.reset_position()
            
            # 2. Enable the pump
            print(f"Enabling pump {pump_index}")
            self.pumps[pump_index].value(0)  # Low = enabled
            
            # 3. Send movement command to GRBL
            print(f"Dispensing {amount_oz} oz ({distance_mm} mm) from pump {pump_index}")
            if not self.grbl.move(distance_mm):
                # If move command failed, disable pump and return False
                print("Failed to send GRBL movement command")
                self.pumps[pump_index].value(1)  # Disable pump
                return False
            
            # 4. Wait for the move to complete
            if not self.grbl.wait_for_completion():
                # If move completion failed, disable pump and return False
                print("Failed to complete GRBL movement")
                self.pumps[pump_index].value(1)  # Disable pump
                return False
            
            # 5. Disable the pump
            print(f"Disabling pump {pump_index}")
            self.pumps[pump_index].value(1)  # High = disabled
            
            # 6. Reset GRBL position
            self.grbl.reset_position()
            
            print(f"Pump {pump_index} forward test completed successfully")
            return True
            
        except Exception as e:
            print(f"Error testing pump {pump_index}: {e}")
            # Make sure pump is disabled in case of error
            if pump_index >= 0 and pump_index < len(self.pumps):
                self.pumps[pump_index].value(1)  # Disable pump
            return False
    
    def test_pump_backward(self, pump_index, amount_oz):
        """
        Test a pump by dispensing a specific amount backward.
        
        Args:
            pump_index: The index of the pump to test.
            amount_oz: The amount to dispense in fluid ounces.
            
        Returns:
            bool: True if the test was successful, False otherwise.
        """
        print(f"\n--- Testing Pump {pump_index} Backward ({amount_oz} oz) ---")
        
        # Validate parameters
        if not self.validate_pump_index(pump_index) or not self.validate_amount(amount_oz):
            return False
        
        try:
            # Convert ounces to millimeters (negative for backward)
            distance_mm = -amount_oz * constants.MM_PER_OZ
            
            # 1. Reset GRBL position
            print("Resetting GRBL position")
            self.grbl.reset_position()
            
            # 2. Enable the pump
            print(f"Enabling pump {pump_index}")
            self.pumps[pump_index].value(0)  # Low = enabled
            
            # 3. Send movement command to GRBL
            print(f"Running backward {amount_oz} oz ({-distance_mm} mm) from pump {pump_index}")
            if not self.grbl.move(distance_mm):
                # If move command failed, disable pump and return False
                print("Failed to send GRBL movement command")
                self.pumps[pump_index].value(1)  # Disable pump
                return False
            
            # 4. Wait for the move to complete
            if not self.grbl.wait_for_completion():
                # If move completion failed, disable pump and return False
                print("Failed to complete GRBL movement")
                self.pumps[pump_index].value(1)  # Disable pump
                return False
            
            # 5. Disable the pump
            print(f"Disabling pump {pump_index}")
            self.pumps[pump_index].value(1)  # High = disabled
            
            # 6. Reset GRBL position
            self.grbl.reset_position()
            
            print(f"Pump {pump_index} backward test completed successfully")
            return True
            
        except Exception as e:
            print(f"Error testing pump {pump_index}: {e}")
            # Make sure pump is disabled in case of error
            if pump_index >= 0 and pump_index < len(self.pumps):
                self.pumps[pump_index].value(1)  # Disable pump
            return False


# Simple test script when run directly
if __name__ == "__main__":
    print("VHS Coffeeman Pump Controller Test Tool")
    print("--------------------------------------")
    
    # Create the tester
    tester = PumpTester()
    
    try:
        # Ask which pump to test
        print(f"\nAvailable pumps: 0-{len(tester.pumps) - 1}")
        pump_index = int(input("Enter pump index to test: ").strip())
        
        # Validate pump index
        if not tester.validate_pump_index(pump_index):
            raise ValueError(f"Invalid pump index: {pump_index}")
            
        # Ask for direction
        direction = input("Test direction (f=forward, b=backward): ").strip().lower()
        
        # Ask for amount
        amount_oz = float(input(f"Enter amount to dispense (oz, {constants.MIN_PUMP_OZ}-{constants.MAX_PUMP_OZ}): ").strip())
        
        # Validate amount
        if not tester.validate_amount(amount_oz):
            raise ValueError(f"Invalid amount: {amount_oz} oz")
            
        # Run the test
        if direction == 'f':
            tester.test_pump(pump_index, amount_oz)
        elif direction == 'b':
            tester.test_pump_backward(pump_index, amount_oz)
        else:
            print("Invalid direction. Use 'f' for forward or 'b' for backward")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Clean up: make sure all pumps are disabled
        for i, pump in enumerate(tester.pumps):
            pump.value(1)  # Disable all pumps
            print(f"Ensured pump {i} is disabled")
        print("Test complete, all pumps disabled")
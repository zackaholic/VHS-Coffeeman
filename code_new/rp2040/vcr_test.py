"""
vcr_test.py - Simple VCR Controller Testing Module for VHS Coffeeman

This module provides basic testing functionality for verifying the VCR controller
on the VHS Coffeeman system. It focuses on the essential tests:
- Play button activation
- Eject button activation

Usage:
    import time
    from vcr_test import VCRTester
    
    # Initialize the tester
    tester = VCRTester()
    
    # Test play button
    tester.test_play()
    
    # Test eject button
    tester.test_eject()
"""

import time
from machine import Pin
from config import pins, constants

class VCRTester:
    """Provides basic testing functionality for the VCR controller."""
    
    def __init__(self, extended_press=False):
        """
        Initialize the VCR tester with pin setup.
        
        Args:
            extended_press: If True, use longer button press durations for better
                           visibility when testing with LEDs or multimeter.
        """
        # Initialize the play and eject button pins as outputs
        self.play_pin = Pin(pins.VCR_PLAY, Pin.OUT)
        self.eject_pin = Pin(pins.VCR_EJECT, Pin.OUT)
        
        # Set pins to initial state (inactive)
        self.play_pin.value(0)
        self.eject_pin.value(0)
        
        # Set button press duration based on test mode
        if extended_press:
            self.button_press_ms = 2000  # 2 seconds for testing visibility
        else:
            self.button_press_ms = constants.BUTTON_PRESS_MS  # Normal duration from config
        
        print(f"VCR Tester initialized (press duration: {self.button_press_ms}ms)")
    
    def press_button(self, button_pin, description="button"):
        """
        Press a button (momentary pulse).
        
        Args:
            button_pin: The Pin object for the button.
            description: A description of the button for logging.
            
        Returns:
            bool: True if the button press was executed, False otherwise.
        """
        try:
            print(f"Pressing {description} button")
            
            # Set the pin high (active)
            button_pin.value(1)
            
            # Wait for the button press duration
            time.sleep_ms(self.button_press_ms)
            
            # Set the pin low (inactive)
            button_pin.value(0)
            
            print(f"{description} button press complete")
            return True
            
        except Exception as e:
            print(f"Error pressing {description} button: {e}")
            
            # Make sure the pin is set low (inactive) in case of error
            try:
                button_pin.value(0)
            except:
                pass
                
            return False
    
    def test_play(self):
        """
        Test the play button.
        
        Returns:
            bool: True if the play button was pressed successfully, False otherwise.
        """
        print("\n--- Testing Play Button ---")
        return self.press_button(self.play_pin, "play")
    
    def test_eject(self):
        """
        Test the eject button.
        
        Returns:
            bool: True if the eject button was pressed successfully, False otherwise.
        """
        print("\n--- Testing Eject Button ---")
        return self.press_button(self.eject_pin, "eject")


# Simple test script when run directly
if __name__ == "__main__":
    print("VHS Coffeeman VCR Controller Test Tool")
    print("-------------------------------------")
    
    # Ask for test mode
    extended = input("Use extended press duration for testing (y/n)? ").lower().startswith('y')
    
    # Create the tester
    tester = VCRTester(extended_press=extended)
    
    # Ask for test mode
    print("\nTest options:")
    print("1: Test play button")
    print("2: Test eject button")
    print("3: Test both buttons sequentially")
    
    try:
        choice = input("Enter test number (1-3): ")
        choice = int(choice.strip())
        
        if choice == 1:
            tester.test_play()
        elif choice == 2:
            tester.test_eject()
        elif choice == 3:
            tester.test_play()
            time.sleep(2)  # 2 second pause between buttons
            tester.test_eject()
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Make sure pins are in safe state
        tester.play_pin.value(0)
        tester.eject_pin.value(0)
        print("Test complete, pins reset to safe state")
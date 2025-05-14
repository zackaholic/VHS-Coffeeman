"""
vcr_controller.py - VCR Control Module for VHS Coffeeman

This module handles the VCR tape deck functionality for the VHS Coffeeman system.
It provides a class for controlling the VCR's play and eject buttons via GPIO pins.

Classes:
    VCRController: Controls the VCR's play and eject buttons

The VCRController class is responsible for:
    - Initializing the play and eject button pins
    - Triggering the play button (momentary pulse)
    - Triggering the eject button (momentary pulse)
    - Reporting the current VCR state if applicable

Usage:
    from vcr_controller import VCRController
    from config import pins
    
    # Initialize the controller
    vcr = VCRController()
    
    # Trigger the play button
    vcr.play()
    
    # Trigger the eject button
    vcr.eject()

The controller uses the pin definitions in config.py for the play and eject buttons.
The button presses are implemented as momentary pulses with appropriate timing to
simulate a physical button press.

Error handling is included to detect and report any issues with the button pins.

This module depends on:
    - config.py for pin definitions
"""

import time
from machine import Pin
from config import pins, constants

class VCRController:
    """Controls the VCR's play and eject buttons."""
    
    def __init__(self):
        """Initialize the VCR controller with pin setup."""
        # Initialize the play and eject button pins as outputs
        self.play_pin = Pin(pins.VCR_PLAY, Pin.OUT)
        self.eject_pin = Pin(pins.VCR_EJECT, Pin.OUT)
        
        # Set pins to initial state (inactive)
        self.play_pin.value(0)
        self.eject_pin.value(0)
    
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
            time.sleep_ms(constants.BUTTON_PRESS_MS)
            
            # Set the pin low (inactive)
            button_pin.value(0)
            
            return True
            
        except Exception as e:
            print(f"Error pressing {description} button: {e}")
            
            # Make sure the pin is set low (inactive) in case of error
            try:
                button_pin.value(0)
            except:
                pass
                
            return False
    
    def play(self):
        """
        Trigger the play button.
        
        Returns:
            bool: True if the play button was pressed successfully, False otherwise.
        """
        return self.press_button(self.play_pin, "play")
    
    def eject(self):
        """
        Trigger the eject button.
        
        Returns:
            bool: True if the eject button was pressed successfully, False otherwise.
        """
        return self.press_button(self.eject_pin, "eject")
"""
grbl_interface.py - GRBL Interface Module for VHS Coffeeman

This module handles communication with the GRBL controller for the VHS Coffeeman system.
It provides a class for sending movement commands to the GRBL controller and monitoring
the completion of those commands.

Classes:
    GRBLInterface: Manages communication with the GRBL controller

The GRBLInterface class is responsible for:
    - Initializing the serial connection to the GRBL controller
    - Sending movement commands to the GRBL controller
    - Resetting the current position to zero
    - Reading and parsing responses from the GRBL controller
    - Monitoring the GRBL_EN pin to detect when a move is complete

Usage:
    from grbl_interface import GRBLInterface
    from config import pins, constants
    
    # Initialize the interface
    grbl = GRBLInterface()
    
    # Reset the current position to zero
    grbl.reset_position()
    
    # Send a movement command
    grbl.move(distance_mm=100, feed_rate=2000)
    
    # Wait for the move to complete
    grbl.wait_for_completion()

The interface uses the pin definitions and constants in config.py for GRBL communication.
Commands are sent as G-code strings over the serial connection.
The completion of a move is detected by monitoring the GRBL_EN pin.

Error handling is included to detect and report any issues with the GRBL controller,
including timeouts and communication errors.

This module depends on:
    - config.py for pin definitions and GRBL settings
"""

import time
from machine import Pin, UART
from config import pins, constants

class GRBLInterface:
    """Interface for communicating with the GRBL controller."""
    
    def __init__(self):
        """Initialize the GRBL interface with UART and pin setup."""
        # Initialize UART for GRBL communication
        self.uart = UART(0, 
                         baudrate=constants.GRBL_BAUDRATE,
                         tx=Pin(pins.UART_TX),
                         rx=Pin(pins.UART_RX))
        self.uart.init(bits=8, parity=None, stop=1)
        
        # Initialize the GRBL_EN pin for monitoring move completion
        self.grbl_en = Pin(pins.GRBL_EN, Pin.IN)
        
        # Command constants
        self.RESET_POSITION = b'G92X0Y0\n'
        
        # Initialize GRBL
        self.reset_position()
    
    def reset_position(self):
        """Reset the current position to zero."""
        self.uart.write(self.RESET_POSITION)
        self.read_response()
    
    def move(self, distance_mm, feed_rate=None):
        """
        Send a movement command to GRBL.
        
        Args:
            distance_mm: Distance to move in millimeters.
            feed_rate: Feed rate for the move. Defaults to GRBL_PUMP_RATE.
        
        Returns:
            bool: True if command was sent successfully, False otherwise.
        """
        if feed_rate is None:
            feed_rate = constants.GRBL_PUMP_RATE
        
        try:
            # Compose GRBL command
            command = f"G1X{distance_mm}F{feed_rate}\n".encode()
            self.uart.write(command)
            return True
        except Exception as e:
            print(f"GRBL move error: {e}")
            return False
    
    def move_backward(self, distance_mm, feed_rate=None):
        """
        Send a backward movement command to GRBL.
        
        Args:
            distance_mm: Distance to move in millimeters (positive value).
            feed_rate: Feed rate for the move. Defaults to GRBL_PUMP_RATE.
            
        Returns:
            bool: True if command was sent successfully, False otherwise.
        """
        return self.move(-abs(distance_mm), feed_rate)
    
    def read_response(self):
        """
        Read and parse a response from GRBL.
        
        Returns:
            str or None: The response from GRBL, or None if a timeout occurs.
        """
        # Start timeout timer
        start_time = time.ticks_ms()
        
        # Wait for data from GRBL
        while self.uart.any() == 0:
            time.sleep_ms(1)
            
            # Check for timeout
            if time.ticks_ms() - start_time > constants.GRBL_TIMEOUT_MS:
                print("Timeout waiting for GRBL response")
                return None
        
        # Read the response
        response = self.uart.readline()
        if response:
            response = response.decode('utf-8', 'ignore').strip()
        
        return response
    
    def wait_for_completion(self, timeout_ms=None):
        """
        Wait for GRBL to complete the current move.
        
        This method monitors the GRBL_EN pin to detect when a move is complete.
        The pin is high when GRBL is idle and low when GRBL is executing a move.
        
        Args:
            timeout_ms: Timeout in milliseconds. Defaults to 5 times the GRBL timeout.
            
        Returns:
            bool: True if the move completed successfully, False if a timeout occurred.
        """
        if timeout_ms is None:
            timeout_ms = constants.GRBL_TIMEOUT_MS * 5
        
        start_time = time.ticks_ms()
        
        # First, wait for GRBL_EN to go low (indicating move in progress)
        print("Waiting for GRBL to start movement")
        while self.grbl_en.value() == 1:
            time.sleep_ms(10)
            
            # Check for timeout
            if time.ticks_ms() - start_time > timeout_ms:
                print("Timeout waiting for GRBL to start movement")
                return False
            
        # Next, wait for GRBL_EN to go high (indicating move complete)
        print("Waiting for GRBL to complete movement")
        while self.grbl_en.value() == 0:
            time.sleep_ms(10)
            
            # Check for timeout
            if time.ticks_ms() - start_time > timeout_ms:
                print("Timeout waiting for GRBL to complete movement")
                return False
                
        return True
    
    def is_idle(self):
        """
        Check if GRBL is idle (not executing a move).
        
        Returns:
            bool: True if GRBL is idle, False if it's executing a move.
        """
        return self.grbl_en.value() == 1
"""Interface for communicating with GRBL controller."""

import time
import serial
from typing import Optional
import RPi.GPIO as GPIO

from vhs_coffeeman.core.config import Pins, Constants
from vhs_coffeeman.utils.logger import setup_logger

logger = setup_logger(__name__)

class GRBLInterface:
    """Interface for communicating with GRBL controller over UART."""
    
    def __init__(self):
        """Initialize GRBL interface."""
        self.serial = None
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(Pins.GRBL_EN, GPIO.IN)
        self.connect()
    
    def connect(self):
        """Connect to GRBL controller."""
        try:
            self.serial = serial.Serial(
                Constants.GRBL_PORT,
                Constants.GRBL_BAUDRATE,
                timeout=1
            )
            time.sleep(2)  # Wait for GRBL to initialize
            self.serial.flushInput()
            self.reset_position()
            logger.info("Connected to GRBL controller")
        except serial.SerialException as e:
            logger.error(f"Failed to connect to GRBL: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from GRBL controller."""
        if self.serial:
            self.serial.close()
            self.serial = None
            logger.info("Disconnected from GRBL controller")
    
    def send_command(self, command: str) -> Optional[str]:
        """Send a command to GRBL and return the response."""
        if not self.serial:
            raise RuntimeError("GRBL controller not connected")
        
        logger.debug(f"Sending GRBL command: {command}")
        self.serial.write(f"{command}\n".encode())
        time.sleep(0.1)  # Short delay for GRBL to process
        
        response = ""
        start_time = time.time()
        
        # Read response with timeout
        while (time.time() - start_time) < Constants.GRBL_TIMEOUT:
            if self.serial.in_waiting > 0:
                line = self.serial.readline().decode('utf-8').strip()
                response += line + "\n"
                if 'ok' in line or 'error' in line:
                    break
            time.sleep(0.1)
        
        if 'error' in response:
            logger.error(f"GRBL error: {response}")
        else:
            logger.debug(f"GRBL response: {response.strip()}")
        
        return response.strip()
    
    def move_distance(self, distance_mm: float) -> bool:
        """Move the stepper motor a specified distance in mm.
        
        Args:
            distance_mm: Distance to move in millimeters (positive = forward)
            
        Returns:
            bool: True if movement completed successfully
        """
        # Set absolute positioning mode
        self.send_command("G90")
        
        # Set units to millimeters
        self.send_command("G21")
        
        # Set feed rate (speed) - 500 mm/min is a good starting point
        self.send_command("F500")
        
        # Move to the target position
        move_command = f"G1 X{distance_mm:.3f}"
        response = self.send_command(move_command)
        
        # Wait for movement to complete
        start_time = time.time()
        while (time.time() - start_time) < Constants.GRBL_TIMEOUT:
            # Check if GRBL_EN pin is HIGH (movement completed)
            if GPIO.input(Pins.GRBL_EN) == GPIO.HIGH:
                logger.debug("Movement completed")
                return True
            time.sleep(0.1)
        
        logger.error("Movement timeout")
        return False
    
    def reset_position(self):
        """Reset the current position to zero."""
        self.send_command("G92 X0 Y0 Z0")
        logger.debug("GRBL position reset to zero")
    
    def emergency_stop(self):
        """Send immediate stop command to GRBL."""
        self.serial.write("\x18")  # Ctrl+X
        self.reset_position()
        logger.warning("Emergency stop sent to GRBL")
    
    def is_connected(self) -> bool:
        """Check if GRBL controller is connected."""
        return self.serial is not None and self.serial.is_open
    
    def __del__(self):
        """Clean up resources on deletion."""
        self.disconnect()
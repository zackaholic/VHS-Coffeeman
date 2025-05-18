"""Controller for VCR operations."""

import time
from typing import Optional
import RPi.GPIO as GPIO

from vhs_coffeeman.core.config import Pins, Constants
from vhs_coffeeman.utils.logger import setup_logger

logger = setup_logger(__name__)

class VCRController:
    """Controls VCR play and eject buttons via GPIO pins."""
    
    def __init__(self):
        """Initialize VCR controller."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(Pins.VCR_PLAY, GPIO.OUT)
        GPIO.setup(Pins.VCR_EJECT, GPIO.OUT)
        
        # Ensure buttons are not pressed (assuming LOW = not pressed)
        GPIO.output(Pins.VCR_PLAY, GPIO.LOW)
        GPIO.output(Pins.VCR_EJECT, GPIO.LOW)
        
        logger.info("VCR controller initialized")
    
    def press_play(self):
        """Simulate pressing the VCR play button."""
        logger.info("Pressing VCR play button")
        GPIO.output(Pins.VCR_PLAY, GPIO.HIGH)
        time.sleep(Constants.VCR_BUTTON_PRESS_TIME)
        GPIO.output(Pins.VCR_PLAY, GPIO.LOW)
        time.sleep(Constants.VCR_BUTTON_RELEASE_TIME)
        logger.debug("VCR play button pressed and released")
    
    def press_eject(self):
        """Simulate pressing the VCR eject button."""
        logger.info("Pressing VCR eject button")
        GPIO.output(Pins.VCR_EJECT, GPIO.HIGH)
        time.sleep(Constants.VCR_BUTTON_PRESS_TIME)
        GPIO.output(Pins.VCR_EJECT, GPIO.LOW)
        time.sleep(Constants.VCR_BUTTON_RELEASE_TIME)
        logger.debug("VCR eject button pressed and released")
    
    def __del__(self):
        """Clean up resources when deleted."""
        # Ensure buttons are not pressed
        try:
            GPIO.output(Pins.VCR_PLAY, GPIO.LOW)
            GPIO.output(Pins.VCR_EJECT, GPIO.LOW)
        except Exception:
            pass  # GPIO might already be cleaned up
"""Interface for RFID reader."""

import time
from typing import Optional, Tuple
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

from vhs_coffeeman.core.config import Constants
from vhs_coffeeman.utils.logger import setup_logger

logger = setup_logger(__name__)

class RFIDReader:
    """Interface for MFRC522 RFID reader."""
    
    def __init__(self):
        """Initialize RFID reader."""
        try:
            self.reader = SimpleMFRC522()
            logger.info("RFID reader initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RFID reader: {e}")
            raise
    
    def read_tag(self) -> Tuple[Optional[int], Optional[str]]:
        """Read RFID tag and return ID and text.
        
        Returns:
            tuple: (tag_id, text) or (None, None) if no tag was read
        """
        try:
            tag_id, text = self.reader.read_no_block()
            if tag_id:
                logger.info(f"Read RFID tag: {tag_id}")
                return tag_id, text
            return None, None
        except Exception as e:
            logger.error(f"Error reading RFID tag: {e}")
            return None, None
    
    def write_tag(self, text: str) -> bool:
        """Write text to an RFID tag.
        
        Args:
            text: Text to write to the tag
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Writing to RFID tag: {text}")
            self.reader.write_no_block(text)
            logger.debug("Write successful")
            return True
        except Exception as e:
            logger.error(f"Error writing to RFID tag: {e}")
            return False
    
    def wait_for_tag(self, timeout: Optional[float] = None) -> Tuple[Optional[int], Optional[str]]:
        """Wait for an RFID tag to be presented.
        
        Args:
            timeout: Maximum time to wait in seconds, or None for no timeout
            
        Returns:
            tuple: (tag_id, text) or (None, None) if no tag was read within timeout
        """
        logger.info("Waiting for RFID tag...")
        start_time = time.time()
        
        while True:
            tag_id, text = self.read_tag()
            if tag_id is not None:
                return tag_id, text
            
            # Check timeout
            if timeout is not None and (time.time() - start_time) > timeout:
                logger.warning("Timeout waiting for RFID tag")
                return None, None
            
            # Brief delay to avoid hammering the SPI bus
            time.sleep(0.1)
    
    def __del__(self):
        """Clean up resources when deleted."""
        # SimpleMFRC522 doesn't require explicit cleanup
        pass
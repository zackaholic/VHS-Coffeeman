"""Cup sensor interface using VCNL4010 proximity sensor."""

import time
from typing import Optional
import smbus2
import struct

from vhs_coffeeman.core.config import Pins, Constants
from vhs_coffeeman.utils.logger import setup_logger

logger = setup_logger(__name__)


# VCNL4010 I2C address and register definitions
VCNL4010_I2C_ADDRESS = 0x13
VCNL4010_COMMAND = 0x80
VCNL4010_PRODUCTID = 0x81
VCNL4010_PROXIMITYRATE = 0x82
VCNL4010_IRLED = 0x83
VCNL4010_AMBIENTPARAMETER = 0x84
VCNL4010_AMBIENTDATA = 0x85
VCNL4010_PROXIMITYDATA = 0x87
VCNL4010_INTCONTROL = 0x89
VCNL4010_PROX_TIMING = 0x8F

# Command register bits
VCNL4010_MEASUREAMBIENT = 0x10
VCNL4010_MEASUREPROXIMITY = 0x08
VCNL4010_AMBIENTREADY = 0x40
VCNL4010_PROXIMITYREADY = 0x20


class CupSensor:
    """Interface for VCNL4010 proximity sensor to detect cup presence.
    
    The VCNL4010 proximity sensor returns 16-bit values (0-65535) where:
    - Higher values indicate closer objects
    - Lower values indicate farther objects
    
    This class detects cup presence at 15-30mm distance by comparing
    proximity readings against a configurable threshold.
    """
    
    def __init__(self):
        """Initialize the cup sensor.
        
        Sets up I2C communication with the VCNL4010 sensor.
        Note: This assumes I2C is enabled on the default bus (usually bus 1 on RPi).
        
        Raises:
            RuntimeError: If sensor initialization fails
            OSError: If I2C communication fails
        """
        self.bus = None
        self.threshold = Constants.VCNL4010_THRESHOLD
        
        try:
            # Initialize I2C bus (bus 1 is the default on Raspberry Pi)
            logger.info("Initializing I2C bus for VCNL4010 sensor")
            self.bus = smbus2.SMBus(1)  # I2C bus 1 (GPIO2=SDA, GPIO3=SCL)
            
            # Check if sensor is present by reading product ID
            logger.info("Checking VCNL4010 sensor presence")
            product_id = self.bus.read_byte_data(VCNL4010_I2C_ADDRESS, VCNL4010_PRODUCTID)
            if product_id != 0x21:  # VCNL4010 product ID should be 0x21
                raise RuntimeError(f"VCNL4010 not found. Got product ID: 0x{product_id:02x}, expected 0x21")
            
            # Initialize sensor settings
            self._initialize_sensor()
            
            # Test sensor communication with a proximity reading
            test_reading = self._read_proximity()
            logger.info(f"Cup sensor initialized successfully (test reading: {test_reading})")
            logger.info(f"Detection threshold set to: {self.threshold}")
            
        except Exception as e:
            logger.error(f"Failed to initialize cup sensor: {e}")
            if self.bus:
                self.bus.close()
                self.bus = None
            raise RuntimeError(f"Cup sensor initialization failed: {e}")
    
    def _initialize_sensor(self):
        """Initialize VCNL4010 sensor with appropriate settings."""
        # Set proximity measurement rate (default is fine for most applications)
        # Rate = 1.95 measurements per second (0x00)
        self.bus.write_byte_data(VCNL4010_I2C_ADDRESS, VCNL4010_PROXIMITYRATE, 0x00)
        
        # Set IR LED current (default 200mA is usually fine)
        # Current = 200mA (0x14)
        self.bus.write_byte_data(VCNL4010_I2C_ADDRESS, VCNL4010_IRLED, 0x14)
        
        logger.debug("VCNL4010 sensor configured")
    
    def _read_proximity(self) -> int:
        """Read proximity value from the sensor.
        
        Returns:
            int: 16-bit proximity value (0-65535)
        """
        # Start proximity measurement
        self.bus.write_byte_data(VCNL4010_I2C_ADDRESS, VCNL4010_COMMAND, VCNL4010_MEASUREPROXIMITY)
        
        # Wait for measurement to complete
        timeout = 50  # 50ms timeout
        while timeout > 0:
            status = self.bus.read_byte_data(VCNL4010_I2C_ADDRESS, VCNL4010_COMMAND)
            if status & VCNL4010_PROXIMITYREADY:
                break
            time.sleep(0.001)  # 1ms delay
            timeout -= 1
        
        if timeout == 0:
            raise RuntimeError("Timeout waiting for proximity measurement")
        
        # Read 16-bit proximity data (big-endian)
        data = self.bus.read_i2c_block_data(VCNL4010_I2C_ADDRESS, VCNL4010_PROXIMITYDATA, 2)
        proximity = (data[0] << 8) | data[1]
        
        return proximity
    
    def is_cup_present(self) -> bool:
        """Check if a cup is present within detection range.
        
        Reads the proximity sensor and compares against the configured threshold.
        A cup is considered present if the proximity value is above the threshold.
        
        Returns:
            bool: True if cup is detected, False otherwise
            
        Note:
            Returns False if sensor is not initialized or communication fails
        """
        if self.bus is None:
            logger.warning("Cup sensor not initialized")
            return False
        
        try:
            proximity = self._read_proximity()
            is_present = proximity > self.threshold
            
            logger.debug(f"Proximity reading: {proximity}, threshold: {self.threshold}, cup present: {is_present}")
            
            return is_present
            
        except Exception as e:
            logger.error(f"Error reading cup sensor: {e}")
            return False
    
    def get_proximity_value(self) -> Optional[int]:
        """Get the raw proximity sensor value for calibration/debugging.
        
        Returns:
            int: Raw proximity value (0-65535) if successful, None if failed
            
        Note:
            Higher values indicate closer objects.
            Use this method to determine appropriate threshold values.
        """
        if self.bus is None:
            logger.warning("Cup sensor not initialized")
            return None
        
        try:
            proximity = self._read_proximity()
            logger.debug(f"Raw proximity reading: {proximity}")
            return proximity
            
        except Exception as e:
            logger.error(f"Error reading proximity value: {e}")
            return None
    
    def wait_for_cup(self, timeout: Optional[float] = None) -> bool:
        """Wait for a cup to be placed within detection range.
        
        Args:
            timeout: Maximum time to wait in seconds, or None for no timeout
            
        Returns:
            bool: True if cup was detected within timeout, False otherwise
        """
        logger.info("Waiting for cup to be placed...")
        start_time = time.time()
        
        while True:
            if self.is_cup_present():
                logger.info("Cup detected!")
                return True
            
            # Check timeout
            if timeout is not None and (time.time() - start_time) > timeout:
                logger.warning(f"Timeout waiting for cup after {timeout} seconds")
                return False
            
            # Brief delay to avoid hammering the I2C bus
            time.sleep(0.1)
    
    def wait_for_cup_removal(self, timeout: Optional[float] = None) -> bool:
        """Wait for a cup to be removed from detection range.
        
        Args:
            timeout: Maximum time to wait in seconds, or None for no timeout
            
        Returns:
            bool: True if cup was removed within timeout, False otherwise
        """
        logger.info("Waiting for cup to be removed...")
        start_time = time.time()
        
        while True:
            if not self.is_cup_present():
                logger.info("Cup removed!")
                return True
            
            # Check timeout
            if timeout is not None and (time.time() - start_time) > timeout:
                logger.warning(f"Timeout waiting for cup removal after {timeout} seconds")
                return False
            
            # Brief delay to avoid hammering the I2C bus
            time.sleep(0.1)
    
    def calibrate_threshold(self, samples: int = 10, delay: float = 0.5) -> dict:
        """Take multiple proximity readings for threshold calibration.
        
        Args:
            samples: Number of readings to take
            delay: Delay between readings in seconds
            
        Returns:
            dict: Statistics including min, max, average, and recommended threshold
        """
        if self.bus is None:
            logger.error("Cup sensor not initialized")
            return {}
        
        logger.info(f"Taking {samples} proximity readings for calibration...")
        readings = []
        
        for i in range(samples):
            try:
                reading = self._read_proximity()
                readings.append(reading)
                logger.info(f"Reading {i+1}/{samples}: {reading}")
                time.sleep(delay)
            except Exception as e:
                logger.error(f"Error during calibration reading {i+1}: {e}")
        
        if not readings:
            logger.error("No valid readings obtained during calibration")
            return {}
        
        stats = {
            'readings': readings,
            'min': min(readings),
            'max': max(readings),
            'average': sum(readings) / len(readings),
            'count': len(readings)
        }
        
        # Suggest threshold as 80% of minimum reading (conservative approach)
        stats['recommended_threshold'] = int(stats['min'] * 0.8)
        
        logger.info(f"Calibration results: {stats}")
        return stats
    
    def __del__(self):
        """Clean up resources when deleted."""
        if hasattr(self, 'bus') and self.bus:
            try:
                self.bus.close()
            except:
                pass
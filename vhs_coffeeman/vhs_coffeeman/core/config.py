"""Configuration settings for VHS Coffeeman."""

class Pins:
    """GPIO pin assignments."""
    GRBL_EN = 20       # GRBL enable pin
    VCR_PLAY = 16      # VCR play button control
    VCR_EJECT = 12     # VCR eject button control

    # Pump control pins (for enabling stepper drivers)
    PUMP_ENABLE = [
        4, 17, 27, 22, 5,  # Pumps 0-4
        6, 13, 19, 26, 21   # Pumps 5-9
    ]

    # Cup sensor pins (VCNL4010 proximity sensor)
    VCNL4010_SDA = 2   # I2C SDA pin
    VCNL4010_SCL = 3   # I2C SCL pin

class Constants:
    """System constants."""
    # Pump calibration: 100mm movement per fluid ounce
    MM_PER_OZ = 20.0

    # Button press timing
    VCR_BUTTON_PRESS_TIME = 0.25  # seconds
    VCR_BUTTON_RELEASE_TIME = 0.25  # seconds

    # Serial communication
    # Commented out because GRBL will use UART port
    # and no secondary port is necessary
    # SERIAL_PORT = "/dev/ttyS0"  # UART port
    # SERIAL_BAUDRATE = 115200
    GRBL_BAUDRATE = 115200
    GRBL_PORT = "/dev/ttyUSB0"  # USB serial for GRBL
    GRBL_TIMEOUT = 30.0  # seconds - allow time for long pump movements

    # RFID
    MFRC522_SPI_BUS = 0
    MFRC522_SPI_DEVICE = 0
    MFRC522_RESET_PIN = 25

    # Cup sensor (VCNL4010 proximity sensor)
    # Threshold for cup presence detection (values above this indicate cup present)
    # Note: VCNL4010 returns higher values for closer objects
    # Typical range: 0-65535, adjust based on testing at 15-30mm distance
    VCNL4010_THRESHOLD = 2700  # Default threshold, tune based on testing

class States:
    """System states."""
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RECIPE_LOADED = "RECIPE_LOADED"
    POURING = "POURING"
    MAINTENANCE = "MAINTENANCE"
    ERROR = "ERROR"

class Commands:
    """Serial command definitions."""
    # Recipe commands
    RECIPE = "RECIPE"  # Format: RECIPE:rfid_id,pump:amount,pump:amount...
    START_POUR = "START_POUR"
    STOP = "STOP"

    # Maintenance commands
    MAINTENANCE_PREFIX = "MAINTENANCE"
    PRIME_ALL = f"{MAINTENANCE_PREFIX}:PRIME_ALL"
    CLEAN_ALL = f"{MAINTENANCE_PREFIX}:CLEAN_ALL"
    PUMP = f"{MAINTENANCE_PREFIX}:PUMP"  # Format: MAINTENANCE:PUMP:idx:direction:amount

    # Status responses
    READY = "READY"
    POURING = "POURING"  # Format: POURING:pump_idx
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"  # Format: ERROR:message

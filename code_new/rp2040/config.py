"""
config.py - Configuration Module for VHS Coffeeman

This module centralizes all configuration constants and settings for the VHS Coffeeman system.
It serves as a single source of truth for hardware pin definitions, system constants, and
state definitions.

Usage:
    from config import pins, constants, states
    
    # Access pin definitions
    play_pin = pins.VCR_PLAY
    
    # Access system constants
    mm_per_oz = constants.MM_PER_OZ
    
    # Access state definitions
    current_state = states.READY

The configuration is separated into logical sections (pins, constants, states) to make
it easy to locate and modify settings. All values should be treated as read-only.

This module should be imported by all other modules that need access to configuration values.
No other module should define these constants.
"""

class pins:
    # VCR control pins
    VCR_PLAY = 15
    VCR_EJECT = 14
    
    # GRBL control pins
    GRBL_EN = 28  # Input pin to detect GRBL controller status
    UART_TX = 12  # UART TX pin for GRBL communication
    UART_RX = 13  # UART RX pin for GRBL communication
    
    # Pump control pins (stepper enable pins)
    PUMP_PINS = [
        6,   # Pump 0
        7,   # Pump 1
        9,   # Pump 2
        18,  # Pump 3
        19,  # Pump 4
        20,  # Pump 5
        21,  # Pump 6
        22,  # Pump 7
        26,  # Pump 8
        27   # Pump 9
    ]
    
    # Cup presence detection pin
    CUP_PRESENCE = 10
    
    # Raspberry Pi serial communication
    PI_UART_TX = 0  # UART1 TX pin for Pi communication
    PI_UART_RX = 1  # UART1 RX pin for Pi communication

class constants:
    # GRBL settings
    GRBL_BAUDRATE = 115200
    GRBL_PUMP_RATE = 2000  # F2000 feedrate for pump movement
    GRBL_TIMEOUT_MS = 1000  # Timeout for GRBL response in milliseconds
    
    # Pump settings
    MM_PER_OZ = 100  # 100mm of movement per fluid ounce
    NUM_PUMPS = len(pins.PUMP_PINS)
    MAX_PUMP_OZ = 10.0  # Maximum fluid per pump operation
    MIN_PUMP_OZ = 0.1   # Minimum fluid per pump operation
    
    # VCR button control
    BUTTON_PRESS_MS = 200  # Duration to hold button in milliseconds
    
    # Serial communication with Raspberry Pi
    PI_BAUDRATE = 115200
    COMMAND_TIMEOUT_MS = 5000  # Timeout for command execution
    
    # Maintenance settings
    PRIME_AMOUNT_MM = 200  # Amount to move for priming pumps
    CLEAN_AMOUNT_MM = 150  # Amount to move for cleaning pumps
    
    # System settings
    EVENT_LOOP_DELAY_MS = 10  # Main loop delay in milliseconds

class states:
    # System states
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RECIPE_LOADED = "RECIPE_LOADED"
    POURING = "POURING"
    MAINTENANCE = "MAINTENANCE"
    ERROR = "ERROR"

class commands:
    # Serial command types
    RECIPE = "RECIPE"
    START_POUR = "START_POUR"
    STOP = "STOP"
    MAINTENANCE = "MAINTENANCE"
    
    # Serial response types
    READY = "READY"
    POURING = "POURING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"
    
    # Maintenance command types
    PRIME_ALL = "PRIME_ALL"
    CLEAN_ALL = "CLEAN_ALL"
    PUMP = "PUMP"
    
    # Pump directions
    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"
#!/usr/bin/env python3
"""
GPIO Test Script for VHS Coffeeman

This script allows testing GPIO functionality for different hardware components:
- VCR button control (play/eject)
- Pump control outputs
- GRBL enable pin test

Usage:
  python gpio_test.py vcr play  # Test VCR play button
  python gpio_test.py vcr eject  # Test VCR eject button
  python gpio_test.py pump 0  # Test toggling pump 0 twice/second for 10 seconds
  python gpio_test.py pumps  # Test all pumps in sequence
  python gpio_test.py grbl  # Test GRBL enable pin reading
"""

import sys
import time
import RPi.GPIO as GPIO
from vhs_coffeeman.core.config import Pins, Constants

# Set up GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def test_vcr_button(button):
    """Test VCR button press (play or eject)."""
    if button not in ["play", "eject"]:
        print(f"Unknown button: {button}. Use 'play' or 'eject'.")
        return False
    
    pin = Pins.VCR_PLAY if button == "play" else Pins.VCR_EJECT
    
    print(f"Setting up VCR {button.upper()} button on pin {pin}")
    GPIO.setup(pin, GPIO.OUT)
    
    print(f"Pressing VCR {button.upper()} button for {Constants.VCR_BUTTON_PRESS_TIME} seconds")
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(Constants.VCR_BUTTON_PRESS_TIME)
    GPIO.output(pin, GPIO.LOW)
    print(f"Released VCR {button.upper()} button")
    
    return True

def test_pump(pump_index):
    """Test a specific pump by toggling it twice a second for 10 seconds."""
    if not (0 <= pump_index < len(Pins.PUMP_ENABLE)):
        print(f"Invalid pump index: {pump_index}. Must be 0-{len(Pins.PUMP_ENABLE)-1}")
        return False
    
    pin = Pins.PUMP_ENABLE[pump_index]
    print(f"Setting up pump {pump_index} on pin {pin}")
    
    # Setup GPIO
    GPIO.setup(pin, GPIO.OUT)
    
    # Initially ensure pump is off
    GPIO.output(pin, GPIO.LOW)
    
    print(f"Toggling pump {pump_index} twice a second for 10 seconds")
    
    # Toggle the pin twice a second for 10 seconds
    end_time = time.time() + 10
    toggle_count = 0
    
    while time.time() < end_time:
        # Toggle state
        state = toggle_count % 2  # 0 or 1
        GPIO.output(pin, state)
        
        # Print current state
        state_str = "ON" if state else "OFF"
        print(f"\rPump {pump_index} state: {state_str} (toggle count: {toggle_count})", end="")
        
        # Increment toggle count
        toggle_count += 1
        
        # Wait 0.5 seconds before next toggle (2 toggles per second)
        time.sleep(0.5)
    
    # Ensure pump is off when done
    GPIO.output(pin, GPIO.LOW)
    print(f"\nCompleted testing pump {pump_index} with {toggle_count} toggles")
    
    return True

def test_all_pumps():
    """Test all pumps in sequence."""
    print(f"Testing all {len(Pins.PUMP_ENABLE)} pumps in sequence")
    
    # Set up all pump pins
    for i, pin in enumerate(Pins.PUMP_ENABLE):
        print(f"Setting up pump {i} on pin {pin}")
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
    
    # Enable each pump briefly in sequence
    for i, pin in enumerate(Pins.PUMP_ENABLE):
        print(f"Enabling pump {i} for 1 second")
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(pin, GPIO.LOW)
        print(f"Disabled pump {i}")
        time.sleep(0.5)  # Delay between pumps
    
    print("All pumps tested")
    return True

def test_grbl_enable():
    """Test reading the GRBL enable pin."""
    print(f"Setting up GRBL enable pin {Pins.GRBL_EN} as input")
    GPIO.setup(Pins.GRBL_EN, GPIO.IN)
    
    print("Reading GRBL enable pin for 5 seconds (Ctrl+C to stop):")
    try:
        end_time = time.time() + 5
        while time.time() < end_time:
            value = GPIO.input(Pins.GRBL_EN)
            state = "HIGH" if value == GPIO.HIGH else "LOW"
            print(f"\rGRBL enable pin is {state} (value: {value})", end="")
            time.sleep(0.1)
        print("\nGRBL enable pin monitoring complete")
    except KeyboardInterrupt:
        print("\nGRBL enable pin monitoring stopped by user")
    
    return True

def print_usage():
    """Print usage instructions."""
    print("Usage:")
    print("  python gpio_test.py vcr play   # Test VCR play button")
    print("  python gpio_test.py vcr eject  # Test VCR eject button")
    print("  python gpio_test.py pump N     # Test toggling pump N (0-9) twice/second for 10 seconds")
    print("  python gpio_test.py pumps      # Test all pumps in sequence")
    print("  python gpio_test.py grbl       # Test GRBL enable pin reading")

def main():
    """Main function to parse arguments and run tests."""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    try:
        command = sys.argv[1].lower()
        
        if command == "vcr" and len(sys.argv) >= 3:
            button = sys.argv[2].lower()
            test_vcr_button(button)
        elif command == "pump" and len(sys.argv) >= 3:
            try:
                pump_index = int(sys.argv[2])
                test_pump(pump_index)
            except ValueError:
                print(f"Invalid pump index: {sys.argv[2]}. Must be a number.")
                print_usage()
        elif command == "pumps":
            test_all_pumps()
        elif command == "grbl":
            test_grbl_enable()
        else:
            print(f"Unknown command: {command}")
            print_usage()
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup completed")

if __name__ == "__main__":
    main()
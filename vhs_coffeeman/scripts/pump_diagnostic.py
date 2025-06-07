#!/usr/bin/env python3
"""
Pump Diagnostic Script

This script helps diagnose pump control issues by:
1. Testing individual GPIO pins
2. Showing which pins are actually changing state
3. Providing detailed logging of pin states
"""

import sys
import time
import RPi.GPIO as GPIO
from vhs_coffeeman.core.config import Pins

# Set GPIO mode at the start
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def setup_pins():
    """Set up all pump pins as outputs."""
    print("Setting up pump control pins...")
    for i, pin in enumerate(Pins.PUMP_ENABLE):
        print(f"  Pump {i}: GPIO {pin}")
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)  # Start with all disabled
    print("All pins initialized to LOW (disabled)")
    print()

def read_all_pin_states():
    """Read and display current state of all pump pins."""
    states = {}
    for i, pin in enumerate(Pins.PUMP_ENABLE):
        # Switch to input momentarily to read actual pin state
        GPIO.setup(pin, GPIO.IN)
        state = GPIO.input(pin)
        # Switch back to output
        GPIO.setup(pin, GPIO.OUT)
        states[i] = state
    return states

def test_individual_pin(pump_index):
    """Test a single pump pin and monitor all others."""
    if pump_index >= len(Pins.PUMP_ENABLE):
        print(f"Invalid pump index: {pump_index}")
        return
    
    pin = Pins.PUMP_ENABLE[pump_index]
    print(f"Testing pump {pump_index} (GPIO {pin})")
    print("=" * 50)
    
    # Read initial states
    print("Initial pin states:")
    initial_states = read_all_pin_states()
    for i, state in initial_states.items():
        status = "HIGH" if state else "LOW"
        print(f"  Pump {i} (GPIO {Pins.PUMP_ENABLE[i]}): {status}")
    print()
    
    # Enable the target pump
    print(f"Enabling pump {pump_index}...")
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.1)  # Brief delay for signal to settle
    
    # Read states after enabling
    print("Pin states after enabling:")
    enabled_states = read_all_pin_states()
    changes = []
    for i, state in enabled_states.items():
        status = "HIGH" if state else "LOW"
        changed = " <- CHANGED!" if state != initial_states[i] else ""
        print(f"  Pump {i} (GPIO {Pins.PUMP_ENABLE[i]}): {status}{changed}")
        if state != initial_states[i]:
            changes.append(i)
    
    print()
    if len(changes) == 1 and changes[0] == pump_index:
        print("✓ CORRECT: Only the target pump changed state")
    else:
        print(f"✗ PROBLEM: Expected only pump {pump_index} to change, but these pumps changed: {changes}")
        print("This suggests:")
        print("  - Wiring issue (multiple pumps connected to same GPIO)")
        print("  - GPIO pin conflicts")
        print("  - Hardware problem with pump driver boards")
    
    # Wait a moment
    time.sleep(2)
    
    # Disable the pump
    print(f"\nDisabling pump {pump_index}...")
    GPIO.output(pin, GPIO.LOW)
    time.sleep(0.1)
    
    # Read final states
    print("Pin states after disabling:")
    final_states = read_all_pin_states()
    for i, state in final_states.items():
        status = "HIGH" if state else "LOW"
        changed = " <- CHANGED!" if state != enabled_states[i] else ""
        print(f"  Pump {i} (GPIO {Pins.PUMP_ENABLE[i]}): {status}{changed}")
    print()

def test_all_pins_individually():
    """Test each pump pin one at a time."""
    print("Testing all pump pins individually...")
    print("=" * 60)
    
    for i in range(min(3, len(Pins.PUMP_ENABLE))):  # Test first 3 pumps
        test_individual_pin(i)
        print()
        input("Press Enter to continue to next pump...")
        print()

def test_pin_isolation():
    """Test if pins are properly isolated by enabling them one by one."""
    print("Pin isolation test - enabling pumps sequentially...")
    print("=" * 60)
    
    # Enable pumps one by one and monitor
    for i in range(min(3, len(Pins.PUMP_ENABLE))):
        pin = Pins.PUMP_ENABLE[i]
        print(f"Enabling pump {i} (GPIO {pin})...")
        GPIO.output(pin, GPIO.HIGH)
        
        # Check which pins are actually high
        active_pumps = []
        for j, check_pin in enumerate(Pins.PUMP_ENABLE):
            GPIO.setup(check_pin, GPIO.IN)
            if GPIO.input(check_pin):
                active_pumps.append(j)
            GPIO.setup(check_pin, GPIO.OUT)
        
        print(f"  Pumps showing HIGH: {active_pumps}")
        if len(active_pumps) != i + 1:
            print(f"  ✗ PROBLEM: Expected {i + 1} pumps active, got {len(active_pumps)}")
        
        time.sleep(1)
    
    # Disable all
    print("\nDisabling all pumps...")
    for pin in Pins.PUMP_ENABLE:
        GPIO.output(pin, GPIO.LOW)

def print_usage():
    """Print usage instructions."""
    print("Usage:")
    print("  python pump_diagnostic.py test [pump_index]  # Test specific pump")
    print("  python pump_diagnostic.py all               # Test all pumps individually")
    print("  python pump_diagnostic.py isolation         # Test pin isolation")

def main():
    """Main diagnostic function."""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    try:
        setup_pins()
        
        command = sys.argv[1].lower()
        
        if command == "test" and len(sys.argv) >= 3:
            pump_index = int(sys.argv[2])
            test_individual_pin(pump_index)
        elif command == "all":
            test_all_pins_individually()
        elif command == "isolation":
            test_pin_isolation()
        else:
            print(f"Unknown command: {command}")
            print_usage()
    
    except ValueError:
        print("Invalid pump index")
        print_usage()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Ensure all pumps are disabled
        for pin in Pins.PUMP_ENABLE:
            GPIO.output(pin, GPIO.LOW)
        GPIO.cleanup()
        print("GPIO cleanup completed")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Pump Controller Test Script for VHS Coffeeman

This script tests the pump controller functionality:
- Single pump control
- Dispensing specific amounts
- Running pumps forward/backward for maintenance

Usage:
  python pump_test.py enable [pump_index]     # Enable a specific pump
  python pump_test.py disable [pump_index]    # Disable a specific pump
  python pump_test.py dispense [pump] [oz]    # Dispense amount from pump
  python pump_test.py run [pump] [dir] [mm]   # Run pump in direction for distance
                                              # dir = forward|backward
  python pump_test.py sequence                # Run a test sequence on all pumps
"""

import sys
import time
import RPi.GPIO as GPIO

from vhs_coffeeman.hardware.grbl_interface import GrblInterface
from vhs_coffeeman.hardware.pump_controller import PumpController
from vhs_coffeeman.core.config import Pins, Constants

# Set GPIO mode at the start
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def setup():
    """Set up GRBL and pump controller."""
    print("Initializing GRBL interface...")
    grbl = GrblInterface()
    
    print("Initializing pump controller...")
    pump_ctrl = PumpController(grbl)
    
    return grbl, pump_ctrl

def test_enable_pump(pump_ctrl, pump_index):
    """Test enabling a specific pump."""
    print(f"Enabling pump {pump_index}...")
    if pump_ctrl.enable_pump(pump_index):
        print(f"✓ Pump {pump_index} enabled successfully")
        
        # Keep enabled for 3 seconds
        print(f"Keeping pump {pump_index} enabled for 3 seconds...")
        time.sleep(3)
        
        # Disable after test
        pump_ctrl.disable_pump(pump_index)
        print(f"Pump {pump_index} disabled")
    else:
        print(f"✗ Failed to enable pump {pump_index}")

def test_disable_pump(pump_ctrl, pump_index):
    """Test disabling a specific pump."""
    print(f"First enabling pump {pump_index}...")
    pump_ctrl.enable_pump(pump_index)
    time.sleep(1)
    
    print(f"Now disabling pump {pump_index}...")
    if pump_ctrl.disable_pump(pump_index):
        print(f"✓ Pump {pump_index} disabled successfully")
    else:
        print(f"✗ Failed to disable pump {pump_index}")

def test_dispense(pump_ctrl, pump_index, amount_oz):
    """Test dispensing a specific amount from a pump."""
    print(f"Dispensing {amount_oz}oz from pump {pump_index}...")
    if pump_ctrl.dispense(pump_index, amount_oz):
        print(f"✓ Successfully dispensed {amount_oz}oz from pump {pump_index}")
    else:
        print(f"✗ Failed to dispense from pump {pump_index}")

def test_run_pump(pump_ctrl, pump_index, direction, distance_mm):
    """Test running a pump in a specific direction for a distance."""
    print(f"Running pump {pump_index} {direction} for {distance_mm}mm...")
    if pump_ctrl.run_pump(pump_index, direction, distance_mm):
        print(f"✓ Successfully ran pump {pump_index} {direction} for {distance_mm}mm")
    else:
        print(f"✗ Failed to run pump {pump_index}")

def test_sequence(pump_ctrl):
    """Run a test sequence on all pumps."""
    num_pumps = len(Pins.PUMP_ENABLE)
    print(f"Running test sequence on all {num_pumps} pumps...")
    
    # Briefly enable each pump in sequence
    for i in range(num_pumps):
        print(f"\nTesting pump {i}...")
        pump_ctrl.enable_pump(i)
        time.sleep(1)
        pump_ctrl.disable_pump(i)
        time.sleep(0.5)
    
    # Test a short dispense on each pump
    for i in range(num_pumps):
        print(f"\nDispensing a small amount from pump {i}...")
        pump_ctrl.dispense(i, 0.1)  # Just 0.1oz for testing
        time.sleep(0.5)
    
    print("\n✓ Pump sequence test completed")

def print_usage():
    """Print usage instructions."""
    print("Usage:")
    print("  python pump_test.py enable [pump_index]     # Enable a specific pump")
    print("  python pump_test.py disable [pump_index]    # Disable a specific pump")
    print("  python pump_test.py dispense [pump] [oz]    # Dispense amount from pump")
    print("  python pump_test.py run [pump] [dir] [mm]   # Run pump in direction for distance")
    print("                                              # dir = forward|backward")
    print("  python pump_test.py sequence                # Run a test sequence on all pumps")

def main():
    """Main function to parse arguments and run tests."""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    try:
        command = sys.argv[1].lower()
        
        # Set up controllers
        grbl, pump_ctrl = setup()
        
        if command == "enable" and len(sys.argv) >= 3:
            pump_index = int(sys.argv[2])
            test_enable_pump(pump_ctrl, pump_index)
            
        elif command == "disable" and len(sys.argv) >= 3:
            pump_index = int(sys.argv[2])
            test_disable_pump(pump_ctrl, pump_index)
            
        elif command == "dispense" and len(sys.argv) >= 4:
            pump_index = int(sys.argv[2])
            amount_oz = float(sys.argv[3])
            test_dispense(pump_ctrl, pump_index, amount_oz)
            
        elif command == "run" and len(sys.argv) >= 5:
            pump_index = int(sys.argv[2])
            direction = sys.argv[3].lower()
            distance_mm = float(sys.argv[4])
            
            if direction not in ["forward", "backward"]:
                print(f"Invalid direction: {direction}. Must be 'forward' or 'backward'.")
                return
                
            test_run_pump(pump_ctrl, pump_index, direction, distance_mm)
            
        elif command == "sequence":
            test_sequence(pump_ctrl)
            
        else:
            print(f"Unknown command: {command}")
            print_usage()
        
        # Clean up
        pump_ctrl.cleanup()
        grbl.disconnect()
        
    except ValueError:
        print("Invalid numeric argument")
        print_usage()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup completed")

if __name__ == "__main__":
    main()
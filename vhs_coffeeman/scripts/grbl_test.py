#!/usr/bin/env python3
"""
GRBL Interface Test Script for VHS Coffeeman

This script tests communication with the GRBL controller
and basic movement commands.

Usage:
  python grbl_test.py connect        # Test connection to GRBL
  python grbl_test.py move [distance]  # Move a specific distance (mm)
  python grbl_test.py reset          # Reset GRBL position to zero
  python grbl_test.py status         # Get GRBL status
"""

import sys
import time
import RPi.GPIO as GPIO

from vhs_coffeeman.hardware.grbl_interface import GrblInterface
from vhs_coffeeman.core.config import Pins, Constants

# Set GPIO mode at the start
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def test_connection():
    """Test connection to GRBL controller."""
    print("Testing connection to GRBL controller...")
    try:
        grbl = GrblInterface()
        if grbl.is_connected():
            print("✓ GRBL controller connected successfully")
            print(f"  Port: {Constants.GRBL_PORT}")
            print(f"  Baud rate: {Constants.GRBL_BAUDRATE}")
            
            # Get GRBL version
            response = grbl.send_command("$I")
            if response:
                print(f"GRBL response:\n{response}")
            
            grbl.disconnect()
            print("GRBL controller disconnected")
        else:
            print("✗ Failed to connect to GRBL controller")
    except Exception as e:
        print(f"✗ Error connecting to GRBL: {e}")
    finally:
        GPIO.cleanup()

def test_movement(distance_mm=10.0):
    """Test moving the stepper motor a specific distance."""
    print(f"Testing GRBL movement of {distance_mm} mm...")
    try:
        grbl = GrblInterface()
        if not grbl.is_connected():
            print("✗ GRBL controller not connected")
            return
        
        print("Resetting position to zero...")
        grbl.reset_position()
        
        print(f"Moving {distance_mm} mm...")
        start_time = time.time()
        result = grbl.move_distance(distance_mm)
        elapsed_time = time.time() - start_time
        
        if result:
            print(f"✓ Movement completed successfully in {elapsed_time:.2f} seconds")
        else:
            print("✗ Movement failed or timed out")
            
        grbl.disconnect()
        
    except Exception as e:
        print(f"✗ Error during movement test: {e}")
    finally:
        GPIO.cleanup()

def test_reset_position():
    """Test resetting the GRBL position to zero."""
    print("Testing GRBL position reset...")
    try:
        grbl = GrblInterface()
        if not grbl.is_connected():
            print("✗ GRBL controller not connected")
            return
        
        print("Resetting position to zero...")
        grbl.reset_position()
        print("✓ Position reset command sent")
        
        grbl.disconnect()
        
    except Exception as e:
        print(f"✗ Error testing position reset: {e}")
    finally:
        GPIO.cleanup()

def test_grbl_status():
    """Test getting GRBL status."""
    print("Testing GRBL status...")
    try:
        grbl = GrblInterface()
        if not grbl.is_connected():
            print("✗ GRBL controller not connected")
            return
        
        # Query status with ? command
        print("Querying GRBL status...")
        response = grbl.send_command("?")
        if response:
            print(f"Status response: {response}")
        else:
            print("No status response received")
            
        # Check system settings
        print("\nQuerying GRBL settings...")
        settings = grbl.send_command("$$")
        if settings:
            print(f"Settings:\n{settings}")
        
        grbl.disconnect()
        
    except Exception as e:
        print(f"✗ Error getting GRBL status: {e}")
    finally:
        GPIO.cleanup()

def print_usage():
    """Print usage instructions."""
    print("Usage:")
    print("  python grbl_test.py connect         # Test connection to GRBL")
    print("  python grbl_test.py move [distance] # Move a specific distance (mm)")
    print("  python grbl_test.py reset           # Reset GRBL position to zero")
    print("  python grbl_test.py status          # Get GRBL status")

def main():
    """Main function to parse arguments and run tests."""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "connect":
        test_connection()
    elif command == "move":
        distance = 10.0  # Default distance
        if len(sys.argv) >= 3:
            try:
                distance = float(sys.argv[2])
            except ValueError:
                print(f"Invalid distance: {sys.argv[2]}. Must be a number.")
                return
        test_movement(distance)
    elif command == "reset":
        test_reset_position()
    elif command == "status":
        test_grbl_status()
    else:
        print(f"Unknown command: {command}")
        print_usage()

if __name__ == "__main__":
    main()
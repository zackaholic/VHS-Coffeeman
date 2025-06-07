#!/usr/bin/env python3
"""
GRBL Enable Pin Test Script for VHS Coffeeman

This script tests the GRBL enable pin to verify we can detect when motor movements
are in progress and when they complete. This is critical for sequencing logic.

Usage:
  python grbl_enable_test.py monitor     # Monitor enable pin for 10 seconds
  python grbl_enable_test.py move [mm]   # Move and monitor enable pin state
"""

import sys
import time
import threading
import RPi.GPIO as GPIO

from vhs_coffeeman.hardware.grbl_interface import GrblInterface
from vhs_coffeeman.core.config import Pins, Constants

# Set GPIO mode at the start
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Global flag to stop monitoring
stop_monitoring = False

def monitor_enable_pin(duration=None):
    """Monitor the GRBL enable pin and log state changes."""
    global stop_monitoring
    
    print(f"Monitoring GRBL enable pin (GPIO {Pins.GRBL_EN})...")
    GPIO.setup(Pins.GRBL_EN, GPIO.IN)
    
    last_state = None
    start_time = time.time()
    state_changes = []
    
    try:
        while not stop_monitoring:
            current_state = GPIO.input(Pins.GRBL_EN)
            current_time = time.time()
            
            # Log state changes
            if current_state != last_state:
                elapsed = current_time - start_time
                state_str = "HIGH" if current_state else "LOW"
                print(f"[{elapsed:.3f}s] Enable pin: {state_str}")
                state_changes.append((elapsed, current_state))
                last_state = current_state
            
            # Check timeout
            if duration and (current_time - start_time) > duration:
                break
                
            time.sleep(0.01)  # 10ms polling rate
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    
    return state_changes

def test_enable_pin_during_movement(distance_mm=50.0):
    """Test enable pin behavior during a GRBL movement."""
    print(f"Testing GRBL enable pin during {distance_mm}mm movement")
    print("=" * 60)
    
    try:
        # Initialize GRBL
        print("Connecting to GRBL...")
        grbl = GrblInterface()
        if not grbl.is_connected():
            print("✗ GRBL not connected")
            return False
        print("✓ GRBL connected")
        
        # Set up enable pin monitoring
        GPIO.setup(Pins.GRBL_EN, GPIO.IN)
        
        # Read initial state
        initial_state = GPIO.input(Pins.GRBL_EN)
        initial_str = "HIGH" if initial_state else "LOW"
        print(f"Initial enable pin state: {initial_str}")
        
        # Reset position to zero first
        print("Resetting GRBL position...")
        grbl.reset_position()
        time.sleep(0.5)
        
        # Check state after reset
        after_reset_state = GPIO.input(Pins.GRBL_EN)
        after_reset_str = "HIGH" if after_reset_state else "LOW"
        print(f"Enable pin after reset: {after_reset_str}")
        
        # Start monitoring in a separate thread
        global stop_monitoring
        stop_monitoring = False
        
        print(f"\nStarting movement of {distance_mm}mm...")
        print("Monitoring enable pin during movement...")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_enable_pin)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Send movement command
        movement_start = time.time()
        print(f"[0.000s] Sending movement command...")
        
        # Send the movement command
        command = f"G1 X{distance_mm} F1000"  # Move at 1000 mm/min
        response = grbl.send_command(command)
        
        if response:
            print(f"GRBL response: {response.strip()}")
        
        # Wait for movement to complete by checking enable pin
        print("Waiting for movement to complete...")
        movement_in_progress = False
        max_wait_time = 30  # Maximum wait time in seconds
        
        while (time.time() - movement_start) < max_wait_time:
            current_state = GPIO.input(Pins.GRBL_EN)
            
            # Detect when movement starts (pin state changes)
            if not movement_in_progress and current_state != initial_state:
                elapsed = time.time() - movement_start
                print(f"[{elapsed:.3f}s] Movement detected - enable pin changed!")
                movement_in_progress = True
            
            # Detect when movement ends (pin returns to original state)
            elif movement_in_progress and current_state == initial_state:
                elapsed = time.time() - movement_start
                print(f"[{elapsed:.3f}s] Movement completed - enable pin returned to original state")
                break
                
            time.sleep(0.01)
        else:
            print("⚠ Timeout waiting for movement to complete")
        
        # Stop monitoring
        stop_monitoring = True
        time.sleep(0.1)  # Give monitor thread time to stop
        
        # Final state check
        final_state = GPIO.input(Pins.GRBL_EN)
        final_str = "HIGH" if final_state else "LOW"
        print(f"Final enable pin state: {final_str}")
        
        # Analysis
        print("\nAnalysis:")
        if initial_state == final_state:
            print("✓ Enable pin returned to original state")
        else:
            print("✗ Enable pin did not return to original state")
            
        if movement_in_progress:
            print("✓ Movement was detected via enable pin state change")
        else:
            print("✗ No movement detected - enable pin may not change during movements")
            print("  This could mean:")
            print("  - Enable pin is not connected to motor enable signal")
            print("  - Motor drivers are always enabled")
            print("  - Pin is configured incorrectly")
        
        grbl.disconnect()
        return movement_in_progress
        
    except Exception as e:
        print(f"✗ Error during test: {e}")
        return False
    finally:
        stop_monitoring = True
        GPIO.cleanup()

def test_just_monitor():
    """Just monitor the enable pin for 10 seconds."""
    print("Monitoring GRBL enable pin for 10 seconds...")
    print("=" * 50)
    
    try:
        GPIO.setup(Pins.GRBL_EN, GPIO.IN)
        
        initial_state = GPIO.input(Pins.GRBL_EN)
        initial_str = "HIGH" if initial_state else "LOW"
        print(f"Initial state: {initial_str}")
        
        global stop_monitoring
        stop_monitoring = False
        
        state_changes = monitor_enable_pin(duration=10)
        
        print(f"\nMonitoring complete. Detected {len(state_changes)} state changes:")
        for elapsed, state in state_changes:
            state_str = "HIGH" if state else "LOW"
            print(f"  {elapsed:.3f}s: {state_str}")
            
        if not state_changes:
            print("No state changes detected - pin is stable")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        GPIO.cleanup()

def print_usage():
    """Print usage instructions."""
    print("Usage:")
    print("  python grbl_enable_test.py monitor           # Monitor enable pin for 10 seconds")
    print("  python grbl_enable_test.py move [distance]   # Move and monitor enable pin state")
    print("\nThis test verifies that the GRBL enable pin (GPIO 20) changes state during movements.")

def main():
    """Main function to parse arguments and run tests."""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "monitor":
        test_just_monitor()
    elif command == "move":
        distance = 50.0  # Default distance
        if len(sys.argv) >= 3:
            try:
                distance = float(sys.argv[2])
            except ValueError:
                print(f"Invalid distance: {sys.argv[2]}. Must be a number.")
                return
        success = test_enable_pin_during_movement(distance)
        if success:
            print("\n✓ Enable pin test successful - sequencing logic should work")
        else:
            print("\n✗ Enable pin test failed - sequencing logic may need revision")
    else:
        print(f"Unknown command: {command}")
        print_usage()

if __name__ == "__main__":
    main()
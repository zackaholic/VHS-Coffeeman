#!/usr/bin/env python3
"""
Cup Sensor Test Script for VHS Coffeeman

This script tests the VCNL4010 proximity sensor functionality for cup detection.
It provides various testing modes including continuous monitoring, calibration,
and threshold testing.

Usage:
  python cup_sensor_test.py monitor     # Continuously monitor cup presence
  python cup_sensor_test.py raw         # Display raw proximity values
  python cup_sensor_test.py calibrate   # Run calibration routine
  python cup_sensor_test.py threshold   # Test different threshold values
  python cup_sensor_test.py wait        # Wait for cup placement/removal
"""

import sys
import time
import os

# Add the parent directory to the path so we can import from vhs_coffeeman
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from vhs_coffeeman.hardware.cup_sensor import CupSensor
    from vhs_coffeeman.core.config import Constants
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the correct directory and the vhs_coffeeman module is available")
    sys.exit(1)


def monitor_cup_presence():
    """Continuously monitor cup presence with real-time feedback."""
    print("=== Cup Presence Monitor ===")
    print("This will continuously check for cup presence.")
    print("Press Ctrl+C to stop\n")
    
    try:
        sensor = CupSensor()
        print(f"Current threshold: {Constants.VCNL4010_THRESHOLD}")
        print("Monitoring cup presence...\n")
        
        last_state = None
        while True:
            is_present = sensor.is_cup_present()
            proximity = sensor.get_proximity_value()
            
            if is_present != last_state:
                status = "CUP DETECTED!" if is_present else "No cup"
                print(f"[{time.strftime('%H:%M:%S')}] {status} (proximity: {proximity})")
                last_state = is_present
            
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error: {e}")


def display_raw_values():
    """Display raw proximity sensor values for debugging."""
    print("=== Raw Proximity Values ===")
    print("This will display raw sensor readings in real-time.")
    print("Use this to understand sensor behavior and choose thresholds.")
    print("Press Ctrl+C to stop\n")
    
    try:
        sensor = CupSensor()
        print(f"Current threshold: {Constants.VCNL4010_THRESHOLD}")
        print("Raw proximity readings:\n")
        
        while True:
            proximity = sensor.get_proximity_value()
            above_threshold = proximity > Constants.VCNL4010_THRESHOLD if proximity is not None else False
            threshold_indicator = "ABOVE" if above_threshold else "below"
            
            print(f"[{time.strftime('%H:%M:%S')}] Proximity: {proximity:5d} ({threshold_indicator} threshold)")
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nRaw value display stopped by user")
    except Exception as e:
        print(f"Error: {e}")


def run_calibration():
    """Run calibration routine to determine optimal threshold."""
    print("=== Cup Sensor Calibration ===")
    print("This will help you determine the optimal threshold value.")
    print("Follow the prompts to take readings with and without a cup.\n")
    
    try:
        sensor = CupSensor()
        
        # Take readings without cup
        input("1. Remove any cup from the sensor area and press Enter...")
        print("Taking readings WITHOUT cup (background readings)...")
        no_cup_stats = sensor.calibrate_threshold(samples=10, delay=0.3)
        
        if not no_cup_stats:
            print("Failed to get background readings")
            return
        
        print(f"Background readings - Min: {no_cup_stats['min']}, Max: {no_cup_stats['max']}, Avg: {no_cup_stats['average']:.1f}")
        
        # Take readings with cup at target distance
        input("\n2. Place a cup 15-30mm from the sensor and press Enter...")
        print("Taking readings WITH cup at target distance...")
        with_cup_stats = sensor.calibrate_threshold(samples=10, delay=0.3)
        
        if not with_cup_stats:
            print("Failed to get cup readings")
            return
        
        print(f"Cup readings - Min: {with_cup_stats['min']}, Max: {with_cup_stats['max']}, Avg: {with_cup_stats['average']:.1f}")
        
        # Calculate recommended threshold
        if with_cup_stats['min'] > no_cup_stats['max']:
            # Clear separation - use midpoint
            recommended = int((no_cup_stats['max'] + with_cup_stats['min']) / 2)
        else:
            # Overlapping ranges - use conservative approach
            recommended = int(no_cup_stats['max'] * 1.2)
        
        print(f"\n=== Calibration Results ===")
        print(f"Background range: {no_cup_stats['min']} - {no_cup_stats['max']}")
        print(f"Cup range: {with_cup_stats['min']} - {with_cup_stats['max']}")
        print(f"Current threshold: {Constants.VCNL4010_THRESHOLD}")
        print(f"Recommended threshold: {recommended}")
        print(f"\nTo update the threshold, edit VCNL4010_THRESHOLD in config.py")
        
    except Exception as e:
        print(f"Error during calibration: {e}")


def test_threshold():
    """Test different threshold values interactively."""
    print("=== Threshold Testing ===")
    print("This allows you to test different threshold values without editing config.")
    print("Press Ctrl+C to stop\n")
    
    try:
        sensor = CupSensor()
        
        while True:
            try:
                threshold_input = input(f"Enter threshold value (current: {sensor.threshold}, 'q' to quit): ")
                if threshold_input.lower() == 'q':
                    break
                
                new_threshold = int(threshold_input)
                sensor.threshold = new_threshold
                
                print(f"Threshold set to {new_threshold}. Testing...")
                print("Place/remove cup to test detection. Press Enter for next threshold.\n")
                
                start_time = time.time()
                while time.time() - start_time < 10:  # Test for 10 seconds
                    proximity = sensor.get_proximity_value()
                    is_present = sensor.is_cup_present()
                    status = "CUP DETECTED" if is_present else "no cup"
                    
                    print(f"\rProximity: {proximity:5d}, Status: {status}    ", end="", flush=True)
                    time.sleep(0.2)
                
                print("\n")
                
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                break
                
    except Exception as e:
        print(f"Error: {e}")


def test_wait_functions():
    """Test the wait_for_cup and wait_for_cup_removal functions."""
    print("=== Wait Function Testing ===")
    print("This tests the wait_for_cup() and wait_for_cup_removal() functions.")
    print("Press Ctrl+C to stop\n")
    
    try:
        sensor = CupSensor()
        
        while True:
            print("Testing wait_for_cup() - remove any cup and press Enter...")
            input()
            
            print("Waiting for cup placement (10 second timeout)...")
            if sensor.wait_for_cup(timeout=10):
                print("✓ Cup detected!")
                
                print("\nTesting wait_for_cup_removal()...")
                print("Waiting for cup removal (10 second timeout)...")
                if sensor.wait_for_cup_removal(timeout=10):
                    print("✓ Cup removed!")
                else:
                    print("✗ Timeout waiting for cup removal")
            else:
                print("✗ Timeout waiting for cup placement")
            
            if input("\nTest again? (y/n): ").lower() != 'y':
                break
                
    except KeyboardInterrupt:
        print("\nTesting stopped by user")
    except Exception as e:
        print(f"Error: {e}")


def print_usage():
    """Print usage instructions."""
    print("Cup Sensor Test Script")
    print("Usage:")
    print("  python cup_sensor_test.py monitor     # Continuously monitor cup presence")
    print("  python cup_sensor_test.py raw         # Display raw proximity values")
    print("  python cup_sensor_test.py calibrate   # Run calibration routine")
    print("  python cup_sensor_test.py threshold   # Test different threshold values")
    print("  python cup_sensor_test.py wait        # Test wait functions")


def main():
    """Main function to parse arguments and run tests."""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    print("Cup Sensor Test Script")
    print("======================")
    print("Make sure the VCNL4010 sensor is connected:")
    print("- SDA to GPIO2")
    print("- SCL to GPIO3") 
    print("- VCC to 3.3V")
    print("- GND to GND")
    print()
    
    if command == "monitor":
        monitor_cup_presence()
    elif command == "raw":
        display_raw_values()
    elif command == "calibrate":
        run_calibration()
    elif command == "threshold":
        test_threshold()
    elif command == "wait":
        test_wait_functions()
    else:
        print(f"Unknown command: {command}")
        print_usage()


if __name__ == "__main__":
    main()
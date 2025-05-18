#!/usr/bin/env python3
"""
RFID Reader Test Script for VHS Coffeeman

This script tests the RFID reader functionality by continuously scanning for tags
and displaying their IDs and data.

Usage:
  python rfid_test.py read     # Continuously read RFID tags
  python rfid_test.py write    # Write data to an RFID tag
"""

import sys
import time
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

def read_tags(timeout=None):
    """Continuously read RFID tags until timeout or interrupted."""
    reader = SimpleMFRC522()
    print("RFID Reader initialized. Waiting for tags...")
    
    try:
        start_time = time.time()
        while True:
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                print(f"\nTimeout after {timeout} seconds")
                break
            
            print("\rScanning for tag... (Press Ctrl+C to stop)", end="")
            try:
                # Non-blocking read
                id, text = reader.read_no_block()
                if id:
                    print(f"\nTag detected!")
                    print(f"ID: {id}")
                    print(f"Text: {text}")
                    print("\nContinuing to scan... (Press Ctrl+C to stop)")
                    # Reset the start time when a tag is found
                    start_time = time.time() 
            except Exception as e:
                print(f"\nError reading tag: {e}")
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nScan stopped by user")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup completed")

def write_tag():
    """Write data to an RFID tag."""
    reader = SimpleMFRC522()
    print("RFID Writer initialized.")
    
    try:
        text = input("Enter text to write to the tag: ")
        print("Place the tag near the reader...")
        
        reader.write(text)
        print(f"Data written successfully: {text}")
        
        # Confirm by reading back
        print("Reading back the tag data...")
        id, text = reader.read()
        print(f"Tag ID: {id}")
        print(f"Tag text: {text}")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup completed")

def print_usage():
    """Print usage instructions."""
    print("Usage:")
    print("  python rfid_test.py read   # Continuously read RFID tags")
    print("  python rfid_test.py write  # Write data to an RFID tag")

def main():
    """Main function to parse arguments and run tests."""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "read":
        read_tags()
    elif command == "write":
        write_tag()
    else:
        print(f"Unknown command: {command}")
        print_usage()

if __name__ == "__main__":
    main()
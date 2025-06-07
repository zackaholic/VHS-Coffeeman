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

reader = SimpleMFRC522()

def read_tags(timeout=None):
    """Continuously read RFID tags until timeout or interrupted."""
    print("RFID Reader initialized. Place tag near reader to scan...")
    
    try:
        print("Waiting for RFID tag... (Press Ctrl+C to stop)")
        id, text = reader.read()
        print(f"\nTag detected!")
        print(f"ID: {id}")
        print(f"Text: {text}")
        print("Remove tag and place again to scan another, or press Ctrl+C to exit")
        
        # Continue reading for additional tags
        while True:
            print("\nWaiting for next tag... (Press Ctrl+C to stop)")
            id, text = reader.read()
            print(f"\nTag detected!")
            print(f"ID: {id}")
            print(f"Text: {text}")
    
    except KeyboardInterrupt:
        print("\nScan stopped by user")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup completed")

def write_tag():
    """Write data to an RFID tag."""
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
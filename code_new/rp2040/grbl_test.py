"""
grbl_test.py - GRBL Interface Testing Module for VHS Coffeeman

This module provides testing functionality for verifying the GRBL interface
on the VHS Coffeeman system. It allows for testing:
- UART communication with the GRBL controller
- Basic movement commands
- Position reset commands
- GRBL_EN pin monitoring during movements
- Forward and backward movements

Usage:
    import time
    from grbl_test import GRBLTester
    
    # Initialize the tester
    tester = GRBLTester()
    
    # Test basic UART communication
    tester.test_communication()
    
    # Test a simple movement
    tester.test_movement(10)  # Move 10mm
    
    # Test multiple movements
    tester.test_movement_sequence()
    
This module is designed for diagnostic purposes to verify that the GRBL
controller is properly connected and responding to commands.
"""

import time
from machine import Pin, UART
from config import pins, constants

class GRBLTester:
    """Provides testing functionality for the GRBL interface."""
    
    def __init__(self):
        """Initialize the GRBL tester with UART and pin setup."""
        # Initialize UART for GRBL communication
        self.uart = UART(0, 
                         baudrate=constants.GRBL_BAUDRATE,
                         tx=Pin(pins.UART_TX),
                         rx=Pin(pins.UART_RX))
        self.uart.init(bits=8, parity=None, stop=1)
        
        # Initialize the GRBL_EN pin for monitoring move completion
        self.grbl_en = Pin(pins.GRBL_EN, Pin.IN)
        
        # Command constants
        self.RESET_POSITION = b'G92X0Y0\n'
        
        # Response timeout
        self.response_timeout_ms = constants.GRBL_TIMEOUT_MS
        
        print("GRBL Tester initialized")
    
    def send_command(self, command):
        """
        Send a command to the GRBL controller.
        
        Args:
            command: The command to send (bytes or string).
            
        Returns:
            bool: True if command was sent successfully, False otherwise.
        """
        try:
            if isinstance(command, str):
                command = command.encode()
                
            if not command.endswith(b'\n'):
                command += b'\n'
                
            print(f"Sending: {command.decode().strip()}")
            self.uart.write(command)
            return True
            
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
    
    def read_response(self, timeout_ms=None):
        """
        Read a response from the GRBL controller.
        
        Args:
            timeout_ms: Timeout in milliseconds. Default from config.
            
        Returns:
            str or None: The response, or None if a timeout occurs.
        """
        if timeout_ms is None:
            timeout_ms = self.response_timeout_ms
            
        start_time = time.ticks_ms()
        response = b''
        
        # Wait for data from GRBL
        while self.uart.any() == 0:
            time.sleep_ms(10)
            
            # Check for timeout
            if time.ticks_ms() - start_time > timeout_ms:
                print(f"Timeout waiting for response (after {timeout_ms}ms)")
                return None
        
        # Read all available data
        while self.uart.any() > 0:
            data = self.uart.read(1)
            if data:
                response += data
                
            # Small delay to allow more data to arrive
            time.sleep_ms(5)
            
            # Check for extended timeout
            if time.ticks_ms() - start_time > timeout_ms * 2:
                print("Extended timeout while reading response")
                break
        
        # Decode and return the response
        if response:
            try:
                decoded = response.decode('utf-8', 'ignore').strip()
                print(f"Received: {decoded}")
                return decoded
            except UnicodeError:
                print(f"Error decoding response: {response}")
                return None
        
        return None
    
    def reset_position(self):
        """
        Reset the current position to zero.
        
        Returns:
            bool: True if reset was successful, False otherwise.
        """
        print("Resetting position to zero")
        if self.send_command(self.RESET_POSITION):
            response = self.read_response()
            return response is not None
        return False
    
    def move(self, distance_mm, feed_rate=None):
        """
        Send a movement command to GRBL.
        
        Args:
            distance_mm: Distance to move in millimeters.
            feed_rate: Feed rate for the move. Defaults to GRBL_PUMP_RATE.
            
        Returns:
            bool: True if command was sent successfully, False otherwise.
        """
        if feed_rate is None:
            feed_rate = constants.GRBL_PUMP_RATE
            
        command = f"G1X{distance_mm}F{feed_rate}"
        print(f"Moving {distance_mm}mm at F{feed_rate}")
        
        if self.send_command(command):
            response = self.read_response()
            return response is not None
        return False
    
    def wait_for_completion(self, timeout_ms=None):
        """
        Wait for GRBL to complete the current move by monitoring GRBL_EN pin.
        
        Args:
            timeout_ms: Timeout in milliseconds. Default is 5× GRBL timeout.
            
        Returns:
            bool: True if move completed successfully, False if timeout.
        """
        if timeout_ms is None:
            timeout_ms = self.response_timeout_ms * 5
            
        start_time = time.ticks_ms()
        
        # First, look for GRBL_EN to go low (indicating move in progress)
        print("Waiting for GRBL to start movement (GRBL_EN should go LOW)")
        low_detected = False
        
        while time.ticks_ms() - start_time < timeout_ms:
            if self.grbl_en.value() == 0:
                print("Movement started (GRBL_EN is LOW)")
                low_detected = True
                break
            time.sleep_ms(10)
        
        if not low_detected:
            print("Warning: Movement may not have started (GRBL_EN stayed HIGH)")
            print("Check if GRBL controller is powered and connected")
            return False
            
        # Next, wait for GRBL_EN to go high (indicating move complete)
        print("Waiting for GRBL to complete movement (GRBL_EN should go HIGH)")
        
        while time.ticks_ms() - start_time < timeout_ms:
            if self.grbl_en.value() == 1:
                print("Movement completed (GRBL_EN is HIGH)")
                return True
            time.sleep_ms(10)
            
        print(f"Timeout waiting for movement completion (after {timeout_ms}ms)")
        return False
    
    def test_communication(self):
        """
        Test basic communication with the GRBL controller.
        
        Returns:
            bool: True if communication is working, False otherwise.
        """
        print("\n--- Testing GRBL Communication ---")
        print("Sending status query command")
        
        # Send a simple status query
        if not self.send_command('?'):
            print("Failed to send status query")
            return False
            
        # Read response
        response = self.read_response()
        if response is None:
            print("No response from GRBL controller")
            print("Check if GRBL is powered and connected correctly")
            return False
            
        print("Communication test successful")
        return True
    
    def test_position_reset(self):
        """
        Test position reset command.
        
        Returns:
            bool: True if reset was successful, False otherwise.
        """
        print("\n--- Testing Position Reset ---")
        return self.reset_position()
    
    def test_movement(self, distance_mm=10):
        """
        Test a simple movement.
        
        Args:
            distance_mm: Distance to move in millimeters.
            
        Returns:
            bool: True if movement was successful, False otherwise.
        """
        print(f"\n--- Testing {distance_mm}mm Movement ---")
        
        # Reset position first
        if not self.reset_position():
            print("Failed to reset position")
            return False
            
        # Send movement command
        if not self.move(distance_mm):
            print("Failed to send movement command")
            return False
            
        # Wait for completion
        if not self.wait_for_completion():
            print("Movement did not complete")
            return False
            
        print(f"Successfully moved {distance_mm}mm")
        return True
    
    def test_backward_movement(self, distance_mm=10):
        """
        Test a backward movement.
        
        Args:
            distance_mm: Distance to move in millimeters (will be negative).
            
        Returns:
            bool: True if movement was successful, False otherwise.
        """
        # Ensure distance is negative for backward movement
        distance_mm = -abs(distance_mm)
        return self.test_movement(distance_mm)
    
    def test_movement_sequence(self):
        """
        Test a sequence of movements.
        
        Returns:
            bool: True if all movements were successful, False otherwise.
        """
        print("\n--- Testing Movement Sequence ---")
        
        # Reset position
        if not self.reset_position():
            print("Failed to reset position")
            return False
        
        # Define the movement sequence
        sequence = [
            (10, "short forward"),
            (50, "medium forward"),
            (-30, "medium backward"),
            (100, "long forward"),
            (-100, "long backward"),
            (-30, "final backward to return to zero")
        ]
        
        # Execute each movement
        success = True
        for distance, description in sequence:
            print(f"\nTesting {description} movement: {distance}mm")
            
            if not self.move(distance):
                print(f"Failed to send {description} movement command")
                success = False
                break
                
            if not self.wait_for_completion():
                print(f"{description} movement did not complete")
                success = False
                break
                
            print(f"Successfully completed {description} movement")
            time.sleep(1)  # Pause between movements
        
        # Reset position at the end
        self.reset_position()
        
        if success:
            print("\nAll movements in sequence completed successfully")
        else:
            print("\nMovement sequence test failed")
            
        return success
    
    def run_all_tests(self):
        """Run all GRBL interface tests sequentially."""
        print("\n=== Starting GRBL Interface Test Sequence ===")
        
        # Test communication first
        if not self.test_communication():
            print("Communication test failed, aborting remaining tests")
            return False
        
        # Test position reset
        self.test_position_reset()
        
        # Test individual movements
        self.test_movement(10)
        self.test_backward_movement(10)
        
        # Test movement sequence
        self.test_movement_sequence()
        
        print("\n=== GRBL Interface Test Sequence Complete ===")
        return True


# Simple test script when run directly
if __name__ == "__main__":
    print("VHS Coffeeman GRBL Interface Test Tool")
    print("-------------------------------------")
    
    # Create the tester
    tester = GRBLTester()
    
    # Ask for test mode
    print("\nTest options:")
    print("1: Test GRBL communication")
    print("2: Test position reset")
    print("3: Test forward movement (10mm)")
    print("4: Test backward movement (10mm)")
    print("5: Test movement sequence")
    print("6: Run all tests")
    
    try:
        choice = input("Enter test number (1-6): ")
        choice = int(choice.strip())
        
        if choice == 1:
            tester.test_communication()
        elif choice == 2:
            tester.test_position_reset()
        elif choice == 3:
            tester.test_movement(10)
        elif choice == 4:
            tester.test_backward_movement(10)
        elif choice == 5:
            tester.test_movement_sequence()
        elif choice == 6:
            tester.run_all_tests()
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Reset the position before exiting
        try:
            tester.reset_position()
        except:
            pass
        print("Test complete, GRBL position reset")
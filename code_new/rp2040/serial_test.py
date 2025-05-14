"""
serial_test.py - Serial Communication Testing Module for VHS Coffeeman

This module provides testing functionality for verifying serial communication
between the RP2040 and Raspberry Pi. It allows for testing:
- UART initialization
- Sending status messages to the Pi
- Receiving and parsing commands from the Pi
- Testing with sample command formats

The module can operate in two modes:
1. Echo mode - echoes received data back to the sender
2. Test mode - parses and validates received commands

Usage:
    import time
    from serial_test import SerialTester
    
    # Initialize the tester
    tester = SerialTester()
    
    # Run echo test to verify basic communication
    tester.run_echo_test(duration_sec=30)
    
    # Run command parsing test
    tester.run_command_test(duration_sec=30)
"""

import time
from machine import Pin, UART
from config import pins, constants, commands

class SerialTester:
    """Provides testing functionality for serial communication."""
    
    def __init__(self):
        """Initialize the serial tester with UART setup."""
        # Initialize UART for Pi communication
        self.uart = UART(1,
                         baudrate=constants.PI_BAUDRATE,
                         tx=Pin(pins.PI_UART_TX),
                         rx=Pin(pins.PI_UART_RX))
        self.uart.init(bits=8, parity=None, stop=1)
        
        # Buffer for incoming data
        self.buffer = ""
        
        print(f"Serial Tester initialized (UART1, {constants.PI_BAUDRATE} baud)")
        print(f"TX: GPIO {pins.PI_UART_TX}, RX: GPIO {pins.PI_UART_RX}")
    
    def send_message(self, message):
        """
        Send a message to the Raspberry Pi.
        
        Args:
            message: The message to send.
            
        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        try:
            # Add newline to end of message if not present
            if not message.endswith('\n'):
                message += '\n'
                
            # Send the message as bytes
            print(f"Sending: {message.strip()}")
            self.uart.write(message.encode())
            return True
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def read_data(self, timeout_ms=1000):
        """
        Read available data from UART.
        
        Args:
            timeout_ms: Maximum time to wait for data in milliseconds.
            
        Returns:
            str or None: The data read, or None if no data is available.
        """
        start_time = time.ticks_ms()
        
        # Wait for data with timeout
        while self.uart.any() == 0:
            time.sleep_ms(10)
            if time.ticks_ms() - start_time > timeout_ms:
                return None
        
        # Read available data
        data = self.uart.read()
        if data:
            try:
                return data.decode('utf-8')
            except UnicodeError:
                print("Error decoding data")
                return None
        
        return None
    
    def process_buffer(self):
        """
        Process the buffer for complete commands.
        
        Returns:
            str or None: A complete command if available, None otherwise.
        """
        if '\n' in self.buffer:
            # Split the buffer at the first newline
            command, self.buffer = self.buffer.split('\n', 1)
            return command.strip()
        
        return None
    
    def parse_command(self, command_str):
        """
        Parse a command string and validate its format.
        
        Args:
            command_str: The command string to parse.
            
        Returns:
            dict or None: A parsed command object if valid, None otherwise.
        """
        try:
            print(f"Parsing: {command_str}")
            
            # Handle simple commands
            if command_str == commands.START_POUR:
                print("Valid START_POUR command")
                return {'type': commands.START_POUR}
                
            elif command_str == commands.STOP:
                print("Valid STOP command")
                return {'type': commands.STOP}
            
            # Handle complex commands (with ':' separator)
            if ':' in command_str:
                parts = command_str.split(':', 1)
                command_type = parts[0]
                
                if command_type == commands.RECIPE:
                    # Validate recipe format
                    recipe_parts = parts[1].split(',')
                    if len(recipe_parts) < 2:
                        print("Invalid recipe format: missing ingredients")
                        return None
                    
                    # Check recipe ID
                    recipe_id = recipe_parts[0]
                    
                    # Validate at least one ingredient
                    valid_ingredients = 0
                    for i in range(1, len(recipe_parts)):
                        if ':' in recipe_parts[i]:
                            pump_str, amount_str = recipe_parts[i].split(':', 1)
                            try:
                                pump_index = int(pump_str)
                                amount_oz = float(amount_str)
                                valid_ingredients += 1
                            except ValueError:
                                print(f"Invalid pump or amount: {recipe_parts[i]}")
                        else:
                            print(f"Malformed ingredient: {recipe_parts[i]}")
                    
                    if valid_ingredients > 0:
                        print(f"Valid RECIPE command: ID={recipe_id}, {valid_ingredients} ingredients")
                        return {'type': commands.RECIPE, 'valid': True}
                    else:
                        print("Invalid RECIPE command: no valid ingredients")
                        return None
                
                elif command_type == commands.MAINTENANCE:
                    maint_action = parts[1]
                    
                    # Validate maintenance action
                    if maint_action in [commands.PRIME_ALL, commands.CLEAN_ALL]:
                        print(f"Valid MAINTENANCE command: {maint_action}")
                        return {'type': commands.MAINTENANCE, 'action': maint_action}
                    
                    # Check for pump-specific maintenance
                    if maint_action.startswith(commands.PUMP + ':'):
                        pump_parts = maint_action.split(':')
                        if len(pump_parts) == 4:  # PUMP:NUM:DIRECTION:AMOUNT
                            try:
                                pump_index = int(pump_parts[1])
                                direction = pump_parts[2]
                                amount = float(pump_parts[3])
                                
                                if direction in [commands.FORWARD, commands.BACKWARD]:
                                    print(f"Valid PUMP maintenance command: pump {pump_index}, {direction}, {amount}")
                                    return {'type': commands.MAINTENANCE, 'action': commands.PUMP}
                                else:
                                    print(f"Invalid direction: {direction}")
                            except ValueError:
                                print(f"Invalid pump index or amount")
                        else:
                            print(f"Malformed pump maintenance command")
                    
                    print(f"Invalid maintenance action: {maint_action}")
                    return None
                
                else:
                    print(f"Unknown command type: {command_type}")
                    return None
            
            else:
                print(f"Malformed command: {command_str}")
                return None
                
        except Exception as e:
            print(f"Error parsing command: {e}")
            return None
    
    def run_echo_test(self, duration_sec=30):
        """
        Run an echo test for the specified duration.
        
        Echo test simply reads any data received and echoes it back,
        allowing basic UART communication to be verified.
        
        Args:
            duration_sec: Duration to run the test in seconds.
        """
        print(f"\n--- Starting Echo Test (duration: {duration_sec} seconds) ---")
        print("Any data received will be echoed back")
        print("Use serial terminal on Raspberry Pi to send test messages")
        
        end_time = time.time() + duration_sec
        
        # Clear buffer
        self.buffer = ""
        
        while time.time() < end_time:
            # Read available data
            data = self.read_data(timeout_ms=100)
            
            if data:
                print(f"Received: {data}")
                
                # Echo back
                self.send_message(f"ECHO: {data}")
            
            # Small delay
            time.sleep_ms(10)
        
        print("Echo test complete")
    
    def run_command_test(self, duration_sec=30):
        """
        Run a command parsing test for the specified duration.
        
        This test reads data, assembles complete commands, and validates them.
        It sends appropriate responses based on command parsing results.
        
        Args:
            duration_sec: Duration to run the test in seconds.
        """
        print(f"\n--- Starting Command Test (duration: {duration_sec} seconds) ---")
        print("Parsing commands and sending responses")
        print("Use serial terminal on Raspberry Pi to send test commands:")
        print("  - RECIPE:12345,0:1.5,3:1.0")
        print("  - START_POUR")
        print("  - STOP")
        print("  - MAINTENANCE:PRIME_ALL")
        print("  - MAINTENANCE:PUMP:3:FORWARD:100")
        
        end_time = time.time() + duration_sec
        
        # Clear buffer
        self.buffer = ""
        
        while time.time() < end_time:
            # Read available data
            data = self.read_data(timeout_ms=100)
            
            if data:
                # Add to buffer
                self.buffer += data
                
                # Check for complete command
                command_str = self.process_buffer()
                if command_str:
                    # Parse the command
                    parsed = self.parse_command(command_str)
                    
                    if parsed:
                        # Send appropriate response based on command type
                        if parsed['type'] == commands.RECIPE:
                            self.send_message(commands.READY)
                        elif parsed['type'] == commands.START_POUR:
                            self.send_message(commands.POURING)
                            time.sleep(1)
                            self.send_message(commands.COMPLETE)
                        elif parsed['type'] == commands.STOP:
                            self.send_message(commands.READY)
                        elif parsed['type'] == commands.MAINTENANCE:
                            self.send_message(commands.READY)
                    else:
                        # Send error for invalid command
                        self.send_message(f"{commands.ERROR}:Invalid command format")
            
            # Small delay
            time.sleep_ms(10)
        
        print("Command test complete")
    
    def send_status_sequence(self):
        """
        Send a sequence of status messages to test Pi reception.
        
        This can be used to verify the Pi can receive and parse status messages.
        """
        print("\n--- Sending Status Message Sequence ---")
        
        # Send all status message types
        self.send_message(commands.READY)
        time.sleep(1)
        
        self.send_message(commands.POURING)
        time.sleep(1)
        
        self.send_message(f"{commands.POURING}:1")
        time.sleep(1)
        
        self.send_message(commands.COMPLETE)
        time.sleep(1)
        
        self.send_message(f"{commands.ERROR}:Test error message")
        
        print("Status sequence complete")


# Simple test script when run directly
if __name__ == "__main__":
    print("VHS Coffeeman Serial Communication Test Tool")
    print("------------------------------------------")
    
    # Create the tester
    tester = SerialTester()
    
    # Ask for test mode
    print("\nTest options:")
    print("1: Run echo test")
    print("2: Run command parsing test")
    print("3: Send status message sequence")
    
    try:
        choice = input("Enter test number (1-3): ")
        choice = int(choice.strip())
        
        if choice == 1:
            duration = int(input("Enter test duration in seconds: "))
            tester.run_echo_test(duration)
        elif choice == 2:
            duration = int(input("Enter test duration in seconds: "))
            tester.run_command_test(duration)
        elif choice == 3:
            tester.send_status_sequence()
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        print("Test complete")
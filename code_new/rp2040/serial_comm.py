"""
serial_comm.py - Serial Communication Module for VHS Coffeeman

This module handles serial communication between the RP2040 and Raspberry Pi for the
VHS Coffeeman system. It provides classes for parsing incoming commands and sending
status messages back to the Pi.

Classes:
    SerialCommands: Enumeration of valid commands and responses
    SerialCommunication: Manages serial communication with the Raspberry Pi

The SerialCommunication class is responsible for:
    - Initializing the serial connection to the Raspberry Pi
    - Checking for incoming commands in a non-blocking way
    - Parsing raw serial data into structured command objects
    - Sending formatted status messages back to the Raspberry Pi
    - Parsing recipe commands into a usable format
    - Parsing maintenance commands into a usable format

Usage:
    from serial_comm import SerialCommunication, SerialCommands
    
    # Initialize the serial connection
    serial = SerialCommunication()
    
    # Check for incoming commands
    command = serial.check_for_command()
    if command:
        command_type = command.get('type')
        if command_type == SerialCommands.RECIPE:
            recipe_id = command.get('id')
            ingredients = command.get('ingredients')
            # Process recipe...
        elif command_type == SerialCommands.START_POUR:
            # Start pouring...
    
    # Send a status message
    serial.send_status(SerialCommands.READY)
    serial.send_status(SerialCommands.ERROR, "Pump failure")

Command Format:
    - Recipe: RECIPE:ID,PUMP:AMOUNT,PUMP:AMOUNT,...
    - Control: START_POUR, STOP
    - Maintenance: MAINTENANCE:ACTION, MAINTENANCE:PUMP:NUM:DIRECTION:AMOUNT

Response Format:
    - Status: READY, POURING, COMPLETE
    - Error: ERROR:message

Validation is included for all incoming commands, with proper error handling for
malformed commands.

This module depends on:
    - config.py for serial communication settings
"""

import time
from machine import Pin, UART
from config import pins, constants, commands

class SerialCommunication:
    """Manages serial communication with the Raspberry Pi."""
    
    def __init__(self):
        """Initialize the serial connection to the Raspberry Pi."""
        # Initialize UART for Pi communication
        self.uart = UART(1,
                         baudrate=constants.PI_BAUDRATE,
                         tx=Pin(pins.PI_UART_TX),
                         rx=Pin(pins.PI_UART_RX))
        self.uart.init(bits=8, parity=None, stop=1)
        
        # Buffer for incoming data
        self.buffer = ""
    
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
            self.uart.write(message.encode())
            return True
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def send_status(self, status_type, message=None):
        """
        Send a status message to the Raspberry Pi.
        
        Args:
            status_type: The type of status message (e.g., READY, POURING, etc.).
            message: An optional message to include with the status.
            
        Returns:
            bool: True if the status was sent successfully, False otherwise.
        """
        if message:
            status = f"{status_type}:{message}"
        else:
            status = status_type
            
        print(f"Sending status: {status}")
        return self.send_message(status)
    
    def check_for_command(self):
        """
        Check for incoming commands from the Raspberry Pi.
        
        This method is non-blocking and should be called regularly in the main loop.
        
        Returns:
            dict or None: A parsed command object if a complete command is available,
                          None otherwise.
        """
        # Check if data is available
        if self.uart.any():
            # Read available data
            data = self.uart.read()
            if data:
                # Decode and add to buffer
                try:
                    text = data.decode('utf-8')
                    self.buffer += text
                except UnicodeError:
                    print("Error decoding serial data")
        
        # Check for complete commands in buffer
        if '\n' in self.buffer:
            # Split the buffer at the first newline
            command_str, self.buffer = self.buffer.split('\n', 1)
            
            # Strip whitespace
            command_str = command_str.strip()
            
            # If there's a command, parse it
            if command_str:
                return self.parse_command(command_str)
        
        # No complete command available
        return None
    
    def parse_command(self, command_str):
        """
        Parse a command string into a structured command object.
        
        Args:
            command_str: The command string to parse.
            
        Returns:
            dict or None: A parsed command object if parsing is successful,
                          None otherwise.
        """
        try:
            print(f"Parsing command: {command_str}")
            
            # Handle simple commands
            if command_str == commands.START_POUR:
                return {'type': commands.START_POUR}
            elif command_str == commands.STOP:
                return {'type': commands.STOP}
            
            # Handle complex commands (with ':' separator)
            if ':' in command_str:
                parts = command_str.split(':', 1)
                command_type = parts[0]
                
                if command_type == commands.RECIPE:
                    return self.parse_recipe_command(parts[1])
                elif command_type == commands.MAINTENANCE:
                    return self.parse_maintenance_command(parts[1])
                else:
                    print(f"Unknown command type: {command_type}")
            else:
                print(f"Malformed command: {command_str}")
            
            return None
            
        except Exception as e:
            print(f"Error parsing command: {e}")
            return None
    
    def parse_recipe_command(self, recipe_str):
        """
        Parse a recipe command string into a structured recipe object.
        
        Format: RECIPE:ID,PUMP:AMOUNT,PUMP:AMOUNT,...
        
        Args:
            recipe_str: The recipe string to parse.
            
        Returns:
            dict or None: A parsed recipe object if parsing is successful,
                          None otherwise.
        """
        try:
            # Split the recipe string by commas
            parts = recipe_str.split(',')
            
            # The first part should be the recipe ID
            recipe_id = parts[0]
            
            # The remaining parts are pump:amount pairs
            ingredients = []
            for i in range(1, len(parts)):
                if ':' in parts[i]:
                    pump_str, amount_str = parts[i].split(':', 1)
                    try:
                        pump_index = int(pump_str)
                        amount_oz = float(amount_str)
                        ingredients.append((pump_index, amount_oz))
                    except ValueError:
                        print(f"Invalid pump or amount: {parts[i]}")
                else:
                    print(f"Malformed ingredient: {parts[i]}")
            
            return {
                'type': commands.RECIPE,
                'id': recipe_id,
                'ingredients': ingredients
            }
            
        except Exception as e:
            print(f"Error parsing recipe command: {e}")
            return None
    
    def parse_maintenance_command(self, maintenance_str):
        """
        Parse a maintenance command string into a structured maintenance object.
        
        Formats:
            - MAINTENANCE:ACTION
            - MAINTENANCE:PUMP:NUM:DIRECTION:AMOUNT
        
        Args:
            maintenance_str: The maintenance string to parse.
            
        Returns:
            dict or None: A parsed maintenance object if parsing is successful,
                          None otherwise.
        """
        try:
            # Check for simple maintenance actions
            if maintenance_str == commands.PRIME_ALL:
                return {
                    'type': commands.MAINTENANCE,
                    'action': commands.PRIME_ALL
                }
            elif maintenance_str == commands.CLEAN_ALL:
                return {
                    'type': commands.MAINTENANCE,
                    'action': commands.CLEAN_ALL
                }
            
            # Check for pump-specific maintenance actions
            if maintenance_str.startswith(commands.PUMP + ':'):
                # Format: PUMP:NUM:DIRECTION:AMOUNT
                parts = maintenance_str.split(':')
                if len(parts) == 4:
                    try:
                        pump_index = int(parts[1])
                        direction = parts[2]  # FORWARD or BACKWARD
                        amount = float(parts[3])
                        
                        return {
                            'type': commands.MAINTENANCE,
                            'action': commands.PUMP,
                            'pump_index': pump_index,
                            'direction': direction,
                            'amount': amount
                        }
                    except ValueError:
                        print(f"Invalid pump index or amount: {maintenance_str}")
                else:
                    print(f"Malformed pump maintenance command: {maintenance_str}")
            
            print(f"Unknown maintenance command: {maintenance_str}")
            return None
            
        except Exception as e:
            print(f"Error parsing maintenance command: {e}")
            return None
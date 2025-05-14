"""
state_machine.py - State Machine Module for VHS Coffeeman

This module implements the system's state management for the VHS Coffeeman system.
It provides a class for managing the system's state and handling transitions between states.

Classes:
    StateMachine: Manages the system's state and processes commands

The StateMachine class is responsible for:
    - Maintaining the current system state
    - Processing commands based on the current state
    - Handling transitions between states
    - Managing error conditions and recovery

States:
    - INITIALIZING: System is starting up
    - READY: System is waiting for commands
    - RECIPE_LOADED: A recipe has been loaded and is ready to pour
    - POURING: System is actively dispensing a drink
    - MAINTENANCE: System is performing maintenance operations
    - ERROR: An error has occurred and the system is in a recovery state

Usage:
    from state_machine import StateMachine
    from pump_controller import PumpController
    from vcr_controller import VCRController
    from serial_comm import SerialCommunication
    from recipe import Recipe
    from maintenance import Maintenance

    # Initialize all components
    pump_controller = PumpController()
    vcr_controller = VCRController()
    serial = SerialCommunication()
    maintenance = Maintenance(pump_controller)

    # Initialize the state machine
    state_machine = StateMachine(
        pump_controller=pump_controller,
        vcr_controller=vcr_controller,
        serial=serial,
        maintenance=maintenance
    )

    # Enable debug mode for detailed logging
    state_machine.debug = True

    # Process a command
    command = serial.check_for_command()
    if command:
        state_machine.handle_command(command)

The state machine ensures that commands are only processed when in the appropriate state.
For example, START_POUR is only valid when in the RECIPE_LOADED state.

Error handling is included to detect and recover from error conditions, with appropriate
state transitions and status messages.

This module depends on:
    - config.py for state definitions
    - pump_controller.py for dispensing operations
    - vcr_controller.py for VCR control
    - serial_comm.py for communication with the Raspberry Pi
    - recipe.py for recipe management
    - maintenance.py for maintenance operations
"""

import time
from config import states, commands
from recipe import Recipe

class StateMachine:
    """Manages the system's state and processes commands."""

    def __init__(self, pump_controller, vcr_controller, serial, maintenance, debug=False):
        """
        Initialize the state machine with all required components.

        Args:
            pump_controller: A PumpController instance.
            vcr_controller: A VCRController instance.
            serial: A SerialCommunication instance.
            maintenance: A Maintenance instance.
            debug: Enable detailed debug logging.
        """
        # Store component references
        self.pump_controller = pump_controller
        self.vcr_controller = vcr_controller
        self.serial = serial
        self.maintenance = maintenance

        # Debug flag for detailed logging
        self.debug = debug

        # Initialize state
        self.state = states.INITIALIZING

        # Initialize recipe
        self.current_recipe = None

        # Track state history for debugging
        self.state_history = [states.INITIALIZING]

        # Set system to READY state after initialization
        self.transition_to(states.READY)

        if self.debug:
            self.debug_log("State machine initialized with debug logging enabled")

    def debug_log(self, message):
        """
        Log a debug message if debug mode is enabled.

        Args:
            message: The message to log.
        """
        if self.debug:
            print(f"[STATE MACHINE DEBUG] {message}")

    def transition_to(self, new_state):
        """
        Transition to a new state and report the change.

        Args:
            new_state: The new state to transition to.

        Returns:
            bool: True if the transition was successful, False otherwise.
        """
        try:
            old_state = self.state
            self.state = new_state

            # Add to state history
            self.state_history.append(new_state)
            if len(self.state_history) > 10:
                self.state_history.pop(0)  # Keep history manageable

            # Standard logging
            print(f"State transition: {old_state} -> {new_state}")

            # Detailed debug logging
            if self.debug:
                self.debug_log(f"STATE TRANSITION: {old_state} -> {new_state}")
                self.debug_log(f"State history: {' -> '.join(self.state_history)}")

            # Send status update based on new state
            if new_state == states.READY:
                self.debug_log("Sending READY status to Pi")
                self.serial.send_status(commands.READY)
            elif new_state == states.POURING:
                self.debug_log("Sending POURING status to Pi")
                self.serial.send_status(commands.POURING)
            elif new_state == states.ERROR:
                self.debug_log("Sending ERROR status to Pi")
                self.serial.send_status(commands.ERROR, "System in error state")

            return True

        except Exception as e:
            print(f"Error transitioning to state {new_state}: {e}")
            if self.debug:
                self.debug_log(f"TRANSITION ERROR: Failed to transition from {old_state} to {new_state}")
                self.debug_log(f"Error details: {str(e)}")

            # Make sure we're in an error state if there was a problem
            self.state = states.ERROR
            self.serial.send_status(commands.ERROR, str(e))
            return False

    def handle_command(self, command):
        """
        Process a command based on the current state.

        Args:
            command: A parsed command object.

        Returns:
            bool: True if the command was handled successfully, False otherwise.
        """
        try:
            command_type = command.get('type')

            # Standard logging
            print(f"Handling command in state {self.state}: {command}")

            # Debug logging
            if self.debug:
                self.debug_log(f"COMMAND RECEIVED: {command_type} in state {self.state}")
                self.debug_log(f"Full command: {command}")

            # Process command based on current state
            if self.state == states.READY:
                if self.debug:
                    self.debug_log(f"Processing {command_type} command in READY state")
                return self.handle_command_in_ready_state(command, command_type)

            elif self.state == states.RECIPE_LOADED:
                if self.debug:
                    self.debug_log(f"Processing {command_type} command in RECIPE_LOADED state")
                return self.handle_command_in_recipe_loaded_state(command, command_type)

            elif self.state == states.POURING:
                if self.debug:
                    self.debug_log(f"Processing {command_type} command in POURING state")
                return self.handle_command_in_pouring_state(command, command_type)

            elif self.state == states.MAINTENANCE:
                if self.debug:
                    self.debug_log(f"Processing {command_type} command in MAINTENANCE state")
                return self.handle_command_in_maintenance_state(command, command_type)

            elif self.state == states.ERROR:
                # In error state, only accept reset commands
                if self.debug:
                    self.debug_log(f"Processing {command_type} command in ERROR state")

                if command_type == commands.STOP:
                    self.debug_log("STOP command received in ERROR state - attempting system reset")
                    return self.reset_system()
                else:
                    if self.debug:
                        self.debug_log(f"Command {command_type} not allowed in ERROR state")
                    print(f"Command {command_type} not allowed in ERROR state")
                    self.serial.send_status(commands.ERROR, "System in error state, use STOP to reset")
                    return False

            else:
                if self.debug:
                    self.debug_log(f"INVALID STATE: {self.state}")
                print(f"Unknown state: {self.state}")
                self.transition_to(states.ERROR)
                return False

        except Exception as e:
            print(f"Error handling command: {e}")
            if self.debug:
                self.debug_log(f"COMMAND HANDLING ERROR: {str(e)}")
            self.transition_to(states.ERROR)
            self.serial.send_status(commands.ERROR, str(e))
            return False

    def handle_command_in_ready_state(self, command, command_type):
        """
        Handle commands in the READY state.

        Args:
            command: The full command object.
            command_type: The type of command.

        Returns:
            bool: True if the command was handled successfully, False otherwise.
        """
        if command_type == commands.RECIPE:
            if self.debug:
                self.debug_log("Received RECIPE command in READY state")

            # Create a recipe from the command
            if self.debug:
                self.debug_log("Creating recipe from command")
            recipe = Recipe.from_command(command)

            if recipe:
                if self.debug:
                    self.debug_log(f"Valid recipe created with ID: {recipe.id}")
                    self.debug_log(f"Recipe contains {len(recipe.ingredients)} ingredients")

                self.current_recipe = recipe
                self.transition_to(states.RECIPE_LOADED)
                return True
            else:
                if self.debug:
                    self.debug_log("Failed to create valid recipe from command")
                self.serial.send_status(commands.ERROR, "Invalid recipe")
                return False

        elif command_type == commands.MAINTENANCE:
            if self.debug:
                self.debug_log("Received MAINTENANCE command in READY state")
                self.debug_log("Transitioning to MAINTENANCE state")

            # Transition to maintenance state
            self.transition_to(states.MAINTENANCE)

            # Execute the maintenance command
            if self.debug:
                action = command.get('action', 'unknown')
                self.debug_log(f"Executing maintenance action: {action}")

            success = self.maintenance.execute_command(command)

            if self.debug:
                result = "successful" if success else "failed"
                self.debug_log(f"Maintenance execution {result}")
                self.debug_log("Transitioning back to READY state")

            # Transition back to ready state
            self.transition_to(states.READY)
            return success

        else:
            if self.debug:
                self.debug_log(f"Command {command_type} not allowed in READY state")
            print(f"Command {command_type} not allowed in READY state")
            return False

    def handle_command_in_recipe_loaded_state(self, command, command_type):
        """
        Handle commands in the RECIPE_LOADED state.

        Args:
            command: The full command object.
            command_type: The type of command.

        Returns:
            bool: True if the command was handled successfully, False otherwise.
        """
        if command_type == commands.START_POUR:
            if self.debug:
                self.debug_log("Received START_POUR command in RECIPE_LOADED state")
                self.debug_log("Beginning drink dispensing sequence")

            # Transition to pouring state
            self.transition_to(states.POURING)

            # Trigger VCR play
            if self.debug:
                self.debug_log("Triggering VCR play button")
            self.vcr_controller.play()

            # Wait a moment for the VCR to start playing
            if self.debug:
                self.debug_log("Waiting for VCR to start playing (1 second delay)")
            time.sleep(1)

            # Execute the recipe
            if self.debug:
                self.debug_log("Executing recipe (dispensing ingredients)")
            success = self.current_recipe.execute(self.pump_controller)

            # Handle completion
            if success:
                if self.debug:
                    self.debug_log("Recipe execution completed successfully")
                    self.debug_log("Sending COMPLETE status to Pi")
                self.serial.send_status(commands.COMPLETE)

                # Trigger VCR eject
                if self.debug:
                    self.debug_log("Triggering VCR eject button")
                self.vcr_controller.eject()
            else:
                if self.debug:
                    self.debug_log("Recipe execution failed")
                self.serial.send_status(commands.ERROR, "Failed to execute recipe")
                self.transition_to(states.ERROR)
                return False

            # Reset the system
            if self.debug:
                self.debug_log("Clearing current recipe")
                self.debug_log("Transitioning back to READY state")
            self.current_recipe = None
            self.transition_to(states.READY)
            return True

        elif command_type == commands.STOP:
            if self.debug:
                self.debug_log("Received STOP command in RECIPE_LOADED state")
                self.debug_log("Abandoning loaded recipe")

            # Reset the system
            self.current_recipe = None
            self.transition_to(states.READY)
            return True

        elif command_type == commands.RECIPE:
            if self.debug:
                self.debug_log("Received RECIPE command in RECIPE_LOADED state")
                self.debug_log("Updating currently loaded recipe")

            # Update the recipe
            recipe = Recipe.from_command(command)
            if recipe:
                if self.debug:
                    self.debug_log(f"Valid recipe update with ID: {recipe.id}")
                    self.debug_log(f"Updated recipe contains {len(recipe.ingredients)} ingredients")
                self.current_recipe = recipe
                return True
            else:
                if self.debug:
                    self.debug_log("Failed to create valid recipe from update command")
                self.serial.send_status(commands.ERROR, "Invalid recipe")
                return False

        else:
            if self.debug:
                self.debug_log(f"Command {command_type} not allowed in RECIPE_LOADED state")
            print(f"Command {command_type} not allowed in RECIPE_LOADED state")
            return False

    def handle_command_in_pouring_state(self, command, command_type):
        """
        Handle commands in the POURING state.

        Args:
            command: The full command object.
            command_type: The type of command.

        Returns:
            bool: True if the command was handled successfully, False otherwise.
        """
        if command_type == commands.STOP:
            if self.debug:
                self.debug_log("Received STOP command in POURING state")
                self.debug_log("Stopping all pumps immediately")

            # Stop all pumps
            self.pump_controller.disable_all()

            # Reset the system
            if self.debug:
                self.debug_log("Clearing current recipe")
                self.debug_log("Transitioning back to READY state")
            self.current_recipe = None
            self.transition_to(states.READY)
            return True

        else:
            if self.debug:
                self.debug_log(f"Command {command_type} not allowed in POURING state")
            print(f"Command {command_type} not allowed in POURING state")
            return False

    def handle_command_in_maintenance_state(self, command, command_type):
        """
        Handle commands in the MAINTENANCE state.

        Args:
            command: The full command object.
            command_type: The type of command.

        Returns:
            bool: True if the command was handled successfully, False otherwise.
        """
        if command_type == commands.MAINTENANCE:
            if self.debug:
                action = command.get('action', 'unknown')
                self.debug_log(f"Received MAINTENANCE command in MAINTENANCE state: {action}")

            # Execute the maintenance command
            success = self.maintenance.execute_command(command)

            if self.debug:
                result = "successful" if success else "failed"
                self.debug_log(f"Maintenance execution {result}")

            return success

        elif command_type == commands.STOP:
            if self.debug:
                self.debug_log("Received STOP command in MAINTENANCE state")
                self.debug_log("Stopping all pumps")

            # Stop all pumps
            self.pump_controller.disable_all()

            # Transition to ready state
            if self.debug:
                self.debug_log("Transitioning back to READY state")
            self.transition_to(states.READY)
            return True

        else:
            if self.debug:
                self.debug_log(f"Command {command_type} not allowed in MAINTENANCE state")
            print(f"Command {command_type} not allowed in MAINTENANCE state")
            return False

    def reset_system(self):
        """
        Reset the system to a known good state.

        Returns:
            bool: True if the system was reset successfully, False otherwise.
        """
        try:
            print("Resetting system")
            if self.debug:
                self.debug_log("SYSTEM RESET initiated")

            # Stop all pumps
            if self.debug:
                self.debug_log("Disabling all pumps")
            self.pump_controller.disable_all()

            # Clear current recipe
            if self.debug:
                self.debug_log("Clearing current recipe")
            self.current_recipe = None

            # Transition to ready state
            if self.debug:
                self.debug_log("Transitioning to READY state")
            self.transition_to(states.READY)

            if self.debug:
                self.debug_log("System reset completed successfully")
            return True

        except Exception as e:
            print(f"Error resetting system: {e}")
            if self.debug:
                self.debug_log(f"SYSTEM RESET ERROR: {str(e)}")
            self.serial.send_status(commands.ERROR, str(e))
            return False

    def dump_state(self):
        """
        Dump the current state information for debugging.

        Returns:
            str: A string representation of the current state.
        """
        info = [
            f"Current State: {self.state}",
            f"State History: {' -> '.join(self.state_history)}",
            f"Current Recipe: {'Set' if self.current_recipe else 'None'}",
        ]

        if self.current_recipe:
            info.append(f"  Recipe ID: {self.current_recipe.id}")
            info.append(f"  Ingredients: {len(self.current_recipe.ingredients)}")

        return "\n".join(info)
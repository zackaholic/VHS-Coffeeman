"""
state_machine.py - State Machine Module for VHS Coffeeman (Raspberry Pi)

This module implements the system's state management for the VHS Coffeeman system
running on Raspberry Pi. It provides event-driven state management with hardware
abstraction.

Classes:
    StateMachine: Manages the system's state and processes hardware events

The StateMachine class is responsible for:
    - Maintaining the current system state
    - Processing hardware events and state transitions
    - Coordinating hardware operations through HardwareManager
    - Managing the complete drink dispensing workflow
    - Handling error conditions and recovery

States:
    - IDLE: System is waiting for RFID tag insertion
    - RECIPE_LOADED: A recipe has been loaded from RFID tag
    - WAITING_FOR_CUP: Recipe loaded, waiting for cup to be placed
    - POURING: System is actively dispensing a drink
    - POURING_COMPLETE: Dispensing finished, tape ejected
    - DRINK_READY: Drink complete, waiting for cup removal
    - ERROR: An error has occurred and the system is in recovery state

Events:
    - RFID_DETECTED: RFID tag has been detected
    - CUP_PLACED: Cup has been placed and detected
    - CUP_REMOVED: Cup has been removed
    - POUR_COMPLETE: Drink dispensing has completed
    - STOP: Emergency stop or reset command

Usage:
    from core.state_machine import StateMachine
    from core.hardware_manager import HardwareManager
    
    hardware = HardwareManager()
    state_machine = StateMachine(hardware)
    state_machine.start()
"""

import time
import threading
from enum import Enum
from typing import Dict, Any, Optional
from utils.logger import get_logger
from core.hardware_manager import HardwareManager

logger = get_logger(__name__)


class States(Enum):
    """System states for the VHS Coffeeman."""
    IDLE = "IDLE"
    RECIPE_LOADED = "RECIPE_LOADED"
    WAITING_FOR_CUP = "WAITING_FOR_CUP"
    POURING = "POURING"
    POURING_COMPLETE = "POURING_COMPLETE"
    DRINK_READY = "DRINK_READY"
    ERROR = "ERROR"


class Events(Enum):
    """Events that can trigger state transitions."""
    RFID_DETECTED = "RFID_DETECTED"
    CUP_PLACED = "CUP_PLACED"
    CUP_REMOVED = "CUP_REMOVED"
    POUR_COMPLETE = "POUR_COMPLETE"
    STOP = "STOP"


class StateMachine:
    """Manages the system's state and processes hardware events."""
    
    def __init__(self, hardware_manager: HardwareManager, debug: bool = False):
        """
        Initialize the state machine with hardware manager.
        
        Args:
            hardware_manager: HardwareManager instance for hardware control
            debug: Enable detailed debug logging
        """
        self.hardware = hardware_manager
        self.debug = debug
        
        # Initialize state
        self.state = States.IDLE
        self.previous_state = None
        
        # Recipe management
        self.current_recipe: Optional[Dict[str, Any]] = None
        self.current_tag_id: Optional[str] = None
        
        # State history for debugging
        self.state_history = [States.IDLE]
        
        # Media playback tracking
        self.media_playing = False
        
        # Setup hardware event callbacks
        self._setup_hardware_callbacks()
        
        # Initialize LED state
        self.hardware.set_led_attractor()
        
        logger.info("State machine initialized")
        if self.debug:
            self._debug_log("State machine initialized with debug logging enabled")
    
    def _debug_log(self, message: str):
        """Log a debug message if debug mode is enabled."""
        if self.debug:
            logger.debug(f"[STATE MACHINE] {message}")
    
    def _setup_hardware_callbacks(self):
        """Setup callbacks for hardware events."""
        self.hardware.set_rfid_callback(self._on_rfid_detected)
        self.hardware.set_cup_placed_callback(self._on_cup_placed)
        self.hardware.set_cup_removed_callback(self._on_cup_removed)
        self.hardware.set_pour_complete_callback(self._on_pour_complete)
        
        self._debug_log("Hardware callbacks configured")
    
    def start(self):
        """Start the state machine and hardware monitoring."""
        logger.info("Starting state machine")
        self.hardware.start_monitoring()
        self._debug_log("State machine started")
    
    def stop(self):
        """Stop the state machine and hardware monitoring."""
        logger.info("Stopping state machine")
        self.hardware.stop_monitoring()
        self._debug_log("State machine stopped")
    
    def _transition_to(self, new_state: States):
        """
        Transition to a new state and handle state-specific actions.
        
        Args:
            new_state: The new state to transition to
        """
        try:
            old_state = self.state
            self.previous_state = old_state
            self.state = new_state
            
            # Add to state history
            self.state_history.append(new_state)
            if len(self.state_history) > 10:
                self.state_history.pop(0)  # Keep history manageable
            
            logger.info(f"State transition: {old_state.value} -> {new_state.value}")
            
            if self.debug:
                self._debug_log(f"STATE TRANSITION: {old_state.value} -> {new_state.value}")
                self._debug_log(f"State history: {' -> '.join([s.value for s in self.state_history])}")
            
            # Handle state entry actions
            self._handle_state_entry(new_state, old_state)
            
        except Exception as e:
            logger.error(f"Error transitioning to state {new_state.value}: {e}")
            self._transition_to(States.ERROR)
    
    def _handle_state_entry(self, new_state: States, old_state: States):
        """Handle actions when entering a new state."""
        try:
            if new_state == States.IDLE:
                self._enter_idle_state()
            elif new_state == States.RECIPE_LOADED:
                self._enter_recipe_loaded_state()
            elif new_state == States.WAITING_FOR_CUP:
                self._enter_waiting_for_cup_state()
            elif new_state == States.POURING:
                self._enter_pouring_state()
            elif new_state == States.POURING_COMPLETE:
                self._enter_pouring_complete_state()
            elif new_state == States.DRINK_READY:
                self._enter_drink_ready_state()
            elif new_state == States.ERROR:
                self._enter_error_state(old_state)
                
        except Exception as e:
            logger.error(f"Error in state entry for {new_state.value}: {e}")
            if new_state != States.ERROR:
                self._transition_to(States.ERROR)
    
    def _enter_idle_state(self):
        """Actions when entering IDLE state."""
        self._debug_log("Entering IDLE state")
        
        # Clear recipe data
        self.current_recipe = None
        self.current_tag_id = None
        self.media_playing = False
        
        # Set attractor LEDs
        self.hardware.set_led_attractor()
        
        logger.info("System ready - waiting for RFID tag")
    
    def _enter_recipe_loaded_state(self):
        """Actions when entering RECIPE_LOADED state."""
        self._debug_log("Entering RECIPE_LOADED state")
        
        logger.info(f"Recipe loaded: {self.current_recipe.get('name', 'Unknown')}")
        
        # Check if cup is already present
        if self.hardware.is_cup_present():
            self._debug_log("Cup already present, proceeding to WAITING_FOR_CUP")
            self._transition_to(States.WAITING_FOR_CUP)
        else:
            # Transition to waiting for cup
            self._transition_to(States.WAITING_FOR_CUP)
    
    def _enter_waiting_for_cup_state(self):
        """Actions when entering WAITING_FOR_CUP state."""
        self._debug_log("Entering WAITING_FOR_CUP state")
        
        # Set red LEDs to indicate cup needed
        self.hardware.set_led_no_cup()
        
        logger.info("Recipe ready - please place cup to begin")
        
        # If cup is already present, proceed immediately
        if self.hardware.is_cup_present():
            self._debug_log("Cup detected immediately, proceeding to pour")
            self._transition_to(States.POURING)
    
    def _enter_pouring_state(self):
        """Actions when entering POURING state."""
        self._debug_log("Entering POURING state")
        
        # Set white LEDs for pouring
        self.hardware.set_led_pouring()
        
        logger.info("Starting drink dispensing sequence")
        
        # Start media playback (video starts when pouring begins)
        self._start_media_playback()
        
        # Start the pour operation
        success = self.hardware.start_pour(self.current_recipe)
        
        if not success:
            logger.error("Failed to start pour operation")
            self._transition_to(States.ERROR)
    
    def _enter_pouring_complete_state(self):
        """Actions when entering POURING_COMPLETE state."""
        self._debug_log("Entering POURING_COMPLETE state")
        
        # Keep white LEDs on
        self.hardware.set_led_pouring()
        
        logger.info("Drink dispensing completed - ejecting tape")
        
        # Eject the VCR tape
        self.hardware.eject_vcr()
        
        # Transition to drink ready
        self._transition_to(States.DRINK_READY)
    
    def _enter_drink_ready_state(self):
        """Actions when entering DRINK_READY state."""
        self._debug_log("Entering DRINK_READY state")
        
        # Keep white LEDs on until cup is removed
        self.hardware.set_led_pouring()
        
        logger.info("Drink ready - please take your cup")
    
    def _enter_error_state(self, previous_state: States):
        """Actions when entering ERROR state."""
        self._debug_log(f"Entering ERROR state from {previous_state.value}")
        
        # Emergency stop all operations
        self.hardware.stop_pour()
        
        # TODO: Set error LED pattern
        logger.error("System in error state - manual reset required")
    
    def _start_media_playback(self):
        """Start video playback for the current recipe."""
        try:
            self._debug_log("Starting media playback")
            
            if self.current_tag_id:
                success = self.hardware.start_video_for_tag(self.current_tag_id)
                if success:
                    self.media_playing = True
                    logger.info("Media playback started")
                else:
                    logger.warning("Failed to start media playback - continuing without video")
                    self.media_playing = False
            else:
                logger.warning("No tag ID available for media playback")
                self.media_playing = False
            
        except Exception as e:
            logger.error(f"Error starting media playback: {e}")
            self.media_playing = False
            # Media failure doesn't stop drink making
    
    def _load_recipe_from_tag(self, tag_id: str) -> bool:
        """
        Load recipe data based on RFID tag ID.
        
        Args:
            tag_id: The RFID tag identifier
            
        Returns:
            bool: True if recipe loaded successfully, False otherwise
        """
        try:
            self._debug_log(f"Loading recipe for tag: {tag_id}")
            
            # Get recipe from the recipe loader
            recipe_data = self.hardware.get_recipe_by_tag(tag_id)
            
            if not recipe_data:
                logger.error(f"No recipe found for tag: {tag_id}")
                return False
            
            # Validate the recipe
            success = self.hardware.load_recipe(recipe_data)
            
            if success:
                self.current_recipe = recipe_data
                self.current_tag_id = tag_id
                logger.info(f"Recipe loaded successfully: {recipe_data['name']}")
                return True
            else:
                logger.error("Failed to validate recipe")
                return False
                
        except Exception as e:
            logger.error(f"Error loading recipe for tag {tag_id}: {e}")
            return False
    
    # Hardware Event Handlers
    def _on_rfid_detected(self, tag_id: str):
        """Handle RFID tag detection event."""
        self._debug_log(f"RFID event: tag detected {tag_id}")
        
        if self.state == States.IDLE:
            logger.info(f"RFID tag detected: {tag_id}")
            
            # Load the recipe for this tag
            if self._load_recipe_from_tag(tag_id):
                self._transition_to(States.RECIPE_LOADED)
            else:
                logger.error(f"Failed to load recipe for tag: {tag_id}")
                self._transition_to(States.ERROR)
        else:
            self._debug_log(f"RFID detected in {self.state.value} state - ignoring")
    
    def _on_cup_placed(self):
        """Handle cup placed event."""
        self._debug_log("Cup placed event")
        
        if self.state == States.WAITING_FOR_CUP:
            logger.info("Cup detected - ready to pour")
            self._transition_to(States.POURING)
        else:
            self._debug_log(f"Cup placed in {self.state.value} state - noting but not acting")
    
    def _on_cup_removed(self):
        """Handle cup removed event."""
        self._debug_log("Cup removed event")
        
        if self.state == States.POURING:
            # Emergency stop if cup removed during pour
            logger.warning("Cup removed during pour - emergency stop")
            self.hardware.stop_pour()
            self._transition_to(States.ERROR)
            
        elif self.state == States.DRINK_READY:
            # Normal completion - cup taken
            logger.info("Cup removed - cycle complete")
            self._transition_to(States.IDLE)
            
        else:
            self._debug_log(f"Cup removed in {self.state.value} state - noting but not acting")
    
    def _on_pour_complete(self):
        """Handle pour completion event."""
        self._debug_log("Pour complete event")
        
        if self.state == States.POURING:
            logger.info("Pour operation completed")
            self._transition_to(States.POURING_COMPLETE)
        else:
            self._debug_log(f"Pour complete in {self.state.value} state - unexpected")
    
    # Public interface methods
    def emergency_stop(self):
        """Emergency stop the system."""
        logger.warning("Emergency stop requested")
        self._debug_log("Emergency stop triggered")
        
        self.hardware.stop_pour()
        self._transition_to(States.ERROR)
    
    def reset_system(self):
        """Reset the system from error state."""
        if self.state == States.ERROR:
            logger.info("Resetting system from error state")
            self._debug_log("System reset requested")
            
            # Clear all state
            self.current_recipe = None
            self.current_tag_id = None
            self.media_playing = False
            
            # Return to idle
            self._transition_to(States.IDLE)
            return True
        else:
            logger.warning(f"Reset requested in {self.state.value} state - ignoring")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "state": self.state.value,
            "previous_state": self.previous_state.value if self.previous_state else None,
            "current_recipe": self.current_recipe.get("name") if self.current_recipe else None,
            "current_tag_id": self.current_tag_id,
            "cup_present": self.hardware.is_cup_present(),
            "media_playing": self.media_playing,
            "state_history": [s.value for s in self.state_history[-5:]]  # Last 5 states
        }
    
    def cleanup(self):
        """Clean up state machine resources."""
        logger.info("Cleaning up state machine")
        
        # Stop hardware monitoring
        self.stop()
        
        # Clean up hardware
        self.hardware.cleanup()
        
        logger.info("State machine cleanup completed")
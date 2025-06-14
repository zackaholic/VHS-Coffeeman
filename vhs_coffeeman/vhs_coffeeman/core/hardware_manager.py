"""
hardware_manager.py - Hardware Manager for VHS Coffeeman

This module provides a hardware abstraction layer for the VHS Coffeeman system.
It manages all hardware components and provides a unified interface for the state machine.

Classes:
    HardwareManager: Manages all hardware components and provides event callbacks

The HardwareManager class handles:
    - Initialization of all hardware components
    - Event-driven hardware monitoring
    - Hardware abstraction for the state machine
    - LED control and status indication
    - Error handling and recovery

Usage:
    from core.hardware_manager import HardwareManager
    
    def on_rfid_detected(tag_id):
        print(f"RFID detected: {tag_id}")
        
    def on_cup_placed():
        print("Cup placed")
        
    hardware = HardwareManager()
    hardware.set_rfid_callback(on_rfid_detected)
    hardware.set_cup_placed_callback(on_cup_placed)
    hardware.start_monitoring()
"""

import time
import threading
from typing import Callable, Optional, Dict, Any, List, Tuple
import RPi.GPIO as GPIO
from utils.logger import setup_logger
from hardware.rfid_reader import RFIDReader
from hardware.cup_sensor import CupSensor, MockCupSensor
from hardware.grbl_interface import GRBLInterface
from hardware.pump_controller import PumpController
from hardware.vcr_controller import VCRController
from media.video_player import VideoPlayer
from recipes.recipe_loader import RecipeLoader, BasicRecipeLoader

logger = setup_logger(__name__)


class HardwareManager:
    """Manages all hardware components and provides event callbacks."""
    
    def __init__(self):
        """Initialize the hardware manager and all components."""
        logger.info("Initializing Hardware Manager")
        
        # Set GPIO mode globally before initializing any components
        # Disable warnings for pins already in use
        GPIO.setwarnings(False)
        try:
            GPIO.setmode(GPIO.BCM)
            logger.debug("Set GPIO mode to BCM")
        except Exception as e:
            logger.warning(f"GPIO mode already set: {e}")
        
        # Initialize hardware components
        self.rfid_reader = RFIDReader()
        
        # Try to initialize cup sensor, use mock if it fails
        try:
            self.cup_sensor = CupSensor()
            self._cup_sensor_available = True
        except Exception as e:
            logger.warning(f"Cup sensor initialization failed, using mock sensor for dry run: {e}")
            self.cup_sensor = MockCupSensor()
            self._cup_sensor_available = False
        
        self.grbl_interface = GRBLInterface()
        self.pump_controller = PumpController(self.grbl_interface)
        self.vcr_controller = VCRController()
        self.video_player = VideoPlayer(media_directory="media")
        self.recipe_loader = RecipeLoader()
        
        # Event callbacks
        self.rfid_callback: Optional[Callable[[str], None]] = None
        self.cup_placed_callback: Optional[Callable[[], None]] = None
        self.cup_removed_callback: Optional[Callable[[], None]] = None
        self.pour_complete_callback: Optional[Callable[[], None]] = None
        
        # State tracking for conditional polling
        self.should_poll_rfid: bool = True
        self.should_poll_cup_sensor: bool = False  # Only poll when needed
        
        # Monitoring state
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Cup sensor state tracking
        self._cup_present = False
        self._last_cup_state = False
        self._cup_sensor_consecutive_failures = 0
        
        # RFID state tracking
        self._last_rfid_tag = None
        
        logger.info("Hardware Manager initialized successfully")
    
    def set_rfid_callback(self, callback: Callable[[str], None]):
        """Set callback for RFID detection events."""
        self.rfid_callback = callback
        logger.debug("RFID callback set")
    
    def set_cup_placed_callback(self, callback: Callable[[], None]):
        """Set callback for cup placed events."""
        self.cup_placed_callback = callback
        logger.debug("Cup placed callback set")
    
    def set_cup_removed_callback(self, callback: Callable[[], None]):
        """Set callback for cup removed events."""
        self.cup_removed_callback = callback
        logger.debug("Cup removed callback set")
    
    def set_pour_complete_callback(self, callback: Callable[[], None]):
        """Set callback for pour completion events."""
        self.pour_complete_callback = callback
        logger.debug("Pour complete callback set")
    
    def enable_rfid_polling(self):
        """Enable RFID tag polling."""
        self.should_poll_rfid = True
        logger.debug("RFID polling enabled")
    
    def disable_rfid_polling(self):
        """Disable RFID tag polling."""
        self.should_poll_rfid = False
        logger.debug("RFID polling disabled")
    
    def enable_cup_sensor_polling(self):
        """Enable cup sensor polling."""
        self.should_poll_cup_sensor = True
        logger.debug("Cup sensor polling enabled")
    
    def disable_cup_sensor_polling(self):
        """Disable cup sensor polling."""
        self.should_poll_cup_sensor = False
        logger.debug("Cup sensor polling disabled")
    
    def start_monitoring(self):
        """Start hardware monitoring in a separate thread."""
        if self._monitoring:
            logger.warning("Hardware monitoring already started")
            return
            
        logger.info("Starting hardware monitoring")
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_hardware, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop hardware monitoring."""
        if not self._monitoring:
            logger.warning("Hardware monitoring not running")
            return
            
        logger.info("Stopping hardware monitoring")
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
    
    def _monitor_hardware(self):
        """Monitor hardware for events (runs in separate thread)."""
        logger.info("Hardware monitoring thread started")
        
        while self._monitoring:
            try:
                # Check for RFID tags
                self._check_rfid()
                
                # Check cup sensor
                self._check_cup_sensor()
                
                # Brief delay to prevent excessive polling
                time.sleep(0.2)  # Slower polling for sensor stability
                
            except Exception as e:
                logger.error(f"Error in hardware monitoring: {e}")
                time.sleep(1.0)  # Longer delay on error
        
        logger.info("Hardware monitoring thread stopped")
    
    def _check_rfid(self):
        """Check for RFID tag detection."""
        # Only poll RFID when we should be looking for new tags
        if not self.should_poll_rfid:
            return
            
        try:
            tag_id, text = self.rfid_reader.read_tag()
            
            # Only trigger callback on new tag detection
            if tag_id and tag_id != self._last_rfid_tag:
                logger.info(f"RFID tag detected: {tag_id}")
                self._last_rfid_tag = tag_id
                
                if self.rfid_callback:
                    self.rfid_callback(str(tag_id))
            
            # Clear last tag if no tag present
            if not tag_id:
                self._last_rfid_tag = None
                
        except Exception as e:
            logger.error(f"Error reading RFID: {e}")
    
    def _check_cup_sensor(self):
        """Check cup sensor for state changes."""
        # Only poll cup sensor when we should be monitoring it
        if not self.should_poll_cup_sensor:
            return
            
        try:
            cup_present = self.cup_sensor.is_cup_present()
            
            # Reset failure counter on successful read
            self._cup_sensor_consecutive_failures = 0
            
            # Check for state change
            if cup_present != self._last_cup_state:
                logger.info(f"Cup sensor state changed: {'present' if cup_present else 'removed'}")
                
                if cup_present and self.cup_placed_callback:
                    self.cup_placed_callback()
                elif not cup_present and self.cup_removed_callback:
                    self.cup_removed_callback()
                
                self._last_cup_state = cup_present
            
            # Update internal state
            self._cup_present = cup_present
            
        except Exception as e:
            self._cup_sensor_consecutive_failures += 1
            
            # Only log error after multiple consecutive failures
            if self._cup_sensor_consecutive_failures >= 10:
                logger.error(f"Cup sensor failed {self._cup_sensor_consecutive_failures} times in a row: {e}")
                # Reset counter to avoid spam
                self._cup_sensor_consecutive_failures = 0
            elif self._cup_sensor_consecutive_failures == 1:
                logger.debug(f"Cup sensor read failed (attempt 1/10): {e}")
            elif self._cup_sensor_consecutive_failures == 5:
                logger.warning(f"Cup sensor read failed 5 times in a row: {e}")
    
    def is_cup_present(self) -> bool:
        """Check if cup is currently present."""
        return self._cup_present
    
    def get_recipe_by_tag(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """Get a recipe by RFID tag ID."""
        try:
            logger.info(f"Looking up recipe for tag: {tag_id}")
            
            # Get movie name for logging
            movie_name = self.recipe_loader.get_movie_name(tag_id)
            
            # Get the pump list from the new recipe system
            pump_list = self.recipe_loader.get_recipe_by_tag_id(tag_id)
            
            if pump_list:
                logger.info(f"Found recipe for {movie_name}: {len(pump_list)} ingredients")
                
                # Convert pump list back to legacy format for compatibility
                recipe = self._pump_list_to_recipe_dict(tag_id, movie_name or f"Recipe {tag_id}", pump_list)
                return recipe
            else:
                logger.warning(f"No recipe found for tag: {tag_id}")
                return None
            
        except Exception as e:
            logger.error(f"Error getting recipe for tag {tag_id}: {e}")
            return None
    
    def _pump_list_to_recipe_dict(self, tag_id: str, name: str, pump_list: List[Tuple[int, float]]) -> Dict[str, Any]:
        """Convert pump list to legacy recipe dictionary format.
        
        Args:
            tag_id: RFID tag ID
            name: Recipe/movie name  
            pump_list: List of (pump_number, amount) tuples
            
        Returns:
            Recipe dictionary in legacy format
        """
        ingredients = []
        for pump_number, amount in pump_list:
            ingredients.append({
                "pump": pump_number,
                "amount": amount,
                "name": f"Pump {pump_number}"  # Generic name for legacy compatibility
            })
        
        return {
            "name": name,
            "tag_id": tag_id,
            "description": f"Recipe for {name}",
            "ingredients": ingredients
        }
    
    def load_recipe(self, recipe_data: Dict[str, Any]) -> bool:
        """Load a recipe for dispensing."""
        try:
            logger.info(f"Loading recipe: {recipe_data.get('name', 'Unknown')}")
            
            # Basic validation
            if 'ingredients' not in recipe_data:
                logger.error("Recipe missing ingredients")
                return False
            
            ingredients = recipe_data['ingredients']
            if not isinstance(ingredients, list) or len(ingredients) == 0:
                logger.error("Recipe has no ingredients")
                return False
            
            logger.info("Recipe loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading recipe: {e}")
            return False
    
    def start_pour(self, recipe_data: Dict[str, Any]) -> bool:
        """Start pouring the loaded recipe."""
        try:
            logger.info("Starting pour sequence")
            
            # Execute the recipe using pump controller
            success = self.pump_controller.execute_recipe(recipe_data)
            
            if success:
                logger.info("Pour sequence completed successfully")
                if self.pour_complete_callback:
                    self.pour_complete_callback()
            else:
                logger.error("Pour sequence failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error during pour: {e}")
            return False
    
    def stop_pour(self):
        """Emergency stop of current pour operation."""
        try:
            logger.warning("Emergency stop requested")
            self.pump_controller.disable_all_pumps()
            logger.info("All pumps stopped")
            
        except Exception as e:
            logger.error(f"Error stopping pumps: {e}")
    
    def play_vcr(self):
        """Trigger VCR play button."""
        try:
            logger.info("Triggering VCR play")
            self.vcr_controller.play()
            
        except Exception as e:
            logger.error(f"Error triggering VCR play: {e}")
    
    def eject_vcr(self):
        """Trigger VCR eject button and stop video playback."""
        try:
            logger.info("Triggering VCR eject")
            
            # Stop video playback to maintain VHS illusion
            self.stop_video()
            
            # Eject the physical tape
            self.vcr_controller.eject()
            
        except Exception as e:
            logger.error(f"Error triggering VCR eject: {e}")
    
    def start_video_for_tag(self, tag_id: str) -> bool:
        """Start video playback for the given tag ID."""
        try:
            logger.info(f"Starting video for tag: {tag_id}")
            
            # Convert RFID tag ID to movie name
            movie_name = self.recipe_loader.get_movie_name(tag_id)
            if not movie_name:
                logger.warning(f"No movie name found for tag {tag_id}")
                return False
            
            logger.info(f"Tag {tag_id} maps to movie: {movie_name}")
            return self.video_player.play_video_for_tag(movie_name)
            
        except Exception as e:
            logger.error(f"Error starting video for tag {tag_id}: {e}")
            return False
    
    def stop_video(self):
        """Stop current video playback."""
        try:
            logger.info("Stopping video playback")
            self.video_player.stop_video()
            
        except Exception as e:
            logger.error(f"Error stopping video: {e}")
    
    # LED Control Functions (Placeholders)
    def set_led_attractor(self):
        """Set LEDs to attractor pattern (idle state)."""
        # TODO: Implement LED control
        logger.debug("Setting LEDs to attractor pattern")
        pass
    
    def set_led_no_cup(self):
        """Set LEDs to red (no cup detected)."""
        # TODO: Implement LED control
        logger.debug("Setting LEDs to red (no cup)")
        pass
    
    def set_led_cup_ready(self):
        """Set LEDs to green (cup detected, ready to pour)."""
        # TODO: Implement LED control
        logger.debug("Setting LEDs to green (cup ready)")
        pass
    
    def set_led_pouring(self):
        """Set LEDs to white (actively pouring)."""
        # TODO: Implement LED control
        logger.debug("Setting LEDs to white (pouring)")
        pass
    
    def cleanup(self):
        """Clean up hardware resources."""
        logger.info("Cleaning up hardware resources")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Stop all pumps
        try:
            self.pump_controller.disable_all_pumps()
        except Exception as e:
            logger.error(f"Error stopping pumps during cleanup: {e}")
        
        # Cleanup individual components
        try:
            self.rfid_reader.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up RFID reader: {e}")
        
        try:
            self.cup_sensor.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up cup sensor: {e}")
        
        try:
            self.video_player.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up video player: {e}")
        
        logger.info("Hardware cleanup completed")
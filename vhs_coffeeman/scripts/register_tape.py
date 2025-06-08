#!/usr/bin/env python3
"""
RFID Tape Registration Tool for VHS Coffeeman

This tool allows you to register new VHS tapes by:
1. Waiting for an RFID tag to be detected
2. Prompting for the movie title to associate with that tag
3. Adding the new entry to tapes.json
4. Automatically ejecting the tape when registration is complete

Usage:
    python scripts/register_tape.py          # Register tapes with auto-eject
    python scripts/register_tape.py --list   # List registered tapes
    python scripts/register_tape.py --no-eject  # Register without auto-eject
    
Then insert a VHS tape and enter the movie title when prompted.
"""

import os
import sys
import json
import signal
import time
import re
import argparse
from typing import Dict, Optional

# Add the vhs_coffeeman package to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, 'vhs_coffeeman'))

try:
    # Suppress GPIO warnings for cleaner output
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
    
    # Force GPIO mode to BCM early to avoid conflicts
    # This must be done before importing RFID reader
    try:
        GPIO.setmode(GPIO.BCM)
    except ValueError:
        # Mode already set, clean up and retry
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
    
    from vhs_coffeeman.hardware.rfid_reader import RFIDReader
    from vhs_coffeeman.hardware.vcr_controller import VCRController
    from vhs_coffeeman.utils.logger import setup_logger
except ImportError as e:
    print(f"Error importing VHS Coffeeman modules: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)

logger = setup_logger(__name__)

class TapeRegistrationTool:
    """Tool for registering RFID tags with movie names."""
    
    def __init__(self):
        """Initialize the tape registration tool."""
        self.rfid_reader = None
        self.vcr_controller = None
        self.tapes_file = os.path.join(project_root, 'vhs_coffeeman', 'recipes', 'tapes.json')
        self.running = True
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("VHS Coffeeman - RFID Tape Registration Tool")
        print("=" * 50)
        print(f"Tapes file: {self.tapes_file}")
        print()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print("\nShutdown signal received. Cleaning up...")
        self.running = False
    
    def _load_existing_tapes(self) -> Dict[str, str]:
        """Load existing tapes from tapes.json."""
        try:
            if os.path.exists(self.tapes_file):
                with open(self.tapes_file, 'r') as f:
                    tapes = json.load(f)
                print(f"Loaded {len(tapes)} existing tape(s)")
                return tapes
            else:
                print("No existing tapes.json found - will create new file")
                return {}
        except Exception as e:
            print(f"Error loading existing tapes: {e}")
            return {}
    
    def _save_tapes(self, tapes: Dict[str, str]) -> bool:
        """Save tapes dictionary to tapes.json."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.tapes_file), exist_ok=True)
            
            # Write with pretty formatting
            with open(self.tapes_file, 'w') as f:
                json.dump(tapes, f, indent=2, sort_keys=True)
            
            print(f"✓ Saved tapes.json with {len(tapes)} entries")
            return True
            
        except Exception as e:
            print(f"✗ Error saving tapes.json: {e}")
            return False
    
    def _sanitize_movie_title(self, title: str) -> str:
        """Sanitize movie title for consistency."""
        # Remove extra whitespace and normalize spaces
        sanitized = re.sub(r'\s+', '_', title.strip())
        
        # Remove any characters that might cause issues
        allowed_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
        sanitized = ''.join(c for c in sanitized if c in allowed_chars)
        
        return sanitized
    
    def _get_movie_title(self, tag_id: str, existing_tapes: Dict[str, str]) -> Optional[str]:
        """Get movie title from user input."""
        try:
            # Check if tag already exists
            if tag_id in existing_tapes:
                current_title = existing_tapes[tag_id]
                print(f"⚠️  Tag {tag_id} is already registered as: {current_title}")
                response = input("Do you want to overwrite it? (y/N): ").strip().lower()
                if response != 'y':
                    print("Registration cancelled.")
                    return None
            
            # Get movie title from user
            while True:
                title = input("Enter movie title: ").strip()
                
                if not title:
                    print("Movie title cannot be empty. Please try again.")
                    continue
                
                # Sanitize the title
                sanitized_title = self._sanitize_movie_title(title)
                
                if sanitized_title != title:
                    print(f"Title will be saved as: {sanitized_title}")
                    confirm = input("Is this OK? (Y/n): ").strip().lower()
                    if confirm == 'n':
                        continue
                
                return sanitized_title
                
        except KeyboardInterrupt:
            print("\nCancelled by user.")
            return None
        except Exception as e:
            print(f"Error getting movie title: {e}")
            return None
    
    def _eject_tape(self):
        """Eject the tape using VCR controller."""
        try:
            print("Ejecting tape...")
            logger.info("Attempting VCR eject")
            self.vcr_controller.press_eject()
            print("✓ Tape ejected")
            
            # Wait for tape to physically leave the RFID reader's range
            print("Waiting for tape to clear...")
            time.sleep(3.0)
            print("Ready for next tape")
            
        except Exception as e:
            print(f"✗ Error ejecting tape: {e}")
            logger.error(f"VCR eject error: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self, auto_eject: bool = True):
        """Run the tape registration tool.
        
        Args:
            auto_eject: Whether to automatically eject tape after successful registration
        """
        try:
            # Initialize RFID reader
            print("Initializing RFID reader...")
            self.rfid_reader = RFIDReader()
            
            # Reduce RFID reader logging verbosity to avoid timeout spam
            import logging
            rfid_logger = logging.getLogger('vhs_coffeeman.hardware.rfid_reader')
            rfid_logger.setLevel(logging.ERROR)  # Only show errors, not info/warnings
            
            print("✓ RFID reader initialized")
            
            # Initialize VCR controller
            print("Initializing VCR controller...")
            try:
                self.vcr_controller = VCRController()
                print("✓ VCR controller initialized")
            except Exception as e:
                print(f"✗ VCR controller initialization failed: {e}")
                logger.error(f"VCR controller error: {e}")
                raise
            print()
            
            # Load existing tapes
            tapes = self._load_existing_tapes()
            
            if tapes:
                print("Current registered tapes:")
                for tag_id, movie in sorted(tapes.items()):
                    print(f"  {tag_id}: {movie}")
                print()
            
            print("Ready to register new tapes!")
            if auto_eject:
                print("Tapes will be automatically ejected after successful registration.")
            else:
                print("Auto-eject disabled - tapes will remain inserted after registration.")
            print("Insert a VHS tape to register it, or press Ctrl+C to exit.")
            print("-" * 50)
            
            print("\nWaiting for RFID tag...")
            
            while self.running:
                try:
                    # Wait for tag with 1 second timeout to allow checking self.running
                    tag_id, _ = self.rfid_reader.wait_for_tag(timeout=1.0)
                    
                    if tag_id is None:
                        continue  # Timeout, check if we should keep running
                    
                    # Convert tag ID to string for consistency
                    tag_id_str = str(tag_id)
                    
                    print(f"✓ Detected RFID tag: {tag_id_str}")
                    
                    # Get movie title from user
                    movie_title = self._get_movie_title(tag_id_str, tapes)
                    
                    if movie_title:
                        # Add to tapes dictionary
                        tapes[tag_id_str] = movie_title
                        
                        # Save to file
                        if self._save_tapes(tapes):
                            print(f"✓ Successfully registered: {tag_id_str} -> {movie_title}")
                            
                            # Eject the tape to provide tactile feedback
                            if auto_eject:
                                self._eject_tape()
                        else:
                            print("✗ Failed to save registration")
                    
                    print("-" * 50)
                    print("Waiting for next RFID tag...")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error during registration: {e}")
                    logger.error(f"Registration error: {e}")
                    
        except Exception as e:
            print(f"Failed to initialize: {e}")
            logger.error(f"Initialization error: {e}")
            return 1
        
        finally:
            print("\nCleaning up...")
            # GPIO cleanup will be handled by the RFID reader destructor
            
        print("Tape registration tool exited.")
        return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RFID Tape Registration Tool for VHS Coffeeman",
        epilog="Insert a VHS tape and enter the movie title when prompted."
    )
    parser.add_argument(
        "--list", "-l", 
        action="store_true",
        help="List currently registered tapes and exit"
    )
    parser.add_argument(
        "--tapes-file",
        help="Path to tapes.json file (default: auto-detect)"
    )
    parser.add_argument(
        "--no-eject",
        action="store_true",
        help="Don't eject tape after successful registration"
    )
    
    args = parser.parse_args()
    
    # Handle list option
    if args.list:
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tapes_file = args.tapes_file or os.path.join(project_root, 'vhs_coffeeman', 'recipes', 'tapes.json')
            
            if os.path.exists(tapes_file):
                with open(tapes_file, 'r') as f:
                    tapes = json.load(f)
                
                print("Currently registered tapes:")
                if tapes:
                    for tag_id, movie in sorted(tapes.items()):
                        print(f"  {tag_id}: {movie}")
                else:
                    print("  No tapes registered yet.")
            else:
                print("No tapes.json file found.")
            
            return 0
            
        except Exception as e:
            print(f"Error listing tapes: {e}")
            return 1
    
    # Run the registration tool
    tool = TapeRegistrationTool()
    if args.tapes_file:
        tool.tapes_file = args.tapes_file
    
    return tool.run(auto_eject=not args.no_eject)

if __name__ == "__main__":
    sys.exit(main())
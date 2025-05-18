#!/bin/bash
# Helper script to activate the virtual environment

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_DIR=$(dirname "$SCRIPT_DIR")
VENV_DIR="$PROJECT_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
  echo "Virtual environment not found at $VENV_DIR"
  echo "Please create it first by running 'python -m venv venv' in the project directory"
  exit 1
fi

# Source the activation script
source "$VENV_DIR/bin/activate"

# Print success message
echo "Virtual environment activated."
echo "You can now run the test scripts:"
echo "  ./scripts/gpio_test.py"
echo "  ./scripts/rfid_test.py"
echo "  ./scripts/grbl_test.py" 
echo "  ./scripts/pump_test.py"
echo
echo "To deactivate the virtual environment, run 'deactivate'"
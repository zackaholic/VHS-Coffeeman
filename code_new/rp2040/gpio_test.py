"""
gpio_test.py - GPIO Testing Module for VHS Coffeeman

This module provides testing functions for verifying GPIO pin connections
on the VHS Coffeeman system. It allows for systematic testing of:
- Pump enable pins (outputs)
- VCR control pins (outputs)
- GRBL_EN pin (input)
- UART pins (function testing)

Usage:
    import time
    from gpio_test import GPIOTester
    
    # Initialize the tester
    tester = GPIOTester()
    
    # Test pump pins individually
    tester.test_pump_pin(0)  # Test pump 0
    
    # Test all pump pins sequentially
    tester.test_all_pump_pins()
    
    # Test VCR control pins
    tester.test_vcr_pins()
    
    # Monitor GRBL_EN pin
    tester.monitor_grbl_en(duration_sec=10)
    
This module is designed for diagnostic purposes and should be used
before full system testing to verify hardware connections.
"""

import time
from machine import Pin
from config import pins, constants

class GPIOTester:
    """Provides testing functionality for GPIO pins."""
    
    def __init__(self):
        """Initialize the GPIO tester with pin setup."""
        # Test durations
        self.toggle_duration_ms = 1000  # 1 second per state for measurement
        self.vcr_test_duration_ms = 2000  # 2 seconds for VCR button press
        
        # Initialize pump pins
        self.pump_pins = []
        for pin_num in pins.PUMP_PINS:
            self.pump_pins.append(Pin(pin_num, Pin.OUT, value=1))  # Start disabled (high)
        
        # Initialize VCR pins
        self.play_pin = Pin(pins.VCR_PLAY, Pin.OUT, value=0)  # Start inactive
        self.eject_pin = Pin(pins.VCR_EJECT, Pin.OUT, value=0)  # Start inactive
        
        # Initialize GRBL_EN pin
        self.grbl_en = Pin(pins.GRBL_EN, Pin.IN)
        
        print("GPIO Tester initialized")
    
    def test_pump_pin(self, pump_index):
        """
        Test a specific pump enable pin.
        
        Args:
            pump_index: The index of the pump to test.
        """
        if pump_index < 0 or pump_index >= len(self.pump_pins):
            print(f"Invalid pump index: {pump_index}")
            return
        
        print(f"Testing Pump {pump_index} pin (GPIO {pins.PUMP_PINS[pump_index]})")
        print("Pin should toggle between HIGH (disabled) and LOW (enabled)")
        print("Measure with multimeter to verify")
        
        # Start with pump disabled
        self.pump_pins[pump_index].value(1)  # High = disabled
        
        # Toggle the pin several times with delay
        for i in range(3):
            print(f"Setting Pump {pump_index} ENABLED (LOW)")
            self.pump_pins[pump_index].value(0)  # Low = enabled
            time.sleep_ms(self.toggle_duration_ms)
            
            print(f"Setting Pump {pump_index} DISABLED (HIGH)")
            self.pump_pins[pump_index].value(1)  # High = disabled
            time.sleep_ms(self.toggle_duration_ms)
        
        print(f"Pump {pump_index} pin test complete")
    
    def test_all_pump_pins(self):
        """Test all pump pins sequentially."""
        print("Testing all pump pins sequentially")
        
        for i in range(len(self.pump_pins)):
            self.test_pump_pin(i)
    
    def test_vcr_pins(self):
        """Test the VCR control pins (play and eject)."""
        print("Testing VCR control pins")
        print("Measure with multimeter to verify")
        
        # Test play pin
        print(f"Testing VCR play pin (GPIO {pins.VCR_PLAY})")
        print("Pin should go HIGH for 2 seconds")
        self.play_pin.value(1)
        time.sleep_ms(self.vcr_test_duration_ms)
        self.play_pin.value(0)
        time.sleep_ms(self.toggle_duration_ms)
        
        # Test eject pin
        print(f"Testing VCR eject pin (GPIO {pins.VCR_EJECT})")
        print("Pin should go HIGH for 2 seconds")
        self.eject_pin.value(1)
        time.sleep_ms(self.vcr_test_duration_ms)
        self.eject_pin.value(0)
        
        print("VCR pin test complete")
    
    def monitor_grbl_en(self, duration_sec=10):
        """
        Monitor the GRBL_EN pin for the specified duration.
        
        Args:
            duration_sec: Duration to monitor in seconds.
        """
        print(f"Monitoring GRBL_EN pin (GPIO {pins.GRBL_EN}) for {duration_sec} seconds")
        print("Current value should be reported every second")
        print("When GRBL is idle, pin should be HIGH")
        print("When GRBL is moving, pin should be LOW")
        
        end_time = time.time() + duration_sec
        
        while time.time() < end_time:
            value = self.grbl_en.value()
            state = "HIGH (idle)" if value == 1 else "LOW (moving)"
            print(f"GRBL_EN: {state}")
            time.sleep(1)
        
        print("GRBL_EN monitoring complete")
    
    def test_uart_pins(self):
        """
        Print information about UART pins for testing.
        This doesn't actually test functionality but provides pin info.
        """
        print("UART Pin Information:")
        print(f"GRBL UART TX: GPIO {pins.UART_TX}")
        print(f"GRBL UART RX: GPIO {pins.UART_RX}")
        print(f"Pi UART TX: GPIO {pins.PI_UART_TX}")
        print(f"Pi UART RX: GPIO {pins.PI_UART_RX}")
        print("Use a logic analyzer or oscilloscope to verify UART signals")
    
    def run_all_tests(self):
        """Run all GPIO tests sequentially."""
        print("Starting full GPIO test sequence")
        
        # Test pump pins
        self.test_all_pump_pins()
        
        # Test VCR pins
        self.test_vcr_pins()
        
        # Monitor GRBL_EN
        self.monitor_grbl_en(5)  # 5 seconds
        
        # Display UART pin info
        self.test_uart_pins()
        
        print("All GPIO tests complete")


# Simple test script when run directly
if __name__ == "__main__":
    print("VHS Coffeeman GPIO Test Tool")
    print("---------------------------")
    
    # Create the tester
    tester = GPIOTester()
    
    # Ask for test mode
    print("\nTest options:")
    print("1: Test single pump pin")
    print("2: Test all pump pins")
    print("3: Test VCR pins")
    print("4: Monitor GRBL_EN pin")
    print("5: Show UART pin information")
    print("6: Run all tests")
    
    try:
        choice = input("Enter test number (1-6): ")
        choice = int(choice.strip())
        
        if choice == 1:
            pump_idx = int(input("Enter pump index (0-9): "))
            tester.test_pump_pin(pump_idx)
        elif choice == 2:
            tester.test_all_pump_pins()
        elif choice == 3:
            tester.test_vcr_pins()
        elif choice == 4:
            duration = int(input("Enter monitoring duration in seconds: "))
            tester.monitor_grbl_en(duration)
        elif choice == 5:
            tester.test_uart_pins()
        elif choice == 6:
            tester.run_all_tests()
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Clean up: make sure all pins are in safe state
        for pin in tester.pump_pins:
            pin.value(1)  # Disable all pumps
        tester.play_pin.value(0)  # Inactive
        tester.eject_pin.value(0)  # Inactive
        print("Test complete, pins reset to safe state")
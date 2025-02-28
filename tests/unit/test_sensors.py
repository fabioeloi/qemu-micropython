"""
Unit tests for sensors module
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add the src directory to the path so we can import the sensors module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Create mock classes for MicroPython modules that might not be available during testing
class MockI2C:
    def __init__(self, *args, **kwargs):
        pass
    
    def scan(self):
        return []
    
    def readfrom_mem(self, addr, reg, nbytes):
        return bytes([0] * nbytes)
    
    def writeto_mem(self, addr, reg, data):
        pass
    
    def readfrom(self, addr, nbytes):
        return bytes([0] * nbytes)
    
    def writeto(self, addr, data):
        pass

class MockPin:
    OUT = 0
    IN = 1
    
    def __init__(self, *args, **kwargs):
        pass

# Mock MicroPython's machine module
sys.modules['machine'] = MagicMock()
sys.modules['machine'].I2C = MockI2C
sys.modules['machine'].Pin = MockPin

# Now we can import our module
from lib import sensors

class TestSensors(unittest.TestCase):
    """Test cases for sensors module"""
    
    def test_read_temperature_returns_float(self):
        """Test that read_temperature returns a float value"""
        temp = sensors.read_temperature()
        self.assertIsInstance(temp, float)
    
    def test_read_humidity_returns_float(self):
        """Test that read_humidity returns a float value"""
        humidity = sensors.read_humidity()
        self.assertIsInstance(humidity, float)
    
    def test_read_pressure_returns_float(self):
        """Test that read_pressure returns a float value"""
        pressure = sensors.read_pressure()
        self.assertIsInstance(pressure, float)

if __name__ == '__main__':
    unittest.main()
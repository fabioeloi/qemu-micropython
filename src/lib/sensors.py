"""
Sensor library for STM32 IoT applications
----------------------------------------
Provides interfaces for common sensors
"""
import time
from machine import Pin, I2C

# Constants for supported sensors
SENSOR_BME280 = 0x76  # BME280 temperature/humidity/pressure sensor
SENSOR_SHT31 = 0x44   # SHT31 temperature/humidity sensor

class SensorBase:
    """Base class for sensors"""
    def __init__(self, i2c=None, addr=None):
        if i2c is None:
            # Default I2C if not provided
            self.i2c = I2C(1, scl=Pin('PB6'), sda=Pin('PB7'))
        else:
            self.i2c = i2c
        
        self.addr = addr
        self.initialized = False
    
    def is_connected(self):
        """Check if the sensor is connected"""
        if self.addr is None:
            return False
        return self.addr in self.i2c.scan()
    
    def initialize(self):
        """Initialize the sensor"""
        raise NotImplementedError("Sensor implementation must override initialize()")
    
    def read(self):
        """Read data from sensor"""
        raise NotImplementedError("Sensor implementation must override read()")

class BME280(SensorBase):
    """BME280 temperature, humidity and pressure sensor"""
    def __init__(self, i2c=None, addr=SENSOR_BME280):
        super().__init__(i2c, addr)
        self.temp_calibration = None
        self.press_calibration = None
        self.hum_calibration = None
    
    def initialize(self):
        if not self.is_connected():
            raise RuntimeError("BME280 not found on I2C bus")
        
        # Read calibration data
        self._read_calibration_data()
        
        # Configure sensor
        # Normal mode, temperature oversampling x1, pressure oversampling x1, humidity oversampling x1
        self.i2c.writeto_mem(self.addr, 0xF2, bytes([0x01]))  # Humidity control
        self.i2c.writeto_mem(self.addr, 0xF4, bytes([0x27]))  # Temperature, pressure control
        
        self.initialized = True
    
    def _read_calibration_data(self):
        # This is a simplified implementation
        # In a real implementation, we would read and process all calibration registers
        self.temp_calibration = 1.0
        self.press_calibration = 1.0
        self.hum_calibration = 1.0
    
    def read(self):
        """Read temperature, pressure, and humidity"""
        if not self.initialized:
            self.initialize()
        
        # In a real implementation, we would read the raw sensor data
        # and apply calibration calculations
        
        # Simulate reading for QEMU demonstration
        # In reality, we would read from the actual sensor registers
        raw_temp = self.i2c.readfrom_mem(self.addr, 0xFA, 3)
        raw_press = self.i2c.readfrom_mem(self.addr, 0xF7, 3)
        raw_hum = self.i2c.readfrom_mem(self.addr, 0xFD, 2)
        
        # Simulated values based on raw data
        temperature = 25.0 + (raw_temp[0] % 10) / 10
        pressure = 1013.25 + (raw_press[0] % 50)
        humidity = 50.0 + (raw_hum[0] % 20)
        
        return {
            'temperature': temperature,
            'pressure': pressure,
            'humidity': humidity
        }

class SHT31(SensorBase):
    """SHT31 temperature and humidity sensor"""
    def __init__(self, i2c=None, addr=SENSOR_SHT31):
        super().__init__(i2c, addr)
    
    def initialize(self):
        if not self.is_connected():
            raise RuntimeError("SHT31 not found on I2C bus")
        
        # Send measurement command: high repeatability
        self.i2c.writeto(self.addr, bytes([0x2C, 0x06]))
        time.sleep_ms(20)  # Wait for measurement
        
        self.initialized = True
    
    def read(self):
        """Read temperature and humidity"""
        if not self.initialized:
            self.initialize()
        
        # Send measurement command: high repeatability
        self.i2c.writeto(self.addr, bytes([0x2C, 0x06]))
        time.sleep_ms(20)  # Wait for measurement
        
        # Read 6 bytes of data
        data = self.i2c.readfrom(self.addr, 6)
        
        # Extract temperature and humidity (see datasheet for formula)
        temp_raw = (data[0] << 8) | data[1]
        temperature = -45 + (175 * temp_raw / 65535)
        
        hum_raw = (data[3] << 8) | data[4]
        humidity = 100 * hum_raw / 65535
        
        return {
            'temperature': temperature,
            'humidity': humidity
        }

# Global sensor instances
_temperature_sensor = None
_humidity_sensor = None
_pressure_sensor = None

def initialize_sensors(i2c=None):
    """Initialize all available sensors"""
    global _temperature_sensor, _humidity_sensor, _pressure_sensor
    
    if i2c is None:
        i2c = I2C(1, scl=Pin('PB6'), sda=Pin('PB7'))
    
    # Scan for available sensors
    devices = i2c.scan()
    
    if SENSOR_BME280 in devices:
        bme280 = BME280(i2c)
        bme280.initialize()
        _temperature_sensor = bme280
        _humidity_sensor = bme280
        _pressure_sensor = bme280
        print("BME280 sensor initialized")
    elif SENSOR_SHT31 in devices:
        sht31 = SHT31(i2c)
        sht31.initialize()
        _temperature_sensor = sht31
        _humidity_sensor = sht31
        print("SHT31 sensor initialized")
    else:
        print("No supported sensors found")

def read_temperature():
    """Read temperature from the best available sensor"""
    global _temperature_sensor
    
    if _temperature_sensor is None:
        initialize_sensors()
    
    if _temperature_sensor is None:
        # Return simulated data if no sensor is available
        return 25.0
    
    return _temperature_sensor.read()['temperature']

def read_humidity():
    """Read humidity from the best available sensor"""
    global _humidity_sensor
    
    if _humidity_sensor is None:
        initialize_sensors()
    
    if _humidity_sensor is None:
        # Return simulated data if no sensor is available
        return 50.0
    
    return _humidity_sensor.read()['humidity']

def read_pressure():
    """Read pressure from the best available sensor"""
    global _pressure_sensor
    
    if _pressure_sensor is None:
        initialize_sensors()
    
    if _pressure_sensor is None:
        # Return simulated data if no sensor is available
        return 1013.25
    
    if 'pressure' in _pressure_sensor.read():
        return _pressure_sensor.read()['pressure']
    else:
        return 1013.25
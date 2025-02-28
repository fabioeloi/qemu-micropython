"""
MicroPython STM32 IoT Application
---------------------------------
This is the main application entry point.
"""
import machine
import time
import network
from machine import Pin, I2C, SPI

# Import our custom modules
try:
    import sensors
    import iot_client
except ImportError:
    print("Custom modules not found. Basic demo only.")

# Board LED pins for STM32F4-Discovery
leds = {
    'green': Pin('PD12', Pin.OUT),
    'orange': Pin('PD13', Pin.OUT),
    'red': Pin('PD14', Pin.OUT),
    'blue': Pin('PD15', Pin.OUT)
}

def blink_led(led_name, count=3, delay=0.2):
    """Blink a specific LED"""
    led = leds.get(led_name)
    if not led:
        print(f"LED {led_name} not found")
        return
        
    for _ in range(count):
        led.on()
        time.sleep(delay)
        led.off()
        time.sleep(delay)

def setup():
    """Initialize hardware and peripherals"""
    print("Setting up hardware...")
    
    # Set up I2C for sensors
    try:
        i2c = I2C(1, scl=Pin('PB6'), sda=Pin('PB7'))
        devices = i2c.scan()
        if devices:
            print(f"I2C devices found: {[hex(d) for d in devices]}")
        else:
            print("No I2C devices found")
    except Exception as e:
        print(f"I2C setup failed: {e}")
    
    # Set up SPI for additional peripherals
    try:
        spi = SPI(1, SPI.MASTER, baudrate=1000000, polarity=0, phase=0)
        print("SPI initialized")
    except Exception as e:
        print(f"SPI setup failed: {e}")
    
    # Set up networking if available
    try:
        if hasattr(network, 'WLAN'):
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            print("WiFi initialized")
        elif hasattr(network, 'WIZNET5K'):
            nic = network.WIZNET5K()
            print("Ethernet initialized")
    except Exception as e:
        print(f"Network setup failed: {e}")
    
    # Indicate setup is complete
    blink_led('green', count=2)
    print("Setup complete")

def main():
    """Main application loop"""
    print("\nSTM32 IoT Application Starting...")
    setup()
    
    print("Starting main loop...")
    count = 0
    
    try:
        while True:
            # Toggle the blue LED to show the system is running
            leds['blue'].toggle()
            
            # Simulate sensor reading
            if count % 5 == 0:
                print(f"Reading sensors... (loop count: {count})")
                try:
                    if 'sensors' in globals():
                        temp = sensors.read_temperature()
                        humidity = sensors.read_humidity()
                        print(f"Temperature: {temp}°C, Humidity: {humidity}%")
                except Exception as e:
                    print(f"Sensor reading failed: {e}")
                    blink_led('red')
            
            # Simulate IoT data transmission
            if count % 10 == 0 and count > 0:
                print("Sending data to IoT platform...")
                try:
                    if 'iot_client' in globals():
                        iot_client.send_telemetry({
                            'temperature': 25.0 + (count % 10) / 10,
                            'humidity': 50 + (count % 20),
                            'uptime': count
                        })
                except Exception as e:
                    print(f"IoT transmission failed: {e}")
                    blink_led('orange')
            
            time.sleep(1)
            count += 1
            
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    finally:
        # Clean shutdown
        for led in leds.values():
            led.off()
        print("Application shutdown complete")

if __name__ == "__main__":
    main()
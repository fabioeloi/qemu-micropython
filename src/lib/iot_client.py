"""
IoT Client for MicroPython STM32
--------------------------------
Provides connectivity to IoT platforms
"""
import json
import time
import machine
import network

# Configuration
DEFAULT_MQTT_HOST = "mqtt.example.com"
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_CLIENT_ID = "stm32-device"
DEFAULT_MQTT_TOPIC = "devices/stm32/telemetry"

# Try to import MQTT if available
try:
    from umqtt.simple import MQTTClient
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("MQTT library not available, telemetry will be simulated")

class IoTClient:
    """Base IoT client class"""
    def __init__(self, device_id=None):
        self.device_id = device_id or self._get_device_id()
        self.connected = False
    
    def _get_device_id(self):
        """Generate a unique device ID"""
        unique_id = machine.unique_id()
        return "stm32-" + "-".join(["{:02x}".format(b) for b in unique_id])
    
    def connect(self):
        """Connect to the IoT platform"""
        raise NotImplementedError("IoT client implementation must override connect()")
    
    def disconnect(self):
        """Disconnect from the IoT platform"""
        raise NotImplementedError("IoT client implementation must override disconnect()")
    
    def send_telemetry(self, data):
        """Send telemetry data to the IoT platform"""
        raise NotImplementedError("IoT client implementation must override send_telemetry()")
    
    def receive_command(self):
        """Receive command from the IoT platform"""
        raise NotImplementedError("IoT client implementation must override receive_command()")

class MQTTIoTClient(IoTClient):
    """MQTT-based IoT client"""
    def __init__(self, device_id=None, mqtt_host=DEFAULT_MQTT_HOST, 
                 mqtt_port=DEFAULT_MQTT_PORT, mqtt_client_id=None, stream=None):
        super().__init__(device_id)
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_client_id = mqtt_client_id or self.device_id
        self.mqtt_client = None
        self.stream = stream # Store the custom stream
        self.telemetry_topic = f"{DEFAULT_MQTT_TOPIC}/{self.device_id}"
        self.command_topic = f"devices/{self.device_id}/commands"
    
    def connect(self):
        """Connect to MQTT broker"""
        if not MQTT_AVAILABLE:
            print("MQTT library not available, operating in simulation mode")
            self.connected = True
            return True
        
        try:
            if self.stream:
                # When using a custom stream, host and port for MQTTClient might be None or placeholders,
                # as the stream itself handles the actual connection endpoint.
                # umqtt.simple.MQTTClient expects server, port, user, password, client_id, ssl, ssl_params, sock
                # We pass our stream as `sock`.
                # The `server` and `port` parameters are not strictly used by umqtt.simple if `sock` is provided,
                # but they are positional, so we provide them.
                # Let's use placeholder or the configured values if they make sense.
                # For a UART stream, host/port don't map directly.
                self.mqtt_client = MQTTClient(client_id=self.mqtt_client_id, 
                                              server=self.mqtt_host if self.mqtt_host else "uart.stream", 
                                              port=self.mqtt_port if self.mqtt_port else 0, 
                                              sock=self.stream,
                                              ssl=False) # Assuming no SSL over UART stream
            else:
                self.mqtt_client = MQTTClient(self.mqtt_client_id, self.mqtt_host, self.mqtt_port)
            
            self.mqtt_client.connect()
            self.mqtt_client.set_callback(self._on_message)
            self.mqtt_client.subscribe(self.command_topic)
            self.connected = True
            print(f"Connected to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.mqtt_client and self.connected:
            try:
                self.mqtt_client.disconnect()
                self.connected = False
                print("Disconnected from MQTT broker")
                return True
            except Exception as e:
                print(f"Error disconnecting from MQTT broker: {e}")
                return False
        return True
    
    def send_telemetry(self, data):
        """Send telemetry data to MQTT broker"""
        if not self.connected:
            self.connect()
        
        # Add timestamp and device ID
        data['device_id'] = self.device_id
        data['timestamp'] = time.time()
        
        # Convert to JSON
        json_data = json.dumps(data)
        
        if not MQTT_AVAILABLE or not self.mqtt_client:
            # Simulation mode
            print(f"[SIMULATED] Publishing to {self.telemetry_topic}: {json_data}")
            return True
        
        try:
            self.mqtt_client.publish(self.telemetry_topic, json_data)
            return True
        except Exception as e:
            print(f"Failed to publish MQTT message: {e}")
            self.connected = False
            return False
    
    def receive_command(self):
        """Check for incoming commands"""
        if not MQTT_AVAILABLE or not self.mqtt_client or not self.connected:
            return None
        
        try:
            self.mqtt_client.check_msg()
            # Actual message handling is done in _on_message callback
            return True
        except Exception as e:
            print(f"Error checking MQTT messages: {e}")
            return None
    
    def _on_message(self, topic, message):
        """Handle incoming MQTT messages"""
        try:
            topic_str = topic.decode('utf-8')
            message_str = message.decode('utf-8')
            
            if topic_str == self.command_topic:
                print(f"Received command: {message_str}")
                self._handle_command(json.loads(message_str))
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def _handle_command(self, command):
        """Process a command received from the IoT platform"""
        if 'action' in command:
            action = command['action']
            print(f"Executing action: {action}")
            
            if action == 'reboot':
                print("Rebooting device...")
                machine.reset()
            elif action == 'led_on' and 'color' in command:
                print(f"Turning on LED: {command['color']}")
                # Implementation would activate the specified LED
            elif action == 'led_off' and 'color' in command:
                print(f"Turning off LED: {command['color']}")
                # Implementation would deactivate the specified LED
            else:
                print(f"Unknown action: {action}")

# Create global client instance
_iot_client = None

def get_client(client_type='mqtt', **kwargs):
    """Get or create the IoT client instance"""
    global _iot_client
    
    if _iot_client is None:
        if client_type.lower() == 'mqtt':
            _iot_client = MQTTIoTClient(**kwargs)
        else:
            raise ValueError(f"Unsupported IoT client type: {client_type}")
    
    return _iot_client

def send_telemetry(data):
    """Send telemetry data using the default client"""
    client = get_client()
    return client.send_telemetry(data)

def receive_command():
    """Check for commands using the default client"""
    client = get_client()
    return client.receive_command()

def initialize(client_type='mqtt', **kwargs):
    """Initialize the IoT client"""
    client = get_client(client_type, **kwargs)
    return client.connect()
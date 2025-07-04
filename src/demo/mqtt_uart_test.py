import machine
import time
import json
from lib.iot_client import MQTTIoTClient, MQTT_AVAILABLE
from lib.uart_socket_wrapper import UARTSocket

# --- Test Configuration ---
DEFAULT_UART_ID = 0
DEFAULT_BAUDRATE = 115200
# These are conceptual for UARTSocket, but MQTTClient might still expect something.
# The actual host/port for the *mock broker script* are set when running that script.
DEFAULT_MOCK_BROKER_HOST_CONCEPTUAL = "uart_broker"
DEFAULT_MOCK_BROKER_PORT_CONCEPTUAL = 0 # Not used by UARTSocket directly

DEFAULT_CLIENT_ID_BASE = "stm32-uart-mqtt-device"

# --- Global state for received messages ---
received_messages = {} # topic -> payload

def mqtt_message_callback(topic, msg):
    """Callback for incoming MQTT messages."""
    topic_str = topic.decode('utf-8')
    msg_str = msg.decode('utf-8')
    print(f"TEST_CALLBACK: Received on topic '{topic_str}': {msg_str}")
    received_messages[topic_str] = msg_str

def setup_mqtt_client(uart_id, baudrate, client_id_suffix="", use_uart_stream=True, custom_stream=None):
    """Helper to initialize UART, UARTSocket (if applicable), and MQTTIoTClient."""
    print(f"\n--- Setting up MQTT Client (UART_ID={uart_id}, Baud={baudrate}, ClientIDSuffix='{client_id_suffix}') ---")

    if not MQTT_AVAILABLE:
        print("TEST_SETUP: umqtt.simple library is not available. Cannot proceed.")
        return None, None

    client_id = f"{DEFAULT_CLIENT_ID_BASE}{client_id_suffix}"
    uart = None
    stream_to_use = custom_stream

    if use_uart_stream and custom_stream is None:
        try:
            uart = machine.UART(uart_id, baudrate=baudrate, txbuf=2048, rxbuf=2048, timeout=100, timeout_char=100)
            print(f"TEST_SETUP: UART({uart_id}) initialized at {baudrate} baud.")
        except Exception as e:
            print(f"TEST_SETUP: Error initializing UART({uart_id}): {e}")
            return None, None

        uart_sock = UARTSocket(uart, host=DEFAULT_MOCK_BROKER_HOST_CONCEPTUAL, port=DEFAULT_MOCK_BROKER_PORT_CONCEPTUAL)
        print("TEST_SETUP: UARTSocket wrapper created for UART.")
        stream_to_use = uart_sock
    elif custom_stream:
        print("TEST_SETUP: Using provided custom stream.")
    else: # Not using UART stream and no custom stream (implies direct TCP, not for this test script's focus)
        print("TEST_SETUP: Configuring for direct TCP (not the primary test path for mqtt_uart_test.py).")
        # This case would require network interface to be up.

    print(f"TEST_SETUP: Initializing MQTTIoTClient with Client ID: {client_id}")
    mqtt_client = MQTTIoTClient(
        mqtt_client_id=client_id,
        mqtt_host=DEFAULT_MOCK_BROKER_HOST_CONCEPTUAL, # Conceptual for UART stream
        mqtt_port=DEFAULT_MOCK_BROKER_PORT_CONCEPTUAL, # Conceptual for UART stream
        stream=stream_to_use # This will be UARTSocket or the custom_stream
    )
    # Set the callback for all tests that might receive messages
    mqtt_client.mqtt_client.set_callback(mqtt_message_callback)
    print("TEST_SETUP: MQTTIoTClient initialized.")
    return mqtt_client, uart # uart is returned to allow for potential error simulation access

def cleanup_client(mqtt_client, uart_stream_obj):
    """Helper to disconnect client and close stream if applicable."""
    print("\n--- Cleaning up client ---")
    if mqtt_client and mqtt_client.connected:
        print("TEST_CLEANUP: Disconnecting MQTT client...")
        mqtt_client.disconnect()
    if uart_stream_obj and hasattr(uart_stream_obj, 'close'): # UARTSocket has close
        print("TEST_CLEANUP: Closing UARTSocket...")
        uart_stream_obj.close()
    print("TEST_CLEANUP: Cleanup complete.")

# --- Test Cases ---

def test_connect_ping_disconnect(uart_id, baudrate):
    """
    Tests basic MQTT connect, implicit PING (via keepalive if long enough,
    or relies on broker PINGREQ handling if client sends one), and disconnect.
    """
    print("\n===== Test: Connect, Ping (Implicit), Disconnect =====")
    test_passed = False
    mqtt_client, uart_obj_for_stream = setup_mqtt_client(uart_id, baudrate, client_id_suffix="-conn-ping-disc")

    if not mqtt_client:
        print("TEST_CONN_PING_DISC: FAIL - MQTT client setup failed.")
        return False

    uart_stream = mqtt_client.stream # This is the UARTSocket instance

    try:
        print("TEST_CONN_PING_DISC: Attempting to connect...")
        if mqtt_client.connect():
            print("TEST_CONN_PING_DISC: Connection successful.")

            # PING Test: umqtt.simple handles PINGREQ automatically based on keepalive.
            # For a short test, a PINGREQ might not be sent.
            # If keepalive is set in MQTTClient (default is 0, meaning disabled),
            # and connection is idle for `keepalive` seconds, check_msg() or wait_msg()
            # would send a PINGREQ.
            # Our mock broker logs PINGREQ and sends PINGRESP.
            # We will rely on observing broker logs for PINGREQ/PINGRESP.
            print("TEST_CONN_PING_DISC: Connection active. Monitor broker logs for PINGREQ/PINGRESP if keepalive triggers.")
            print("TEST_CONN_PING_DISC: (Note: umqtt.simple default keepalive is 0, may not send PING unless keepalive > 0)")
            # To force a PING for testing, one might need to modify umqtt.simple or use a client with explicit ping.
            # For now, this part is more of an observation point.
            # Let's simulate some delay to allow for potential keepalive PING
            if mqtt_client.mqtt_client.keepalive > 0:
                print(f"TEST_CONN_PING_DISC: Keepalive is {mqtt_client.mqtt_client.keepalive}s. Waiting...")
                time.sleep(mqtt_client.mqtt_client.keepalive + 5) # Wait longer than keepalive
                mqtt_client.mqtt_client.check_msg() # Trigger potential PING
                print("TEST_CONN_PING_DISC: check_msg() called after keepalive duration.")
            else:
                print("TEST_CONN_PING_DISC: Keepalive is 0. No PINGREQ will be sent automatically by umqtt.simple.")
                # We can try a check_msg to see if broker pings us (not standard)
                mqtt_client.mqtt_client.check_msg()


            print("TEST_CONN_PING_DISC: Attempting to disconnect...")
            if mqtt_client.disconnect():
                print("TEST_CONN_PING_DISC: Disconnection successful.")
                test_passed = True
            else:
                print("TEST_CONN_PING_DISC: FAIL - Disconnection failed.")
        else:
            print("TEST_CONN_PING_DISC: FAIL - Connection failed.")

    except Exception as e:
        print(f"TEST_CONN_PING_DISC: FAIL - Exception during test: {e}")
    finally:
        cleanup_client(mqtt_client, uart_stream)

    print(f"===== Test Connect, Ping, Disconnect: {'PASS' if test_passed else 'FAIL'} =====")
    return test_passed

def test_publish_subscribe_echo(uart_id, baudrate):
    """Tests publishing, subscribing, and receiving echoed messages."""
    print("\n===== Test: Publish, Subscribe, Echo =====")
    test_passed = False
    client_id_suffix = "-pub-sub-echo"
    client_id = f"{DEFAULT_CLIENT_ID_BASE}{client_id_suffix}"

    # Topics for this test
    echo_topic_template = f"devices/{client_id}/test_echo"
    # The mock broker is set to subscribe the client to its own telemetry topic for echo
    # and the command topic. We will use the command topic for a clear echo test.
    # Let's define a specific topic pattern the client will subscribe to for echo.
    subscribe_topic = f"device/+/test_echo_reply" # Client subscribes to this
    publish_to_trigger_echo_topic = f"device/{client_id}/test_echo_reply" # Client publishes to this, broker echoes

    no_echo_topic = f"devices/{client_id}/no_echo_test"

    mqtt_client, uart_obj_for_stream = setup_mqtt_client(uart_id, baudrate, client_id_suffix=client_id_suffix)

    if not mqtt_client:
        print("TEST_PUB_SUB_ECHO: FAIL - MQTT client setup failed.")
        return False

    uart_stream = mqtt_client.stream
    received_messages.clear() # Clear previous test messages

    try:
        if mqtt_client.connect():
            print("TEST_PUB_SUB_ECHO: Connection successful.")

            # Subscribe to the reply topic (where broker will echo)
            print(f"TEST_PUB_SUB_ECHO: Subscribing to '{subscribe_topic}'...")
            mqtt_client.mqtt_client.subscribe(subscribe_topic.encode('utf-8'))
            print("TEST_PUB_SUB_ECHO: subscribe() called. Waiting briefly for SUBACK (handled by umqtt).")
            time.sleep(1) # Give time for SUBACK to be processed by broker and client

            # Publish to the topic that the broker should echo back on 'subscribe_topic'
            payload_echo = {"message_type": "echo_test", "value": int(time.time())}
            payload_echo_json = json.dumps(payload_echo)
            print(f"TEST_PUB_SUB_ECHO: Publishing to '{publish_to_trigger_echo_topic}': {payload_echo_json}")
            mqtt_client.mqtt_client.publish(publish_to_trigger_echo_topic.encode('utf-8'), payload_echo_json.encode('utf-8'))

            print("TEST_PUB_SUB_ECHO: Waiting for echoed message...")
            time.sleep(1) # Initial wait
            mqtt_client.mqtt_client.check_msg() # Process incoming
            time.sleep(1) # Allow callback to process

            echo_received = False
            if publish_to_trigger_echo_topic in received_messages: # Broker echoes on the same topic it received
                if received_messages[publish_to_trigger_echo_topic] == payload_echo_json:
                    print(f"TEST_PUB_SUB_ECHO: PASS - Echo received successfully on '{publish_to_trigger_echo_topic}'.")
                    echo_received = True
                else:
                    print(f"TEST_PUB_SUB_ECHO: FAIL - Echo mismatch. Expected '{payload_echo_json}', got '{received_messages[publish_to_trigger_echo_topic]}'.")
            else:
                print(f"TEST_PUB_SUB_ECHO: FAIL - No echo received on '{publish_to_trigger_echo_topic}'. Messages: {received_messages}")

            # Publish to an unsubscribed topic (client is not subscribed, broker won't echo to client)
            received_messages.clear() # Clear for the no_echo part
            payload_no_echo = {"message_type": "no_echo_test", "value": "test2"}
            payload_no_echo_json = json.dumps(payload_no_echo)
            print(f"TEST_PUB_SUB_ECHO: Publishing to unsubscribed (by client) topic '{no_echo_topic}': {payload_no_echo_json}")
            # Note: The MQTTIoTClient.send_telemetry uses a pre-defined topic.
            # We use the raw mqtt_client.publish here for specific topic control.
            mqtt_client.mqtt_client.publish(no_echo_topic.encode('utf-8'), payload_no_echo_json.encode('utf-8'))

            print("TEST_PUB_SUB_ECHO: Waiting briefly to ensure no message on unsubscribed topic...")
            time.sleep(2)
            mqtt_client.mqtt_client.check_msg()

            no_echo_correct = True
            if no_echo_topic in received_messages:
                print(f"TEST_PUB_SUB_ECHO: FAIL - Message received on '{no_echo_topic}' when none expected.")
                no_echo_correct = False
            else:
                print(f"TEST_PUB_SUB_ECHO: PASS - No message received on '{no_echo_topic}', as expected.")

            if echo_received and no_echo_correct:
                test_passed = True
        else:
            print("TEST_PUB_SUB_ECHO: FAIL - Connection failed.")

    except Exception as e:
        print(f"TEST_PUB_SUB_ECHO: FAIL - Exception during test: {e}")
    finally:
        cleanup_client(mqtt_client, uart_stream)

    print(f"===== Test Publish, Subscribe, Echo: {'PASS' if test_passed else 'FAIL'} =====")
    return test_passed

def test_publish_with_uart_errors(uart_id, baudrate):
    """
    Observational test for MQTT operations with simulated UART errors/noise.
    This test relies on the custom UART driver's error simulation capabilities,
    which are not directly part of UARTSocket standard implementation.
    This test assumes such features would be in the underlying machine.UART if it's a custom one.
    For standard machine.UART, this test is purely observational on existing robustness.
    """
    print("\n===== Test: Publish with UART Errors (Observational) =====")
    test_passed = True # This is observational, so it "passes" by running
    mqtt_client, uart_for_stream = setup_mqtt_client(uart_id, baudrate, client_id_suffix="-uart-errors")

    if not mqtt_client:
        print("TEST_UART_ERRORS: FAIL - MQTT client setup failed.")
        return False # Cannot observe if setup fails

    uart_stream = mqtt_client.stream # This is the UARTSocket instance
                                     # uart_for_stream is the actual machine.UART if created

    print("TEST_UART_ERRORS: This test is observational.")
    print("TEST_UART_ERRORS: If using a custom UART driver with error simulation, enable it now.")
    print("TEST_UART_ERRORS: Otherwise, this tests robustness against any natural UART noise.")

    # Attempt to enable error/noise simulation on the UART object
    # These methods are expected to exist on the custom UART driver used in the QEMU environment
    if uart_for_stream:
        if hasattr(uart_for_stream, "set_error_simulation"):
            print("TEST_UART_ERRORS: Enabling UART error simulation (rate=0.1).")
            uart_for_stream.set_error_simulation(0.1) # Example: 10% error rate
        else:
            print("TEST_UART_ERRORS: uart.set_error_simulation method not found. Skipping.")

        if hasattr(uart_for_stream, "set_noise_simulation"):
            print("TEST_UART_ERRORS: Enabling UART noise simulation (level=0.05).")
            uart_for_stream.set_noise_simulation(0.05) # Example: 5% noise level
        else:
            print("TEST_UART_ERRORS: uart.set_noise_simulation method not found. Skipping.")
    else:
        print("TEST_UART_ERRORS: UART object (uart_for_stream) is None. Cannot set error/noise simulation.")


    try:
        print("TEST_UART_ERRORS: Attempting to connect...")
        if mqtt_client.connect():
            print("TEST_UART_ERRORS: Connection successful (or seemed to be).")

            payload = {"data_quality": "potentially_corrupt", "value": 123}
            json_payload = json.dumps(payload)
            print(f"TEST_UART_ERRORS: Attempting to publish: {json_payload}")

            # Using the client's send_telemetry method
            if mqtt_client.send_telemetry(payload):
                print("TEST_UART_ERRORS: send_telemetry reported success.")
            else:
                print("TEST_UART_ERRORS: send_telemetry reported failure. Check logs for errors.")
                # This doesn't mean the test "failed" in a hard sense, just an observation.

            print("TEST_UART_ERRORS: Attempting to check for messages (e.g. an echo if broker is set up for it)...")
            time.sleep(1)
            mqtt_client.mqtt_client.check_msg() # Might encounter errors here
            print("TEST_UART_ERRORS: check_msg executed.")

            print("TEST_UART_ERRORS: Attempting to disconnect...")
            mqtt_client.disconnect()
            print("TEST_UART_ERRORS: Disconnect attempt finished.")

        else:
            print("TEST_UART_ERRORS: Connection failed. This might be expected with high error rates.")

    except Exception as e:
        print(f"TEST_UART_ERRORS: Exception during MQTT operations with (simulated) UART errors: {e}")
        # This is an expected outcome in some error simulation scenarios.
    finally:
        if uart_for_stream:
            if hasattr(uart_for_stream, "set_error_simulation"):
                print("TEST_UART_ERRORS: Disabling UART error simulation.")
                uart_for_stream.set_error_simulation(0)
            if hasattr(uart_for_stream, "set_noise_simulation"):
                print("TEST_UART_ERRORS: Disabling UART noise simulation.")
                uart_for_stream.set_noise_simulation(0)

        cleanup_client(mqtt_client, uart_stream)

    print("===== Test Publish with UART Errors: COMPLETED (Observational) =====")
    return test_passed # Observational test is considered "passed" if it runs fully

def run_all_tests(uart_id, baudrate):
    """Runs all defined MQTT test cases sequentially."""
    print(f"\n===== Starting MQTT UART Test Suite (UART_ID={uart_id}, Baudrate={baudrate}) =====")

    results = {}

    results["connect_ping_disconnect"] = test_connect_ping_disconnect(uart_id, baudrate)
    time.sleep(2) # Pause between tests

    results["publish_subscribe_echo"] = test_publish_subscribe_echo(uart_id, baudrate)
    time.sleep(2) # Pause between tests

    results["publish_with_uart_errors"] = test_publish_with_uart_errors(uart_id, baudrate)

    print("\n===== MQTT UART Test Suite Summary =====")
    all_passed = True
    for test_name, status in results.items():
        print(f"Test '{test_name}': {'PASS' if status else 'FAIL'}")
        if not status:
            all_passed = False

    print(f"Overall Test Suite Result: {'PASS' if all_passed else 'FAIL'}")
    print("========================================")
    return all_passed

if __name__ == "__main__":
    # Configuration for the test run
    # These could be overridden by reading from a config file or args if running in a more complex harness
    uart_to_use = DEFAULT_UART_ID
    baudrate_to_use = DEFAULT_BAUDRATE

    print("----------------------------------------------------")
    print("--- MicroPython MQTT over UART Test Suite Runner ---")
    print("----------------------------------------------------")
    print(f"Target UART ID: {uart_to_use}, Baudrate: {baudrate_to_use}")
    print("Ensure the MQTT Mock Broker is running on the host and accessible.")
    print("The 'accessibility' for UART means a UART-to-TCP bridge (like socat or similar)")
    print("is correctly set up if the mock broker is TCP-based.")
    print("----------------------------------------------------")

    # Run the test suite
    run_all_tests(uart_to_use, baudrate_to_use)

    print("\nTest script finished.")
    # Note: If running on a board that goes into deep sleep or specific power modes,
    # ensure it stays active for the duration of the tests.
    # For QEMU, this is not an issue.
```

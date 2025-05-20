# MQTT Simulation over UART

## 1. Overview

This document describes the MQTT simulation setup for the STM32 IoT Virtual Development Environment. The primary purpose of this simulation is to allow testing of MQTT-based communication for MicroPython applications running in QEMU, without requiring a full network stack or a cloud-based MQTT broker.

The basic mechanism involves:
- A **host-side mock MQTT broker** (`tools/mqtt_mock_broker.py`) that listens on a TCP port.
- The MicroPython application on QEMU using its UART interface for communication.
- A **UART-to-TCP bridge** (e.g., `socat`) on the host that connects the QEMU's UART output to the mock broker's TCP port.
- A **UART socket wrapper** (`src/lib/uart_socket_wrapper.py`) in MicroPython that provides a socket-like interface over the UART, allowing the standard `umqtt.simple` library to be used with minimal changes.

This setup enables developers to test MQTT client logic, message publishing, and subscription handling in an isolated and controlled environment.

## 2. Components

### `tools/mqtt_mock_broker.py`
- A Python 3 script that acts as a simple MQTT broker.
- Listens for incoming TCP connections on a configurable host and port.
- Handles a single client connection at a time.
- Supports basic MQTT commands (CONNECT, PUBLISH, SUBSCRIBE, UNSUBSCRIBE, PINGREQ, DISCONNECT) with QoS 0.
- Echoes PUBLISH messages back to the client if the topic matches an active subscription.
- Provides console logging for received packets and actions taken.

### `src/lib/uart_socket_wrapper.py`
- A MicroPython module containing the `UARTSocket` class.
- This class wraps a `machine.UART` instance to provide a socket-like interface (`read`, `write`, `settimeout`, `close`, etc.).
- It allows the `umqtt.simple.MQTTClient` to use a UART peripheral as its communication stream.

### Modifications to `src/lib/iot_client.py`
- The `MQTTIoTClient` class in `src/lib/iot_client.py` was modified to accept an optional `stream` parameter in its constructor.
- If a `stream` object (like an instance of `UARTSocket`) is provided, the `MQTTIoTClient` will use this stream for MQTT communication instead of creating a network socket. This allows it to work over UART.

### `src/demo/mqtt_uart_test.py`
- A MicroPython example script that demonstrates how to use the MQTT simulation.
- Initializes UART, wraps it with `UARTSocket`.
- Uses `MQTTIoTClient` with the `UARTSocket` stream to connect to the host mock broker.
- Contains test functions for connecting, publishing, subscribing, receiving echoed messages, and observing behavior with (simulated) UART errors.

## 3. Setup and Usage

### Running the Mock Broker
The mock broker is a Python script that needs to be run on the host machine.

```bash
python3 tools/mqtt_mock_broker.py --host 127.0.0.1 --port 18888
```
- `--host`: The host address for the broker to listen on (default: `127.0.0.1`).
- `--port`: The TCP port for the broker to listen on (default: `18888`).

The broker will log its activity to the console.

### QEMU Configuration for UART Redirection
To connect QEMU's UART to the mock broker's TCP port, a UART-to-TCP bridge tool like `socat` can be used on the host.

1.  **Start `socat` (or a similar tool):**
    This command creates a pseudo-terminal (PTY) and links it to the TCP port where the mock broker is listening.

    ```bash
    socat PTY,link=/tmp/ttyS0,raw,echo=0 TCP:127.0.0.1:18888
    ```
    - `/tmp/ttyS0` is an example path for the PTY. Choose a suitable path.
    - `127.0.0.1:18888` should match the host and port the mock broker is using.

2.  **Configure QEMU to use the PTY for its serial port:**
    When launching QEMU, redirect one of its serial ports (e.g., `serial0` which often maps to `UART(0)` in MicroPython) to the PTY created by `socat`.

    ```bash
    qemu-system-arm \
        # ... other QEMU options (machine, kernel, etc.) ...
        -serial chardev:char_pty_serial0 \
        -chardev pty,id=char_pty_serial0,path=/tmp/ttyS0
        # ... or for older QEMU versions: -serial pty:/tmp/ttyS0
    ```
    Replace `/tmp/ttyS0` with the actual PTY path used by `socat`.

    Alternatively, QEMU can directly connect its serial port to a TCP server if the mock broker acts as a server (which it does). If you run the mock broker first, QEMU can connect to it as a client:
    ```bash
    # Start mock broker: python tools/mqtt_mock_broker.py --host 127.0.0.1 --port 18888
    # Then run QEMU with serial redirection to TCP client:
    qemu-system-arm \
        # ... other QEMU options ...
        -serial tcp:127.0.0.1:18888
    ```
    In this case, `socat` is not needed. The MicroPython script would use `UART(0)` as usual, and QEMU handles the redirection.

### Running the MicroPython Test Script
The `src/demo/mqtt_uart_test.py` script can be uploaded to the MicroPython filesystem on QEMU (e.g., using `mpremote` or by building it into the firmware) and then run from the MicroPython REPL:

```python
>>> import machine
>>> from src.demo import mqtt_uart_test
>>> # Configure UART ID and Baudrate if different from defaults in the script
>>> mqtt_uart_test.DEFAULT_UART_ID = 0
>>> mqtt_uart_test.DEFAULT_BAUDRATE = 115200
>>> mqtt_uart_test.run_all_tests(mqtt_uart_test.DEFAULT_UART_ID, mqtt_uart_test.DEFAULT_BAUDRATE)
```
The script will output test progress and results to the MicroPython console (QEMU's serial output).

## 4. Simulated MQTT Features

The mock broker and client setup primarily focus on **QoS 0** communication.

-   **Supported Commands:**
    -   `CONNECT`: Client requests connection.
    -   `CONNACK`: Broker acknowledges connection (always accepts).
    -   `PUBLISH`: Client sends a message. The mock broker will log this. If the topic is subscribed to by the client itself (an implicit behavior of the mock broker for simplicity), the message is echoed back to the client.
    -   `SUBSCRIBE`: Client subscribes to topic filters. The mock broker grants QoS 0 for all subscriptions.
    -   `SUBACK`: Broker acknowledges subscription.
    -   `UNSUBSCRIBE`: Client unsubscribes from topics.
    -   `UNSUBACK`: Broker acknowledges unsubscription.
    -   `PINGREQ`: Client pings broker to keep connection alive.
    -   `PINGRESP`: Broker responds to ping.
    -   `DISCONNECT`: Client disconnects.

-   **QoS 0 Focus:** All operations are treated as QoS 0. No support for message acknowledgements like PUBACK, PUBREC, PUBREL, PUBCOMP for QoS 1 or 2.

-   **Subscription Behavior (Echoing):**
    -   When the client subscribes to a topic, the mock broker stores this subscription.
    -   If the client publishes a message to a topic it is subscribed to, the mock broker will "echo" this PUBLISH message back to the client on the same topic. This helps test the client's receive path.
    -   The `MQTTIoTClient` by default subscribes to a command topic (`devices/{client_id}/commands`). The `mqtt_uart_test.py` script also demonstrates subscribing to custom topics.

## 5. Testing with UART Error/Noise Simulation

The environment allows for testing MQTT client resilience against UART communication issues if the underlying `machine.UART` implementation in QEMU (or a custom wrapper) supports error and noise simulation. The `src/demo/mqtt_uart_test.py` script includes a test case (`test_publish_with_uart_errors`) that attempts to use these features.

-   **Usage:**
    If the `machine.UART` object (referenced as `uart_for_stream` in the test script) has the methods:
    -   `uart_for_stream.set_error_simulation(rate)`: Call this to simulate random byte errors. `rate` is a float (e.g., `0.1` for 10% error rate).
    -   `uart_for_stream.set_noise_simulation(level)`: Call this to simulate random noise bytes being inserted. `level` is a float (e.g., `0.05` for 5% noise level relative to data).

    To disable, call them with `0`:
    -   `uart_for_stream.set_error_simulation(0)`
    -   `uart_for_stream.set_noise_simulation(0)`

-   **Purpose:**
    This allows developers to observe how the `UARTSocket` wrapper and the `umqtt.simple` library handle corrupted or noisy UART data. It helps in assessing the robustness of the MQTT communication over a potentially unreliable serial link. The test `test_publish_with_uart_errors` is primarily observational.

    **Note:** Standard MicroPython `machine.UART` typically does not include these simulation methods. They are assumed to be part of a custom UART driver/feature within this specific QEMU-based development environment.

## 6. Limitations

This MQTT simulation has several limitations and is **not a fully compliant MQTT broker**:

-   **QoS Levels:** Only QoS 0 is effectively supported. While the client might request other QoS levels in SUBSCRIBE packets, the broker grants QoS 0, and PUBLISH messages are handled as QoS 0.
-   **Authentication:** No support for MQTT username/password authentication or other security mechanisms (e.g., TLS/SSL, as communication is often over local TCP or PTY).
-   **Persistent Sessions:** Clean Session flag is implicitly treated as true. No session state is persisted across client disconnections.
-   **Wildcard Complexity:** Limited testing of complex topic wildcard subscriptions (`+`, `#`). Basic wildcards might work if `umqtt.simple` handles them locally before sending to the broker, but the broker's matching logic is simple.
-   **Single Client:** The mock broker is designed to handle only one client connection at a time.
-   **Retained Messages:** No support for retained messages.
-   **Last Will and Testament:** No support for LWT messages.
-   **Message Size:** The mock broker has a simplified remaining length decoding, assuming message lengths are less than 128 bytes for the main payload part. Larger messages might not be handled correctly.

## 7. Troubleshooting

-   **Connection Refused (Mock Broker):**
    -   Ensure the mock broker script (`tools/mqtt_mock_broker.py`) is running on the host.
    -   Verify the host IP and port used by the broker match the TCP endpoint configured for QEMU's UART redirection (e.g., in `socat` or QEMU's `-serial tcp` arguments).
    -   Check host firewall rules if connecting from QEMU to a non-localhost broker address.

-   **Connection Issues (QEMU to Broker via `socat`):**
    -   Ensure `socat` is running and the PTY path (`/tmp/ttyS0` or similar) matches QEMU's `-serial` configuration.
    -   Check permissions for the PTY device file.

-   **MicroPython Script Errors (`mqtt_uart_test.py`):**
    -   **`ImportError` for `umqtt.simple`:** Ensure `umqtt.simple` is available in your MicroPython build's frozen modules or on its filesystem.
    -   **`OSError` (e.g., `ENODEV`, `EIO`) from `machine.UART`:** Verify the UART ID (`0`, `1`, etc.) is correct for your QEMU setup or STM32 board. Ensure baudrate and other UART parameters are compatible.
    -   **MQTT connection timeouts/failures:** Check broker logs for any error messages. Increase timeouts in `UARTSocket` or `umqtt.simple` if communication is very slow, although this is unlikely in a local simulation.

-   **Messages Not Appearing / Echo Not Working:**
    -   Verify the topic strings used for publishing and subscribing match exactly (case-sensitive).
    -   Check the mock broker's console output. It logs all received PUBLISH messages and any subscriptions it's aware of. This can show if messages are reaching the broker and if the broker is attempting to echo them.
    -   Ensure the `mqtt_message_callback` in `mqtt_uart_test.py` is correctly set on the `mqtt_client.mqtt_client` instance.
    -   Call `mqtt_client.check_msg()` or `mqtt_client.wait_msg()` in your MicroPython script's loop to process incoming messages. The example script uses `check_msg()`.

-   **Debugging Tips:**
    -   Increase logging verbosity if possible (e.g., add more `print()` statements in `UARTSocket` or the test script).
    -   Use `mpremote` to inspect the MicroPython environment, view files, and run commands interactively.
    -   If using `socat` with a PTY, you can try tools like `minicom` or `screen` on the host to connect to the PTY and observe raw data flow (though this might interfere with `socat`'s connection to the broker).

This simulation provides a valuable tool for developing and testing MQTT applications in the STM32 IoT Virtual Development Environment, keeping in mind its scope and limitations.

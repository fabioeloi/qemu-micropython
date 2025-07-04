# CoAP Simulation for MicroPython in QEMU

## 1. Overview

This document describes the CoAP (Constrained Application Protocol) simulation setup designed for testing MicroPython CoAP client applications within the STM32 IoT Virtual Development Environment. The core idea is to enable MicroPython code running in QEMU (the "guest") to communicate via CoAP with a mock server running on the host machine.

This simulation relies on:
-   The `microCoAPy` library for providing the CoAP client API in MicroPython.
-   QEMU's user-mode networking (`-net user`), which allows the guest to access the host machine using a default IP address (`10.0.2.2`).
-   A host-side mock CoAP server that listens for UDP packets from the QEMU guest.

This setup allows developers to test CoAP client logic, message construction, and response handling without needing a physical network connection or an external CoAP server.

## 2. Components

### MicroPython CoAP Library (`src/lib/microcoapy/`)

*   **Library Used:** The project utilizes the `insighio/microCoAPy` library, which has been added to `src/lib/microcoapy/`.
*   **Role:** This library provides the necessary CoAP client functionalities (constructing packets, sending requests, parsing responses) for MicroPython applications.
*   **Integration:** It is included in the MicroPython firmware build via the manifest file `config/micropython/manifest.py`, which freezes the library files, making them available for import (e.g., `from microcoapy import microcoapy`).

### Host-Side CoAP Mock Server (`tools/coap_mock_server.py`)

*   **Implementation:** A Python 3 script that uses the `aiocoap` library to create a simple CoAP server.
*   **Functionality:** It listens for incoming CoAP requests on a configurable UDP host address and port (defaulting to `0.0.0.0:5683`).
*   **Resources:** The mock server provides several predefined resources for testing:
    *   `/test/hello`: A simple resource that returns a "Hello" message on GET.
    *   `/test/status`: A stateful resource that can be read (GET) and updated (PUT/POST) with JSON payloads.
    *   `/test/echo`: A resource that echoes back the payload received in a POST or PUT request.
    *   `/.well-known/core`: Standard resource for resource discovery.

### MicroPython Client Example/Test Script (`src/demo/coap_client_test.py`)

*   **Purpose:** This script demonstrates how to use the `microCoAPy` library in a MicroPython application to send CoAP requests to the host mock server and handle responses.
*   **Examples:** It includes examples of GET, POST, and PUT requests to the various resources exposed by the mock server.

## 3. Setup and Usage

Follow these steps to set up and use the CoAP simulation:

### Step 1: Install Host Dependency (`aiocoap`)

The host-side mock server requires the `aiocoap` Python library. Install it on your host machine:

```bash
python -m pip install aiocoap
# or
# pip install aiocoap
```

### Step 2: Run the Host CoAP Mock Server

Start the mock server on your host machine before running the MicroPython client in QEMU:

```bash
python tools/coap_mock_server.py --host 0.0.0.0 --port 5683
```
*   `--host`: Specifies the IP address the server listens on. `0.0.0.0` makes it accessible from QEMU.
*   `--port`: Specifies the UDP port. The default CoAP port is `5683`.
You can configure these if needed. The server will log its activity to the console.

### Step 3: Configure and Run QEMU

*   **Networking:** Standard QEMU user-mode networking is generally sufficient. This is often enabled by default or by using an argument like `-net user` in your QEMU launch command.
*   **Host IP Address:** When using user-mode networking, QEMU makes the host machine accessible to the guest OS at the IP address `10.0.2.2` (this is QEMU's default gateway, which also routes to the host).
*   **No Port Forwarding Needed (for guest-to-host):** Unlike scenarios where the host needs to initiate connections *to* the guest (which would require `hostfwd`), for the guest (MicroPython client) to connect to a server on the host at `10.0.2.2`, no special `hostfwd` rules are typically needed.

### Step 4: Run the MicroPython Client Test Script

1.  Ensure the `microCoAPy` library is frozen into your MicroPython firmware (as per `config/micropython/manifest.py`).
2.  Upload or include `src/demo/coap_client_test.py` in the MicroPython filesystem within QEMU.
3.  From the MicroPython REPL in QEMU, import and run the test script:

    ```python
    >>> import src.demo.coap_client_test
    >>> src.demo.coap_client_test.run_coap_client_tests()
    ```
    The client script is configured to send requests to the mock server at `10.0.2.2` on the port specified (e.g., 5683).

## 4. Simulated CoAP Features by Mock Server

The `tools/coap_mock_server.py` provides the following CoAP features:

*   **Request Methods:** Supports `GET`, `POST`, and `PUT` requests for its defined resources.
*   **Response Codes:** Returns standard CoAP response codes such as:
    *   `2.05 Content` (for successful GET requests or echo responses)
    *   `2.04 Changed` (for successful PUT/POST updates to `/test/status`)
    *   `4.04 Not Found` (for requests to undefined resources)
    *   `4.05 Method Not Allowed` (if a resource doesn't support a method)
    *   `4.00 Bad Request` (e.g., for malformed JSON payloads)
*   **Content Formats:** Handles `text/plain` and `application/json` content formats for relevant resources.
*   **Stateful Resources:** The `/test/status` resource maintains its state between requests, allowing clients to PUT new data and then GET it back to verify changes.
*   **Resource Discovery:** Supports basic resource discovery via `/.well-known/core`.

## 5. Limitations

*   **Mock Server Functionality:** The host-side mock server is intended for basic testing and is not a fully compliant or feature-rich CoAP server.
    *   **Observe:** While the `StatusResource` is an `ObservableResource` from `aiocoap`, the mock server script does not currently have explicit logic to manage observation relationships or send notifications beyond the initial setup. Full Observe (RFC 7641) testing would require more server-side logic.
    *   **Block-wise Transfers:** Handling of block-wise transfers (CoAP messages split into multiple blocks) depends on the underlying `aiocoap` library's default behavior. The mock server itself does not add specific logic for managing block transfers.
*   **Security:** DTLS (Datagram Transport Layer Security) for CoAP is not implemented in this simulation setup. Communication occurs over unencrypted UDP.
*   **Focus:** The primary goal is to test MicroPython client application logic against a controllable server, not to simulate complex network topologies or all CoAP server behaviors.

## 6. Troubleshooting

*   **Client: "No response" / Timeouts / `OSError: [Errno 113] EHOSTUNREACH` (or similar):**
    *   Verify the `tools/coap_mock_server.py` is running on the host.
    *   Ensure the IP address and port in `src/demo/coap_client_test.py` (e.g., `COAP_HOST_IP = "10.0.2.2"`, `COAP_HOST_PORT = 5683`) match where the mock server is listening.
    *   Confirm QEMU is running with user-mode networking enabled, allowing the guest to reach `10.0.2.2`.
    *   Check for host firewall rules that might be blocking UDP packets on the specified port.

*   **Host Server: `ImportError: No module named 'aiocoap'`:**
    *   The `aiocoap` library is not installed on the host. Install it using `pip install aiocoap`.

*   **Host Server: Address/Port Conflict Errors (e.g., "Address already in use"):**
    *   Another application on your host might be using the same UDP port. Stop the conflicting application or choose a different port for the mock server (and update the client script accordingly).

*   **General Debugging:**
    *   Examine the console output from `tools/coap_mock_server.py` for logs of received requests and any server-side errors.
    *   Check the MicroPython console output (from QEMU) for client-side error messages or print statements from `src/demo/coap_client_test.py`.
```

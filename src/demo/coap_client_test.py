# src/demo/coap_client_test.py

# This script demonstrates CoAP client functionality using the microCoAPy library.
# It assumes:
# 1. The 'microcoapy' library is available in the MicroPython path
#    (e.g., in '/lib/microcoapy/microcoapy.py' or similar).
# 2. The QEMU guest has network access (e.g., via '-net user').
# 3. The host-side 'tools/coap_mock_server.py' is running and listening on
#    COAP_HOST_IP:COAP_HOST_PORT.

import time
try:
    import usocket as socket
except ImportError:
    import socket # Standard Python socket for fallback if needed, though MicroPython uses usocket

# Attempt to import microcoapy - adjust if it's a directory or single file
try:
    from microcoapy import microcoapy # If microcoapy is a package/directory
                                  # Or: import microcoapy # if microcoapy.py is directly in lib
except ImportError as e:
    print(f"CRITICAL: microCoAPy library not found. Ensure it's in src/lib/microcoapy/ and frozen. {e}")
    # In a real scenario, you might copy it into your project's lib folder.
    # For this test, we'll raise SystemExit if it's not found.
    raise SystemExit("microCoAPy library not found.")

# Configuration for the CoAP Host Server
COAP_HOST_IP = "10.0.2.2"  # Default QEMU host IP from guest
COAP_HOST_PORT = 5683     # Default CoAP port

# Global variable to store the last received packet for assertions
last_received_packet = None
last_sender_info = None

def received_message_callback(packet, sender):
    global last_received_packet, last_sender_info
    print("----------------------------------------")
    print(f"Message received from: {sender}")
    print(f"Packet: {packet.toString()}") # microCoAPy's method to dump packet info
    if packet.payload:
        try:
            payload_str = packet.payload.decode('utf-8')
            print(f"Payload (UTF-8): '{payload_str}'")
        except UnicodeDecodeError:
            print(f"Payload (bytes): {packet.payload!r}")
    print("----------------------------------------")
    last_received_packet = packet
    last_sender_info = sender

def run_coap_client_tests():
    print(f"Starting CoAP client tests against {COAP_HOST_IP}:{COAP_HOST_PORT}...")

    coap_client = microcoapy.Coap()
    coap_client.responseCallback = received_message_callback

    # Start the client (opens UDP socket)
    # The start() method in microCoAPy by default binds to port 5683.
    # If the client needs to use a different source port, it can be passed to start() or Coap() constructor.
    try:
        client_socket_port = 5684 # Example client port, can be 0 for OS to pick
        coap_client.start(client_socket_port)
        print(f"CoAP client started, listening for responses on UDP port {client_socket_port}")
    except Exception as e:
        print(f"Error starting CoAP client: {e}")
        print("Ensure network is available and client_socket_port is not in use.")
        return False

    success_count = 0
    failure_count = 0
    global last_received_packet # Allow modification in test functions

    # --- Test 1: GET /test/hello ---
    print("\n[Test 1] GET /test/hello")
    last_received_packet = None
    try:
        bytes_sent = coap_client.get(COAP_HOST_IP, COAP_HOST_PORT, "test/hello")
        print(f"GET request sent ({bytes_sent} bytes). Waiting for response...")
        coap_client.poll(1000) # Poll for 1 second for a response

        if last_received_packet and last_received_packet.code == microcoapy.COAP_RESPONSE_CODE.COAP_CONTENT:
            expected_payload = b"Hello from CoAP Mock Server!"
            if last_received_packet.payload == expected_payload:
                print(f"GET /test/hello: PASS. Payload: {last_received_packet.payload.decode('utf-8')}")
                success_count +=1
            else:
                print(f"GET /test/hello: FAIL. Payload mismatch. Got: {last_received_packet.payload!r}, Expected: {expected_payload!r}")
                failure_count += 1
        elif last_received_packet:
            print(f"GET /test/hello: FAIL. Received CoAP code {last_received_packet.code}, expected CONTENT (2.05).")
            failure_count += 1
        else:
            print("GET /test/hello: FAIL. No response received.")
            failure_count += 1
    except Exception as e:
        print(f"GET /test/hello: ERROR - {e}")
        failure_count += 1

    # --- Test 2: POST /test/echo ---
    print("\n[Test 2] POST /test/echo")
    last_received_packet = None
    post_payload = b"Echo this message!"
    try:
        bytes_sent = coap_client.post(COAP_HOST_IP, COAP_HOST_PORT, "test/echo", post_payload,
                                      content_format=microcoapy.COAP_CONTENT_FORMAT.COAP_TEXT_PLAIN)
        print(f"POST request sent ({bytes_sent} bytes). Waiting for response...")
        coap_client.poll(1000)

        if last_received_packet and last_received_packet.code == microcoapy.COAP_RESPONSE_CODE.COAP_CONTENT:
            if last_received_packet.payload == post_payload:
                print(f"POST /test/echo: PASS. Echoed payload: {last_received_packet.payload.decode('utf-8')}")
                success_count +=1
            else:
                print(f"POST /test/echo: FAIL. Payload mismatch. Got: {last_received_packet.payload!r}, Expected: {post_payload!r}")
                failure_count += 1
        elif last_received_packet:
            print(f"POST /test/echo: FAIL. Received CoAP code {last_received_packet.code}, expected CONTENT (2.05).")
            failure_count += 1
        else:
            print("POST /test/echo: FAIL. No response received.")
            failure_count += 1
    except Exception as e:
        print(f"POST /test/echo: ERROR - {e}")
        failure_count += 1

    # --- Test 3: PUT /test/status to update, then GET to verify ---
    print("\n[Test 3] PUT /test/status and GET /test/status")
    last_received_packet = None
    put_payload_json = '{"status": "active", "value": 777}'
    put_payload_bytes = put_payload_json.encode('utf-8')

    try:
        # PUT request
        bytes_sent = coap_client.put(COAP_HOST_IP, COAP_HOST_PORT, "test/status", put_payload_bytes,
                                     content_format=microcoapy.COAP_CONTENT_FORMAT.COAP_APPLICATION_JSON)
        print(f"PUT request sent ({bytes_sent} bytes). Waiting for response...")
        coap_client.poll(1000) # Wait for ACK / separate response

        if last_received_packet and last_received_packet.code == microcoapy.COAP_RESPONSE_CODE.COAP_CHANGED:
            print(f"PUT /test/status: PASS (Received CHANGED 2.04).")
            success_count +=1
        elif last_received_packet:
            print(f"PUT /test/status: FAIL. Received CoAP code {last_received_packet.code}, expected CHANGED (2.04).")
            failure_count += 1
            # Continue to GET anyway to see what server returns
        else:
            print("PUT /test/status: FAIL. No response to PUT received.")
            failure_count += 1
            # Continue to GET anyway

        # GET request to verify
        print("Sending GET /test/status to verify PUT...")
        last_received_packet = None # Reset for the GET response
        bytes_sent = coap_client.get(COAP_HOST_IP, COAP_HOST_PORT, "test/status")
        print(f"GET request sent ({bytes_sent} bytes). Waiting for response...")
        coap_client.poll(1000)

        if last_received_packet and last_received_packet.code == microcoapy.COAP_RESPONSE_CODE.COAP_CONTENT:
            # Assuming server sends back the JSON payload after PUT
            if last_received_packet.payload == put_payload_bytes:
                 print(f"GET after PUT /test/status: PASS. Payload: {last_received_packet.payload.decode('utf-8')}")
                 success_count +=1 # This test actually has two success points
            else:
                print(f"GET after PUT /test/status: FAIL. Payload mismatch. Got: {last_received_packet.payload!r}, Expected: {put_payload_bytes!r}")
                failure_count += 1
        elif last_received_packet:
            print(f"GET after PUT /test/status: FAIL. Received CoAP code {last_received_packet.code}, expected CONTENT (2.05).")
            failure_count += 1
        else:
            print("GET after PUT /test/status: FAIL. No response to GET received.")
            failure_count += 1

    except Exception as e:
        print(f"PUT/GET /test/status: ERROR - {e}")
        failure_count += 1

    # --- Test 4: GET non-existent resource ---
    print("\n[Test 4] GET /test/nonexistent")
    last_received_packet = None
    try:
        bytes_sent = coap_client.get(COAP_HOST_IP, COAP_HOST_PORT, "test/nonexistent")
        print(f"GET request sent ({bytes_sent} bytes). Waiting for response...")
        coap_client.poll(1000)

        if last_received_packet and last_received_packet.code == microcoapy.COAP_RESPONSE_CODE.COAP_NOT_FOUND:
            print(f"GET /test/nonexistent: PASS. Received NOT_FOUND (4.04).")
            success_count +=1
        elif last_received_packet:
            print(f"GET /test/nonexistent: FAIL. Received CoAP code {last_received_packet.code}, expected NOT_FOUND (4.04).")
            failure_count += 1
        else:
            print("GET /test/nonexistent: FAIL. No response received.")
            failure_count += 1
    except Exception as e:
        print(f"GET /test/nonexistent: ERROR - {e}")
        failure_count += 1

    # Stop the client
    print("\nStopping CoAP client...")
    coap_client.stop()
    print("CoAP client stopped.")

    print("\n--- CoAP Client Test Summary ---")
    total_tests = success_count + failure_count
    print(f"Total assertions/checks: {total_tests}") # Note: Test 3 has two potential success points
    print(f"Passed: {success_count}")
    print(f"Failed: {failure_count}")
    print("================================")

    return failure_count == 0

if __name__ == "__main__":
    # This is important for MicroPython: ensure network is connected before running.
    # For QEMU user-net, it's usually available by default.
    # For real hardware, you'd connect to Wi-Fi/Ethernet here.
    # Example:
    # import network
    # sta_if = network.WLAN(network.STA_IF); sta_if.active(True)
    # sta_if.connect("YOUR_SSID", "YOUR_PASSWORD")
    # while not sta_if.isconnected():
    #     time.sleep(0.1)
    # print("Network connected:", sta_if.ifconfig())

    run_coap_client_tests()
```

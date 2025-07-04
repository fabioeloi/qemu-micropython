import random
try:
    import usocket as socket
except ImportError:
    import socket

from . import coap_macros
from . import coap_packet
from . import coap_option

class Coap:
    """
    MicroCoAPy Client/Server class
    """

    def __init__(self, ipAddress="0.0.0.0", port=coap_macros.COAP_DEFAULT_PORT, sock=None, responseCallback=None):
        self._ipAddress = ipAddress
        self._port = port
        self._sock = sock
        self._responseCallback = responseCallback

        self._messageId = random.randint(0, 65535)
        self._token = random.randint(0, 65535)

        self._transactions = {} # To track ongoing transactions by token

    def close(self):
        if self._sock:
            self._sock.close()
            self._sock = None

    def start(self, clientPort=coap_macros.COAP_DEFAULT_PORT):
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.bind((self._ipAddress, clientPort)) # Bind to specified client port for listening
        # Set non-blocking if possible (MicroPython sockets are often non-blocking by default or via settimeout(0))
        # self._sock.setblocking(False) # Or self._sock.settimeout(0)

    def stop(self):
        self.close()

    def sendPacket(self, packet, destIp, destPort):
        if self._sock is None:
            # If socket not started, maybe start it on a random port or default?
            # For client operations, it's common to start implicitly if not done.
            # However, for this library, explicit start() is preferred.
            raise Exception("Socket not started. Call start() first.")

        bytesSent = self._sock.sendto(packet.toBytes(), (destIp, destPort))
        if bytesSent <= 0:
            raise Exception("Error sending CoAP packet")
        return bytesSent

    # Client: High-level methods (GET, POST, PUT, DELETE)
    def get(self, destIp, destPort, path, confirmable=True, options=None, token=None):
        packet = coap_packet.CoapPacket()
        packet.type = coap_macros.COAP_TYPE.COAP_CON if confirmable else coap_macros.COAP_TYPE.COAP_NONCON
        packet.code = coap_macros.COAP_REQUEST_CODE.COAP_GET
        packet.messageid = self._nextMessageId()
        packet.token = token if token is not None else self._nextToken()

        if options is None:
            options = []

        options.append(coap_option.CoapOption(coap_macros.COAP_OPTION_NUMBER.COAP_URI_PATH, path.encode('utf-8')))
        packet.options = options

        self._transactions[packet.token] = packet # Track this transaction
        return self.sendPacket(packet, destIp, destPort)

    def post(self, destIp, destPort, path, payload, confirmable=True, options=None, token=None, content_format=None):
        packet = coap_packet.CoapPacket()
        packet.type = coap_macros.COAP_TYPE.COAP_CON if confirmable else coap_macros.COAP_TYPE.COAP_NONCON
        packet.code = coap_macros.COAP_REQUEST_CODE.COAP_POST
        packet.messageid = self._nextMessageId()
        packet.token = token if token is not None else self._nextToken()

        if options is None:
            options = []

        options.append(coap_option.CoapOption(coap_macros.COAP_OPTION_NUMBER.COAP_URI_PATH, path.encode('utf-8')))
        if content_format is not None:
            options.append(coap_option.CoapOption(coap_macros.COAP_OPTION_NUMBER.COAP_CONTENT_FORMAT, content_format.to_bytes(1, 'big')))

        packet.options = options
        packet.payload = payload if isinstance(payload, bytes) else payload.encode('utf-8')

        self._transactions[packet.token] = packet
        return self.sendPacket(packet, destIp, destPort)

    def put(self, destIp, destPort, path, payload, confirmable=True, options=None, token=None, content_format=None):
        packet = coap_packet.CoapPacket()
        packet.type = coap_macros.COAP_TYPE.COAP_CON if confirmable else coap_macros.COAP_TYPE.COAP_NONCON
        packet.code = coap_macros.COAP_REQUEST_CODE.COAP_PUT
        packet.messageid = self._nextMessageId()
        packet.token = token if token is not None else self._nextToken()

        if options is None:
            options = []

        options.append(coap_option.CoapOption(coap_macros.COAP_OPTION_NUMBER.COAP_URI_PATH, path.encode('utf-8')))
        if content_format is not None:
            options.append(coap_option.CoapOption(coap_macros.COAP_OPTION_NUMBER.COAP_CONTENT_FORMAT, content_format.to_bytes(1, 'big')))

        packet.options = options
        packet.payload = payload if isinstance(payload, bytes) else payload.encode('utf-8')

        self._transactions[packet.token] = packet
        return self.sendPacket(packet, destIp, destPort)

    def delete(self, destIp, destPort, path, confirmable=True, options=None, token=None):
        packet = coap_packet.CoapPacket()
        packet.type = coap_macros.COAP_TYPE.COAP_CON if confirmable else coap_macros.COAP_TYPE.COAP_NONCON
        packet.code = coap_macros.COAP_REQUEST_CODE.COAP_DELETE
        packet.messageid = self._nextMessageId()
        packet.token = token if token is not None else self._nextToken()

        if options is None:
            options = []

        options.append(coap_option.CoapOption(coap_macros.COAP_OPTION_NUMBER.COAP_URI_PATH, path.encode('utf-8')))
        packet.options = options

        self._transactions[packet.token] = packet
        return self.sendPacket(packet, destIp, destPort)

    def poll(self, timeoutMs=1000, pollCount=1):
        if self._sock is None:
            return

        # Attempt to make socket non-blocking for polling
        try:
            self._sock.settimeout(timeoutMs / 1000.0 / pollCount) # Timeout for each recvfrom call
        except AttributeError:
            # Some MicroPython ports might not have settimeout, or it behaves differently
            # In this case, recvfrom might be blocking or have fixed timeout
            pass

        for _ in range(pollCount):
            try:
                # Max CoAP packet size can be ~1280 (IPv6 MTU) or more, but usually smaller
                # For UDP, can be up to 65507. Let's use a reasonable buffer.
                rawdata, sender = self._sock.recvfrom(1152 + 4) # 1152 for CoAP over UDP + header

                if rawdata:
                    packet = coap_packet.CoapPacket.fromBytes(rawdata)

                    # Check if this packet matches a transaction
                    if packet.token in self._transactions:
                        # Potentially remove transaction or mark as complete based on CON/ACK logic
                        # For now, just forward to callback
                        if self._responseCallback:
                            self._responseCallback(packet, sender)
                        # If CON message, server might expect an ACK. Client role here is simpler.
                        # If we received a CON response, we might need to send an ACK.
                        # microCoAPy client usually sends CON, expects ACK or Reset.
                        # If this is an ACK to our CON, or a separate response.
                        if packet.type == coap_macros.COAP_TYPE.COAP_ACK and \
                           packet.code.isResponse(): #Or COAP_EMPTY if just ACK
                            # This is an ACK to our CON request, possibly with payload.
                            # The callback handles it.
                            # We can clear the transaction if it's a final ACK/response for this token.
                            # This simplistic client doesn't handle separate ACKs vs piggybacked responses well for clearing transactions
                            if packet.code != coap_macros.COAP_RESPONSE_CODE.COAP_EMPTY or packet.payload: # If it's not just an empty ACK
                                if packet.token in self._transactions:
                                    del self._transactions[packet.token]

                        elif packet.type == coap_macros.COAP_TYPE.COAP_RST: # Reset received
                            if packet.token in self._transactions:
                                del self._transactions[packet.token]
                            # Handle reset appropriately (e.g. log error)

                        # If server sends CON and we need to ACK (less common for simple client)
                        if packet.type == coap_macros.COAP_TYPE.COAP_CON and packet.code.isResponse():
                            ack_packet = coap_packet.CoapPacket()
                            ack_packet.type = coap_macros.COAP_TYPE.COAP_ACK
                            ack_packet.code = coap_macros.COAP_RESPONSE_CODE.COAP_EMPTY # Empty ACK
                            ack_packet.messageid = packet.messageid # ACK the received message ID
                            ack_packet.token = packet.token # Echo token
                            self.sendPacket(ack_packet, sender[0], sender[1])


                    elif self._responseCallback: # Unmatched token, but pass to callback anyway
                        self._responseCallback(packet, sender)

            except socket.timeout: # More standard way to check for no data on non-blocking socket
                continue # No data received in this poll interval
            except OSError as e:
                # In MicroPython, EAGAIN or EWOULDBLOCK indicates no data
                if e.args[0] == 11: # EAGAIN / EWOULDBLOCK
                    continue
                else:
                    # print(f"Socket error during poll: {e}") # Or handle more gracefully
                    pass # Ignore other socket errors for now during poll
            except Exception as e:
                # print(f"Error processing received packet: {e}")
                pass # Ignore for now

    def _nextMessageId(self):
        self._messageId = (self._messageId + 1) & 0xFFFF # Wrap around 16-bit
        return self._messageId

    def _nextToken(self):
        # Token can be up to 8 bytes. microCoAPy original uses a 16-bit int.
        # For simplicity, let's stick to a 16-bit integer token, encoded as needed.
        self._token = (self._token + 1) & 0xFFFF
        # Return as bytes. Length will be inferred by CoapPacket based on value.
        # If token is 0, it will be empty bytes.
        if self._token == 0: # Avoid token value 0 if it means "empty token"
            self._token = 1
        return self._token.to_bytes(2, 'big') # Use 2 bytes for token for simplicity

    # Server methods (basic example, not fully implemented for robust server)
    def sendResponse(self, remote_ip, remote_port, message_id, token, payload=None, response_code=coap_macros.COAP_RESPONSE_CODE.COAP_CONTENT, content_format=None):
        response_packet = coap_packet.CoapPacket()
        # Determine if ACK or CON based on original request (not tracked here, assume ACK for now)
        response_packet.type = coap_macros.COAP_TYPE.COAP_ACK
        response_packet.code = response_code
        response_packet.messageid = message_id # Echo message ID for ACK
        response_packet.token = token         # Echo token

        if content_format is not None:
            response_packet.options.append(coap_option.CoapOption(coap_macros.COAP_OPTION_NUMBER.COAP_CONTENT_FORMAT, content_format.to_bytes(1, 'big')))

        if payload:
            response_packet.payload = payload if isinstance(payload, bytes) else payload.encode('utf-8')

        self.sendPacket(response_packet, remote_ip, remote_port)

    # Example of a simple server loop (would need more robust handling)
    # def serverLoop(self, callback):
    #     if self._sock is None:
    #         self.start(self._port) # Start listening on the server port
    #     print(f"CoAP server listening on {self._ipAddress}:{self._port}")

    #     while True:
    #         try:
    #             rawdata, sender = self._sock.recvfrom(1024)
    #             if rawdata:
    #                 request_packet = coap_packet.CoapPacket.fromBytes(rawdata)
    #                 print(f"Server received packet from {sender}: {request_packet.toString()}")

    #                 # Invoke user-defined callback to handle the request
    #                 # This callback would be responsible for generating and sending a response
    #                 callback(request_packet, sender, self) # Pass self to allow callback to use sendResponse

    #         except Exception as e:
    #             print(f"Server error: {e}")
    #             # May need to re-initialize socket on some errors
    #             time.sleep(1)
```

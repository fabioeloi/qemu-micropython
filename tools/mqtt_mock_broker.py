import socket
import struct
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# MQTT Control Packet Types
CONNECT = 0x10
CONNACK = 0x20
PUBLISH = 0x30
PUBACK = 0x40 # Not implementing for QoS 0 focus, but good to list
PUBREC = 0x50
PUBREL = 0x60
PUBCOMP = 0x70
SUBSCRIBE = 0x80
SUBACK = 0x90
UNSUBSCRIBE = 0xA0
UNSUBACK = 0xB0
PINGREQ = 0xC0
PINGRESP = 0xD0
DISCONNECT = 0xE0

# CONNACK Reason Codes
CONNECTION_ACCEPTED = 0x00

class MQTTMockBroker:
    def __init__(self, host='127.0.0.1', port=18888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.client_id = None
        self.subscriptions = {} # topic -> qos (0 for now)
        self.packet_id_counter = 1 # For PUBACK, SUBACK, UNSUBACK

    def _next_packet_id(self):
        pid = self.packet_id_counter
        self.packet_id_counter += 1
        if self.packet_id_counter > 0xFFFF:
            self.packet_id_counter = 1
        return pid

    def _parse_mqtt_packet(self, data):
        if not data:
            return None, None, None
        
        packet_type = data[0] & 0xF0
        # Remaining length decoding (simplified for now, assumes length < 128)
        remaining_length = data[1]
        payload = data[2:2+remaining_length]
        
        return packet_type, remaining_length, payload

    def _create_connack_packet(self, session_present=0, reason_code=0):
        fixed_header = struct.pack('!BB', CONNACK, 2) # Type, Remaining Length
        variable_header = struct.pack('!BB', session_present, reason_code)
        return fixed_header + variable_header

    def _create_publish_packet(self, topic, message, packet_id=None, qos=0, retain=0, dup=0):
        # Fixed header (first byte)
        header_byte1 = PUBLISH | (dup << 3) | (qos << 1) | retain

        # Variable header: Topic
        topic_bytes = topic.encode('utf-8')
        variable_header = struct.pack('!H', len(topic_bytes)) + topic_bytes
        if qos > 0:
            if packet_id is None:
                packet_id = self._next_packet_id()
            variable_header += struct.pack('!H', packet_id)

        # Payload
        payload_bytes = message.encode('utf-8') if isinstance(message, str) else message

        # Remaining length
        remaining_length = len(variable_header) + len(payload_bytes)
        
        # Remaining length encoding (simplified)
        if remaining_length > 127:
            # This simplified version doesn't handle multi-byte remaining lengths
            raise ValueError("Message too long for simplified remaining length encoding")
        
        return bytes([header_byte1, remaining_length]) + variable_header + payload_bytes

    def _create_suback_packet(self, packet_id, reason_codes):
        fixed_header = struct.pack('!B', SUBACK) # Type
        variable_header = struct.pack('!H', packet_id)
        payload = bytes(reason_codes)
        remaining_length = len(variable_header) + len(payload)
        return fixed_header + bytes([remaining_length]) + variable_header + payload
        
    def _create_unsuback_packet(self, packet_id):
        fixed_header = struct.pack('!B', UNSUBACK) # Type
        variable_header = struct.pack('!H', packet_id)
        remaining_length = len(variable_header)
        return fixed_header + bytes([remaining_length]) + variable_header

    def _create_pingresp_packet(self):
        return struct.pack('!BB', PINGRESP, 0)

    def handle_connect(self, payload):
        # Protocol Name (MQTT)
        proto_name_len = struct.unpack('!H', payload[:2])[0]
        proto_name = payload[2:2+proto_name_len].decode('utf-8')
        offset = 2 + proto_name_len
        
        # Protocol Level, Connect Flags, Keep Alive
        protocol_level, connect_flags, keep_alive = struct.unpack('!BBH', payload[offset:offset+4])
        offset += 4
        
        # Client ID
        client_id_len = struct.unpack('!H', payload[offset:offset+2])[0]
        offset += 2
        self.client_id = payload[offset:offset+client_id_len].decode('utf-8')
        
        logging.info(f"BROKER: CONNECT received from ClientID='{self.client_id}', Protocol='{proto_name}', ProtocolLevel={protocol_level}, ConnectFlags={hex(connect_flags)}, KeepAlive={keep_alive}")
        
        connack_packet = self._create_connack_packet(reason_code=CONNECTION_ACCEPTED)
        self.client_socket.sendall(connack_packet)
        logging.info(f"BROKER: CONNACK sent to ClientID='{self.client_id}' with ReasonCode={CONNECTION_ACCEPTED}")

    def handle_publish(self, payload):
        topic_len = struct.unpack('!H', payload[:2])[0]
        topic = payload[2:2+topic_len].decode('utf-8')
        offset = 2 + topic_len
        
        # Assuming QoS 0, no packet ID in variable header for incoming message
        message_payload = payload[offset:] # Keep as bytes for now
        
        try:
            message_str = message_payload.decode('utf-8')
            log_message = message_str
        except UnicodeDecodeError:
            log_message = message_payload.hex() # Log hex if not valid UTF-8

        logging.info(f"BROKER: PUBLISH received from ClientID='{self.client_id}': Topic='{topic}', Message='{log_message}' (PayloadHex: {message_payload.hex()})")
        
        # Echo to subscribed clients (in this case, only self if subscribed)
        # This mock broker only handles one client at a time, so it echoes to the sender if subscribed.
        if topic in self.subscriptions:
            logging.info(f"BROKER: Topic '{topic}' is in subscriptions for ClientID='{self.client_id}'. Echoing PUBLISH.")
            # For QoS 0, server just sends PUBLISH. No PUBACK expected from client for this echo.
            publish_echo_packet = self._create_publish_packet(topic, message_payload) # Send original bytes
            self.client_socket.sendall(publish_echo_packet)
            logging.info(f"BROKER: Echo PUBLISH sent to ClientID='{self.client_id}': Topic='{topic}', Message='{log_message}'")
        else:
            logging.info(f"BROKER: Topic '{topic}' not in subscriptions for ClientID='{self.client_id}'. No echo sent.")

    def handle_subscribe(self, payload):
        packet_id = struct.unpack('!H', payload[:2])[0]
        offset = 2
        
        topics_requested = []
        reason_codes = []
        
        while offset < len(payload):
            topic_filter_len = struct.unpack('!H', payload[offset:offset+2])[0]
            offset += 2
            topic_filter = payload[offset:offset+topic_filter_len].decode('utf-8')
            offset += topic_filter_len
            requested_qos = payload[offset] # QoS for this topic
            offset += 1
            
            self.subscriptions[topic_filter] = requested_qos # Store with requested QoS
            topics_requested.append(topic_filter)
            # For this mock, we always grant QoS 0, regardless of requested_qos
            granted_qos = 0x00 
            reason_codes.append(granted_qos) 
            logging.info(f"BROKER: SUBSCRIBE received from ClientID='{self.client_id}': TopicFilter='{topic_filter}', RequestedQoS={requested_qos}, PacketID={packet_id}")
            
        suback_packet = self._create_suback_packet(packet_id, reason_codes)
        self.client_socket.sendall(suback_packet)
        logging.info(f"BROKER: SUBACK sent to ClientID='{self.client_id}': PacketID={packet_id}, GrantedQoS/ReasonCodes={reason_codes}")

    def handle_unsubscribe(self, payload):
        packet_id = struct.unpack('!H', payload[:2])[0]
        offset = 2
        
        unsubscribed_topics = []
        while offset < len(payload):
            topic_filter_len = struct.unpack('!H', payload[offset:offset+2])[0]
            offset += 2
            topic_filter = payload[offset:offset+topic_filter_len].decode('utf-8')
            offset += topic_filter_len
            
            logging.info(f"BROKER: UNSUBSCRIBE received from ClientID='{self.client_id}': TopicFilter='{topic_filter}', PacketID={packet_id}")
            if topic_filter in self.subscriptions:
                del self.subscriptions[topic_filter]
                logging.info(f"BROKER: Subscription to '{topic_filter}' removed for ClientID='{self.client_id}'.")
            else:
                logging.warning(f"BROKER: ClientID='{self.client_id}' tried to UNSUBSCRIBE from non-existent subscription '{topic_filter}'.")
            unsubscribed_topics.append(topic_filter)

        # MQTT v3.1.1 UNSUBACK does not have a payload with reason codes.
        # MQTT v5.0 UNSUBACK can have reason codes. This broker is more v3.1.1 like.
        unsuback_packet = self._create_unsuback_packet(packet_id) 
        self.client_socket.sendall(unsuback_packet)
        logging.info(f"BROKER: UNSUBACK sent to ClientID='{self.client_id}': PacketID={packet_id} (for topics: {unsubscribed_topics})")


    def handle_pingreq(self):
        logging.info(f"BROKER: PINGREQ received from ClientID='{self.client_id}'")
        pingresp_packet = self._create_pingresp_packet()
        self.client_socket.sendall(pingresp_packet)
        logging.info(f"BROKER: PINGRESP sent to ClientID='{self.client_id}'")

    def handle_disconnect(self):
        logging.info(f"BROKER: DISCONNECT received from ClientID='{self.client_id}'")
        # No response packet for DISCONNECT
        return False # Signal to close connection

    def process_packet(self, packet_type, payload):
        if packet_type == CONNECT:
            self.handle_connect(payload)
        elif packet_type == PUBLISH:
            self.handle_publish(payload)
        elif packet_type == SUBSCRIBE:
            self.handle_subscribe(payload)
        elif packet_type == UNSUBSCRIBE:
            self.handle_unsubscribe(payload)
        elif packet_type == PINGREQ:
            self.handle_pingreq()
        elif packet_type == DISCONNECT:
            return self.handle_disconnect() # This will return False
        else:
            logging.warning(f"BROKER: Unsupported packet type: {hex(packet_type)} from ClientID='{self.client_id or 'Unknown'}'")
        return True # Signal to keep connection open

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        logging.info(f"MQTT Mock Broker listening on {self.host}:{self.port}")

        try:
            while True: # Outer loop to accept new connections
                self.client_socket, self.client_address = self.server_socket.accept()
                logging.info(f"BROKER: Accepted connection from {self.client_address}")
                self.client_id = None # Reset for new connection
                self.subscriptions = {} # Reset for new connection
                
                try:
                    keep_conn_open = True
                    while keep_conn_open:
                        # Simple blocking read. For a real broker, use selectors/asyncio.
                        # First byte: Packet Type and Flags
                        # This part assumes the client sends valid MQTT packets.
                        # A robust broker would have more sophisticated framing and error handling.
                        first_byte = self.client_socket.recv(1)
                        if not first_byte:
                            logging.info(f"BROKER: Client {self.client_address} (ClientID: {self.client_id or 'N/A'}) closed connection (no data for first byte).")
                            break
                        
                        packet_type = first_byte[0] & 0xF0
                        
                        # Decode remaining length (simplified for single byte)
                        # A full implementation needs to handle multi-byte remaining length.
                        length_byte = self.client_socket.recv(1)
                        if not length_byte:
                            logging.warning(f"BROKER: Client {self.client_address} (ClientID: {self.client_id or 'N/A'}) closed connection abruptly after first byte.")
                            break
                        remaining_length = length_byte[0] # Assumes length < 128
                        
                        payload = b''
                        if remaining_length > 0:
                            payload = self.client_socket.recv(remaining_length)
                            if len(payload) < remaining_length:
                                logging.warning(f"BROKER: Did not receive full payload from {self.client_address} (ClientID: {self.client_id or 'N/A'}). Expected {remaining_length}, got {len(payload)}. Closing connection.")
                                break 
                        
                        logging.debug(f"BROKER: Received Raw from ClientID='{self.client_id or 'Unknown'}': TypeByte={hex(first_byte[0])}, RemLenByte={hex(length_byte[0])}, Payload={payload.hex()}")
                        
                        keep_conn_open = self.process_packet(packet_type, payload)
                        if not keep_conn_open: # DISCONNECT received or critical error
                            logging.info(f"BROKER: Closing connection with {self.client_address} (ClientID: {self.client_id}) as requested by client or due to error.")
                            break
                
                except socket.timeout:
                    logging.warning(f"BROKER: Socket timeout with {self.client_address} (ClientID: {self.client_id or 'N/A'})")
                except ConnectionResetError:
                    logging.warning(f"BROKER: Connection reset by {self.client_address} (ClientID: {self.client_id or 'N/A'})")
                except Exception as e:
                    logging.error(f"BROKER: Error during client handling for {self.client_address} (ClientID: {self.client_id or 'N/A'}): {e}", exc_info=True)
                finally:
                    if self.client_socket:
                        self.client_socket.close()
                    logging.info(f"BROKER: Connection closed with {self.client_address} (ClientID: {self.client_id or 'N/A'})")
                    # self.client_id and self.subscriptions are reset at the start of the accept loop

        except KeyboardInterrupt:
            logging.info("BROKER: Shutting down...")
        finally:
            if self.server_socket:
                self.server_socket.close()
            logging.info("BROKER: Stopped.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MQTT Mock Broker")
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind the broker to.')
    parser.add_argument('--port', type=int, default=18888, help='Port to bind the broker to.')
    args = parser.parse_args()

    broker = MQTTMockBroker(host=args.host, port=args.port)
    broker.run()

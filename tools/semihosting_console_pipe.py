import socket
import struct
import argparse
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - HOST_PIPE - %(levelname)s - %(message)s')

def recv_all(sock, length):
    """Helper function to receive exactly 'length' bytes from socket."""
    data = b''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError(f"Socket closed prematurely. Expected {length} bytes, got {len(data)} before close.")
        data += more
    return data

def handle_client_connection(client_socket, client_address):
    """Handles a single client connection: reads framed messages and echoes them back."""
    logging.info(f"Handling connection from {client_address}")
    try:
        while True:
            # 1. Read 2 bytes for length
            len_bytes = recv_all(client_socket, 2)
            if not len_bytes:
                logging.info(f"Client {client_address} disconnected (no length bytes).")
                break
            
            # 2. Unpack length (big-endian)
            payload_len = struct.unpack('>H', len_bytes)[0]
            logging.debug(f"Received length header: {len_bytes.hex()} -> {payload_len} bytes")

            # 3. Read payload_len bytes
            if payload_len == 0:
                payload = b''
                logging.info(f"Host received empty frame (0 bytes) from {client_address}.")
            else:
                payload = recv_all(client_socket, payload_len)
                if not payload: # Should be caught by recv_all EOFError if socket closes prematurely
                    logging.warning(f"Client {client_address} disconnected while expecting payload of {payload_len} bytes.")
                    break
                try:
                    # Attempt to decode for logging, but work with raw bytes for echo
                    payload_str = payload.decode('utf-8')
                    logging.info(f"Host received from {client_address}: '{payload_str}' ({payload_len} bytes)")
                except UnicodeDecodeError:
                    logging.info(f"Host received from {client_address}: {payload.hex()} ({payload_len} bytes, binary)")

            # 4. Echo back: Send length bytes
            logging.debug(f"Host echoing length {payload_len} ({len_bytes.hex()}) to {client_address}")
            client_socket.sendall(len_bytes)

            # 5. Echo back: Send payload bytes
            if payload_len > 0:
                logging.debug(f"Host echoing payload ({payload.hex() if len(payload) < 50 else str(len(payload)) + ' bytes'}) to {client_address}")
                client_socket.sendall(payload)
            
            logging.info(f"Host successfully echoed {payload_len} byte payload to {client_address}.")

    except EOFError as e:
        logging.warning(f"EOFError with client {client_address}: {e}")
    except socket.error as e:
        logging.error(f"Socket error with client {client_address}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error with client {client_address}: {e}", exc_info=True)
    finally:
        logging.info(f"Closing connection with {client_address}")
        client_socket.close()

def main():
    parser = argparse.ArgumentParser(description="Host-side pipe for QEMU semihosting console (TCP client mode).")
    parser.add_argument(
        '--qemu-host', 
        type=str, 
        default='127.0.0.1', 
        help="Host where QEMU's TCP server for serial is running (default: 127.0.0.1)."
    )
    parser.add_argument(
        '--qemu-port', 
        type=int, 
        required=True, 
        help="Port where QEMU's TCP server for serial is listening (e.g., if QEMU is run with -serial tcp::PORT,server,nowait)."
    )
    parser.add_argument(
        '--retry-interval',
        type=int,
        default=5,
        help="Interval in seconds to retry connection to QEMU if it fails (default: 5)."
    )

    args = parser.parse_args()

    logging.info(f"Host pipe starting. Attempting to connect to QEMU at {args.qemu_host}:{args.qemu_port}")

    while True: # Outer loop to allow reconnection
        client_socket = None
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((args.qemu_host, args.qemu_port))
            logging.info(f"Successfully connected to QEMU at {args.qemu_host}:{args.qemu_port}")
            
            # The client_socket here is the connection *to* QEMU.
            # QEMU's -serial tcp::PORT,server,nowait makes QEMU the server. This script is a client to QEMU.
            # The "client_address" for handle_client_connection is effectively QEMU's server address.
            handle_client_connection(client_socket, (args.qemu_host, args.qemu_port))
            
            # If handle_client_connection returns, it means QEMU (or the pipe to it) disconnected.
            logging.info("QEMU side disconnected or connection handler exited.")

        except socket.error as e:
            logging.error(f"Socket error while trying to connect or during handling: {e}")
            if client_socket:
                client_socket.close()
        except KeyboardInterrupt:
            logging.info("Host pipe shutting down by user request (Ctrl+C).")
            if client_socket:
                client_socket.close()
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            if client_socket:
                client_socket.close()
        
        logging.info(f"Attempting to reconnect to QEMU in {args.retry_interval} seconds...")
        time.sleep(args.retry_interval)

if __name__ == "__main__":
    main()
```

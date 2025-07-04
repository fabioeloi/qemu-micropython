import logging
import asyncio
import argparse
import json # For JSON payloads

try:
    import aiocoap.resource as resource
    from aiocoap import Context, Message, CONTENT, CHANGED, NOT_FOUND, METHOD_NOT_ALLOWED, BAD_REQUEST
    from aiocoap.numbers import ContentFormat
except ImportError:
    print("CRITICAL: aiocoap library not found. Please install it: pip install aiocoap")
    raise SystemExit("aiocoap library not found.")

# --- Resource Classes ---
class HelloResource(resource.Resource):
    async def render_get(self, request):
        payload = b"Hello from CoAP Mock Server!"
        return Message(payload=payload, code=CONTENT)

class StatusResource(resource.ObservableResource): # Observable for potential future Observe support
    def __init__(self):
        super().__init__()
        self.status_data = {"status": "initial", "value": 0, "description": "Device Status"}
        # Notify observers when resource changes
        # self.notify_coap_observers() # Call this after changing self.status_data

    async def render_get(self, request):
        logging.info(f"StatusResource GET: Current status: {self.status_data}")
        return Message(payload=json.dumps(self.status_data).encode('utf-8'),
                               code=CONTENT,
                               content_format=ContentFormat.APPLICATION_JSON)

    async def render_put(self, request):
        try:
            payload_str = request.payload.decode('utf-8')
            payload = json.loads(payload_str)
            logging.info(f"StatusResource PUT: Received payload: {payload}")

            # Simple update: merge new data into existing data
            # More complex validation could be added here
            for key in payload:
                if key in self.status_data:
                    self.status_data[key] = payload[key]
                else:
                    logging.warning(f"StatusResource PUT: Ignoring unknown key '{key}' in payload.")

            logging.info(f"StatusResource PUT: Status updated to: {self.status_data}")
            self.updated_state() # For observers

            return Message(payload=json.dumps(self.status_data).encode('utf-8'),
                                   code=CHANGED,
                                   content_format=ContentFormat.APPLICATION_JSON)
        except json.JSONDecodeError:
            logging.error("StatusResource PUT: Invalid JSON payload.")
            return Message(code=BAD_REQUEST, payload=b"Invalid JSON payload")
        except UnicodeDecodeError:
            logging.error("StatusResource PUT: Payload not valid UTF-8.")
            return Message(code=BAD_REQUEST, payload=b"Payload not valid UTF-8")
        except Exception as e:
            logging.error(f"StatusResource PUT: Error processing request: {e}")
            return Message(code=aiocoap.INTERNAL_SERVER_ERROR)

    async def render_post(self, request):
        # For this resource, let POST behave like PUT
        logging.info("StatusResource POST: Treating as PUT.")
        return await self.render_put(request)

class EchoResource(resource.Resource):
    async def render_post(self, request):
        logging.info(f"EchoResource POST: Received payload: {request.payload!r}")
        # Echo back the payload with the same content format, if provided
        response_payload = request.payload
        response_code = CONTENT
        response_cf = request.opt.content_format if request.opt.content_format is not None else ContentFormat.TEXT_PLAIN

        return Message(payload=response_payload, code=response_code, content_format=response_cf)

    async def render_put(self, request): # Also allow PUT for echo
        logging.info(f"EchoResource PUT: Received payload: {request.payload!r}")
        response_payload = request.payload
        response_code = CONTENT # Or CHANGED if preferred for PUT
        response_cf = request.opt.content_format if request.opt.content_format is not None else ContentFormat.TEXT_PLAIN
        return Message(payload=response_payload, code=response_code, content_format=response_cf)

async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - COAP_SERVER - %(levelname)s - %(message)s')
    # You can set aiocoap's own logger to DEBUG for more verbose output if needed
    # logging.getLogger("coap").setLevel(logging.DEBUG)
    # logging.getLogger("coap-server").setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(description="Host-side CoAP Mock Server")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="Host to bind the server to (e.g., '0.0.0.0' for all interfaces, '::' for IPv6, default: 0.0.0.0).")
    parser.add_argument("--port", type=int, default=aiocoap.COAP_PORT,
                        help=f"Port to bind the server to (default: {aiocoap.COAP_PORT}).")
    args = parser.parse_args()

    # Resource tree
    root = resource.Site()
    root.add_resource(['.well-known', 'core'], resource.WKCResource(root.get_resources_as_linkheader))
    root.add_resource(['test', 'hello'], HelloResource())
    status_res = StatusResource() # Create instance to hold state
    root.add_resource(['test', 'status'], status_res)
    root.add_resource(['test', 'echo'], EchoResource())

    bind_address = (args.host, args.port)
    logging.info(f"Starting CoAP Mock Server on {bind_address[0]}:{bind_address[1]}")

    try:
        server_context = await Context.create_server_context(root, bind=bind_address)
    except OSError as e:
        logging.error(f"Failed to create CoAP server context at {bind_address}: {e}")
        logging.error("Ensure the address/port is not in use and host is correctly specified.")
        logging.error("For IPv6, try host '::'. For IPv4, try '0.0.0.0'.")
        return
    except Exception as e:
        logging.error(f"Unexpected error creating CoAP server context: {e}")
        return

    try:
        # Keep the server running indefinitely
        await asyncio.get_event_loop().create_future()
    except KeyboardInterrupt:
        logging.info("CoAP Mock Server shutting down...")
    finally:
        await server_context.shutdown()
        logging.info("CoAP server shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application terminated by user.")
    except Exception as e: # Catch-all for other startup errors
        logging.error(f"Failed to start asyncio event loop: {e}")
```

from . import coap_macros
from . import coap_option
from . import coap_reader
from . import coap_writer

class CoapPacket:
    """
    Represents a CoAP packet.
    Handles parsing from bytes and serializing to bytes.
    """
    def __init__(self):
        self.version = coap_macros.COAP_VERSION
        self.type = coap_macros.COAP_TYPE.COAP_CON  # Default to Confirmable
        self.tokenlength = 0
        self.code = coap_macros.COAP_REQUEST_CODE.COAP_GET # Default to GET
        self.messageid = 0
        self.token = b'' # Should be bytes, up to 8 bytes
        self.options = [] # List of CoapOption objects
        self.payload = b'' # Should be bytes

    def addOption(self, optionNumber, optionValue):
        # Ensure optionValue is bytes
        if not isinstance(optionValue, bytes):
            if isinstance(optionValue, str):
                optionValue = optionValue.encode('utf-8')
            elif isinstance(optionValue, int):
                # For integer options like Content-Format, convert to minimal bytes
                if optionValue == 0:
                    optionValue = b'' # Empty byte string for zero value if allowed by option type
                else:
                    optionValue = optionValue.to_bytes((optionValue.bit_length() + 7) // 8, 'big')

            else:
                raise TypeError("Option value must be bytes, string, or int")

        new_option = coap_option.CoapOption(optionNumber, optionValue)
        self.options.append(new_option)
        # Options should be sorted by number for serialization
        self.options.sort(key=lambda o: o.number)


    @staticmethod
    def fromBytes(rawBytes):
        packet = CoapPacket()
        reader = coap_reader.CoapReader(rawBytes)

        # Header
        val = reader.read(1)[0]
        packet.version = (val & 0xC0) >> 6
        if packet.version != coap_macros.COAP_VERSION:
            raise ValueError("Invalid CoAP version")

        packet.type = (val & 0x30) >> 4
        packet.tokenlength = (val & 0x0F)

        packet.code_value = reader.read(1)[0] # Store raw code value
        # Set the code object based on the value (e.g. from COAP_REQUEST_CODE or COAP_RESPONSE_CODE)
        # This logic might need refinement if you have separate classes for request/response codes
        packet.code = packet.code_value # For now, store the int. User can check against COAP_REQUEST_CODE/COAP_RESPONSE_CODE

        packet.messageid = int.from_bytes(reader.read(2), 'big')

        if packet.tokenlength > 0:
            if packet.tokenlength > 8:
                raise ValueError("Token length too large (max 8 bytes)")
            packet.token = reader.read(packet.tokenlength)

        # Options
        current_option_number = 0
        while reader.peek() != coap_macros.COAP_MESSAGE_PAYLOAD_MARKER and not reader.isAtEnd():
            option_header = reader.read(1)[0]
            if option_header == coap_macros.COAP_MESSAGE_PAYLOAD_MARKER: # Should be caught by peek, but double check
                break

            delta = (option_header & 0xF0) >> 4
            length = (option_header & 0x0F)

            if delta == 13:
                delta = reader.read(1)[0] + 13
            elif delta == 14:
                delta = int.from_bytes(reader.read(2), 'big') + 269
            elif delta == 15: # Is payload marker, should have been caught
                raise ValueError("Invalid option delta 15 (payload marker)")

            if length == 13:
                length = reader.read(1)[0] + 13
            elif length == 14:
                length = int.from_bytes(reader.read(2), 'big') + 269
            elif length == 15: # Is payload marker
                 raise ValueError("Invalid option length 15 (payload marker)")

            current_option_number += delta
            option_value = reader.read(length)

            packet.options.append(coap_option.CoapOption(current_option_number, option_value))

        # Payload
        if not reader.isAtEnd() and reader.peek() == coap_macros.COAP_MESSAGE_PAYLOAD_MARKER:
            reader.read(1) # Consume payload marker
            packet.payload = reader.readAllRemaining()

        return packet

    def toBytes(self):
        writer = coap_writer.CoapWriter()

        # Header
        val = (self.version & 0x03) << 6
        val |= (self.type & 0x03) << 4

        token_bytes = self.token
        if not isinstance(token_bytes, bytes): # If token was set as int, convert
            if self.token == 0 and self.tokenlength == 0: # Handle zero token explicitly
                 token_bytes = b''
            else:
                 # Try to fit into specified tokenlength, or minimal bytes
                 token_len_bytes = self.tokenlength if self.tokenlength > 0 else (self.token.bit_length() + 7) // 8
                 if token_len_bytes > 8: token_len_bytes = 8 # Max 8
                 token_bytes = self.token.to_bytes(token_len_bytes, 'big')

        actual_token_length = len(token_bytes)
        if actual_token_length > 8:
            raise ValueError("Token too long (max 8 bytes)")
        val |= (actual_token_length & 0x0F)

        writer.write(val.to_bytes(1, 'big'))

        # Code (use the integer value directly)
        # Ensure self.code is an integer. If it's an enum-like object, get its value.
        code_val_to_write = self.code
        if hasattr(self.code, 'value'): # Simple check if it's an enum-like obj with a value
            code_val_to_write = self.code.value
        elif not isinstance(self.code, int):
            raise TypeError(f"Packet code must be an integer, not {type(self.code)}")
        writer.write(code_val_to_write.to_bytes(1, 'big'))

        writer.write(self.messageid.to_bytes(2, 'big'))

        if actual_token_length > 0:
            writer.write(token_bytes)

        # Options (must be sorted by number)
        self.options.sort(key=lambda o: o.number)
        last_option_number = 0
        for opt in self.options:
            delta = opt.number - last_option_number
            length = len(opt.value)

            # Delta
            if delta <= 12:
                d = delta
            elif delta <= 255 + 13:
                d = 13
            else:
                d = 14

            # Length
            if length <= 12:
                l = length
            elif length <= 255 + 13:
                l = 13
            else:
                l = 14

            writer.write(((d << 4) | l).to_bytes(1, 'big'))

            if d == 13:
                writer.write((delta - 13).to_bytes(1, 'big'))
            elif d == 14:
                writer.write((delta - 269).to_bytes(2, 'big'))

            if l == 13:
                writer.write((length - 13).to_bytes(1, 'big'))
            elif l == 14:
                writer.write((length - 269).to_bytes(2, 'big'))

            writer.write(opt.value)
            last_option_number = opt.number

        # Payload
        if self.payload is not None and len(self.payload) > 0:
            writer.write(coap_macros.COAP_MESSAGE_PAYLOAD_MARKER.to_bytes(1, 'big'))
            writer.write(self.payload)

        return writer.getBytes()

    def toString(self):
        # Basic string representation for debugging
        parts = []
        parts.append(f"Ver: {self.version}")
        type_str = {0: "CON", 1: "NON", 2: "ACK", 3: "RST"}.get(self.type, "UNK")
        parts.append(f"Type: {type_str}({self.type})")

        # Code representation
        code_klass, code_detail = coap_macros.ValueToCode(self.code)
        parts.append(f"Code: {code_klass}.{code_detail:02d} ({self.code})")

        parts.append(f"MID: {self.messageid}")
        parts.append(f"Token: {self.token.hex() if self.token else 'None'}") # Show token as hex

        if self.options:
            parts.append("Options:")
            for opt in self.options:
                parts.append(f"  {opt.toString()}")
        if self.payload:
            try:
                payload_preview = self.payload.decode('utf-8')
                if len(payload_preview) > 30: payload_preview = payload_preview[:30] + "..."
                parts.append(f"Payload: '{payload_preview}' ({len(self.payload)} bytes)")
            except UnicodeDecodeError:
                parts.append(f"Payload: {self.payload.hex()} ({len(self.payload)} bytes)")
        else:
            parts.append("Payload: None")

        return "\n  ".join(parts)

    def getOption(self, option_number):
        """Returns a list of all options with the given number."""
        return [opt for opt in self.options if opt.number == option_number]

    def getFirstOption(self, option_number):
        """Returns the first option with the given number, or None."""
        for opt in self.options:
            if opt.number == option_number:
                return opt
        return None
```

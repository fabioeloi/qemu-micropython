from . import coap_macros

class CoapOption:
    """
    Represents a CoAP option.
    """
    def __init__(self, number=0, value=b''):
        self.number = number
        # Value should always be stored as bytes internally
        if isinstance(value, str):
            self.value = value.encode('utf-8')
        elif isinstance(value, int):
            # For integer options like Content-Format, convert to minimal bytes
            if value == 0 and (number == coap_macros.COAP_OPTION_NUMBER.COAP_CONTENT_FORMAT or number == coap_macros.COAP_OPTION_NUMBER.COAP_ACCEPT): # common uint options
                 self.value = b'' # Empty byte for zero value is common for uint options of length 0-2
            elif value == 0 : # Other int options might not allow empty value for 0
                 self.value = value.to_bytes(1, 'big') if value <=255 else value.to_bytes(2,'big') # Default to 1 or 2 bytes for 0 if not specific format
            else:
                 self.value = value.to_bytes((value.bit_length() + 7) // 8, 'big')
        elif isinstance(value, bytes):
            self.value = value
        else:
            raise TypeError("Option value must be bytes, string, or int")

    def toString(self):
        # Try to decode value as UTF-8 for display if it's a common text-based option
        # Otherwise, display as hex.
        option_name = "Unknown"
        for attr, val in coap_macros.COAP_OPTION_NUMBER.__dict__.items():
            if val == self.number:
                option_name = attr
                break

        display_value = ""
        if self.number in [coap_macros.COAP_OPTION_NUMBER.COAP_URI_HOST,
                           coap_macros.COAP_OPTION_NUMBER.COAP_LOCATION_PATH,
                           coap_macros.COAP_OPTION_NUMBER.COAP_URI_PATH,
                           coap_macros.COAP_OPTION_NUMBER.COAP_URI_QUERY,
                           coap_macros.COAP_OPTION_NUMBER.COAP_PROXY_URI,
                           coap_macros.COAP_OPTION_NUMBER.COAP_PROXY_SCHEME]:
            try:
                display_value = self.value.decode('utf-8')
            except UnicodeDecodeError:
                display_value = self.value.hex() + " (hex)"
        elif self.number in [coap_macros.COAP_OPTION_NUMBER.COAP_CONTENT_FORMAT,
                             coap_macros.COAP_OPTION_NUMBER.COAP_ACCEPT,
                             coap_macros.COAP_OPTION_NUMBER.COAP_MAX_AGE,
                             coap_macros.COAP_OPTION_NUMBER.COAP_URI_PORT,
                             coap_macros.COAP_OPTION_NUMBER.COAP_OBSERVE,
                             coap_macros.COAP_OPTION_NUMBER.COAP_SIZE1,
                             coap_macros.COAP_OPTION_NUMBER.COAP_SIZE2]: # Common numeric options
            if len(self.value) == 0: # For options like Content-Format=0 (text/plain)
                display_value = "0"
            else:
                try:
                    display_value = str(int.from_bytes(self.value, 'big'))
                except: # Should not happen if value is bytes
                    display_value = self.value.hex() + " (hex)"
        elif self.number == coap_macros.COAP_OPTION_NUMBER.COAP_ETAG:
             display_value = self.value.hex() # ETag is opaque
        else: # Default to hex for other or unknown options
            display_value = self.value.hex() + " (hex)"
            if not self.value: display_value = "(empty)"


        return f"Option Number: {self.number} ({option_name}), Value: {display_value} (Length: {len(self.value)})"
```

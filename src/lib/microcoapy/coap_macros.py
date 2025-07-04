# RFC 7252 - The Constrained Application Protocol (CoAP)
#
# MACROS taken from RFC7252


# CoAP message types
class COAP_TYPE:
    COAP_CON = 0  # Confirmable
    COAP_NONCON = 1  # Non-confirmable
    COAP_ACK = 2  # Acknowledgement
    COAP_RESET = 3  # Reset


# CoAP request codes
class COAP_REQUEST_CODE:
    COAP_EMPTY = 0
    COAP_GET = 1
    COAP_POST = 2
    COAP_PUT = 3
    COAP_DELETE = 4


# CoAP response codes
class COAP_RESPONSE_CODE:
    # Success
    COAP_EMPTY = 0 # Technically not a response code, but used for empty ACK/RST
    COAP_CREATED = 65  # 2.01
    COAP_DELETED = 66  # 2.02
    COAP_VALID = 67  # 2.03
    COAP_CHANGED = 68  # 2.04
    COAP_CONTENT = 69  # 2.05
    # Client Error
    COAP_BAD_REQUEST = 128  # 4.00
    COAP_UNAUTHORIZED = 129  # 4.01
    COAP_BAD_OPTION = 130  # 4.02
    COAP_FORBIDDEN = 131  # 4.03
    COAP_NOT_FOUND = 132  # 4.04
    COAP_METHOD_NOT_ALLOWED = 133  # 4.05
    COAP_NOT_ACCEPTABLE = 134  # 4.06
    COAP_PRECONDITION_FAILED = 140  # 4.12
    COAP_REQUEST_ENTITY_TOO_LARGE = 141  # 4.13
    COAP_UNSUPPORTED_CONTENT_FORMAT = 143  # 4.15
    # Server Error
    COAP_INTERNAL_SERVER_ERROR = 160  # 5.00
    COAP_NOT_IMPLEMENTED = 161  # 5.01
    COAP_BAD_GATEWAY = 162  # 5.02
    COAP_SERVICE_UNAVAILABLE = 163  # 5.03
    COAP_GATEWAY_TIMEOUT = 164  # 5.04
    COAP_PROXYING_NOT_SUPPORTED = 165  # 5.05

    def isSuccess(code):
        return (code >= 64 and code < 128)

    def isClientError(code):
        return (code >= 128 and code < 160)

    def isServerError(code):
        return (code >= 160 and code < 192) # As per RFC, codes are class.detail (e.g., 2.05 is 2<<5 + 05 = 69)
                                            # Classes: 0=request/empty, 2=success, 4=client_error, 5=server_error
                                            # So, response codes start from 2.00 (which is not used).
                                            # Class 2: 2.01-2.31 (65-95)
                                            # Class 4: 4.00-4.31 (128-159)
                                            # Class 5: 5.00-5.31 (160-191)
    def isRequest(code_value): # code_value is the raw int (1-4 for GET/POST/PUT/DELETE)
        return code_value >= COAP_REQUEST_CODE.COAP_GET and code_value <= COAP_REQUEST_CODE.COAP_DELETE

    def isResponse(code_value): # code_value is the raw int (e.g., 69 for 2.05)
        return (code_value >= 64 and code_value < 192)


# CoAP option numbers
class COAP_OPTION_NUMBER:
    COAP_IF_MATCH = 1
    COAP_URI_HOST = 3
    COAP_ETAG = 4
    COAP_IF_NONE_MATCH = 5
    COAP_OBSERVE = 6
    COAP_URI_PORT = 7
    COAP_LOCATION_PATH = 8
    COAP_URI_PATH = 11
    COAP_CONTENT_FORMAT = 12
    COAP_MAX_AGE = 14
    COAP_URI_QUERY = 15
    COAP_ACCEPT = 17
    COAP_LOCATION_QUERY = 20
    COAP_BLOCK2 = 23 # Not fully supported by this simple library
    COAP_BLOCK1 = 27 # Not fully supported by this simple library
    COAP_SIZE2 = 28  # Not fully supported by this simple library
    COAP_PROXY_URI = 35
    COAP_PROXY_SCHEME = 39
    COAP_SIZE1 = 60 # Not fully supported by this simple library

# CoAP content-formats
class COAP_CONTENT_FORMAT:
    COAP_TEXT_PLAIN = 0
    COAP_APPLICATION_LINK_FORMAT = 40
    COAP_APPLICATION_XML = 41
    COAP_APPLICATION_OCTET_STREAM = 42
    COAP_APPLICATION_EXI = 47
    COAP_APPLICATION_JSON = 50
    COAP_APPLICATION_CBOR = 60 # New addition in RFC 8323 (was application/cbor-seq in some drafts)

# CoAP defaults
COAP_DEFAULT_PORT = 5683
COAP_DEFAULT_MAX_AGE = 60
COAP_DEFAULT_ACK_TIMEOUT = 2
COAP_DEFAULT_ACK_RANDOM_FACTOR = 1.5
COAP_MAX_RETRANSMIT = 4
COAP_MAX_MESSAGE_ID = 65535 # 2^16 - 1
COAP_MAX_TOKEN = 0xFFFFFFFFFFFFFFFF # 2^64 -1 (but we use a smaller int in practice for simplicity)
COAP_MESSAGE_PAYLOAD_MARKER = 0xFF

COAP_VERSION = 1

# Helper to convert class.detail to code value
def CodeToValue(klass, detail):
    return (klass << 5) | detail

# Helper to get class and detail from code value
def ValueToCode(value):
    if value == 0: # Empty
        return (0,0)
    klass = value >> 5
    detail = value & 0x1F # 0b00011111
    return (klass, detail)

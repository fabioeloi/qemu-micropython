class CoapWriter:
    """
    Helper class to construct a byte buffer.
    """
    def __init__(self):
        self._buffer = bytearray()

    def write(self, dataBytes):
        if not isinstance(dataBytes, (bytes, bytearray)):
            raise TypeError("Data must be bytes or bytearray")
        self._buffer.extend(dataBytes)

    def getBytes(self):
        return bytes(self._buffer) # Return an immutable bytes object

    def getLength(self):
        return len(self._buffer)
```

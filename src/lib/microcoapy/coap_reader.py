class CoapReader:
    """
    Helper class to read from a byte buffer.
    """
    def __init__(self, dataBytes):
        self._data = dataBytes
        self._pos = 0

    def read(self, numBytes):
        if self._pos + numBytes > len(self._data):
            raise IndexError("Not enough data to read")

        result = self._data[self._pos : self._pos + numBytes]
        self._pos += numBytes
        return result

    def peek(self):
        if self.isAtEnd():
            return None # Or raise error, depends on desired behavior
        return self._data[self._pos]

    def readAllRemaining(self):
        result = self._data[self._pos:]
        self._pos = len(self._data)
        return result

    def isAtEnd(self):
        return self._pos >= len(self._data)

    def getPosition(self):
        return self._pos

    def getRemainingLength(self):
        return len(self._data) - self._pos
```

import machine
import time
import uerrno # For non-blocking error

class UARTSocket:
    def __init__(self, uart_instance, host=None, port=None):
        """
        Initialize the UARTSocket wrapper.
        :param uart_instance: An initialized machine.UART object.
        :param host: Not used by UART, but kept for socket-like interface compatibility.
        :param port: Not used by UART, but kept for socket-like interface compatibility.
        """
        self.uart = uart_instance
        self._timeout = None # Default is blocking
        self._internal_read_timeout_ms = 10 # Short timeout for polling UART buffer
        self.peer_closed = False

    def write(self, buf):
        """
        Write data to the UART.
        :param buf: Buffer containing data to write.
        :return: Number of bytes written.
        """
        if self.peer_closed:
            raise OSError(uerrno.ECONNRESET, "Connection reset by peer")
        try:
            return self.uart.write(buf)
        except Exception as e:
            # Simulate socket-like errors if UART write fails unexpectedly
            self.peer_closed = True
            raise OSError(uerrno.ECONNRESET, "UART write error") from e


    def read(self, size):
        """
        Read data from the UART.
        This is a blocking read, but uses internal timeouts for polling.
        :param size: Number of bytes to read.
        :return: Bytes read, or b'' if timeout occurs and non-blocking,
                 or if peer closed.
        """
        if self.peer_closed:
            return b''

        buf = bytearray()
        start_time = time.ticks_ms()

        while len(buf) < size:
            bytes_available = self.uart.any()
            if bytes_available > 0:
                read_now = min(bytes_available, size - len(buf))
                data_chunk = self.uart.read(read_now)
                if data_chunk:
                    buf.extend(data_chunk)
                else:
                    # Should not happen if any() > 0, but as a safeguard
                    # This could indicate peer closed if it returns None consistently
                    pass

            if self._timeout is not None: # Non-blocking mode with timeout
                if time.ticks_diff(time.ticks_ms(), start_time) > self._timeout * 1000:
                    if not buf: # No data read within timeout
                        # In non-blocking mode, EWOULDBLOCK is expected if no data
                        raise OSError(uerrno.EWOULDBLOCK)
                    break # Return whatever was read
            else: # Blocking mode (timeout is None)
                # For blocking, we rely on the short internal timeout to prevent hard lock
                # if no data is coming. If a longer external timeout is needed,
                # settimeout() should be used.
                if self.uart.any() == 0: # No data, pause briefly
                    time.sleep_ms(self._internal_read_timeout_ms)

            # Check for overall timeout if one was set via settimeout()
            # This check is mostly for when _timeout is 0 (non-blocking) or very small.
            # For longer timeouts, the main blocking logic is above.
            if self._timeout == 0 and not buf: # Non-blocking and nothing read
                 raise OSError(uerrno.EWOULDBLOCK)


        if not buf and size > 0:
            # If we expected data but got none, and it wasn't a timeout,
            # it might imply the other side closed. Difficult to distinguish
            # from just no data without a clear EOF signal over UART.
            # For now, we return b'' which is standard for socket closed.
            self.peer_closed = True # Assume closed if read returns nothing when expecting data
            return b''

        return bytes(buf)

    def readinto(self, buf, nbytes=0):
        """
        Read up to nbytes into buf. If nbytes is not specified or 0,
        read up to len(buf).
        Returns number of bytes read.
        """
        if self.peer_closed:
            return 0 # No bytes read if connection is already considered closed

        read_len = len(buf) if nbytes == 0 else min(nbytes, len(buf))

        data_read = self.read(read_len)

        if data_read:
            for i in range(len(data_read)):
                buf[i] = data_read[i]
            return len(data_read)
        else:
            # If read() returned b'', it means timeout or closed
            # If timeout and non-blocking, read() would raise EWOULDBLOCK
            # If blocking and timeout, read() returns partial or b''
            # If closed, read() returns b''
            if self._timeout is not None and self._timeout > 0: # Timed blocking
                return 0 # Timeout occurred, 0 bytes read
            elif self._timeout == 0: # Non-blocking
                 # read() should have raised EWOULDBLOCK if no data
                 # if we are here with no data, could be an issue or just no data yet
                return 0 # Or raise EWOULDBLOCK if that's the contract
            else: # Blocking, no timeout set (or timeout is None)
                # If read returns b'' in this case, it implies closed.
                self.peer_closed = True
                return 0


    def readline(self):
        """
        Read a line from UART.
        """
        if self.peer_closed:
            return b''

        line = bytearray()
        start_time = time.ticks_ms()
        while True:
            if self.uart.any() > 0:
                char = self.uart.read(1)
                if char:
                    line.extend(char)
                    if char == b'\n':
                        break
                else: # read returned None, could mean peer closed
                    self.peer_closed = True
                    break

            if self._timeout is not None:
                if time.ticks_diff(time.ticks_ms(), start_time) > self._timeout * 1000:
                    # Timeout occurred
                    if self._timeout == 0: # Non-blocking
                        raise OSError(uerrno.EWOULDBLOCK)
                    break # Return what we have
            else: # Blocking
                time.sleep_ms(self._internal_read_timeout_ms) # Pause briefly

        if not line and self.peer_closed: # No data and determined peer closed
            return b''
        return bytes(line)

    def close(self):
        """
        Close the UART. (UARTs don't have a 'close' in the socket sense,
        so this is more about signaling intent and deinitializing if necessary)
        """
        # UARTs in MicroPython don't always have a deinit() or close() that
        # behaves like a socket close. We'll mark it as closed for our wrapper.
        # If the specific UART instance had a deinit(), you might call it here.
        # e.g., if hasattr(self.uart, 'deinit'): self.uart.deinit()
        self.peer_closed = True
        print("UARTSocket: close() called.")


    def settimeout(self, value):
        """
        Set the timeout for read operations.
        :param value: Timeout in seconds. 0 for non-blocking, None for blocking.
        """
        if value is not None and value < 0:
            raise ValueError("Timeout value must be non-negative or None")
        self._timeout = value
        # Note: The actual UART read operations might not directly support timeouts
        # in the same way sockets do. This timeout is managed by the wrapper logic.
        # For non-blocking (value=0), read() will attempt one read and return.
        # For blocking (value=None), read() will wait indefinitely (with short polls).
        # For timed blocking (value > 0), read() will wait up to 'value' seconds.

    def makefile(self, mode='rb', buffering=0):
        """
        Return a file-like object associated with the socket.
        MicroPython sockets often return self for this, as they implement
        the relevant methods (read, write, etc.).
        """
        # Check if mode is binary, as UART communication is binary
        if 'b' not in mode:
            # Not strictly necessary to raise error, but good practice
            # print("Warning: UARTSocket makefile opened in non-binary mode.")
            pass
        return self

    # Add dummy methods for socket compatibility if umqtt.simple needs them
    def connect(self, address):
        # This would typically be called on a socket object to connect to a remote.
        # For UARTSocket, the "connection" is implicit with the UART line.
        # We can make this a no-op or raise an error if called.
        # print("UARTSocket: connect() called, but UART is connection-oriented by nature.")
        pass

    def bind(self, address):
        # Similar to connect, UART doesn't bind in the same way.
        # print("UARTSocket: bind() called, no-op for UART.")
        pass

    def listen(self, backlog):
        # Server-side socket method, not applicable.
        # print("UARTSocket: listen() called, no-op for UART.")
        pass

    def accept(self):
        # Server-side socket method, not applicable.
        # print("UARTSocket: accept() called, no-op for UART.")
        return None, None # Or raise error

    def getsockname(self):
        # Return some dummy info or info about the UART if useful
        return ('uart', self.uart.name() if hasattr(self.uart, 'name') else str(self.uart))

    def getpeername(self):
        # UART has no distinct peer name like a TCP socket
        return ('uart_peer', 'unknown')

    def setsockopt(self, level, optname, value):
        # Generally no-op for UART, unless specific UART features map to socket options
        # print(f"UARTSocket: setsockopt({level}, {optname}, {value}) called, no-op.")
        pass

    # Required by some libraries that check for fileno
    def fileno(self):
        # UARTs don't have file descriptors in the same way.
        # Return a conventional error indicator or a dummy value.
        # -1 is often used if no real fileno.
        return -1

# Example Usage (for testing within this file if needed, normally imported)
if __name__ == '__main__':
    # This example assumes you have a UART(0) available and configured.
    # For actual testing, you'd need a loopback or another device on UART0.
    try:
        uart = machine.UART(0, baudrate=115200) # Adjust UART ID and params as needed
        print("UART(0) initialized for testing UARTSocket.")
    except Exception as e:
        print(f"Failed to initialize UART(0): {e}")
        print("Please ensure UART(0) is available and correctly configured.")
        uart = None

    if uart:
        socket_uart = UARTSocket(uart)

        # Test write
        print("Testing write...")
        bytes_written = socket_uart.write(b"Hello UART Socket\n")
        print(f"Bytes written: {bytes_written}")

        # Test read (requires data to be sent to UART0)
        # To test this part, you'd need to connect UART0 TX to RX (loopback)
        # or send data from another device to UART0.
        print("\nTesting read (with 5s timeout)...")
        socket_uart.settimeout(5.0) # 5 seconds timeout
        try:
            data = socket_uart.read(20) # Try to read up to 20 bytes
            if data:
                print(f"Data read: {data}")
            else:
                print("No data read (or timeout). Is UART0 in loopback or receiving data?")
        except OSError as e:
            if e.args[0] == uerrno.EWOULDBLOCK:
                print("Read timed out (EWOULDBLOCK) as expected if no data.")
            else:
                print(f"Read error: {e}")

        # Test non-blocking read
        print("\nTesting non-blocking read (settimeout(0))...")
        socket_uart.settimeout(0)
        try:
            data_nonblock = socket_uart.read(10)
            if data_nonblock: # Unlikely to get data immediately unless already in buffer
                print(f"Data read (non-blocking): {data_nonblock}")
            else:
                print("No data read (non-blocking), as expected if buffer is empty.")
        except OSError as e:
            if e.args[0] == uerrno.EWOULDBLOCK:
                print("Read non-blocking timed out (EWOULDBLOCK), as expected if no data.")
            else:
                print(f"Read error (non-blocking): {e}")

        # Test readline
        print("\nTesting readline (with 5s timeout, send 'test\\n' to UART0)...")
        socket_uart.settimeout(5.0)
        try:
            line = socket_uart.readline()
            if line:
                print(f"Line read: {line.strip()}") # .strip() to remove trailing \n
            else:
                print("No line read (or timeout).")
        except OSError as e:
            if e.args[0] == uerrno.EWOULDBLOCK:
                print("Readline timed out (EWOULDBLOCK).")
            else:
                print(f"Readline error: {e}")

        # Test makefile
        print("\nTesting makefile...")
        file_obj = socket_uart.makefile('rb')
        if file_obj is socket_uart:
            print("makefile() returned self, as expected for basic MicroPython sockets.")
            # You could try file_obj.read() here too

        socket_uart.close()
        print("\nUARTSocket closed.")

        # Example of re-opening UART if needed, though UARTSocket doesn't deinit by default
        # uart.init(baudrate=115200) # Re-init if uart.deinit() was called in close()

    print("\nUARTSocket example finished.")

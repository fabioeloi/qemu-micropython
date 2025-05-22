# Semihosting with `usemihosting` Module

## 1. Overview

Semihosting is a mechanism that enables code running on an embedded target (like MicroPython in QEMU) to perform Input/Output (I/O) operations using the resources of the host computer where the emulator or debugger is running. Essentially, the target requests services (like file access or console I/O) from the host.

The `usemihosting` MicroPython module provides a Pythonic interface to these semihosting operations, allowing MicroPython scripts running within QEMU to directly interact with the host system for tasks such as file manipulation, time retrieval, and console-based data exchange.

## 2. Enabling Semihosting in QEMU

To use the `usemihosting` module, semihosting must be enabled when launching QEMU. This is typically done via command-line arguments. For this project, the QEMU configuration (e.g., in `config/qemu/stm32f4.cfg`) often includes options like:

```
-semihosting-config enable=on,target=native
```

-   `enable=on`: Turns on semihosting.
-   `target=native`: Uses the host system's native I/O (as opposed to GDB-specific semihosting, for example).

Ensure your QEMU launch command or configuration file correctly enables semihosting.

## 3. `usemihosting` Module API

The module provides access to various host functionalities:

### General Utility Functions

*   **`usemihosting.is_semihosting_available()` -> `bool`**
    *   Checks if semihosting operations appear to be functional.
    *   Returns `True` if semihosting is detected (e.g., by successfully calling a benign semihosting operation like `SYS_CLOCK`), `False` otherwise.

*   **`usemihosting.time()` -> `int`**
    *   Returns the number of seconds since the epoch (January 1, 1970, UTC), as reported by the host system via the `SYS_TIME` semihosting call.

*   **`usemihosting.clock()` -> `int`**
    *   Returns the number of centiseconds (1/100th of a second) since the program's execution started (or since the debugger connected and enabled semihosting), as reported by the host via `SYS_CLOCK`.

*   **`usemihosting.exit(return_code=0)`**
    *   Terminates the QEMU simulation.
    *   The optional `return_code` (an integer) is passed to the `SYS_REPORTEXCEPTION` semihosting call with the `ADP_Stopped_ApplicationExit` reason code. The host debugger or QEMU itself might use this code.
    *   This function should not return.

### File I/O Operations

These functions allow interaction with the host system's filesystem. Paths are typically relative to the directory where QEMU was launched or as configured by the semihosting environment.

*   **`usemihosting.open(path: str, mode: str)` -> `SemihostingFile`**
    *   Opens a file on the host system.
    *   `path`: A string representing the path to the file on the host.
    *   `mode`: A Python standard file mode string (e.g., `'r'`, `'rb'`, `'w'`, `'wb'`, `'a'`, `'ab'`, `'r+'`, `'w+'`, `'a+'`, etc.).
    *   Returns a `SemihostingFile` object that provides stream-like methods for file interaction.
    *   Raises `OSError` on failure.

*   **`SemihostingFile` Object Methods:**
    The object returned by `usemihosting.open()` supports the following methods:
    *   `read(size: int = -1)` -> `bytes` or `str` (depending on mode)
        *   Reads up to `size` bytes from the file. If `size` is -1 or omitted, reads until EOF.
        *   Returns bytes if opened in binary mode (`'b'`), otherwise returns a string (after decoding, though semihosting itself is binary; text mode implies host-side handling or assumes UTF-8).
    *   `readinto(buf)` -> `int`
        *   Reads bytes into the pre-allocated writable buffer `buf`.
        *   Returns the number of bytes read.
    *   `readline()` -> `bytes` or `str`
        *   Reads a single line from the file, including the newline character.
    *   `write(buf)` -> `int`
        *   Writes the given buffer (string or bytes) to the file.
        *   Returns the number of bytes written.
    *   `close()`
        *   Closes the file on the host. Subsequent operations on the file object will fail.
    *   `seek(offset: int, whence: int = 0)` -> `int`
        *   Changes the current file position.
        *   `offset`: The offset in bytes.
        *   `whence`: Defines the reference point: `0` for start of file (SEEK_SET), `1` for current position (SEEK_CUR), `2` for end of file (SEEK_END).
        *   **Limitation for `SEEK_CUR`**: The underlying C implementation of `usemihosting` may not support `SEEK_CUR` directly due to the lack of a standard `SYS_TELL` semihosting operation. If so, attempts to use `whence=1` might raise an `OSError(EOPNOTSUPP)`. The Python stream layer might attempt to emulate it if it caches the position.
        *   Returns the new absolute file position.
    *   `tell()` -> `int`
        *   Returns the current file position in bytes. This relies on the Python stream layer's position caching if `SEEK_CUR` is not directly supported at the C level for semihosting.
    *   `flush()`
        *   This is currently a no-op in the C implementation, as semihosting `SYS_FLUSH` is not universally standard or typically required (files are often flushed on close by the host).
    *   **Context Manager Support:**
        `SemihostingFile` objects can be used with the `with` statement, ensuring the file is automatically closed.
        ```python
        with usemihosting.open("host_file.txt", "w") as f:
            f.write("Hello via semihosting!")
        ```

*   **`usemihosting.remove(path: str)`**
    *   Removes (deletes) a file on the host system.
    *   `path`: The path to the file to remove.
    *   Raises `OSError` on failure (e.g., if the file does not exist).

*   **`usemihosting.rename(old_path: str, new_path: str)`**
    *   Renames or moves a file on the host system.
    *   `old_path`: The current path of the file.
    *   `new_path`: The new path for the file.
    *   Raises `OSError` on failure. Behavior when `new_path` exists can be host-dependent (often overwrite).

*   **Currently Unimplemented File Operations:**
    Functions like `listdir`, `mkdir`, `rmdir`, and `stat` are not yet implemented in the `usemihosting` module in this initial version.

### Console Data Pipe (Guest-Host Communication)

These functions allow raw byte data to be sent between the MicroPython environment in QEMU and a script running on the host, using QEMU's serial console as the communication channel. **This requires specific QEMU setup and a host-side script.**

*   **QEMU Setup for Console Pipe:**
    QEMU's serial console output must be redirected to a TCP port. This allows an external script to connect to it.
    Example QEMU command:
    ```bash
    qemu-system-arm ... -serial tcp::4444,server,nowait ...
    ```
    (Replace `4444` with your desired port).

*   **Host-Side Script (`tools/semihosting_console_pipe.py`):**
    For the console pipe functions to work, the `tools/semihosting_console_pipe.py` script (or a similar custom script) **must be running on the host machine**. This script connects to the TCP port that QEMU's serial output is redirected to.
    Example host command:
    ```bash
    python tools/semihosting_console_pipe.py --qemu-port 4444
    ```
    The provided `semihosting_console_pipe.py` script acts as an echo server: it reads a framed message from QEMU and sends the same message back.

*   **`usemihosting.framed_console_send(data: bytes)`**
    *   Sends a byte string `data` to the host via the semihosting debug console (`SYS_WRITEC`).
    *   **Framing:** The data is prefixed with a 2-byte big-endian length header. This allows the receiving end (the host script) to know how many bytes to expect for the payload.
    *   Maximum payload size is 65535 bytes (0xFFFF).

*   **`usemihosting.framed_console_recv()` -> `bytes`**
    *   Receives a length-prefixed frame of data from the host via the semihosting debug console (`SYS_READC`).
    *   It first reads the 2-byte length header, then reads that many bytes for the payload.
    *   Returns the received payload as a `bytes` object.
    *   This function is blocking.

## 4. Error Handling

File operations in `usemihosting` will generally raise an `OSError` exception upon failure. The module attempts to use the `errno` value provided by the host system through the `SYS_ERRNO` semihosting call, mapping it to MicroPython's `uerrno` constants where possible.

## 5. Example Usage

Refer to the test scripts for more detailed examples:
-   File I/O: `tests/semihosting/test_file_io.py`
-   Console Pipe: `tests/semihosting/test_console_pipe.py`

### Basic File Write/Read

```python
import usemihosting
import uerrno

filename = "semi_test.txt"
content_written = "Hello from MicroPython via Semihosting!\nLine 2."

try:
    # Write to a file on the host
    with usemihosting.open(filename, "w") as f:
        f.write(content_written)
    print(f"Successfully wrote to '{filename}' on the host.")

    # Read back from the file
    with usemihosting.open(filename, "r") as f:
        content_read = f.read()
        print(f"Read from '{filename}':\n{content_read}")
    
    assert content_read == content_written

    # Clean up
    usemihosting.remove(filename)
    print(f"Successfully removed '{filename}' from the host.")

except OSError as e:
    print(f"An OSError occurred: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

### Console Data Pipe (Conceptual - Requires Host Script)

This example shows the MicroPython side. The `tools/semihosting_console_pipe.py` script must be running on the host, connected to QEMU's serial TCP port.

```python
import usemihosting

if usemihosting.is_semihosting_available():
    print("Semihosting detected. Testing console pipe...")
    
    message_to_send = b"Ping from MicroPython!"
    
    try:
        print(f"Sending to host: {message_to_send!r}")
        usemihosting.framed_console_send(message_to_send)
        
        print("Waiting for echo from host...")
        received_message = usemihosting.framed_console_recv()
        
        print(f"Received from host: {received_message!r}")
        
        if received_message == message_to_send:
            print("Console pipe echo successful!")
        else:
            print("Console pipe echo mismatch.")
            
    except OSError as e:
        print(f"Console pipe OSError: {e}")
    except Exception as e:
        print(f"Console pipe unexpected error: {e}")
else:
    print("Semihosting not available, skipping console pipe test.")
```

## 6. Limitations and Future Work

*   **`SEEK_CUR` Limitation:** Seeking relative to the current position (`whence=1`) in files may not be supported directly by all semihosting implementations and might raise an error.
*   **No Directory Operations:** Functions like `listdir`, `mkdir`, `rmdir` are not currently implemented.
*   **No `stat` Operation:** Getting file metadata (size, type, timestamps) via a `stat`-like function is not implemented.
*   **Console Pipe is Raw Bytes:** The `framed_console_send`/`recv` functions provide a raw byte stream. They do not implement any higher-level networking protocols.
*   **Error Mapping:** The mapping from host `errno` to MicroPython `uerrno` is basic and might not cover all cases or host variations perfectly.
*   **Performance:** Semihosting is generally slow due to the debug communication mechanism. It's suitable for debugging and simple I/O, not high-performance data transfer.

Future work could include addressing these limitations, particularly adding more file system operations and potentially more robust error handling or console communication features.
```

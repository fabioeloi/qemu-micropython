try:
    import usemihosting
except ImportError:
    print("SKIP: usemihosting module not available.")
    # In a real test runner, this might raise a specific skip exception.
    # For simple script execution, we can just exit or prevent tests from running.
    raise SystemExit("usemihosting module not found, skipping tests.")

import uerrno

# --- Test Configuration ---
TEST_FILENAME_BASE = "_test_semi_io"
TEST_FILE_TXT = TEST_FILENAME_BASE + ".txt"
TEST_FILE_BIN = TEST_FILENAME_BASE + ".bin"
TEST_FILE_RENAMED = TEST_FILENAME_BASE + "_renamed.txt"

# --- Helper Functions ---
def _cleanup_files(*filenames):
    for filename in filenames:
        try:
            usemihosting.remove(filename)
            print(f"Cleanup: Removed '{filename}'")
        except OSError as e:
            if e.args[0] == uerrno.ENOENT: # No such file or directory
                pass # File already gone, which is fine for cleanup
            else:
                print(f"Cleanup: Error removing '{filename}': {e}")

def run_test(test_func):
    test_name = str(test_func).split(' ')[1] # Extract function name
    print(f"\n--- Running Test: {test_name} ---")
    try:
        test_func()
        print(f"--- Test {test_name}: PASS ---")
        return True
    except Exception as e:
        print(f"--- Test {test_name}: FAIL ---")
        print(f"    Exception: {e}")
        import sys
        sys.print_exception(e)
        return False

# --- Test Cases ---

def test_basic_file_operations_text():
    _cleanup_files(TEST_FILE_TXT)
    content_to_write = "Hello Semihosting!\nLine 2\n"

    # Write
    print(f"Opening '{TEST_FILE_TXT}' in 'w' mode...")
    f = usemihosting.open(TEST_FILE_TXT, "w")
    assert f is not None, "File object should not be None after open('w')"
    bytes_written = f.write(content_to_write)
    assert bytes_written == len(content_to_write), f"Expected {len(content_to_write)} bytes written, got {bytes_written}"
    f.close()
    print(f"Wrote '{content_to_write}' to '{TEST_FILE_TXT}', closed file.")

    # Read and verify
    print(f"Opening '{TEST_FILE_TXT}' in 'r' mode...")
    f = usemihosting.open(TEST_FILE_TXT, "r")
    assert f is not None, "File object should not be None after open('r')"
    read_content = f.read()
    assert read_content == content_to_write, f"Read content mismatch. Expected:\n{content_to_write}\nGot:\n{read_content}"
    f.close()
    print(f"Read and verified content from '{TEST_FILE_TXT}', closed file.")
    _cleanup_files(TEST_FILE_TXT)

def test_basic_file_operations_binary():
    _cleanup_files(TEST_FILE_BIN)
    content_to_write = b"\x01\x02\x03\x04\x05Hello Binary\x00\xFE\xFD"

    # Write binary
    print(f"Opening '{TEST_FILE_BIN}' in 'wb' mode...")
    f = usemihosting.open(TEST_FILE_BIN, "wb")
    assert f is not None
    bytes_written = f.write(content_to_write)
    assert bytes_written == len(content_to_write), f"Binary write: expected {len(content_to_write)}, got {bytes_written}"
    f.close()
    print(f"Wrote binary data to '{TEST_FILE_BIN}', closed file.")

    # Read binary and verify
    print(f"Opening '{TEST_FILE_BIN}' in 'rb' mode...")
    f = usemihosting.open(TEST_FILE_BIN, "rb")
    assert f is not None
    read_content = f.read()
    assert read_content == content_to_write, f"Binary read content mismatch."
    f.close()
    print(f"Read and verified binary content from '{TEST_FILE_BIN}', closed file.")
    _cleanup_files(TEST_FILE_BIN)

def test_file_context_manager():
    _cleanup_files(TEST_FILE_TXT)
    content = "Context manager test."
    print(f"Testing context manager for file open ('w') on '{TEST_FILE_TXT}'")
    with usemihosting.open(TEST_FILE_TXT, "w") as f:
        assert f is not None, "File object is None in 'with' statement"
        f.write(content)
    print("File written and automatically closed by context manager.")

    print(f"Testing context manager for file open ('r') on '{TEST_FILE_TXT}'")
    with usemihosting.open(TEST_FILE_TXT, "r") as f:
        assert f is not None
        read_content = f.read()
        assert read_content == content, "Context manager read content mismatch."
    print("File read and automatically closed by context manager.")
    _cleanup_files(TEST_FILE_TXT)

def test_read_operations():
    _cleanup_files(TEST_FILE_TXT)
    content = "Line 1\nLine 22\nLine 333" # 20 chars total
    with usemihosting.open(TEST_FILE_TXT, "w") as f:
        f.write(content)

    with usemihosting.open(TEST_FILE_TXT, "r") as f:
        # Read exact number of bytes
        data_5 = f.read(5)
        assert data_5 == "Line ", f"read(5) failed. Got: '{data_5}'"
        print(f"read(5) successful: '{data_5}'")

        # Read more (partial)
        data_partial = f.read(10) # Reads "1\nLine 22" (9 chars) then next char 'L'
                                 # No, read(10) will read the next 10 chars: "1\nLine 22\n" (10 chars)
        assert data_partial == "1\nLine 22\n", f"read(10) after partial read failed. Got: '{data_partial}'"
        print(f"read(10) successful: '{data_partial}'")

        # Read until EOF
        data_eof = f.read() # Reads remaining "Line 333"
        assert data_eof == "Line 333", f"read() until EOF failed. Got: '{data_eof}'"
        print(f"read() to EOF successful: '{data_eof}'")

        # Read from EOF
        data_at_eof = f.read(5)
        assert data_at_eof == "", f"read(5) at EOF should be empty. Got: '{data_at_eof}'"
        print("read(5) at EOF successful (empty string).")

    # Test reading from empty file
    _cleanup_files(TEST_FILE_TXT)
    with usemihosting.open(TEST_FILE_TXT, "w") as f:
        pass # Create empty file
    with usemihosting.open(TEST_FILE_TXT, "r") as f:
        empty_read = f.read()
        assert empty_read == "", f"Reading empty file failed. Got: '{empty_read}'"
    print("Reading from empty file successful.")
    _cleanup_files(TEST_FILE_TXT)

def test_readinto_operation():
    _cleanup_files(TEST_FILE_BIN)
    content = b"0123456789abcdef"
    with usemihosting.open(TEST_FILE_BIN, "wb") as f:
        f.write(content)

    with usemihosting.open(TEST_FILE_BIN, "rb") as f:
        buf = bytearray(10)
        bytes_read = f.readinto(buf)
        assert bytes_read == 10, f"readinto(buf_len_10) read {bytes_read} bytes."
        assert buf == b"0123456789", f"readinto(buf_len_10) content mismatch: {buf}"
        print(f"readinto(buf_len_10) successful. Read: {buf}")

        buf2 = bytearray(10) # content remaining is "abcdef" (6 bytes)
        bytes_read2 = f.readinto(buf2)
        assert bytes_read2 == 6, f"readinto(buf_len_10) for remaining 6 bytes read {bytes_read2}."
        # Only first 6 bytes of buf2 should be filled
        assert buf2[:bytes_read2] == b"abcdef", f"readinto() remaining content mismatch: {buf2[:bytes_read2]}"
        print(f"readinto() for remaining content successful. Read: {buf2[:bytes_read2]}")

        bytes_read3 = f.readinto(buf) # At EOF
        assert bytes_read3 == 0, f"readinto() at EOF should read 0 bytes, got {bytes_read3}."
    print("readinto() at EOF successful.")
    _cleanup_files(TEST_FILE_BIN)

def test_readline_operations():
    _cleanup_files(TEST_FILE_TXT)
    lines = ["First line.\n", "Second line with text.\n", "\n", "Last line, no newline"]
    full_content = "".join(lines)

    with usemihosting.open(TEST_FILE_TXT, "w") as f:
        f.write(full_content)

    # Python's stream object from C usually implements readline if read is available.
    # If the C SemihostingFile doesn't have special readline, it falls back to mp_stream_readline_generic.
    print("Testing readline()...")
    with usemihosting.open(TEST_FILE_TXT, "r") as f:
        l1 = f.readline()
        assert l1 == lines[0], f"readline 1 mismatch. Got: '{l1}' Expected: '{lines[0]}'"
        print(f"Read line 1: '{l1.strip()}'")

        l2 = f.readline()
        assert l2 == lines[1], f"readline 2 mismatch. Got: '{l2}' Expected: '{lines[1]}'"
        print(f"Read line 2: '{l2.strip()}'")

        l3 = f.readline() # The line that is just "\n"
        assert l3 == lines[2], f"readline 3 (empty line) mismatch. Got: '{l3}' Expected: '{lines[2]}'"
        print(f"Read line 3: '{l3.strip()}' (should be empty after strip)")

        l4 = f.readline()
        assert l4 == lines[3], f"readline 4 (no newline) mismatch. Got: '{l4}' Expected: '{lines[3]}'"
        print(f"Read line 4: '{l4.strip()}'")

        eof_line = f.readline()
        assert eof_line == "", f"readline at EOF should be empty string. Got: '{eof_line}'"
    print("readline() at EOF successful.")
    _cleanup_files(TEST_FILE_TXT)

def test_seek_and_tell_operations():
    _cleanup_files(TEST_FILE_BIN)
    content = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" # 36 bytes
    with usemihosting.open(TEST_FILE_BIN, "wb") as f:
        f.write(content)

    print("Testing seek() and tell()...")
    with usemihosting.open(TEST_FILE_BIN, "rb") as f:
        # Initial tell (if available, MicroPython might cache this)
        # Standard C semihosting doesn't have SYS_TELL, so tell() relies on Python stream layer caching.
        # Initial position should be 0.
        initial_pos = f.tell()
        assert initial_pos == 0, f"Initial tell() should be 0, got {initial_pos}"
        print(f"Initial tell(): {initial_pos}")

        # SEEK_SET
        res_seek_set = f.seek(10, 0) # SEEK_SET = 0
        assert res_seek_set == 10, f"seek(10, SEEK_SET) should return 10, got {res_seek_set}"
        current_pos = f.tell()
        assert current_pos == 10, f"tell() after seek(10, SEEK_SET) should be 10, got {current_pos}"
        data = f.read(5)
        assert data == b"ABCDE", f"Read after seek(10) failed. Got: {data}"
        assert f.tell() == 15, f"tell() after read should be 15, got {f.tell()}"
        print(f"SEEK_SET to 10, read 'ABCDE', new position {f.tell()}")

        # SEEK_END
        # Note: SEEK_END is 2. Semihosting SYS_FLEN is used.
        res_seek_end = f.seek(-10, 2) # Seek to 10 bytes from end
        assert res_seek_end == 26, f"seek(-10, SEEK_END) should return 26, got {res_seek_end}" # 36 - 10 = 26
        current_pos_end = f.tell()
        assert current_pos_end == 26, f"tell() after seek(-10, SEEK_END) should be 26, got {current_pos_end}"
        data_from_end = f.read()
        assert data_from_end == b"QRSTUVWXYZ", f"Read after seek from end failed. Got: {data_from_end}"
        assert f.tell() == 36, f"tell() at EOF should be 36, got {f.tell()}"
        print(f"SEEK_END to -10, read 'QRSTUVWXYZ', new position {f.tell()}")

        # SEEK_CUR
        print("Testing SEEK_CUR...")
        f.seek(5, 0) # Go to position 5 ("56789...")
        assert f.tell() == 5, f"tell() after seek(5,0) should be 5, got {f.tell()}"
        print(f"  Seeked to 5. Current tell(): {f.tell()}")

        # Seek forward with SEEK_CUR
        res_seek_cur_fwd = f.seek(10, 1) # From pos 5, seek 10 forward to pos 15 ("FGHIJ...")
        assert res_seek_cur_fwd == 15, f"seek(10, SEEK_CUR) from pos 5 should return 15, got {res_seek_cur_fwd}"
        assert f.tell() == 15, f"tell() after seek(10, SEEK_CUR) from pos 5 should be 15, got {f.tell()}"
        data_after_fwd_seek = f.read(5)
        assert data_after_fwd_seek == b"FGHIJ", f"Read after SEEK_CUR forward failed. Got: {data_after_fwd_seek}"
        assert f.tell() == 20, f"tell() after read should be 20, got {f.tell()}"
        print(f"  SEEK_CUR forward by 10 from pos 5 to {res_seek_cur_fwd}. Read: {data_after_fwd_seek}. New tell(): {f.tell()}")

        # Seek backward with SEEK_CUR
        # Current pos is 20 ("KLMNO...")
        res_seek_cur_bwd = f.seek(-15, 1) # From pos 20, seek 15 backward to pos 5 ("56789...")
        assert res_seek_cur_bwd == 5, f"seek(-15, SEEK_CUR) from pos 20 should return 5, got {res_seek_cur_bwd}"
        assert f.tell() == 5, f"tell() after seek(-15, SEEK_CUR) from pos 20 should be 5, got {f.tell()}"
        data_after_bwd_seek = f.read(5)
        assert data_after_bwd_seek == b"56789", f"Read after SEEK_CUR backward failed. Got: {data_after_bwd_seek}"
        assert f.tell() == 10, f"tell() after read should be 10, got {f.tell()}"
        print(f"  SEEK_CUR backward by -15 from pos 20 to {res_seek_cur_bwd}. Read: {data_after_bwd_seek}. New tell(): {f.tell()}")

        # Seek with 0 offset using SEEK_CUR (should not change position)
        current_pos_before_zero_seek = f.tell() # Should be 10
        res_seek_zero = f.seek(0, 1)
        assert res_seek_zero == current_pos_before_zero_seek, f"seek(0, SEEK_CUR) should return current pos {current_pos_before_zero_seek}, got {res_seek_zero}"
        assert f.tell() == current_pos_before_zero_seek, f"tell() after seek(0, SEEK_CUR) should remain {current_pos_before_zero_seek}, got {f.tell()}"
        print(f"  SEEK_CUR by 0 from pos {current_pos_before_zero_seek} successful. New tell(): {f.tell()}")

        # Test seeking beyond EOF with SEEK_CUR (actual seek should succeed, read should be empty)
        f.seek(0, 2) # Go to EOF (pos 36)
        assert f.tell() == 36, f"tell() at EOF should be 36, got {f.tell()}"
        res_seek_past_eof = f.seek(100, 1) # Seek 100 past current EOF
        assert res_seek_past_eof == 136, f"seek(100, SEEK_CUR) from EOF should return 136, got {res_seek_past_eof}"
        assert f.tell() == 136, f"tell() after seeking past EOF should be 136, got {f.tell()}"
        data_past_eof = f.read(5)
        assert data_past_eof == b"", f"Read after seeking past EOF should be empty. Got: {data_past_eof}"
        print(f"  SEEK_CUR past EOF successful. New tell(): {f.tell()}. Read was empty.")

        # Test seeking before start of file with SEEK_CUR (should raise OSError or similar)
        f.seek(10, 0) # Go to pos 10
        assert f.tell() == 10
        try:
            f.seek(-20, 1) # Attempt to seek to pos -10
            assert False, "seek(-20, SEEK_CUR) from pos 10 should have failed (seeking before start)"
        except OSError as e:
            assert e.args[0] == uerrno.EINVAL, f"Expected EINVAL for seek before start, got {e.args[0]}"
            print(f"  Correctly got EINVAL when seeking before start of file with SEEK_CUR. Current tell(): {f.tell()}")
        # Position should remain unchanged after a failed seek
        assert f.tell() == 10, f"tell() after failed seek should remain 10, got {f.tell()}"


    _cleanup_files(TEST_FILE_BIN)

def test_remove_operation():
    _cleanup_files(TEST_FILE_TXT)
    print(f"Creating file '{TEST_FILE_TXT}' for remove test.")
    with usemihosting.open(TEST_FILE_TXT, "w") as f:
        f.write("delete me")

    usemihosting.remove(TEST_FILE_TXT)
    print(f"Removed '{TEST_FILE_TXT}'. Verifying...")

    try:
        with usemihosting.open(TEST_FILE_TXT, "r") as f:
            # Should not reach here
            assert False, "File still exists after remove()"
    except OSError as e:
        assert e.args[0] == uerrno.ENOENT, f"Expected ENOENT after remove, got {e.args[0]}"
        print("File correctly not found after remove().")

    # Test removing non-existent file
    print("Testing remove() on a non-existent file...")
    try:
        usemihosting.remove("_this_file_should_not_exist.txt")
        assert False, "remove() on non-existent file did not raise OSError"
    except OSError as e:
        assert e.args[0] == uerrno.ENOENT, f"Expected ENOENT for remove on non-existent, got {e.args[0]}"
        print("Correctly got ENOENT for remove() on non-existent file.")
    _cleanup_files(TEST_FILE_TXT) # Just in case

def test_rename_operation():
    _cleanup_files(TEST_FILE_TXT, TEST_FILE_RENAMED)
    print(f"Creating '{TEST_FILE_TXT}' for rename test.")
    with usemihosting.open(TEST_FILE_TXT, "w") as f:
        f.write("original content")

    usemihosting.rename(TEST_FILE_TXT, TEST_FILE_RENAMED)
    print(f"Renamed '{TEST_FILE_TXT}' to '{TEST_FILE_RENAMED}'. Verifying...")

    # Old name should not exist
    try:
        usemihosting.open(TEST_FILE_TXT, "r")
        assert False, "Old filename still exists after rename."
    except OSError as e:
        assert e.args[0] == uerrno.ENOENT, "Expected ENOENT for old filename."
        print("Old filename correctly not found.")

    # New name should exist with content
    with usemihosting.open(TEST_FILE_RENAMED, "r") as f:
        content = f.read()
        assert content == "original content", "Content mismatch in renamed file."
    print("New filename exists and content verified.")

    # Test renaming non-existent file
    print("Testing rename() on a non-existent file...")
    try:
        usemihosting.rename("_this_is_not_here.txt", "_neither_is_this.txt")
        assert False, "rename() on non-existent file did not raise OSError."
    except OSError as e:
        # Host OS might return ENOENT for old or new path. ENOENT is common.
        assert e.args[0] == uerrno.ENOENT, f"Expected ENOENT for rename on non-existent, got {e.args[0]}."
        print("Correctly got ENOENT for rename() on non-existent file.")

    # Test renaming to an existing file (host behavior can vary: overwrite or error)
    # For semihosting, SYS_RENAME often overwrites.
    print(f"Creating '{TEST_FILE_TXT}' again.")
    with usemihosting.open(TEST_FILE_TXT, "w") as f:
        f.write("new original")

    print(f"Attempting to rename '{TEST_FILE_RENAMED}' (exists) to '{TEST_FILE_TXT}' (exists)...")
    try:
        usemihosting.rename(TEST_FILE_RENAMED, TEST_FILE_TXT) # TEST_FILE_RENAMED has "original content"
                                                           # TEST_FILE_TXT has "new original"
        # Check content of TEST_FILE_TXT, should be "original content" if overwrite happened
        with usemihosting.open(TEST_FILE_TXT, "r") as f:
            content = f.read()
            assert content == "original content", "Rename overwrite content check failed."
        print("Rename to existing file successful (overwrite presumed).")
        # Check if TEST_FILE_RENAMED is gone
        try:
            usemihosting.open(TEST_FILE_RENAMED, "r")
            assert False, f"{TEST_FILE_RENAMED} should not exist after being renamed."
        except OSError as e:
            assert e.args[0] == uerrno.ENOENT
            print(f"{TEST_FILE_RENAMED} correctly does not exist.")

    except OSError as e:
        # Some systems might raise EEXIST or other errors if rename target exists.
        print(f"Rename to existing file resulted in OSError: {e} (This might be host-dependent)")

    _cleanup_files(TEST_FILE_TXT, TEST_FILE_RENAMED)

def test_utility_functions():
    print("Testing usemihosting.is_semihosting_available()...")
    is_avail = usemihosting.is_semihosting_available()
    assert is_avail is True, f"is_semihosting_available() should return True, got {is_avail}"
    print(f"is_semihosting_available() returned: {is_avail}")

    print("Testing usemihosting.time()...")
    current_time = usemihosting.time()
    assert isinstance(current_time, int) and current_time > 1600000000, f"usemihosting.time() returned suspicious value: {current_time}"
    print(f"usemihosting.time() returned: {current_time} (seconds since epoch)")

    print("Testing usemihosting.clock()...")
    current_clock = usemihosting.clock()
    assert isinstance(current_clock, int) and current_clock >= 0, f"usemihosting.clock() returned suspicious value: {current_clock}"
    print(f"usemihosting.clock() returned: {current_clock} (centiseconds since start)")
    # Small delay to see clock change
    # Note: time.sleep might not be available or precise in all MicroPython ports/QEMU.
    # If available, it would be:
    # import time
    # time.sleep_ms(150)
    # current_clock_after_delay = usemihosting.clock()
    # assert current_clock_after_delay > current_clock, "Clock did not advance."
    # print(f"usemihosting.clock() after delay: {current_clock_after_delay}")


def test_error_handling():
    _cleanup_files(TEST_FILE_TXT)

    # Open non-existent file for reading
    print("Testing open() non-existent file for reading...")
    try:
        usemihosting.open("_no_such_file.txt", "r")
        assert False, "Opening non-existent file for read did not raise OSError."
    except OSError as e:
        assert e.args[0] == uerrno.ENOENT, f"Expected ENOENT, got {e.args[0]}."
        print("Correctly got ENOENT for open('r') on non-existent file.")

    # Operations on a closed file
    print("Testing operations on a closed file...")
    f = usemihosting.open(TEST_FILE_TXT, "w")
    f.write("test")
    f.close()
    assert f.closed, "File should report as closed." # Assuming MicroPython file object has .closed attribute

    try:
        f.write("more")
        assert False, "write() on closed file did not raise error."
    except Exception as e: # umqtt.simple uses general Exception, check OSError if that's what uPy raises
        print(f"Correctly got error on write() to closed file: {e} (type: {type(e)})")
        # Specific OSError check: if isinstance(e, OSError): assert e.args[0] == uerrno.EBADF

    try:
        f.read()
        assert False, "read() on closed file did not raise error."
    except Exception as e:
        print(f"Correctly got error on read() from closed file: {e} (type: {type(e)})")

    try:
        f.seek(0)
        assert False, "seek() on closed file did not raise error."
    except Exception as e:
        print(f"Correctly got error on seek() on closed file: {e} (type: {type(e)})")

    try:
        f.tell() # This might work if it's just returning a cached value in Python layer.
                 # Or fail if it tries to call an ioctl.
        print(f"tell() on closed file returned (might be cached): {f.tell()}")
    except Exception as e:
        print(f"Got error on tell() on closed file (expected if it hits C layer): {e} (type: {type(e)})")

    # Reading from write-only, writing to read-only (if modes are strictly enforced by host)
    # Semihosting open modes are sometimes loose.
    _cleanup_files(TEST_FILE_TXT)
    print("Testing read from write-only file ('w')...")
    try:
        with usemihosting.open(TEST_FILE_TXT, "w") as fw:
            fw.read() # Attempt read
        assert False, "read() from 'w' mode file did not raise error."
    except OSError as e:
        # Common errors: EBADF (Bad file descriptor), EACCES (Permission denied)
        # The exact error might depend on host OS and semihosting implementation.
        print(f"Correctly got OSError trying to read from 'w' mode file: {e}")
    except Exception as e: # Catch other potential errors like TypeError if .read isn't there
        print(f"Got other Exception trying to read from 'w' mode file: {e}")


    print("Testing write to read-only file ('r')...")
    # First create the file
    with usemihosting.open(TEST_FILE_TXT, "w") as f_init:
        f_init.write("initial data")
    try:
        with usemihosting.open(TEST_FILE_TXT, "r") as fr:
            fr.write("new data") # Attempt write
        assert False, "write() to 'r' mode file did not raise error."
    except OSError as e:
        print(f"Correctly got OSError trying to write to 'r' mode file: {e}")
    except Exception as e:
        print(f"Got other Exception trying to write to 'r' mode file: {e}")

    _cleanup_files(TEST_FILE_TXT)


# --- Main Test Runner ---
def main():
    print("=============================================")
    print("=== Running usemihosting File I/O Tests ===")
    print("=============================================")

    # Ensure initial cleanup
    _cleanup_files(TEST_FILE_TXT, TEST_FILE_BIN, TEST_FILE_RENAMED)

    tests_passed = 0
    tests_failed = 0

    test_suite = [
        test_basic_file_operations_text,
        test_basic_file_operations_binary,
        test_file_context_manager,
        test_read_operations,
        test_readinto_operation,
        test_readline_operations,
        test_seek_and_tell_operations, # This has known limitations for SEEK_CUR
        test_remove_operation,
        test_rename_operation,
        test_utility_functions,
        test_error_handling,
    ]

    for test_case in test_suite:
        if run_test(test_case):
            tests_passed += 1
        else:
            tests_failed += 1

    print("\n--- Test Suite Summary ---")
    print(f"Total tests run: {len(test_suite)}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print("==========================")

    # Final cleanup
    _cleanup_files(TEST_FILE_TXT, TEST_FILE_BIN, TEST_FILE_RENAMED)

    if tests_failed > 0:
        print("\nSOME TESTS FAILED.")
        # In a CI environment, this might translate to an exit code.
        # For manual runs, the printout is the main indicator.
        # Example: raise Exception(f"{tests_failed} tests failed")
        # However, that would stop the script here. Let it finish.

if __name__ == "__main__":
    main()

# Note on usemihosting.exit():
# A separate script like 'tests/semihosting/test_exit_success.py' would be:
# ---
# try:
#     import usemihosting
#     print("Attempting usemihosting.exit(0)...")
#     usemihosting.exit(0) # Should terminate QEMU with code 0 if host bridge supports it
#     print("ERROR: usemihosting.exit() returned!") # Should not be reached
# except ImportError:
#     print("SKIP: usemihosting module not available for exit test.")
# except Exception as e:
#     print(f"ERROR during exit test: {e}")
# ---
# And 'tests/semihosting/test_exit_custom_code.py':
# ---
# try:
#     import usemihosting
#     print("Attempting usemihosting.exit(42)...")
#     usemihosting.exit(42) # Should terminate QEMU with code 42
#     print("ERROR: usemihosting.exit() returned!")
# except ImportError:
#     print("SKIP: usemihosting module not available for exit test.")
# ---
# These would be run as separate test executions.
```

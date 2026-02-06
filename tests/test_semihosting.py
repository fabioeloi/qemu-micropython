"""
Test script for QEMU semihosting integration

This script tests the qemu_console module which provides
semihosting-based console output for MicroPython in QEMU.
"""

import sys

def test_semihosting():
    """Test semihosting functionality"""
    
    print("=== Testing QEMU Semihosting Integration ===")
    print("")
    
    try:
        import qemu_console
        print("[OK] qemu_console module imported successfully")
    except ImportError as e:
        print(f"[FAIL] Cannot import qemu_console: {e}")
        print("Semihosting module not available")
        return False
    
    # Test if semihosting is available
    print("\n1. Checking semihosting availability...")
    try:
        if qemu_console.available():
            print("[OK] Semihosting is available")
        else:
            print("[WARN] Semihosting reports not available")
            return False
    except Exception as e:
        print(f"[FAIL] Error checking availability: {e}")
        return False
    
    # Test string output
    print("\n2. Testing string output via semihosting...")
    try:
        qemu_console.print_text("Hello from MicroPython via semihosting!\r\n")
        print("[OK] String output successful")
    except Exception as e:
        print(f"[FAIL] String output failed: {e}")
        return False
    
    # Test character output
    print("\n3. Testing character output via semihosting...")
    try:
        test_chars = [72, 101, 108, 108, 111, 10]  # "Hello\n"
        for ch in test_chars:
            qemu_console.print_char(ch)
        print("[OK] Character output successful")
    except Exception as e:
        print(f"[FAIL] Character output failed: {e}")
        return False
    
    # Test multiple strings
    print("\n4. Testing multiple string outputs...")
    try:
        messages = [
            "Line 1: Testing semihosting\r\n",
            "Line 2: Multiple messages\r\n",
            "Line 3: Final test line\r\n",
        ]
        for msg in messages:
            qemu_console.print_text(msg)
        print("[OK] Multiple string outputs successful")
    except Exception as e:
        print(f"[FAIL] Multiple outputs failed: {e}")
        return False
    
    print("\n=== All Tests Passed ===")
    return True

if __name__ == "__main__":
    success = test_semihosting()
    sys.exit(0 if success else 1)

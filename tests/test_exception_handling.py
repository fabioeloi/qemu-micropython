"""
Test script for MicroPython exception handling in GDB

This script tests the enhanced exception handling capabilities
of the GDB integration.
"""

def test_simple_exception():
    """Test a simple exception case"""
    x = 42
    y = 0
    try:
        result = x / y  # Will raise ZeroDivisionError
    except ZeroDivisionError as e:
        print(f"Caught expected exception: {e}")
        return "Exception handled"

def test_nested_exception():
    """Test nested exception handling"""
    def inner_function():
        items = [1, 2, 3]
        return items[5]  # Will raise IndexError
    
    try:
        inner_function()
    except IndexError as e:
        try:
            # Try something else that will fail
            int("not a number")  # Will raise ValueError
        except ValueError as e2:
            print(f"Caught nested exception: {e2}")
            return "Nested exception handled"

def test_custom_exception():
    """Test custom exception class"""
    class CustomError(Exception):
        def __init__(self, message, code):
            self.message = message
            self.code = code
    
    try:
        raise CustomError("Something went wrong", 42)
    except CustomError as e:
        print(f"Caught custom exception: {e.message} (code: {e.code})")
        return "Custom exception handled"

def test_exception_with_locals():
    """Test exception with local variable state"""
    x = 100
    y = "test"
    items = [1, 2, 3]
    data = {"key": "value"}
    
    try:
        # Create some local variables
        temp = x + len(items)
        # Raise an exception
        raise RuntimeError("Test exception with locals")
    except RuntimeError as e:
        print(f"Exception raised with locals: {e}")
        return "Exception with locals handled"

def main():
    """Main test function"""
    print("=== Exception Handling Test ===")
    
    # Run all tests
    tests = [
        test_simple_exception,
        test_nested_exception,
        test_custom_exception,
        test_exception_with_locals
    ]
    
    for test in tests:
        print(f"\nRunning {test.__name__}...")
        try:
            result = test()
            print(f"Test completed: {result}")
        except Exception as e:
            print(f"Test failed: {e}")

if __name__ == "__main__":
    main() 
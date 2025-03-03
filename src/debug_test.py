"""
MicroPython GDB Integration Test Script

This script exercises various Python features to test the GDB integration.
It includes different data types, function calls, and exception handling
to verify that the debugger can properly inspect the Python state.
"""

# Global variables for testing
test_string = "Hello, Debugger!"
test_number = 42
test_list = [1, 2, 3, "four", 5.0]
test_dict = {"name": "GDB Test", "version": 1.0}

def factorial(n):
    """Recursive function to test stack inspection"""
    # Local variables
    result = 1
    current = n
    
    # Test different types
    numbers = list(range(1, n + 1))
    description = f"Computing factorial of {n}"
    
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

def process_data(data):
    """Function to test error handling"""
    try:
        # Local variables of different types
        items = []
        count = 0
        
        for item in data:
            count += 1
            items.append(str(item).upper())
            
            # Artificial delay for debugging
            for _ in range(1000):
                pass
            
            # Raise exception for testing
            if isinstance(item, dict):
                raise ValueError("Dictionary not allowed in data")
    
    except Exception as e:
        # Test exception handling
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"Error ({error_type}): {error_msg}")
        return None
    
    return items

def main():
    """Main test function"""
    print("Starting GDB integration test...")
    
    # Test factorial calculation
    result = factorial(5)
    print(f"Factorial result: {result}")
    
    # Test data processing
    test_data = [
        "first",
        123,
        3.14,
        [1, 2, 3],
        {"key": "value"}  # This will trigger an error
    ]
    
    processed = process_data(test_data)
    print(f"Processed data: {processed}")
    
    print("Test completed")

if __name__ == "__main__":
    main() 
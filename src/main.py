
def test_zero_division():
    '''Test division by zero exception'''
    print("Testing division by zero...")
    a = 10
    b = 0
    # This will raise ZeroDivisionError
    result = a / b
    return result

def test_index_error():
    '''Test index error exception'''
    print("Testing index error...")
    items = [1, 2, 3]
    # This will raise IndexError
    item = items[5]
    return item

def test_attribute_error():
    '''Test attribute error exception'''
    print("Testing attribute error...")
    class TestClass:
        def __init__(self):
            self.value = 42
    
    obj = TestClass()
    # This will raise AttributeError
    return obj.nonexistent_attribute

def test_nested_exception():
    '''Test nested exception handling'''
    print("Testing nested exception...")
    
    def inner_function():
        items = [1, 2, 3]
        return items[5]  # This will raise IndexError
    
    try:
        inner_function()
    except IndexError:
        # This will raise ZeroDivisionError
        return 1 / 0

def test_custom_exception():
    '''Test custom exception handling'''
    print("Testing custom exception...")
    
    class CustomError(Exception):
        def __init__(self, message, code):
            self.message = message
            self.code = code
            super().__init__(f"{message} (code: {code})")
    
    # This will raise CustomError
    raise CustomError("This is a custom error", 42)

def main():
    '''Main function'''
    print("Starting exception visualization tests...")
    
    try:
        test_zero_division()
    except ZeroDivisionError as e:
        print(f"Caught ZeroDivisionError: {e}")
    
    try:
        test_index_error()
    except IndexError as e:
        print(f"Caught IndexError: {e}")
    
    try:
        test_attribute_error()
    except AttributeError as e:
        print(f"Caught AttributeError: {e}")
    
    try:
        test_nested_exception()
    except ZeroDivisionError as e:
        print(f"Caught nested ZeroDivisionError: {e}")
    
    try:
        test_custom_exception()
    except Exception as e:
        print(f"Caught CustomError: {e}")
    
    print("All tests completed")
    return 42

if __name__ == "__main__":
    main()

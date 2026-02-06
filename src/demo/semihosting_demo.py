"""
Demonstration of QEMU Semihosting for MicroPython

Shows practical examples of using semihosting for reliable
console output when running MicroPython in QEMU.
"""

def demo_basic_output():
    """Demonstrate basic semihosting output"""
    try:
        import qemu_console
        
        if not qemu_console.available():
            print("Semihosting not available, using standard print")
            return
        
        qemu_console.print_text("\r\n--- Basic Output Demo ---\r\n")
        qemu_console.print_text("This text is output via ARM semihosting\r\n")
        qemu_console.print_text("It provides reliable console I/O in QEMU\r\n")
        
    except ImportError:
        print("qemu_console module not available")

def demo_progress_indicator():
    """Demonstrate a progress indicator using semihosting"""
    try:
        import qemu_console
        import time
        
        if not qemu_console.available():
            return
        
        qemu_console.print_text("\r\n--- Progress Indicator Demo ---\r\n")
        qemu_console.print_text("Processing: [")
        
        for i in range(20):
            qemu_console.print_char(ord('.'))
            time.sleep(0.1)
        
        qemu_console.print_text("]\r\n")
        qemu_console.print_text("Complete!\r\n")
        
    except ImportError:
        pass

def demo_formatted_output():
    """Demonstrate formatted output with semihosting"""
    try:
        import qemu_console
        
        if not qemu_console.available():
            return
        
        qemu_console.print_text("\r\n--- Formatted Output Demo ---\r\n")
        
        # Simulate sensor readings
        temperature = 23.5
        humidity = 65
        pressure = 1013
        
        qemu_console.print_text(f"Temperature: {temperature:.1f}C\r\n")
        qemu_console.print_text(f"Humidity: {humidity}%\r\n")
        qemu_console.print_text(f"Pressure: {pressure}hPa\r\n")
        
    except ImportError:
        pass

def main():
    """Run all demonstrations"""
    print("Starting QEMU Semihosting Demonstrations")
    print("=========================================")
    
    demo_basic_output()
    demo_progress_indicator()
    demo_formatted_output()
    
    print("\nDemonstrations complete")

if __name__ == "__main__":
    main()

def add(a, b):
    """Adds two numbers."""
    return a + b

def subtract(a, b):
    """Subtracts two numbers."""
    return a - b

def multiply(a, b):
    """Multiplies two numbers."""
    return a * b

def divide(a, b):
    """Divides two numbers. Handles division by zero."""
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b

# Example usage (optional, but good for testing)
if __name__ == "__main__":
    print(f"Addition: 10 + 5 = {add(10, 5)}")
    print(f"Subtraction: 10 - 5 = {subtract(10, 5)}")
    print(f"Multiplication: 10 * 5 = {multiply(10, 5)}")
    print(f"Division: 10 / 5 = {divide(10, 5)}")
    print(f"Division by zero: 10 / 0 = {divide(10, 0)}")
# calculator.py
"""
A simple command-line calculator program.
This file provides basic arithmetic functionalities.
"""

def add(x, y):
    """Adds two numbers."""
    return x + y

def subtract(x, y):
    """Subtracts two numbers."""
    return x - y

def multiply(x, y):
    """Multiplies two numbers."""
    return x * y

def divide(x, y):
    """Divides two numbers. Handles division by zero."""
    if y == 0:
        return "Error! Division by zero is not allowed."
    return x / y

def calculator():
    """Main function to run the calculator interface."""
    print("=============================")
    print("Simple Python Calculator")
    print("=============================")

    while True:
        # Display menu options
        print("\nSelect operation:")
        print("1. Add      (+) ")
        print("2. Subtract (-) ")
        print("3. Multiply (*) ")
        print("4. Divide   (/) ")
        print("5. Exit")

        choice = input("Enter choice (1/2/3/4/5): ").strip()

        if choice == '5':
            print("\nExiting calculator. Goodbye!")
            break

        try:
            num1 = float(input("Enter first number: "))
            num2 = float(input("Enter second number: "))
        except ValueError:
            print("\nInvalid input. Please enter valid numbers.")
            continue

        result = None
        if choice == '1':
            result = add(num1, num2)
        elif choice == '2':
            result = subtract(num1, num2)
        elif choice == '3':
            result = multiply(num1, num2)
        elif choice == '4':
            result = divide(num1, num2)

        if result is not None:
            print(f"\nResult: {num1} {'+' if choice == '1' else '-' if choice == '2' else '*' if choice == '3' else '/' if choice == '4'}{num2} = {result}")

if __name__ == "__main__":
    calculator()
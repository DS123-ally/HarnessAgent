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
    """Main function to run the simple calculator interface."""
    print("--- Simple Calculator ---")
    print("Select operation:")
    print("1. Add      (+)")
    print("2. Subtract (-)")
    print("3. Multiply (*)")
    print("4. Divide   (/)")

    while True:
        choice = input("Enter choice (1/2/3/4) or 'exit': ")
        if choice == "exit":
            print("Exiting calculator. Goodbye!")
            break

        if choice not in ["1", "2", "3", "4"]:
            print("Invalid choice. Please select a valid option.")
            continue

        try:
            num1 = float(input("Enter first number: "))
            num2 = float(input("Enter second number: "))
        except ValueError:
            print("Invalid input. Please enter numeric values.")
            continue

        operator = ""
        if choice == "1":
            operator = "+"
        elif choice == "2":
            operator = "-"
        elif choice == "3":
            operator = "*"
        elif choice == "4":
            operator = "/"

        print(f"\nResult: {num1} {operator} {num2} = {result}\n")

if __name__ == "__main__":
    calculator()
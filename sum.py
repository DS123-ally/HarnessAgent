def find_min_max(numbers):
    """
    Finds the minimum and maximum number from a list of natural numbers.

    Args:
        numbers (list): A list of natural numbers.

    Returns:
        tuple: A tuple containing (min_value, max_value).
               Returns (None, None) if the list is empty.
    """
    if not numbers:
        return None, None
    
    # Python's built-in min() and max() functions are efficient for this.
    min_val = min(numbers)
    max_val = max(numbers)
    
    return min_val, max_val

if __name__ == "__main__":
    print("--- Min/Max Finder ---")
    
    # Example 1: A standard set of natural numbers
    natural_numbers_set1 = [5, 12, 3, 9, 1]
    min1, max1 = find_min_max(natural_numbers_set1)
    
    if min1 is not None and max1 is not None:
        print(f"Input numbers: {natural_numbers_set1}")
        print(f"Minimum number: {min1}")
        print(f"Maximum number: {max1}")
    else:
        print("Error: The list was empty.")

    print("-" * 20)

    # Example 2: Another set of numbers
    natural_numbers_set2 = [100, 50, 75]
    min2, max2 = find_min_max(natural_numbers_set2)
    
    if min2 is not None and max2 is not None:
        print(f"Input numbers: {natural_numbers_set2}")
        print(f"Minimum number: {min2}")
        print(f"Maximum number: {max2}")
    else:
        print("Error: The list was empty.")

    print("-" * 20)
    
    # Example 3: Handling an empty list
    empty_list = []
    min3, max3 = find_min_max(empty_list)
    if min3 is None and max3 is None:
        print("Testing with an empty list. Min/Max correctly reported as None.")
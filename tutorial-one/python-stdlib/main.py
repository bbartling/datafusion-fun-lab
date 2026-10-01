import sys
import csv
import math

def main():
    # 1. Parse CLI arguments
    if len(sys.argv) != 3:
        print("Usage: python script.py <csv-file> <column>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    column_name = sys.argv[2]

    # 2. Open CSV file and parse headers
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)

            try:
                headers = next(reader)
            except StopIteration:
                print(f"Error: File '{file_path}' is empty.", file=sys.stderr)
                sys.exit(1)

            # 3. Locate requested column index
            if column_name not in headers:
                print(f"Column '{column_name}' not found.", file=sys.stderr)
                print("\nAvailable columns in this file:")
                print("-------------------------------")
                for col in headers:
                    print(f"- {col}")
                print("-------------------------------")
                sys.exit(1)

            column_index = headers.index(column_name)

            # 4. Parse numeric values
            values = []
            for row in reader:
                if column_index < len(row):
                    field = row[column_index]
                    try:
                        num = float(field)
                        values.append(num)
                    except ValueError:
                        continue  # Skip unparseable rows

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        sys.exit(1)

    count = len(values)
    if count == 0:
        print(f"No numeric values found or column evaluated empty for '{column_name}'.", file=sys.stderr)
        sys.exit(1)

    # 5. Calculate Metrics
    total = 0.0
    min_val = values[0]
    max_val = values[0]

    for value in values:
        total += value
        if value > max_val: max_val = value
        if value < min_val: min_val = value

    avg = total / count

    # Sample Variance and Std Dev
    variance_sum = 0.0
    for value in values:
        diff = value - avg
        variance_sum += diff * diff

    if count > 1:
        variance = variance_sum / (count - 1)
    else:
        variance = 0.0

    std_dev = math.sqrt(variance)

    # Median via hand-coded selection sort (apples-to-apples with a simple
    # O(n^2) sort — not Python's built-in Timsort).
    scratchpad = list(values)
    n = len(scratchpad)
    for i in range(n):
        min_i = i
        for j in range(i + 1, n):
            if scratchpad[j] < scratchpad[min_i]:
                min_i = j
        scratchpad[i], scratchpad[min_i] = scratchpad[min_i], scratchpad[i]

    mid = count // 2
    if count % 2 == 0:
        median = (scratchpad[mid - 1] + scratchpad[mid]) / 2.0
    else:
        median = scratchpad[mid]

    # 6. Display statistics
    print("==============================")
    print("Engine:             Python (Standard Lib Only)")
    print(f"Column:             {column_name}")
    print(f"Count:              {count}")
    print(f"Total:              {total:.2f}")
    print(f"Min:                {min_val:.2f}")
    print(f"Max:                {max_val:.2f}")
    print(f"Average:            {avg:.2f}")
    print(f"Median:             {median:.2f}")
    print(f"Sample Variance:    {variance:.4f}")
    print(f"Sample Std Dev:     {std_dev:.4f}")
    print("==============================")

if __name__ == "__main__":
    main()

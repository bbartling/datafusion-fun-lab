import sys
import pandas as pd

def main():
    # 1. Parse CLI arguments
    if len(sys.argv) != 3:
        print("Usage: python script.py <csv-file> <column>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    column_name = sys.argv[2]

    try:
        # 2. Open CSV file
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Locate requested column
    if column_name not in df.columns:
        print(f"Column '{column_name}' not found.", file=sys.stderr)
        print("\nAvailable columns in this file:")
        print("-------------------------------")
        for col in df.columns:
            print(f"- {col}")
        print("-------------------------------")
        sys.exit(1)

    # 4. Parse numeric values and drop missing values/strings
    # errors='coerce' turns non-numeric fields into NaN, then dropna() removes them
    numeric_series = pd.to_numeric(df[column_name], errors='coerce').dropna()

    count = len(numeric_series)
    if count == 0:
        print(f"No numeric values found or column evaluated empty for '{column_name}'.", file=sys.stderr)
        sys.exit(1)

    # 5. Calculate metrics
    total = numeric_series.sum()
    min_val = numeric_series.min()
    max_val = numeric_series.max()
    avg = numeric_series.mean()
    median = numeric_series.median()

    # Pandas defaults to sample variance (ddof=1) matching DataFusion's VAR_SAMP
    variance = numeric_series.var()
    std_dev = numeric_series.std()

    # 6. Display statistics
    print("==============================")
    print("Engine:             Python (Pandas)")
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

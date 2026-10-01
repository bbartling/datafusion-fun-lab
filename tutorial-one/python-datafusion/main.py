import sys
from datafusion import SessionContext


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python main.py <csv-file> <column>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    column_name = sys.argv[2]

    try:
        ctx = SessionContext()
        ctx.register_csv("data_table", file_path)
        # Fail fast if column missing (list available)
        schema = ctx.table("data_table").schema()
        names = [f.name for f in schema]
        if column_name not in names:
            print(f"Column '{column_name}' not found.", file=sys.stderr)
            print("\nAvailable columns in this file:")
            print("-------------------------------")
            for name in names:
                print(f"- {name}")
            print("-------------------------------")
            sys.exit(1)

        query = f"""
            SELECT
                COUNT(TRY_CAST(\"{column_name}\" AS DOUBLE)) AS count,
                SUM(TRY_CAST(\"{column_name}\" AS DOUBLE)) AS total,
                MIN(TRY_CAST(\"{column_name}\" AS DOUBLE)) AS min,
                MAX(TRY_CAST(\"{column_name}\" AS DOUBLE)) AS max,
                AVG(TRY_CAST(\"{column_name}\" AS DOUBLE)) AS avg,
                MEDIAN(TRY_CAST(\"{column_name}\" AS DOUBLE)) AS median,
                VAR_SAMP(TRY_CAST(\"{column_name}\" AS DOUBLE)) AS variance,
                STDDEV_SAMP(TRY_CAST(\"{column_name}\" AS DOUBLE)) AS std_dev
            FROM data_table
        """
        df = ctx.sql(query)
        batches = df.collect()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not batches or batches[0].num_rows == 0:
        print(f"No numeric values found or column evaluated empty for '{column_name}'.", file=sys.stderr)
        sys.exit(1)

    batch = batches[0]
    # Arrow columns as Python scalars via to_pydict / pandas bridge if needed
    try:
        col = lambda i: batch.column(i)
        # Prefer pyarrow scalar extraction
        count = int(col(0)[0].as_py())
        total = float(col(1)[0].as_py() or 0.0)
        min_v = float(col(2)[0].as_py() or 0.0)
        max_v = float(col(3)[0].as_py() or 0.0)
        avg = float(col(4)[0].as_py() or 0.0)
        median = float(col(5)[0].as_py() or 0.0)
        variance = float(col(6)[0].as_py() or 0.0)
        std_dev = float(col(7)[0].as_py() or 0.0)
    except Exception:
        # Fallback: show() already ran logic; just print collect length
        print("Could not extract scalar stats from Arrow batch.", file=sys.stderr)
        sys.exit(1)

    if count == 0:
        print(f"No numeric values found or column evaluated empty for '{column_name}'.", file=sys.stderr)
        sys.exit(1)

    print("==============================")
    print("Engine:             Apache DataFusion (Python)")
    print(f"Column:             {column_name}")
    print(f"Count:              {count}")
    print(f"Total:              {total:.2f}")
    print(f"Min:                {min_v:.2f}")
    print(f"Max:                {max_v:.2f}")
    print(f"Average:            {avg:.2f}")
    print(f"Median:             {median:.2f}")
    print(f"Sample Variance:    {variance:.4f}")
    print(f"Sample Std Dev:     {std_dev:.4f}")
    print("==============================")


if __name__ == "__main__":
    main()

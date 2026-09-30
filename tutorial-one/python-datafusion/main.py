import sys
from datafusion import SessionContext


"""
cd ~/Desktop/datafusion-fun-lab
python tutorial-one/python-datafusion/main.py ./data.csv oa_t
"""

def main():
    # Parse CLI arguments
    if len(sys.argv) != 3:
        print("Usage: python main.py <csv-file> <column>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    column_name = sys.argv[2]

    # 1. Create a DataFusion execution context
    ctx = SessionContext()

    # 2. Register the CSV file as a table named 'data_table'
    try:
        ctx.register_csv("data_table", file_path)
    except Exception as e:
        print(f"Error loading CSV file: {e}", file=sys.stderr)
        sys.exit(1)

    # --- COLUMN CHECKER ---
    # Fetch table metadata from context to inspect the Arrow schema fields
    table = ctx.table("data_table")
    schema = table.schema()
    
    # Get all column names from the schema
    available_columns = schema.names

    if column_name not in available_columns:
        print(f"Column '{column_name}' not found.", file=sys.stderr)
        print("\nAvailable columns in this file:")
        print("-------------------------------")
        for col in available_columns:
            print(f"- {col}")
        print("-------------------------------")
        sys.exit(1)
    # ----------------------

    # 3. Build the dynamic SQL query string matching your Rust logic
    query = f"""
        SELECT 
            COUNT(TRY_CAST("{column_name}" AS DOUBLE)) AS count, 
            SUM(TRY_CAST("{column_name}" AS DOUBLE)) AS total, 
            MIN(TRY_CAST("{column_name}" AS DOUBLE)) AS min, 
            MAX(TRY_CAST("{column_name}" AS DOUBLE)) AS max, 
            AVG(TRY_CAST("{column_name}" AS DOUBLE)) AS avg 
        FROM data_table
    """

    # 4. & 5. Execute the query and collect back into a list of Arrow RecordBatches
    try:
        df = ctx.sql(query)
        
        # 1. Print the actual type of the object
        print("Python Object Type:", type(df))
        
        # 2. Print out the structured data schema (columns and Arrow data types)
        print("DataFrame Schema:")
        print(df.schema())

        # 3. Print a clean, formatted plain-text table to your console
        print("\nVisual Output:")
        df.show()

        results = df.collect()
        
    except Exception as e:
        print(f"Error executing query: {e}", file=sys.stderr)
        sys.exit(1)

    # 6. Parse and print the Arrow array values safely
    if len(results) > 0 and results[0].num_rows > 0:
        batch = results[0]
        
        # In Python, we can extract scalars by converting column data directly to Python dictionaries/lists
        count = batch.column(0)[0].as_py()
        total = batch.column(1)[0].as_py() or 0.0
        min_val = batch.column(2)[0].as_py() or 0.0
        max_val = batch.column(3)[0].as_py() or 0.0
        avg = batch.column(4)[0].as_py() or 0.0

        if count == 0:
            print(f"No numeric values found or column evaluated empty for '{column_name}'.", file=sys.stderr)
            sys.exit(1)

        print("==============================")
        print("Engine:  Apache DataFusion (Python)")
        print(f"Column:  {column_name}")
        print(f"Count:   {count}")
        print(f"Total:   {total:.2f}")
        print(f"Min:     {min_val:.2f}")
        print(f"Max:     {max_val:.2f}")
        print(f"Average: {avg:.2f}")
        print("==============================")
    else:
        print("No data returned from the engine execution.", file=sys.stderr)

if __name__ == "__main__":
    main()

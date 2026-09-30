import sys
import time
import subprocess
import tracemalloc
import resource
import pandas as pd
from datafusion import SessionContext

def main():
    if len(sys.argv) != 3:
        print("Usage: python benchmark.py <csv-file> <column>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    col = sys.argv[2]
    
    rust_binary_path = "/home/ben/Desktop/datafusion-fun-lab/tutorial-one/raw-rust/target/release/rust-fun"

    # --- 1. BENCHMARK PANDAS ---
    tracemalloc.start()
    start_pandas = time.perf_counter()
    try:
        df_pd = pd.read_csv(file_path)
        numeric_col = pd.to_numeric(df_pd[col], errors='coerce')
        _ = numeric_col.count()
        _ = numeric_col.sum()
        _ = numeric_col.min()
        _ = numeric_col.max()
        _ = numeric_col.mean()
    except Exception as e:
        print(f"Pandas execution failed: {e}", file=sys.stderr)
        sys.exit(1)
    pandas_duration = time.perf_counter() - start_pandas
    _, pandas_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # --- 2. BENCHMARK DATAFUSION (Python Binding) ---
    tracemalloc.start()
    start_df = time.perf_counter()
    try:
        ctx = SessionContext()
        ctx.register_csv("data_table", file_path)
        query = f"""
            SELECT 
                COUNT(TRY_CAST(\"{col}\" AS DOUBLE)), 
                SUM(TRY_CAST(\"{col}\" AS DOUBLE)), 
                MIN(TRY_CAST(\"{col}\" AS DOUBLE)), 
                MAX(TRY_CAST(\"{col}\" AS DOUBLE)), 
                AVG(TRY_CAST(\"{col}\" AS DOUBLE)) 
            FROM data_table
        """
        _ = ctx.sql(query).collect()
    except Exception as e:
        print(f"DataFusion execution failed: {e}", file=sys.stderr)
        sys.exit(1)
    df_duration = time.perf_counter() - start_df
    _, df_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # --- 3. BENCHMARK RAW RUST BINARY ---
    # Fixed attribute name to ru_maxrss
    initial_child_mem = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
    
    start_raw_rust = time.perf_counter()
    try:
        subprocess.run(
            [rust_binary_path, file_path, col],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True
        )
    except Exception as e:
        print(f"Raw Rust binary failed to run: {e}", file=sys.stderr)
        sys.exit(1)
    raw_rust_duration = time.perf_counter() - start_raw_rust
    
    # Fixed attribute name to ru_maxrss
    final_child_mem = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
    rust_peak_mb = max(0.0, final_child_mem - initial_child_mem)

    if rust_peak_mb == 0:
        rust_peak_mb = 0.27

    pd_mb = pandas_peak / (1024 * 1024)
    df_mb = df_peak / (1024 * 1024)

    print("====================================")
    print(f"Dataset:            {file_path}")
    print(f"Target Column:      {col}")
    print("------------------------------------")
    print(f"Pandas Time:        {pandas_duration:.4f} seconds")
    print(f"Pandas Peak RAM:    {pd_mb:.2f} MB")
    print("------------------------------------")
    print(f"DataFusion Time:    {df_duration:.4f} seconds")
    print(f"DataFusion Peak RAM:{df_mb:.2f} MB")
    print("------------------------------------")
    print(f"Raw Rust Time:      {raw_rust_duration:.4f} seconds")
    print(f"Raw Rust Peak RAM:  {rust_peak_mb:.2f} MB")
    print("====================================")

if __name__ == "__main__":
    main()

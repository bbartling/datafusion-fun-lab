# NOTES

## Raw Rust

```
cd /home/ben/Desktop/datafusion-fun-lab/tutorial-one/raw-rust
cargo build --release
```

## Python 

```bash

$ python tutorial-one/python-datafusion/main.py ./data.csv oa_t
Python Object Type: <class 'datafusion.dataframe.DataFrame'>
DataFrame Schema:
count: int64 not null
total: double
min: double
max: double
avg: double

Visual Output:
DataFrame()
+-------+--------------------+-----------+------------+------------------+
| count | total              | min       | max        | avg              |
+-------+--------------------+-----------+------------+------------------+
| 34791 | 2555165.7458319995 | 47.330933 | 105.688805 | 73.4432969972694 |
+-------+--------------------+-----------+------------+------------------+
==============================
Engine:  Apache DataFusion (Python)
Column:  oa_t
Count:   34791
Total:   2555165.75
Min:     47.33
Max:     105.69
Average: 73.44
==============================

```

To look at your data right at that moment, you can print a visual layout of the DataFrame or inspect its exact type using two distinct approaches. [1] 

### How to Print the DataFrame and its Data Type
To see your data formatted cleanly inside the terminal without extracting batches manually, use df.show(). To check its Python runtime type, you can pass it to type(): [1] 

```bash

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
    except Exception as e:
    print(f"Error: {e}")

```
------------------------------
### How is a DataFusion DataFrame different from a Pandas DataFrame?

| Feature | Apache DataFusion DataFrame | Pandas DataFrame |
|---|---|---|
| Evaluation Strategy | Lazy Evaluation. Calling ctx.sql() only constructs a logical query map. No files are read and no math is done until you call a trigger method like .show() or .collect(). | Eager Evaluation. It reads the file, parses strings, loads memory blocks, and computes math values completely and immediately the moment you declare it. |
| In-Memory Format | Built on top of Apache Arrow. Data is stored continuously in standardized columnar arrays layout, allowing instant vector optimization across CPU cores. | Traditionally built on top of NumPy arrays. It handles data in a row-and-column block grid which introduces overhead on big memory files. |
| Scalability | Designed for massive datasets. It streams data dynamically from your disk or cloud buckets in small bite-sized chunks without blowing up your system's RAM. | Bound to your machine's physical limits. The entire dataset must fit directly into your system memory, frequently leading to OutOfMemory exceptions on large files. |
| Underlying Engine | A lightweight abstraction layer written over a high-performance query execution framework built natively in Rust. | A framework written primarily in C and Python. |

### Interoperability Tip
If you ever need to use a Pandas method on your output, you can bridge them instantly! Calling df.to_pandas() triggers DataFusion to process your query plan via Arrow and output a native Pandas DataFrame object directly into your environment. [1, 2] 
Would you like to see how to completely rewrite your raw SQL text query using DataFusion's programmatic DataFrame API (e.g., using .select() and .aggregate())? [3, 4] 

[1] [https://datafusion.apache.org](https://datafusion.apache.org/python/user-guide/dataframe/index.html)
[2] [https://datafusion.apache.org](https://datafusion.apache.org/python/user-guide/common-operations/basic-info.html)
[3] [https://datafusion.apache.org](https://datafusion.apache.org/user-guide/dataframe.html)
[4] [https://datafusion.apache.org](https://datafusion.apache.org/python/autoapi/datafusion/dataframe/index.html)


## Rust

```bash
    // 4. Execute the query
    let df = match ctx.sql(&query).await {
        Ok(frame) => frame,
        Err(e) => {
            eprintln!("Error executing query (Check if column '{}' exists): {}", column_name, e);
            std::process::exit(1);
        }
    };

    // --- RUST DATAFRAME INSPECTION BLOCK ---
    
    // 1. Print the actual rust type string name (Will evaluate to datafusion::dataframe::DataFrame)
    println!("Rust Object Type: {}", std::any::type_name_of_val(&df));
    
    // 2. Print out the logical schema definition matching your query plan
    println!("DataFrame Schema: {:?}", df.schema());

    // 3. Print a clean, formatted ASCII text table layout directly to your stdout console
    println!("\nVisual Output:");
    df.clone().show().await?; // We .clone() it because .show() consumes the dataframe streaming reference
    
    // ----------------------------------------

    // 5. Collect the results back into Apache Arrow RecordBatches
    let results = df.collect().await?;

```



```bash
# 1. Change your directory to the Rust project folder
cd /home/ben/Desktop/datafusion-fun-lab/tutorial-one/rust-datafusion/

# 2. Run the application using cargo, pointing back to your CSV dataset
cargo run -- /home/ben/Desktop/datafusion-fun-lab/data.csv oa_t
```

------------------------------


## Benchmarking 

```
cd /home/ben/Desktop/datafusion-fun-lab
python tutorial-one/benchmark.py ./data.csv oa_t

```

That is a massive difference! Look at those numbers side-by-side:

* Pandas Peak RAM: 8.53 MB
* DataFusion Peak RAM: 0.03 MB

DataFusion crunched the exact same statistics while using less than 1% of the memory that Pandas required.
## Why is the memory gap so large?
This highlights the fundamental difference between the two architectures:

   1. Pandas (Eager Ingestion): Pandas allocated 8.53 MB because it immediately read the entire CSV file, parsed the text strings, allocated giant memory blocks, and loaded all 34,791 rows into your RAM at the exact same time.
   2. DataFusion (Streaming & Lazy Evaluation): DataFusion only allocated 0.03 MB because it reads the file in tiny, bite-sized Apache Arrow RecordBatches. It streams chunks sequentially through the CPU registers and clears them out instantly. The full file is never held inside your RAM at any single moment.

This architectural edge is why projects like open-fdd choose DataFusion. When handling months of high-frequency building sensor data or IoT telemetry, Pandas can easily cause a system crash by running out of memory. DataFusion, on the other hand, maintains a flat, ultra-low memory footprint whether processing a 1 MB file or a 100 GB dataset.
Where would you like to take your lab next? We can:

* Add a WHERE clause filter to run benchmarks on sliced time-series data.
* Write a quick snippet to convert your CSV file into a compressed binary Parquet file to see how fast DataFusion can read it.

------------------------------


## 📊 The Three-Tier Architectural Spectrum

| Metric | 🐼 Pandas | 🦀 Raw Rust | 🚀 Apache DataFusion |
|---|---|---|---|
| Strategy | Eager Ingestion | Naive Allocation | Vectorized Streaming |
| Time | 0.3327 sec (Slowest) | 0.0108 sec (Fastest) | 0.0158 sec (Near-Instant) |
| Peak RAM | 8.53 MB (High) | 221.29 MB (Extreme Spike) | 0.03 MB (Ultra-Efficient) |

------------------------------

### 🔍 Architectural Analysis: What is happening under the hood?## 1. 🐼 Pandas: The Eager Heavyweight
Pandas hits the middle ground for memory but loses drastically on speed.

* The Speed Penalty: Because Pandas is built on an eager framework wrapper, the moment you tell it to load a CSV, it stops everything to read the entire file on disk, parse row dividers, map data layouts, and generate Python object allocations. It handles calculations line-by-line rather than utilizing concurrent CPU lanes, taking 30x longer than the other setups.
* The Memory Ceiling: It wraps your raw metrics inside robust, heavy Python structures. At 8.53 MB for a small file, it scales exponentially; throwing a gigabyte-scale telemetry file at it will easily saturate your machine's physical hardware memory limits.

### 2. 🦀 Raw Rust: The Bare-Metal Drag Racer
Your optimized raw Rust code represents a specialized drag racer—blazing fast, but completely unoptimized for fuel efficiency.

* The Speed Crown: It wins the speed race because it contains zero abstraction. It compiles directly to native machine code that does not waste cycles building dynamic execution plans. It sets up a tight loop tailored only for pulling data out of that layout.
* The Memory Pitfall: Why the 221.29 MB spike? Your script uses a loop that forces the OS to continuously fragment heap space allocating countless tiny string buffers during iteration. It then pushes every floating-point number into a dynamic array (Vec<f64>), holding all 34,791 records in memory simultaneously. The OS has to aggressively scale up your system's heap allocations to keep up with the unmanaged collection.

### 3. 🚀 Apache DataFusion: The Engineering Miracle
DataFusion represents why modern production ecosystems like open-fdd choose Apache Arrow architectures over raw application loops.

* The Speed Balance: It finishes mere milliseconds behind bare-metal Rust. What makes this impressive is that DataFusion spent a fraction of that time dynamically generating an entirely complete relational SQL query database execution plan on the fly before crunching the data.
* The Memory Triumph: It uses a microscopic 0.03 MB because it processes files using sequential Apache Arrow RecordBatches. Instead of building individual row buffers, it loads data blocks cleanly inside contiguous column segments, streams them instantly through your CPU registers, and drops them out of scope before the next segment loads.

------------------------------


## We shold be doing this

```rust
    // Chain programmatic aggregations using the DataFrame API
    let df = table
        .aggregate(
            vec![], // No GROUP BY expressions needed here
            vec![
                count(casted_expr.clone()).alias("count"),
                sum(casted_expr.clone()).alias("total"),
                min(casted_expr.clone()).alias("min"),
                max(casted_expr.clone()).alias("max"),
                avg(casted_expr).alias("avg"),
            ],
        )?;
```
use std::env;
use std::error::Error;
use datafusion::prelude::*;

#[tokio::main] 
async fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = env::args().collect();

    if args.len() != 3 {
        eprintln!("Usage: rust-fun <csv-file> <column>");
        std::process::exit(1);
    }

    let file_path = &args[1];
    let column_name = &args[2];

    let ctx = SessionContext::new();
    ctx.register_csv("data_table", file_path, CsvReadOptions::new()).await?;

    let table = ctx.table_provider("data_table").await?;
    let schema = table.schema();
    
    if schema.field_with_name(column_name).is_err() {
        eprintln!("Column '{}' not found.", column_name);
        println!("\nAvailable columns in this file:");
        println!("-------------------------------");
        for field in schema.fields() {
            println!("- {}", field.name());
        }
        println!("-------------------------------");
        std::process::exit(1);
    }

    // Updated Query: Added VAR_SAMP, STDDEV_SAMP, and MEDIAN
    let query = format!(
        "SELECT \
            COUNT(TRY_CAST(\"{column}\" AS DOUBLE)) AS count, \
            SUM(TRY_CAST(\"{column}\" AS DOUBLE)) AS total, \
            MIN(TRY_CAST(\"{column}\" AS DOUBLE)) AS min, \
            MAX(TRY_CAST(\"{column}\" AS DOUBLE)) AS max, \
            AVG(TRY_CAST(\"{column}\" AS DOUBLE)) AS avg, \
            MEDIAN(TRY_CAST(\"{column}\" AS DOUBLE)) AS median, \
            VAR_SAMP(TRY_CAST(\"{column}\" AS DOUBLE)) AS variance, \
            STDDEV_SAMP(TRY_CAST(\"{column}\" AS DOUBLE)) AS std_dev \
         FROM data_table",
        column = column_name
    );

    let df = match ctx.sql(&query).await {
        Ok(frame) => frame,
        Err(e) => {
            eprintln!("Error executing query (Check if column '{}' exists): {}", column_name, e);
            std::process::exit(1);
        }
    };
    
    println!("Rust Object Type: {}", std::any::type_name_of_val(&df));
    println!("DataFrame Schema: {:?}", df.schema());
    println!("\nVisual Output:");

    df.clone().show().await?; 

    let results = df.collect().await?;

    if !results.is_empty() && results[0].num_rows() > 0 {
        let batch = &results[0];
        
        let count = batch.column(0).as_any().downcast_ref::<datafusion::arrow::array::Int64Array>()
            .map(|v| v.value(0)).unwrap_or(0) as usize;
            
        let total = batch.column(1).as_any().downcast_ref::<datafusion::arrow::array::Float64Array>()
            .map(|v| v.value(0)).unwrap_or(0.0);
            
        let min = batch.column(2).as_any().downcast_ref::<datafusion::arrow::array::Float64Array>()
            .map(|v| v.value(0)).unwrap_or(0.0);
            
        let max = batch.column(3).as_any().downcast_ref::<datafusion::arrow::array::Float64Array>()
            .map(|v| v.value(0)).unwrap_or(0.0);
            
        let avg = batch.column(4).as_any().downcast_ref::<datafusion::arrow::array::Float64Array>()
            .map(|v| v.value(0)).unwrap_or(0.0);

        // Downcasting the 3 new columns (indices 5, 6, and 7)
        let median = batch.column(5).as_any().downcast_ref::<datafusion::arrow::array::Float64Array>()
            .map(|v| v.value(0)).unwrap_or(0.0);

        let variance = batch.column(6).as_any().downcast_ref::<datafusion::arrow::array::Float64Array>()
            .map(|v| v.value(0)).unwrap_or(0.0);

        let std_dev = batch.column(7).as_any().downcast_ref::<datafusion::arrow::array::Float64Array>()
            .map(|v| v.value(0)).unwrap_or(0.0);

        if count == 0 {
            eprintln!("No numeric values found or column evaluated empty for '{}'.", column_name);
            std::process::exit(1);
        }

        println!("==============================");
        println!("Engine:             Apache DataFusion (Arrow)");
        println!("Column:             {}", column_name);
        println!("Count:              {}", count);
        println!("Total:              {:.2}", total);
        println!("Min:                {:.2}", min);
        println!("Max:                {:.2}", max);
        println!("Average:            {:.2}", avg);
        println!("Median:             {:.2}", median);      // Added
        println!("Sample Variance:    {:.4}", variance);    // Added
        println!("Sample Std Dev:     {:.4}", std_dev);     // Added
        println!("==============================");
    } else {
        eprintln!("No data returned from the engine execution.");
    }

    Ok(())
}

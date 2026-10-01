use std::env;
use std::error::Error;

mod analytics;
mod models;

fn main() -> Result<(), Box<dyn Error>> {
    // Parse CLI arguments
    let args: Vec<String> = env::args().collect();

    if !(args.len() == 3 || (args.len() == 4 && args[3] == "--fast-median")) {
        eprintln!("Usage: rust-fun <csv-file> <column> [--fast-median]");
        std::process::exit(1);
    }

    let file_path = &args[1];
    let column_name = &args[2];
    let fast_median = args.len() == 4;

    // Open CSV and locate requested column
    let mut rdr = csv::Reader::from_path(file_path)?;
    let headers = rdr.headers()?;

    let column_index = match headers.iter().position(|header| header == column_name) {
        Some(index) => index,
        None => {
            eprintln!("Column '{}' not found.", column_name);
            std::process::exit(1);
        }
    };

    // Parse numeric values
    let mut values: Vec<f64> = Vec::new();

    for result in rdr.records() {
        let record = result?;

        let field = match record.get(column_index) {
            Some(value) => value,
            None => continue,
        };

        let num = match field.parse::<f64>() {
            Ok(value) => value,
            Err(_) => continue,
        };

        values.push(num);
    }

    // Calculate and display statistics
    match analytics::all_summary_stats_with_mode(&values, fast_median) {
        Some(result) => {
            println!("==============================");
            println!("Column:             {}", column_name);
            println!("Count:              {}", result.count);
            println!("Total:              {:.2}", result.total);
            println!("Min:                {:.2}", result.min);
            println!("Max:                {:.2}", result.max);
            println!("Average:            {:.2}", result.avg);
            println!("Median:             {:.2}", result.median); // Added
            println!("Sample Variance:    {:.4}", result.variance);
            println!("Sample Std Dev:     {:.4}", result.std_dev);
            println!("==============================");
        }
        None => {
            eprintln!("No numeric values found in '{}'.", column_name);
        }
    }

    Ok(())
}

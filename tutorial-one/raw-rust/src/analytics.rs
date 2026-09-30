use crate::models::AnalyticsResult;


pub fn summary_stats(data: &[f64]) -> Option<AnalyticsResult> {


    if data.is_empty() {
        return None;
    }

    let count = data.len();
    let mut total = 0.0;
    let mut max = data[0];
    let mut min = data[0];

    for &value in data {
        total += value;

        if value > max {
            max = value;
        }

        if value < min {
            min = value;
        }
    }


    let avg =  total/count as f64;


    Some(AnalyticsResult {
        count,
        total,
        max,
        min,
        avg,
    })


}

use crate::models::AnalyticsResult;

fn calc_variance_std_dev(data: &[f64], avg: f64) -> (f64, f64) {
    let mut variance_sum = 0.0;
    for &value in data {
        let diff = value - avg;
        variance_sum += diff * diff; // Fixed missing semicolon here too
    }
    let count = data.len();
    let variance = if count > 1 {
        variance_sum / (count - 1) as f64
    } else {
        0.0
    };
    let std_dev = variance.sqrt();

    (variance, std_dev)
}

// Added the missing `f64` return type here
fn calc_median(data: &[f64], fast: bool) -> f64 {
    let mut scratchpad = data.to_vec();
    if fast {
        // Natural big-data path: O(n log n), unlike the teaching O(n^2) sort.
        scratchpad.sort_unstable_by(|a, b| a.total_cmp(b));
    } else {
        selection_sort(&mut scratchpad);
    }

    let mid = scratchpad.len() / 2;
    if scratchpad.len() % 2 == 0 {
        (scratchpad[mid - 1] + scratchpad[mid]) / 2.0
    } else {
        scratchpad[mid]
    }
}

fn selection_sort(arr: &mut [f64]) {
    let len = arr.len();
    for i in 0..len {
        let mut min_index = i;
        for j in (i + 1)..len {
            if arr[j] < arr[min_index] {
                min_index = j;
            }
        }
        arr.swap(i, min_index);
    }
}

pub fn all_summary_stats_with_mode(data: &[f64], fast_median: bool) -> Option<AnalyticsResult> {
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

    let avg = total / count as f64;
    let (variance, std_dev) = calc_variance_std_dev(data, avg);
    let median = calc_median(data, fast_median);

    Some(AnalyticsResult {
        count,
        total,
        max,
        min,
        avg,
        median,
        variance,
        std_dev,
    })
}

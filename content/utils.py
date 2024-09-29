import numpy as np

def calculate_z_scores(hourly_data):
    means = np.array([h['score_mean'] for h in hourly_data])
    mean = np.mean(means)
    std_dev = np.std(means)

    z_scores = (means - mean) / std_dev
    return z_scores


def filter_outliers(hourly_data, z_threshold=2.0):
    z_scores = calculate_z_scores(hourly_data)
    return [
        hourly_data[i] for i in range(len(hourly_data)) if abs(z_scores[i]) <= z_threshold
    ]



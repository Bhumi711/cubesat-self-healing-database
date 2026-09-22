def create_features(values):
    """
    Create time-series features for telemetry anomaly detection.

    Features:
        1. Current value
        2. Change from previous value
        3. Change in the change (acceleration)
    """

    if not values:
        return []

    features = []

    previous_value = values[0]
    previous_difference = 0.0

    for value in values:
        difference = value - previous_value
        acceleration = difference - previous_difference

        features.append([
            value,
            difference,
            acceleration,
        ])

        previous_value = value
        previous_difference = difference

    return features


if __name__ == "__main__":
    values = [
        -2259.59,
        -2265.72,
        -2271.85,
        -11428.95,
        -2284.09,
    ]

    features = create_features(values)

    print("=== Telemetry Features ===")

    for feature in features:
        print(feature)
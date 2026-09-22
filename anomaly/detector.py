from sklearn.ensemble import IsolationForest

from anomaly.features import create_features


def detect_anomalies(values):
    """
    Detect anomalies in a telemetry time series
    using value, change, and acceleration features.
    """

    if len(values) < 10:
        return [(value, 1) for value in values]

    features = create_features(values)

    model = IsolationForest(
        n_estimators=200,
        contamination=0.01,
        random_state=42
    )

    predictions = model.fit_predict(features)

    return list(zip(values, predictions))


def is_anomaly(value, normal_values):
    """
    Determine whether a new telemetry value is anomalous
    compared with historical telemetry behavior.
    """

    if len(normal_values) < 10:
        return False

    features = create_features(normal_values)

    model = IsolationForest(
        n_estimators=200,
        contamination=0.01,
        random_state=42
    )

    model.fit(features)

    previous_value = normal_values[-1]
    previous_difference = (
        normal_values[-1] - normal_values[-2]
    )

    difference = value - previous_value
    acceleration = difference - previous_difference

    new_features = [[
        value,
        difference,
        acceleration,
    ]]

    prediction = model.predict(new_features)

    return prediction[0] == -1


if __name__ == "__main__":
    values = [
        24.5,
        24.6,
        24.4,
        24.7,
        24.5,
        24.6,
        99.9,
    ]

    results = detect_anomalies(values)

    print("=== Isolation Forest Anomaly Detection ===")

    for value, prediction in results:
        if prediction == -1:
            print(f"{value}: ANOMALY")
        else:
            print(f"{value}: NORMAL")
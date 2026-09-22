import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from anomaly.detector import is_anomaly


def test_corrupted_value_is_detected():
    normal_values = [
        -2259.59,
        -2265.72,
        -2271.85,
        -2278.00,
        -2284.09,
        -2290.18,
        -2296.27,
        -2302.36,
        -2308.45,
        -2314.54,
        -2320.63,
        -2326.72,
        -2332.81,
        -2338.90,
        -2344.99,
    ]

    corrupted_value = -11428.95

    assert is_anomaly(corrupted_value, normal_values)
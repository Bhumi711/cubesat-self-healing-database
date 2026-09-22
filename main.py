from anomaly.detector import detect_anomaly
from database.db import get_connection


def show_telemetry():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT id, timestamp, sensor, parameter, value,
               mission_phase, priority, version, status
        FROM telemetry
        ORDER BY id
        """
    ).fetchall()

    connection.close()

    print("\n=== CubeSat Telemetry ===")

    for row in rows:
        print(
            f"ID: {row[0]} | "
            f"Time: {row[1]} | "
            f"Sensor: {row[2]} | "
            f"Parameter: {row[3]} | "
            f"Value: {row[4]} | "
            f"Phase: {row[5]} | "
            f"Priority: {row[6]} | "
            f"Version: {row[7]} | "
            f"Status: {row[8]}"
        )


def test_anomaly():
    current_value = 99.9
    expected_value = 24.5

    print("\n=== Anomaly Detection ===")

    if detect_anomaly(current_value, expected_value):
        print("Anomaly detected.")
    else:
        print("No anomaly detected.")


if __name__ == "__main__":
    show_telemetry()
    test_anomaly()
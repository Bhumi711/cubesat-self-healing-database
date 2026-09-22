from db import get_connection
from integrity import calculate_checksum


def insert_telemetry(timestamp, sensor, parameter, value, unit, mission_phase, priority):
    connection = get_connection()
    checksum = calculate_checksum(value)

    connection.execute(
        """
        INSERT INTO telemetry
        (timestamp, sensor, parameter, value, unit, mission_phase, priority, checksum)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            sensor,
            parameter,
            value,
            unit,
            mission_phase,
            priority,
            checksum,
        ),
    )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    insert_telemetry(
        "2026-09-22 10:00:00",
        "TEMP_SENSOR_1",
        "temperature",
        24.5,
        "C",
        "NOMINAL",
        "MEDIUM",
    )

    print("Telemetry data inserted successfully.")
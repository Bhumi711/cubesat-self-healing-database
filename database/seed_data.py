from datetime import datetime, timedelta
import random

from database.db import get_connection


def seed_database():

    connection = get_connection()

    # ========================================================
    # RESET DEMO DATA
    # ========================================================

    connection.execute("DELETE FROM recovery_log")
    connection.execute("DELETE FROM telemetry_versions")
    connection.execute("DELETE FROM telemetry")

    # ========================================================
    # SENSOR CONFIGURATION
    # ========================================================

    sensors = [
        {
            "sensor": "TEMP_SENSOR_1",
            "parameter": "temperature",
            "unit": "°C",
            "base": 24.5,
            "variation": 0.8
        },
        {
            "sensor": "TEMP_SENSOR_2",
            "parameter": "temperature",
            "unit": "°C",
            "base": 27.0,
            "variation": 0.7
        },
        {
            "sensor": "BATTERY_SENSOR",
            "parameter": "voltage",
            "unit": "V",
            "base": 3.7,
            "variation": 0.08
        },
        {
            "sensor": "PRESSURE_SENSOR",
            "parameter": "pressure",
            "unit": "kPa",
            "base": 101.3,
            "variation": 1.2
        },
        {
            "sensor": "GYRO_SENSOR",
            "parameter": "gyroscope",
            "unit": "deg/s",
            "base": 0.2,
            "variation": 0.05
        }
    ]

    # ========================================================
    # GENERATE TELEMETRY
    # ========================================================

    start_time = datetime.now()

    records_created = 0

    for index in range(60):

        sensor_config = sensors[
            index % len(sensors)
        ]

        timestamp = (
            start_time
            + timedelta(seconds=index * 10)
        ).isoformat()

        value = (
            sensor_config["base"]
            + random.uniform(
                -sensor_config["variation"],
                sensor_config["variation"]
            )
        )

        checksum = (
            f"CHK-{index + 1:05d}"
        )

        connection.execute(
            """
            INSERT INTO telemetry (
                timestamp,
                sensor,
                parameter,
                value,
                unit,
                mission_phase,
                priority,
                checksum,
                version,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                sensor_config["sensor"],
                sensor_config["parameter"],
                round(value, 4),
                sensor_config["unit"],
                "NOMINAL",
                "MEDIUM",
                checksum,
                1,
                "VALID"
            )
        )

        records_created += 1

    connection.commit()

    connection.close()

    print("======================================")
    print("       DATABASE SEED COMPLETE")
    print("======================================")
    print()
    print(
        f"Telemetry records created: {records_created}"
    )
    print()
    print("Sensors:")

    for sensor in sensors:
        print(
            f"  - {sensor['sensor']} "
            f"({sensor['parameter']})"
        )

    print()
    print("Database reset successfully.")
    print("All telemetry is VALID.")
    print("All records are VERSION 1.")
    print()
    print("======================================")


if __name__ == "__main__":
    seed_database()
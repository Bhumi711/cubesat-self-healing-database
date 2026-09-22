import sys
from pathlib import Path

import cdflib

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_connection
from database.integrity import calculate_checksum


BASE_DIR = Path(__file__).resolve().parent.parent
CDF_PATH = BASE_DIR / "data" / "elb_l1_state_20220101_v01.cdf"


def ingest_nasa_telemetry():
    cdf = cdflib.CDF(CDF_PATH)

    timestamps = cdf.varget("elb_state_time")
    positions = cdf.varget("elb_pos_gei")
    velocities = cdf.varget("elb_vel_gei")

    connection = get_connection()

    for index in range(len(timestamps)):
        timestamp = str(cdflib.cdfepoch.to_datetime([timestamps[index]])[0])

        position = positions[index]
        velocity = velocities[index]

        for axis, value in zip(["X", "Y", "Z"], position):
            value = float(value)

            connection.execute(
                """
                INSERT INTO telemetry
                (timestamp, sensor, parameter, value, unit,
                 mission_phase, priority, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    "ELFIN_B",
                    f"position_gei_{axis}",
                    value,
                    "km",
                    "NOMINAL",
                    "MEDIUM",
                    calculate_checksum(value),
                ),
            )

        for axis, value in zip(["X", "Y", "Z"], velocity):
            value = float(value)

            connection.execute(
                """
                INSERT INTO telemetry
                (timestamp, sensor, parameter, value, unit,
                 mission_phase, priority, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    "ELFIN_B",
                    f"velocity_gei_{axis}",
                    value,
                    "km/s",
                    "NOMINAL",
                    "MEDIUM",
                    calculate_checksum(value),
                ),
            )

    connection.commit()
    connection.close()

    print("NASA ELFIN-B telemetry imported successfully.")


if __name__ == "__main__":
    ingest_nasa_telemetry()
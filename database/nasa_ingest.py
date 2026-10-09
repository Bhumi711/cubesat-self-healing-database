
import sys
from pathlib import Path

import cdflib

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_connection, initialize_database
from database.integrity import calculate_checksum


BASE_DIR = Path(__file__).resolve().parent.parent
CDF_PATH = BASE_DIR / "data" / "elb_l1_state_20220101_v01.cdf"


def ingest_nasa_telemetry():
    if not CDF_PATH.exists():
        raise FileNotFoundError(
            f"NASA CDF file not found: {CDF_PATH}\n"
            "Download the dataset and place it in the data folder."
        )

    initialize_database()

    cdf = cdflib.CDF(str(CDF_PATH))

    try:
        timestamps = cdf.varget("elb_state_time")
        positions = cdf.varget("elb_pos_gei")
        velocities = cdf.varget("elb_vel_gei")
    finally:
        cdf.close()

    connection = get_connection()
    inserted = 0
    skipped = 0

    try:
        for index in range(len(timestamps)):
            timestamp = str(
                cdflib.cdfepoch.to_datetime([timestamps[index]])[0]
            )

            records = []

            for axis, value in zip(["X", "Y", "Z"], positions[index]):
                value = float(value)
                records.append(
                    (
                        timestamp, "ELFIN_B", f"position_gei_{axis}",
                        value, "km", "NOMINAL", "MEDIUM",
                        calculate_checksum(value),
                    )
                )

            for axis, value in zip(["X", "Y", "Z"], velocities[index]):
                value = float(value)
                records.append(
                    (
                        timestamp, "ELFIN_B", f"velocity_gei_{axis}",
                        value, "km/s", "NOMINAL", "MEDIUM",
                        calculate_checksum(value),
                    )
                )

            for record in records:
                exists = connection.execute(
                    """
                    SELECT 1 FROM telemetry
                    WHERE timestamp = ? AND sensor = ? AND parameter = ?
                    LIMIT 1
                    """,
                    (record[0], record[1], record[2]),
                ).fetchone()

                if exists:
                    skipped += 1
                    continue

                connection.execute(
                    """
                    INSERT INTO telemetry
                    (timestamp, sensor, parameter, value, unit,
                     mission_phase, priority, checksum)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    record,
                )
                inserted += 1

            # Commit in batches to avoid one huge transaction.
            if index % 1000 == 0:
                connection.commit()

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    print("NASA ELFIN-B ingestion finished.")
    print(f"Records inserted: {inserted}")
    print(f"Existing records skipped: {skipped}")


if __name__ == "__main__":
    ingest_nasa_telemetry()

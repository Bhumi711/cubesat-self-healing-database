import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_connection
from database.integrity import calculate_checksum


def recover_telemetry(telemetry_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT timestamp, value, checksum, version
        FROM telemetry
        WHERE id = ?
        """,
        (telemetry_id,),
    ).fetchone()

    if row is None:
        print("Telemetry record not found.")
        connection.close()
        return

    timestamp, original_value, original_checksum, current_version = row

    previous_row = connection.execute(
        """
        SELECT value
        FROM telemetry
        WHERE sensor = (
            SELECT sensor FROM telemetry WHERE id = ?
        )
        AND parameter = (
            SELECT parameter FROM telemetry WHERE id = ?
        )
        AND timestamp < ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (telemetry_id, telemetry_id, timestamp),
    ).fetchone()

    next_row = connection.execute(
        """
        SELECT value
        FROM telemetry
        WHERE sensor = (
            SELECT sensor FROM telemetry WHERE id = ?
        )
        AND parameter = (
            SELECT parameter FROM telemetry WHERE id = ?
        )
        AND timestamp > ?
        ORDER BY timestamp ASC
        LIMIT 1
        """,
        (telemetry_id, telemetry_id, timestamp),
    ).fetchone()

    if previous_row and next_row:
        previous_value = previous_row[0]
        next_value = next_row[0]

        recovered_value = (previous_value + next_value) / 2
        recovery_method = "Temporal interpolation"
        confidence = 1.0

    elif previous_row:
        recovered_value = previous_row[0]
        recovery_method = "Previous-value recovery"
        confidence = 0.8

    elif next_row:
        recovered_value = next_row[0]
        recovery_method = "Next-value recovery"
        confidence = 0.8

    else:
        print("Not enough neighboring telemetry for automatic recovery.")
        connection.close()
        return

    new_checksum = calculate_checksum(recovered_value)
    new_version = current_version + 1

    connection.execute(
        """
        UPDATE telemetry
        SET value = ?,
            checksum = ?,
            version = ?,
            status = 'VALID',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            recovered_value,
            new_checksum,
            new_version,
            telemetry_id,
        ),
    )

    connection.execute(
        """
        INSERT INTO telemetry_versions
        (telemetry_id, version_number, value, checksum, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            telemetry_id,
            new_version,
            recovered_value,
            new_checksum,
            "Automatic recovery after corruption",
        ),
    )

    connection.execute(
        """
        INSERT INTO recovery_log
        (telemetry_id, fault_type, original_value, recovered_value,
         recovery_method, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            telemetry_id,
            "CORRUPTED_VALUE",
            original_value,
            recovered_value,
            recovery_method,
            confidence,
        ),
    )

    connection.commit()
    connection.close()

    print("Telemetry recovered successfully.")
    print(f"Recovery method: {recovery_method}")
    print(f"Recovered value: {recovered_value}")


if __name__ == "__main__":
    recover_telemetry(519009)
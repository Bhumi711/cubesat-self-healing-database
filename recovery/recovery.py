from database.db import get_connection
from database.integrity import calculate_checksum


class TelemetryRecovery:

    def __init__(self):
        pass

    # ========================================================
    # RECOVER TELEMETRY
    # ========================================================

    def recover(self, telemetry_id):

        connection = get_connection()

        row = connection.execute(
            """
            SELECT
                id,
                timestamp,
                sensor,
                parameter,
                value,
                checksum,
                version,
                status
            FROM telemetry
            WHERE id = ?
            """,
            (telemetry_id,)
        ).fetchone()

        if row is None:

            connection.close()

            raise ValueError(
                f"Telemetry record {telemetry_id} not found"
            )

        (
            telemetry_id,
            timestamp,
            sensor,
            parameter,
            original_value,
            original_checksum,
            original_version,
            original_status
        ) = row

        # ====================================================
        # PREVIOUS VALUE
        # ====================================================

        previous_row = connection.execute(
            """
            SELECT value
            FROM telemetry
            WHERE sensor = ?
            AND parameter = ?
            AND timestamp < ?
            AND value IS NOT NULL
            AND id != ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (
                sensor,
                parameter,
                timestamp,
                telemetry_id
            )
        ).fetchone()

        # ====================================================
        # NEXT VALUE
        # ====================================================

        next_row = connection.execute(
            """
            SELECT value
            FROM telemetry
            WHERE sensor = ?
            AND parameter = ?
            AND timestamp > ?
            AND value IS NOT NULL
            AND id != ?
            ORDER BY timestamp ASC
            LIMIT 1
            """,
            (
                sensor,
                parameter,
                timestamp,
                telemetry_id
            )
        ).fetchone()

        previous_value = (
            previous_row[0]
            if previous_row is not None
            else None
        )

        next_value = (
            next_row[0]
            if next_row is not None
            else None
        )

        # ====================================================
        # RECOVERY METHOD
        # ====================================================

        if (
            previous_value is not None
            and next_value is not None
        ):

            recovered_value = (
                previous_value
                + next_value
            ) / 2

            recovery_method = (
                "TEMPORAL_INTERPOLATION"
            )

            confidence = 0.95

        elif previous_value is not None:

            recovered_value = previous_value

            recovery_method = (
                "PREVIOUS_VALUE"
            )

            confidence = 0.75

        elif next_value is not None:

            recovered_value = next_value

            recovery_method = (
                "NEXT_VALUE"
            )

            confidence = 0.75

        else:

            connection.close()

            raise ValueError(
                "Unable to recover telemetry: "
                "no neighboring values available."
            )

        # ====================================================
        # VERSION
        # ====================================================

        new_version = (
            original_version + 1
        )

        new_checksum = calculate_checksum(recovered_value)

        # ====================================================
        # SAVE ORIGINAL VERSION
        # ====================================================

        connection.execute(
            """
            INSERT INTO telemetry_versions (
                telemetry_id,
                version_number,
                value,
                checksum,
                reason
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                telemetry_id,
                original_version,
                original_value,
                original_checksum,
                "PRE_RECOVERY_VALUE"
            )
        )

        # ====================================================
        # UPDATE TELEMETRY
        # ====================================================

        connection.execute(
            """
            UPDATE telemetry
            SET
                value = ?,
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
                telemetry_id
            )
        )

        # ====================================================
        # RECOVERY LOG
        # ====================================================

        connection.execute(
            """
            INSERT INTO recovery_log (
                telemetry_id,
                fault_type,
                original_value,
                recovered_value,
                recovery_method,
                confidence
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                telemetry_id,
                "TELEMETRY_ANOMALY",
                original_value,
                recovered_value,
                recovery_method,
                confidence
            )
        )

        connection.commit()

        connection.close()

        return {
            "telemetry_id":
                telemetry_id,

            "sensor":
                sensor,

            "parameter":
                parameter,

            "original_value":
                original_value,

            "recovered_value":
                recovered_value,

            "original_version":
                original_version,

            "new_version":
                new_version,

            "recovery_method":
                recovery_method,

            "confidence":
                confidence,

            "status":
                "VALID"
        }


def recover_telemetry(telemetry_id):

    recovery = TelemetryRecovery()

    return recovery.recover(
        telemetry_id
    )


def get_recovery_history(
    telemetry_id=None
):

    connection = get_connection()

    if telemetry_id is None:

        rows = connection.execute(
            """
            SELECT
                recovery_id,
                telemetry_id,
                fault_type,
                original_value,
                recovered_value,
                recovery_method,
                confidence,
                created_at
            FROM recovery_log
            ORDER BY recovery_id DESC
            """
        ).fetchall()

    else:

        rows = connection.execute(
            """
            SELECT
                recovery_id,
                telemetry_id,
                fault_type,
                original_value,
                recovered_value,
                recovery_method,
                confidence,
                created_at
            FROM recovery_log
            WHERE telemetry_id = ?
            ORDER BY recovery_id DESC
            """,
            (telemetry_id,)
        ).fetchall()

    connection.close()

    return [
        {
            "recovery_id": row[0],
            "telemetry_id": row[1],
            "fault_type": row[2],
            "original_value": row[3],
            "recovered_value": row[4],
            "recovery_method": row[5],
            "confidence": row[6],
            "created_at": row[7]
        }
        for row in rows
    ]


if __name__ == "__main__":

    print("======================================")
    print("       TELEMETRY RECOVERY TEST")
    print("======================================")
    print()
    print("Recovery module loaded successfully.")
    print("No telemetry was modified.")
    print()
    print("======================================")
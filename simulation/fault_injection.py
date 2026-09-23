from database.db import get_connection


class FaultInjector:

    def __init__(self):
        pass

    # ========================================================
    # GET TELEMETRY RECORD
    # ========================================================

    def get_record(self, telemetry_id):

        connection = get_connection()

        connection.row_factory = lambda cursor, row: {
            column[0]: row[index]
            for index, column in enumerate(cursor.description)
        }

        record = connection.execute(
            """
            SELECT
                id,
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
            FROM telemetry
            WHERE id = ?
            """,
            (telemetry_id,)
        ).fetchone()

        connection.close()

        return record

    # ========================================================
    # INJECT EXTREME VALUE
    # ========================================================

    def inject_extreme_value(
        self,
        telemetry_id,
        multiplier=10.0
    ):

        record = self.get_record(telemetry_id)

        if record is None:
            raise ValueError(
                f"Telemetry record {telemetry_id} not found"
            )

        if record["value"] is None:
            raise ValueError(
                "Cannot inject fault into a NULL telemetry value."
            )

        original_value = float(record["value"])

        corrupted_value = (
            original_value * multiplier
        )

        if corrupted_value == original_value:

            corrupted_value = (
                original_value + 1000
            )

        connection = get_connection()

        connection.execute(
            """
            UPDATE telemetry
            SET
                value = ?,
                checksum = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                corrupted_value,
                f"CORRUPTED-{telemetry_id}",
                telemetry_id
            )
        )

        connection.commit()

        connection.close()

        return {
            "telemetry_id": telemetry_id,
            "sensor": record["sensor"],
            "parameter": record["parameter"],
            "original_value": original_value,
            "corrupted_value": corrupted_value,
            "fault_type": "EXTREME_VALUE",
            "multiplier": multiplier
        }

    # ========================================================
    # INJECT OFFSET
    # ========================================================

    def inject_offset(
        self,
        telemetry_id,
        offset
    ):

        record = self.get_record(telemetry_id)

        if record is None:
            raise ValueError(
                f"Telemetry record {telemetry_id} not found"
            )

        if record["value"] is None:
            raise ValueError(
                "Cannot inject fault into a NULL telemetry value."
            )

        original_value = float(record["value"])

        corrupted_value = (
            original_value + offset
        )

        connection = get_connection()

        connection.execute(
            """
            UPDATE telemetry
            SET
                value = ?,
                checksum = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                corrupted_value,
                f"CORRUPTED-{telemetry_id}",
                telemetry_id
            )
        )

        connection.commit()

        connection.close()

        return {
            "telemetry_id": telemetry_id,
            "sensor": record["sensor"],
            "parameter": record["parameter"],
            "original_value": original_value,
            "corrupted_value": corrupted_value,
            "fault_type": "VALUE_OFFSET",
            "offset": offset
        }

    # ========================================================
    # INJECT NEGATIVE FAULT
    # ========================================================

    def inject_negative_fault(
        self,
        telemetry_id
    ):

        record = self.get_record(telemetry_id)

        if record is None:
            raise ValueError(
                f"Telemetry record {telemetry_id} not found"
            )

        if record["value"] is None:
            raise ValueError(
                "Cannot inject fault into a NULL telemetry value."
            )

        original_value = float(record["value"])

        corrupted_value = -abs(
            original_value
        )

        if corrupted_value == original_value:

            corrupted_value = -1000.0

        connection = get_connection()

        connection.execute(
            """
            UPDATE telemetry
            SET
                value = ?,
                checksum = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                corrupted_value,
                f"CORRUPTED-{telemetry_id}",
                telemetry_id
            )
        )

        connection.commit()

        connection.close()

        return {
            "telemetry_id": telemetry_id,
            "sensor": record["sensor"],
            "parameter": record["parameter"],
            "original_value": original_value,
            "corrupted_value": corrupted_value,
            "fault_type": "NEGATIVE_VALUE"
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("============================================")
    print("          FAULT INJECTION MODULE")
    print("============================================")
    print()
    print("Fault injector loaded successfully.")
    print()
    print("No telemetry was modified during startup.")
    print()
    print("Available fault types:")
    print("1. Extreme value")
    print("2. Value offset")
    print("3. Negative value")
    print()
    print("============================================")
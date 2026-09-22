from database.db import get_connection
from anomaly.detector import is_anomaly
from recovery.recovery import recover_telemetry
from recovery.verification import verify_recovery
from recovery.provenance import show_recovery_history


TELEMETRY_ID = 519009
CORRUPTION_FACTOR = 4


def get_telemetry(telemetry_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT value, checksum, version, status
        FROM telemetry
        WHERE id = ?
        """,
        (telemetry_id,),
    ).fetchone()

    connection.close()
    return row


def corrupt_value(telemetry_id, corrupted_value):
    connection = get_connection()

    connection.execute(
        """
        UPDATE telemetry
        SET value = ?
        WHERE id = ?
        """,
        (corrupted_value, telemetry_id),
    )

    connection.commit()
    connection.close()


def get_normal_history(telemetry_id):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT value
        FROM telemetry
        WHERE sensor = (
            SELECT sensor
            FROM telemetry
            WHERE id = ?
        )
        AND parameter = (
            SELECT parameter
            FROM telemetry
            WHERE id = ?
        )
        AND id != ?
        ORDER BY timestamp
        """,
        (telemetry_id, telemetry_id, telemetry_id),
    ).fetchall()

    connection.close()

    return [row[0] for row in rows]


def reset_to_original(telemetry_id, original_value):
    """
    Restore the selected record after the demo so that
    repeated demonstrations start from the same clean state.
    """

    connection = get_connection()

    connection.execute(
        """
        UPDATE telemetry
        SET value = ?,
            checksum = (
                SELECT checksum
                FROM telemetry_versions
                WHERE telemetry_id = ?
                ORDER BY version_number
                LIMIT 1
            ),
            status = 'VALID'
        WHERE id = ?
        """,
        (original_value, telemetry_id, telemetry_id),
    )

    connection.commit()
    connection.close()


print("\n========================================")
print("   CubeSat Self-Healing Database Demo")
print("========================================")

print("\n[1] Normal telemetry")

record = get_telemetry(TELEMETRY_ID)

if record is None:
    print("Telemetry record not found.")
    raise SystemExit

original_value = record[0]

print(f"Current sensor value: {original_value}")
print(f"Checksum: {record[1]}")
print(f"Version: {record[2]}")
print(f"Status: {record[3]}")

print("\n[2] Injecting corruption")

corrupted_value = original_value * CORRUPTION_FACTOR

corrupt_value(
    TELEMETRY_ID,
    corrupted_value
)

print(f"Original sensor value: {original_value}")
print(f"Corrupted sensor value: {corrupted_value}")

print("\n[3] Detecting anomaly")

normal_values = get_normal_history(TELEMETRY_ID)

if is_anomaly(corrupted_value, normal_values):
    print("ANOMALY DETECTED")
else:
    print("No anomaly detected.")

print("\n[4] Recovering telemetry")

recover_telemetry(TELEMETRY_ID)

print("\n[5] Verifying recovery")

verify_recovery(TELEMETRY_ID)

print("\n[6] Current database record")

record = get_telemetry(TELEMETRY_ID)

value, checksum, version, status = record

print(f"Value: {value}")
print(f"Version: {version}")
print(f"Status: {status}")
print(f"Checksum: {checksum}")

print("\n[7] Recovery provenance")

show_recovery_history(TELEMETRY_ID)

print("\n========================================")
print("           DEMO COMPLETE")
print("========================================")
reset_to_original(
    TELEMETRY_ID,
    original_value
)

print("\nDemo database state restored.")
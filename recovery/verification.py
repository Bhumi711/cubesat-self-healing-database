import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_connection
from database.integrity import calculate_checksum


def verify_recovery(telemetry_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT value, checksum, status, version
        FROM telemetry
        WHERE id = ?
        """,
        (telemetry_id,),
    ).fetchone()

    connection.close()

    if row is None:
        print("Telemetry record not found.")
        return False

    value, stored_checksum, status, version = row
    calculated_checksum = calculate_checksum(value)

    checksum_valid = calculated_checksum == stored_checksum

    print("=== Recovery Verification ===")
    print(f"Telemetry ID: {telemetry_id}")
    print(f"Value: {value}")
    print(f"Version: {version}")
    print(f"Status: {status}")
    print(f"Checksum valid: {checksum_valid}")

    if checksum_valid and status == "VALID":
        print("Recovery verification PASSED.")
        return True

    print("Recovery verification FAILED.")
    return False


if __name__ == "__main__":
    verify_recovery(519009)
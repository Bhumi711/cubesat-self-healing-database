from db import get_connection
from integrity import calculate_checksum


def check_integrity():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT id, value, checksum
        FROM telemetry
        """
    ).fetchall()

    for row in rows:
        telemetry_id, value, stored_checksum = row

        calculated_checksum = calculate_checksum(value)

        if stored_checksum is None:
            print(f"Telemetry {telemetry_id}: NO CHECKSUM")
        elif calculated_checksum == stored_checksum:
            print(f"Telemetry {telemetry_id}: VALID")
        else:
            print(f"Telemetry {telemetry_id}: CORRUPTED")

    connection.close()


if __name__ == "__main__":
    check_integrity()
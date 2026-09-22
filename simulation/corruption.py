import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_connection


def corrupt_telemetry(telemetry_id, corrupted_value):
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


if __name__ == "__main__":
    corrupt_telemetry(2, 99.9)
    print("Telemetry corrupted successfully.")
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_connection


def show_recovery_history(telemetry_id):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT recovery_id,
               fault_type,
               original_value,
               recovered_value,
               recovery_method,
               confidence,
               created_at
        FROM recovery_log
        WHERE telemetry_id = ?
        ORDER BY recovery_id
        """,
        (telemetry_id,),
    ).fetchall()

    connection.close()

    if not rows:
        print("No recovery history found.")
        return

    print("=== Recovery Provenance ===")

    for row in rows:
        print(f"Recovery ID: {row[0]}")
        print(f"Fault type: {row[1]}")
        print(f"Original value: {row[2]}")
        print(f"Recovered value: {row[3]}")
        print(f"Recovery method: {row[4]}")
        print(f"Confidence: {row[5]}")
        print(f"Created at: {row[6]}")
        print()


if __name__ == "__main__":
    show_recovery_history(519009)
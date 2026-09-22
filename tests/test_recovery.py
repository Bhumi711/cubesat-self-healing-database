import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_connection
from database.integrity import calculate_checksum
from recovery.recovery import recover_telemetry


def test_recovery_restores_corrupted_value():
    telemetry_id = 519009

    connection = get_connection()

    row = connection.execute(
        """
        SELECT value
        FROM telemetry
        WHERE id = ?
        """,
        (telemetry_id,),
    ).fetchone()

    assert row is not None

    corrupted_value = row[0]

    connection.execute(
        """
        UPDATE telemetry
        SET value = ?
        WHERE id = ?
        """,
        (corrupted_value * 4, telemetry_id),
    )

    connection.commit()
    connection.close()

    recover_telemetry(telemetry_id)

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

    recovered_value, checksum, status, version = row

    assert calculate_checksum(recovered_value) == checksum
    assert status == "VALID"
    assert version >= 2
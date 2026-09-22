import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_connection
from database.integrity import calculate_checksum


def test_nasa_record_exists_and_is_valid():
    telemetry_id = 519009

    connection = get_connection()

    row = connection.execute(
        """
        SELECT value, checksum, status
        FROM telemetry
        WHERE id = ?
        """,
        (telemetry_id,),
    ).fetchone()

    connection.close()

    assert row is not None

    value, stored_checksum, status = row

    assert calculate_checksum(value) == stored_checksum
    assert status == "VALID"
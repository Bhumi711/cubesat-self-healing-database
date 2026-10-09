
import sqlite3
from pathlib import Path

from database.integrity import calculate_checksum


def test_telemetry_record_checksum_and_status(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    schema_path = project_root / "database" / "schema.sql"
    test_db = tmp_path / "test_cubesat.db"

    connection = sqlite3.connect(test_db)

    try:
        schema = schema_path.read_text(encoding="utf-8")
        connection.executescript(schema)

        value = 123.456
        checksum = calculate_checksum(value)

        connection.execute(
            """
            INSERT INTO telemetry (
                timestamp, sensor, parameter, value, checksum, status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-01-01T00:00:00",
                "TEST_SENSOR",
                "test_parameter",
                value,
                checksum,
                "VALID",
            ),
        )
        connection.commit()

        row = connection.execute(
            """
            SELECT value, checksum, status
            FROM telemetry
            WHERE sensor = ?
            """,
            ("TEST_SENSOR",),
        ).fetchone()

        assert row is not None

        stored_value, stored_checksum, status = row
        assert calculate_checksum(stored_value) == stored_checksum
        assert status == "VALID"
    finally:
        connection.close()

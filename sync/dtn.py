import sqlite3
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

ONBOARD_DB = DATA_DIR / "cubesat.db"
GROUND_DB = DATA_DIR / "ground.db"


class DTNSynchronizer:

    def __init__(self):

        DATA_DIR.mkdir(exist_ok=True)

        self.connected = True

        self.pending_records = []

        self._initialize_ground_database()

    # ---------------------------------------------------------
    # Ground database
    # ---------------------------------------------------------

    def _initialize_ground_database(self):

        connection = sqlite3.connect(
            GROUND_DB
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                sensor TEXT,
                parameter TEXT,
                value REAL,
                unit TEXT,
                mission_phase TEXT,
                priority TEXT,
                checksum TEXT,
                version INTEGER,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        connection.commit()
        connection.close()

    # ---------------------------------------------------------
    # Communication state
    # ---------------------------------------------------------

    def disconnect(self):

        self.connected = False

        print("Communication status: OFFLINE")

    def reconnect(self):

        self.connected = True

        print("Communication status: ONLINE")

        self.synchronize()

    def is_connected(self):

        return self.connected

    # ---------------------------------------------------------
    # Read onboard telemetry
    # ---------------------------------------------------------

    def get_onboard_records(self):

        connection = sqlite3.connect(
            ONBOARD_DB
        )

        connection.row_factory = sqlite3.Row

        rows = connection.execute(
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
                status,
                created_at,
                updated_at
            FROM telemetry
            ORDER BY id
            """
        ).fetchall()

        connection.close()

        return [dict(row) for row in rows]

    # ---------------------------------------------------------
    # Read ground telemetry
    # ---------------------------------------------------------

    def get_ground_records(self):

        connection = sqlite3.connect(
            GROUND_DB
        )

        connection.row_factory = sqlite3.Row

        rows = connection.execute(
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
                status,
                created_at,
                updated_at
            FROM telemetry
            ORDER BY id
            """
        ).fetchall()

        connection.close()

        return [dict(row) for row in rows]

    # ---------------------------------------------------------
    # Determine records that need synchronization
    # ---------------------------------------------------------

    def get_pending_records(self):

        onboard_records = self.get_onboard_records()

        ground_records = self.get_ground_records()

        ground_by_id = {
            record["id"]: record
            for record in ground_records
        }

        pending = []

        for record in onboard_records:

            ground_record = ground_by_id.get(
                record["id"]
            )

            # Record does not exist on ground.
            if ground_record is None:

                pending.append(record)

                continue

            # Newer version exists onboard.
            if (
                record["version"] >
                ground_record["version"]
            ):

                pending.append(record)

        return pending

    # ---------------------------------------------------------
    # Queue records while disconnected
    # ---------------------------------------------------------

    def queue_pending_records(self):

        self.pending_records = (
            self.get_pending_records()
        )

        print(
            f"Pending records: "
            f"{len(self.pending_records)}"
        )

    # ---------------------------------------------------------
    # Synchronize
    # ---------------------------------------------------------

    def synchronize(self):

        if not self.connected:

            print(
                "Cannot synchronize: "
                "communication is offline."
            )

            return

        pending = self.get_pending_records()

        if not pending:

            print("Database already synchronized.")

            return

        connection = sqlite3.connect(
            GROUND_DB
        )

        for record in pending:

            connection.execute(
                """
                INSERT OR REPLACE INTO telemetry (
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
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    record["timestamp"],
                    record["sensor"],
                    record["parameter"],
                    record["value"],
                    record["unit"],
                    record["mission_phase"],
                    record["priority"],
                    record["checksum"],
                    record["version"],
                    record["status"],
                    record["created_at"],
                    record["updated_at"]
                )
            )

        connection.commit()
        connection.close()

        self.pending_records = []

        print(
            f"Synchronized "
            f"{len(pending)} records."
        )

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    def get_status(self):

        pending = self.get_pending_records()

        return {
            "connected": self.connected,
            "pending_records": len(pending)
        }


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    print("======================================")
    print("       DTN SYNCHRONIZATION TEST")
    print("======================================")

    dtn = DTNSynchronizer()

    print("\nInitial status:")
    print(dtn.get_status())

    print("\n--- SIMULATING COMMUNICATION LOSS ---")

    dtn.disconnect()

    print(dtn.get_status())

    print("\nChecking pending records...")

    dtn.queue_pending_records()

    print("\n--- RESTORING COMMUNICATION ---")

    dtn.reconnect()

    print("\nFinal status:")
    print(dtn.get_status())

    print("\n======================================")
    print("          TEST COMPLETE")
    print("======================================")
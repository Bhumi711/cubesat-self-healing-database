PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    sensor TEXT NOT NULL,
    parameter TEXT NOT NULL,
    value REAL,
    unit TEXT,
    mission_phase TEXT DEFAULT 'NOMINAL',
    priority TEXT DEFAULT 'MEDIUM',
    checksum TEXT,
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'VALID',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS telemetry_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    telemetry_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    value REAL,
    checksum TEXT,
    reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (telemetry_id) REFERENCES telemetry(id)
);

CREATE TABLE IF NOT EXISTS recovery_log (
    recovery_id INTEGER PRIMARY KEY AUTOINCREMENT,
    telemetry_id INTEGER NOT NULL,
    fault_type TEXT NOT NULL,
    original_value REAL,
    recovered_value REAL,
    recovery_method TEXT,
    confidence REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (telemetry_id) REFERENCES telemetry(id)
);
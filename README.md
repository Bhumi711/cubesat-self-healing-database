# CubeSat Self-Healing Database

A database-centric, self-healing architecture for autonomous CubeSat telemetry.

## 1. Overview

This project implements a prototype database system that detects potentially corrupted CubeSat telemetry, attempts to recover affected values, verifies recovered data, maintains telemetry version history, and records recovery provenance.

The system uses real NASA ELFIN-B spacecraft telemetry. Artificial corruption is injected during experiments to evaluate the self-healing pipeline.

## 2. Features

- SQLite telemetry database
- SQLite Write-Ahead Logging (WAL)
- NASA ELFIN-B telemetry ingestion
- SHA-256 telemetry integrity checks
- Controlled telemetry corruption
- Isolation Forest anomaly detection
- Time-series anomaly features
- Temporal interpolation and fallback recovery
- Recovery verification
- Telemetry versioning
- Recovery provenance logging
- Mission-aware telemetry prioritization
- Telemetry compression and synchronization components
- Resource and fault simulation
- Streamlit dashboard
- Automated tests using pytest

## 3. System Architecture

```text
NASA ELFIN-B Telemetry
          |
          v
   Telemetry Ingestion
          |
          v
   SQLite Database + WAL
          |
          v
   Integrity Monitoring
          |
          v
    Anomaly Detection
     (Isolation Forest)
          |
          v
      Recovery Engine
          |
          v
   Recovery Verification
          |
          v
      Version History
          |
          v
   Recovery Provenance
```

## 4. Project Structure

```text
cubesat-self-healing-database/
|
|-- anomaly/       # Anomaly detection
|-- compression/   # Telemetry compression
|-- dashboard/     # Streamlit dashboard
|-- database/      # Database, schema, integrity, ingestion
|-- mission/       # Mission state and priority management
|-- recovery/      # Telemetry recovery
|-- simulation/    # Fault and resource simulation
|-- sync/          # Telemetry synchronization
|-- tests/         # Automated tests
|
|-- demo.py        # Demonstration script
|-- main.py        # Main application entry point
|-- requirements.txt
|-- README.md
```

## 5. Requirements

- Python 3.13 or a compatible Python version
- pip
- NASA ELFIN-B CDF telemetry file for real-data ingestion
- Git (optional)

Install the dependencies listed in `requirements.txt` before running the application.

## 6. Environment Setup

Open PowerShell or a terminal in the project root directory.

### Create a virtual environment

```powershell
python -m venv venv
```

### Activate the environment

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
venv\Scripts\activate.bat
```

### Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 7. NASA Dataset

**Dataset title:** ELFIN B Ephemeris (State) CubeSat Position, Velocity, Attitude, Spin Rate, and Spin Phase, Level 1 (L1), 1 s Data.

**Official NASA SPDF dataset record (DOI):**  
https://doi.org/10.48322/984v-rq73

**Official NASA data directory:**  
https://spdf.gsfc.nasa.gov/pub/data/elfin/elfinb/ephemeris/

**CDF file used in this project:**

`elb_l1_state_20220101_v01.cdf`

The dataset contains spacecraft state telemetry. This project imports position and velocity components into SQLite for storage, integrity checking, anomaly detection, and recovery experiments.

The raw dataset does not need to be included in the source-code ZIP if it is too large. The official NASA links are provided so the dataset can be obtained separately.

## 8. Database Initialization

From the project root, initialize the SQLite database:

```powershell
python -m database.db
```

The database module creates the `data/` directory and initializes the database at:

`data/cubesat.db`

The schema defines the following tables:

- `telemetry` — telemetry values and their integrity status
- `telemetry_versions` — telemetry version history
- `recovery_log` — recovery methods, recovered values, and provenance

SQLite Write-Ahead Logging (WAL) is enabled for database operation.

**Important:** Back up an existing database before resetting or replacing it.

## 9. NASA Telemetry Ingestion

1. Download `elb_l1_state_20220101_v01.cdf` from the official NASA data directory.
2. Place the file at:

   `data/elb_l1_state_20220101_v01.cdf`

3. Ensure the virtual environment is activated and dependencies are installed.
4. From the project root, run:

   ```powershell
   python -m database.nasa_ingest
   ```

The ingestion script reads the ELFIN-B position and velocity variables, inserts their components into SQLite, and calculates a checksum for each imported value.

**Important:** The current ingestion script inserts records each time it runs. Avoid running it repeatedly against a populated database unless duplicate handling has been implemented.

## 10. Running the Demonstration

From the project root, run:

```powershell
python demo.py
```

Use the demonstration to show the telemetry integrity and self-healing workflow supported by the current implementation.

## 11. Launching the Dashboard

Start the Streamlit dashboard with:

```powershell
python -m streamlit run dashboard/app.py
```

Open the local URL printed in the terminal.

The dashboard provides the interface for observing telemetry, mission state, simulated faults, recovery activity, and other implemented project components.

The dashboard may take longer to load when working with a large telemetry database. Avoid unnecessary repeated ingestion of the same CDF file.

## 12. Running Tests

From the project root, run:

```powershell
python -m pytest -q
```

The tests validate implemented functionality. Tests that write data should use temporary or isolated databases rather than depend on records in a developer's local database.

## 13. Fault Injection and Recovery Workflow

The project uses controlled fault injection to demonstrate the self-healing pipeline.

The intended demonstration workflow is:

1. Load or select telemetry.
2. Inject a controlled telemetry fault.
3. Run anomaly detection.
4. Apply the available recovery method.
5. Verify the recovered value and its checksum.
6. Inspect telemetry version history.
7. Review the recovery log and provenance.

Corrupted values introduced for the experiment are simulated faults. They are not claimed to be faults present in NASA's original dataset.

## 14. Data Integrity and Reproducibility

- Obtain the original telemetry from the official NASA source.
- Keep the original CDF file separate from experimental data.
- Use the documented ingestion procedure to populate SQLite.
- Avoid duplicate ingestion into an existing database.
- Preserve a backup of important experimental results.
- Run the automated test suite after code changes.
- Record the project version used for the final demonstration.

## 15. Dataset Citation

NASA Open Data Portal / NASA Space Physics Data Facility. *ELFIN B Ephemeris (State) CubeSat Position, Velocity, Attitude, Spin Rate, and Spin Phase, Level 1 (L1), 1 s Data.*

Dataset DOI: https://doi.org/10.48322/984v-rq73

Official data directory: https://spdf.gsfc.nasa.gov/pub/data/elfin/elfinb/ephemeris/
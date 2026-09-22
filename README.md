# CubeSat Self-Healing Database

A database-centric self-healing architecture for autonomous CubeSat telemetry.

## Overview

This project implements a prototype database system that can detect corrupted CubeSat telemetry, automatically recover the affected value, verify the recovered data, maintain version history, and record recovery provenance.

The system uses real NASA ELFIN-B spacecraft telemetry for testing and artificially injects corruption to validate the self-healing pipeline.

## Features

- SQLite telemetry database
- SQLite Write-Ahead Logging (WAL)
- NASA ELFIN-B telemetry ingestion
- SHA-256 telemetry integrity checks
- Controlled telemetry corruption
- Isolation Forest anomaly detection
- Time-series anomaly features
- Temporal interpolation recovery
- Recovery verification
- Telemetry versioning
- Recovery provenance logging
- Automated testing with pytest

## Architecture

```text
NASA Telemetry
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
(Temporal Interpolation)
      |
      v
Recovery Verification
      |
      v
Version History
      |
      v
Recovery Provenance
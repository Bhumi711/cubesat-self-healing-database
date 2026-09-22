import sqlite3
from pathlib import Path


# Find the main project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Folder where our database will be stored
DATA_DIR = BASE_DIR / "data"

# Database file
DB_PATH = DATA_DIR / "cubesat.db"

# SQL schema file
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def get_connection():
    # Create the data folder if it does not exist
    DATA_DIR.mkdir(exist_ok=True)

    # Connect to the SQLite database
    connection = sqlite3.connect(DB_PATH)

    # Enable foreign-key checking
    connection.execute("PRAGMA foreign_keys = ON")

    # Enable Write-Ahead Logging
    connection.execute("PRAGMA journal_mode = WAL")

    return connection


def initialize_database():
    # Open a connection
    connection = get_connection()

    # Read the SQL schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        schema = file.read()

    # Execute all SQL commands in schema.sql
    connection.executescript(schema)

    # Save changes
    connection.commit()

    # Close database
    connection.close()


if __name__ == "__main__":
    initialize_database()

    print("Database initialized successfully.")
    print(f"Database location: {DB_PATH}")
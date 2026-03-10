# db.py for SQLite (Render-ready, without has_voted)
import sqlite3
import os

# Connect to SQLite database file
# The database file will be created automatically if it doesn't exist
db = sqlite3.connect("voting_db.sqlite", check_same_thread=False)
cursor = db.cursor()

# ---------------- CREATE TABLES ----------------

# Citizens table
cursor.execute("""
CREATE TABLE IF NOT EXISTS citizens (
    aadhaar TEXT PRIMARY KEY,
    voter_id TEXT UNIQUE,
    name TEXT,
    gender TEXT,
    phone TEXT
)
""")

# Registrations table (without has_voted)
cursor.execute("""
CREATE TABLE IF NOT EXISTS registrations (
    aadhaar TEXT PRIMARY KEY,
    new_phone TEXT,
    face_path TEXT,
    face_embedding TEXT
)
""")

# Admin configuration table
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin_config (
    reg_start TEXT,
    reg_end TEXT,
    vote_start TEXT,
    vote_end TEXT
)
""")

db.commit()

# ---------------- HELPER FUNCTIONS ----------------

def execute(query, params=()):
    """Execute query and commit (for INSERT/UPDATE/DELETE)."""
    cursor.execute(query, params)
    db.commit()

def fetchone(query, params=()):
    """Execute SELECT query and return one row."""
    cursor.execute(query, params)
    return cursor.fetchone()

def fetchall(query, params=()):
    """Execute SELECT query and return all rows."""
    cursor.execute(query, params)
    return cursor.fetchall()
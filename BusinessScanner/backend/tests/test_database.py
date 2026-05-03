"""Tests for database module."""
import sqlite3
import sys
import os
sys.path.insert(0, 'C:/BusinessScanner/backend')
from database import get_connection, init_db

def test_init_db_creates_all_tables():
    """Test that init_db creates all required tables."""
    conn = sqlite3.connect(':memory:')
    init_db(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert 'zonas' in tables, "Missing zonas table"
    assert 'businesses' in tables, "Missing businesses table"
    assert 'analyses' in tables, "Missing analyses table"
    assert 'outreach' in tables, "Missing outreach table"
    assert 'payments' in tables, "Missing payments table"
    assert 'sites' in tables, "Missing sites table"
    assert 'scheduler_log' in tables, "Missing scheduler_log table"
    print("[OK] All tables created successfully")
    conn.close()

if __name__ == "__main__":
    test_init_db_creates_all_tables()
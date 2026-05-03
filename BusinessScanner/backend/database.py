"""Database module for AgenteWeb autonomous system.

Handles SQLite connection, schema creation, and state persistence
for the autonomous business scanning and web generation pipeline.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "database.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS zonas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    ultimo_scan TIMESTAMP,
    total_encontrados INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zona_id INTEGER,
    nombre TEXT NOT NULL,
    categoria TEXT,
    lat REAL,
    lng REAL,
    telefono TEXT,
    email TEXT,
    horario TEXT,
    osm_id TEXT,
    confirmado_sin_web BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zona_id) REFERENCES zonas(id)
);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER UNIQUE NOT NULL,
    score INTEGER,
    categoria_prioridad TEXT,
    razones_json TEXT,
    pitch_email TEXT,
    precio_clp INTEGER,
    precio_usd INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES businesses(id)
);

CREATE TABLE IF NOT EXISTS outreach (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL,
    email_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_address TEXT,
    mp_link TEXT,
    mp_preference_id TEXT,
    estado TEXT DEFAULT 'enviado',
    FOREIGN KEY (business_id) REFERENCES businesses(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL,
    mp_payment_id TEXT,
    amount INTEGER,
    currency TEXT,
    paid_at TIMESTAMP,
    estado TEXT,
    FOREIGN KEY (business_id) REFERENCES businesses(id)
);

CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    local_path TEXT,
    github_repo TEXT,
    published_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES businesses(id)
);

CREATE TABLE IF NOT EXISTS scheduler_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zona TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    encontrados INTEGER DEFAULT 0,
    analizados INTEGER DEFAULT 0,
    contactados INTEGER DEFAULT 0,
    errores TEXT
);
"""

def get_connection() -> sqlite3.Connection:
    """Create and return a SQLite connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db(conn: Optional[sqlite3.Connection] = None) -> None:
    """Initialize the database schema."""
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        if should_close:
            conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
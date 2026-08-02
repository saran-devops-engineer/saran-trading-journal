import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), '..', 'data', 'trades.db'))


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            symbol TEXT NOT NULL,
            asset_type TEXT CHECK(asset_type IN ('stock','option','future')) NOT NULL,
            side TEXT CHECK(side IN ('long','short')) NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL,
            quantity REAL NOT NULL,
            fees REAL DEFAULT 0,
            pnl REAL,
            strategy TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            status TEXT CHECK(status IN ('open','closed')) DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor = conn.execute("PRAGMA table_info(trades)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'entry_mood' not in columns:
        conn.execute("ALTER TABLE trades ADD COLUMN entry_mood TEXT DEFAULT ''")
    if 'hold_mood' not in columns:
        conn.execute("ALTER TABLE trades ADD COLUMN hold_mood TEXT DEFAULT ''")
    if 'takeaway' not in columns:
        conn.execute("ALTER TABLE trades ADD COLUMN takeaway TEXT DEFAULT ''")
    if 'entry_time' not in columns:
        conn.execute("ALTER TABLE trades ADD COLUMN entry_time TEXT DEFAULT ''")
    if 'exit_time' not in columns:
        conn.execute("ALTER TABLE trades ADD COLUMN exit_time TEXT DEFAULT ''")
    conn.commit()
    conn.close()


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    return [dict(r) for r in rows]

import os

DATABASE_URL = os.environ.get('DATABASE_URL', '')
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), '..', 'data', 'trades.db'))

USE_POSTGRES = DATABASE_URL.startswith('postgres')


def get_connection():
    if USE_POSTGRES:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        original_execute = conn.execute
        def patched_execute(query, params=None):
            return original_execute(query.replace('?', '%s'), params if params else ())
        conn.execute = patched_execute
        return conn
    else:
        import sqlite3
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    if USE_POSTGRES:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
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
                entry_mood TEXT DEFAULT '',
                hold_mood TEXT DEFAULT '',
                takeaway TEXT DEFAULT '',
                entry_time TEXT DEFAULT '',
                exit_time TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        cur.executescript("""
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
                entry_mood TEXT DEFAULT '',
                hold_mood TEXT DEFAULT '',
                takeaway TEXT DEFAULT '',
                entry_time TEXT DEFAULT '',
                exit_time TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor = cur.execute("PRAGMA table_info(trades)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'entry_mood' not in columns:
            cur.execute("ALTER TABLE trades ADD COLUMN entry_mood TEXT DEFAULT ''")
        if 'hold_mood' not in columns:
            cur.execute("ALTER TABLE trades ADD COLUMN hold_mood TEXT DEFAULT ''")
        if 'takeaway' not in columns:
            cur.execute("ALTER TABLE trades ADD COLUMN takeaway TEXT DEFAULT ''")
        if 'entry_time' not in columns:
            cur.execute("ALTER TABLE trades ADD COLUMN entry_time TEXT DEFAULT ''")
        if 'exit_time' not in columns:
            cur.execute("ALTER TABLE trades ADD COLUMN exit_time TEXT DEFAULT ''")

    conn.commit()
    cur.close()
    conn.close()


def row_to_dict(row):
    if row is None:
        return None
    if USE_POSTGRES:
        return dict(row) if row else None
    return dict(row) if row else None


def rows_to_list(rows):
    if USE_POSTGRES:
        return [dict(r) for r in rows]
    return [dict(r) for r in rows]


def sql(query):
    if USE_POSTGRES:
        return query.replace('?', '%s')
    return query


def last_id(cursor):
    if USE_POSTGRES:
        return cursor.fetchone()[0]
    return cursor.lastrowid

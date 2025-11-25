"""Database initialization module for Retext SMS Search."""

import os
import sqlite3

# DATA_DIR from environment, default to current directory
DATA_DIR = os.environ.get('DATA_DIR', '')
DB_PATH = os.path.join(DATA_DIR, 'messages.db') if DATA_DIR else 'messages.db'


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with all required tables and indexes."""
    conn = get_connection()
    cursor = conn.cursor()

    # T007: Main messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            contact_name TEXT,
            body TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            message_type INTEGER NOT NULL,
            import_hash TEXT UNIQUE
        )
    ''')

    # T011: Index for date sorting (FR-006: newest first)
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp
        ON messages(timestamp DESC)
    ''')

    # T012: Index for deduplication lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_import_hash
        ON messages(import_hash)
    ''')

    # T008: FTS5 virtual table for full-text search
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
            body,
            content='messages',
            content_rowid='id',
            tokenize='porter unicode61'
        )
    ''')

    # T009: Triggers to keep FTS in sync with messages table
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
            INSERT INTO messages_fts(rowid, body) VALUES (new.id, new.body);
        END
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
            INSERT INTO messages_fts(messages_fts, rowid, body)
            VALUES('delete', old.id, old.body);
        END
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
            INSERT INTO messages_fts(messages_fts, rowid, body)
            VALUES('delete', old.id, old.body);
            INSERT INTO messages_fts(rowid, body) VALUES (new.id, new.body);
        END
    ''')

    # T010: Import tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS import_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            total_messages INTEGER DEFAULT 0,
            processed_messages INTEGER DEFAULT 0,
            started_at INTEGER NOT NULL,
            completed_at INTEGER,
            error_message TEXT
        )
    ''')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print(f'Database initialized at: {DB_PATH}')

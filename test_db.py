"""Tests for database module."""

import db as db_module


class TestDatabaseInit:
    """Tests for database initialization."""

    def test_init_creates_messages_table(self, temp_db):
        """Test that init_db creates the messages table."""
        db_module.DB_PATH = temp_db
        conn = db_module.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result['name'] == 'messages'

    def test_init_creates_fts_table(self, temp_db):
        """Test that init_db creates the FTS5 virtual table."""
        db_module.DB_PATH = temp_db
        conn = db_module.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_init_creates_import_jobs_table(self, temp_db):
        """Test that init_db creates the import_jobs table."""
        db_module.DB_PATH = temp_db
        conn = db_module.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='import_jobs'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_messages_table_schema(self, temp_db):
        """Test that messages table has correct columns."""
        db_module.DB_PATH = temp_db
        conn = db_module.get_connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(messages)")
        columns = {row['name'] for row in cursor.fetchall()}
        conn.close()

        expected = {'id', 'phone_number', 'contact_name', 'body', 'timestamp', 'message_type', 'import_hash'}
        assert columns == expected


class TestDatabaseConnection:
    """Tests for database connection."""

    def test_get_connection_returns_connection(self, temp_db):
        """Test that get_connection returns a working connection."""
        db_module.DB_PATH = temp_db
        conn = db_module.get_connection()

        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 1

    def test_connection_has_row_factory(self, temp_db):
        """Test that connection returns dict-like rows."""
        db_module.DB_PATH = temp_db
        conn = db_module.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 as value")
        result = cursor.fetchone()
        conn.close()

        assert result['value'] == 1


class TestFTSSync:
    """Tests for FTS5 synchronization."""

    def test_insert_triggers_fts_update(self, temp_db):
        """Test that inserting a message updates the FTS index."""
        db_module.DB_PATH = temp_db
        conn = db_module.get_connection()
        cursor = conn.cursor()

        # Insert a message
        cursor.execute('''
            INSERT INTO messages (phone_number, contact_name, body, timestamp, message_type, import_hash)
            VALUES ('+15551234567', 'Test', 'unique searchable content xyz123', 1700000000000, 1, 'testhash')
        ''')
        conn.commit()

        # Search for it in FTS
        cursor.execute("SELECT * FROM messages_fts WHERE messages_fts MATCH 'xyz123'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_delete_triggers_fts_update(self, temp_db):
        """Test that deleting a message updates the FTS index."""
        db_module.DB_PATH = temp_db
        conn = db_module.get_connection()
        cursor = conn.cursor()

        # Insert a message
        cursor.execute('''
            INSERT INTO messages (phone_number, contact_name, body, timestamp, message_type, import_hash)
            VALUES ('+15551234567', 'Test', 'deletable content abc789', 1700000000000, 1, 'deletehash')
        ''')
        conn.commit()

        # Delete it
        cursor.execute("DELETE FROM messages WHERE import_hash = 'deletehash'")
        conn.commit()

        # Search for it in FTS - should not find
        cursor.execute("SELECT * FROM messages_fts WHERE messages_fts MATCH 'abc789'")
        result = cursor.fetchone()
        conn.close()

        assert result is None

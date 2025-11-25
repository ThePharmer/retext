"""Tests for SMS import script."""

import db as db_module
import import_sms


class TestComputeImportHash:
    """Tests for the hash computation function."""

    def test_hash_is_deterministic(self):
        """Test that same inputs produce same hash."""
        hash1 = import_sms.compute_import_hash(1700000000000, '+15551234567', 'Hello world')
        hash2 = import_sms.compute_import_hash(1700000000000, '+15551234567', 'Hello world')

        assert hash1 == hash2

    def test_hash_is_hex_string(self):
        """Test that hash is a hex string."""
        result = import_sms.compute_import_hash(1700000000000, '+15551234567', 'Hello')

        assert isinstance(result, str)
        assert all(c in '0123456789abcdef' for c in result)

    def test_different_inputs_different_hash(self):
        """Test that different inputs produce different hashes."""
        hash1 = import_sms.compute_import_hash(1700000000000, '+15551234567', 'Hello')
        hash2 = import_sms.compute_import_hash(1700000000001, '+15551234567', 'Hello')
        hash3 = import_sms.compute_import_hash(1700000000000, '+15559999999', 'Hello')
        hash4 = import_sms.compute_import_hash(1700000000000, '+15551234567', 'Goodbye')

        assert hash1 != hash2
        assert hash1 != hash3
        assert hash1 != hash4


class TestCountMessages:
    """Tests for the message counting function."""

    def test_count_messages_in_sample_xml(self, sample_xml_file):
        """Test counting messages in XML file."""
        count = import_sms.count_messages(sample_xml_file)

        assert count == 3

    def test_count_nonexistent_file(self):
        """Test counting messages in nonexistent file."""
        count = import_sms.count_messages('/nonexistent/path.xml')

        assert count is None


class TestImportXML:
    """Tests for the XML import function."""

    def test_import_creates_messages(self, temp_db, sample_xml_file):
        """Test that import creates messages in database."""
        db_module.DB_PATH = temp_db

        imported, duplicates, error = import_sms.import_xml(sample_xml_file)

        assert error is None
        assert imported == 3
        assert duplicates == 0

        # Verify messages in database
        conn = db_module.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM messages')
        count = cursor.fetchone()['count']
        conn.close()

        assert count == 3

    def test_import_extracts_fields(self, temp_db, sample_xml_file):
        """Test that import extracts all message fields."""
        db_module.DB_PATH = temp_db

        import_sms.import_xml(sample_xml_file)

        conn = db_module.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM messages ORDER BY timestamp LIMIT 1')
        msg = cursor.fetchone()
        conn.close()

        assert msg['phone_number'] == '+15551234567'
        assert msg['contact_name'] == 'Test User'
        assert msg['body'] == 'Hello world'
        assert msg['timestamp'] == 1700000000000
        assert msg['message_type'] == 1

    def test_import_handles_missing_contact(self, temp_db, sample_xml_file):
        """Test that import handles messages without contact name."""
        db_module.DB_PATH = temp_db

        import_sms.import_xml(sample_xml_file)

        conn = db_module.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE phone_number = '+15555555555'")
        msg = cursor.fetchone()
        conn.close()

        assert msg['contact_name'] is None
        assert msg['body'] == 'No contact name'

    def test_import_deduplicates_messages(self, temp_db, sample_xml_file):
        """Test that duplicate imports are skipped."""
        db_module.DB_PATH = temp_db

        # First import
        imported1, duplicates1, error1 = import_sms.import_xml(sample_xml_file)
        assert imported1 == 3
        assert duplicates1 == 0

        # Second import of same file
        imported2, duplicates2, error2 = import_sms.import_xml(sample_xml_file)
        assert imported2 == 0
        assert duplicates2 == 3

        # Total should still be 3
        conn = db_module.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM messages')
        count = cursor.fetchone()['count']
        conn.close()

        assert count == 3

    def test_import_populates_fts(self, temp_db, sample_xml_file):
        """Test that imported messages are searchable via FTS."""
        db_module.DB_PATH = temp_db

        import_sms.import_xml(sample_xml_file)

        conn = db_module.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.* FROM messages m
            JOIN messages_fts fts ON m.id = fts.rowid
            WHERE messages_fts MATCH 'Hello'
        ''')
        results = cursor.fetchall()
        conn.close()

        assert len(results) == 1
        assert 'Hello world' in results[0]['body']

    def test_import_invalid_file(self, temp_db):
        """Test import with invalid file path."""
        db_module.DB_PATH = temp_db

        imported, duplicates, error = import_sms.import_xml('/nonexistent/file.xml')

        assert error is not None


class TestInsertBatch:
    """Tests for batch insertion."""

    def test_insert_batch_returns_counts(self, temp_db):
        """Test that insert_batch returns correct counts."""
        db_module.DB_PATH = temp_db
        conn = db_module.get_connection()
        cursor = conn.cursor()

        batch = [
            ('+15551234567', 'Test', 'Message 1', 1700000000000, 1, 'hash1'),
            ('+15551234567', 'Test', 'Message 2', 1700001000000, 1, 'hash2'),
        ]

        result = import_sms.insert_batch(cursor, batch)
        conn.commit()
        conn.close()

        assert result['inserted'] == 2
        assert result['duplicates'] == 0

    def test_insert_batch_handles_duplicates(self, temp_db):
        """Test that insert_batch handles duplicate hashes."""
        db_module.DB_PATH = temp_db
        conn = db_module.get_connection()
        cursor = conn.cursor()

        # First batch
        batch1 = [
            ('+15551234567', 'Test', 'Message 1', 1700000000000, 1, 'samehash'),
        ]
        import_sms.insert_batch(cursor, batch1)
        conn.commit()

        # Second batch with same hash
        batch2 = [
            ('+15551234567', 'Test', 'Message 1', 1700000000000, 1, 'samehash'),
        ]
        result = import_sms.insert_batch(cursor, batch2)
        conn.commit()
        conn.close()

        assert result['inserted'] == 0
        assert result['duplicates'] == 1

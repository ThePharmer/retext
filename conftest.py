"""Pytest fixtures for Retext tests."""

import os
import tempfile

import pytest
from werkzeug.security import generate_password_hash

# Set test environment before importing app
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['PASSWORD_HASH'] = generate_password_hash('testpass123')


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    import db as db_module

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name

    # Patch db module to use temp database
    original_path = db_module.DB_PATH
    db_module.DB_PATH = temp_path

    # Initialize the database
    db_module.init_db()

    yield temp_path

    # Restore original and cleanup
    db_module.DB_PATH = original_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def app(temp_db):
    """Create Flask test application."""
    import db as db_module
    import app as app_module

    # Ensure app uses the temp database
    db_module.DB_PATH = temp_db

    app_module.app.config['TESTING'] = True
    app_module.app.config['WTF_CSRF_ENABLED'] = False

    yield app_module.app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def authenticated_client(client):
    """Create an authenticated test client."""
    # Login first
    client.post('/login', data={'password': 'testpass123'})
    return client


@pytest.fixture
def sample_messages(temp_db):
    """Insert sample messages into the database."""
    import db as db_module

    db_module.DB_PATH = temp_db
    conn = db_module.get_connection()
    cursor = conn.cursor()

    messages = [
        ('+15551234567', 'Alice', 'Hey, are you coming to the party tonight?', 1700000000000, 1, 'hash1'),
        ('+15551234567', 'Alice', 'Don\'t forget to bring the groceries!', 1700001000000, 2, 'hash2'),
        ('+15559876543', 'Bob', 'Happy birthday! Hope you have a great day.', 1700002000000, 1, 'hash3'),
        ('+15555555555', None, 'Meeting at 3pm tomorrow', 1700003000000, 1, 'hash4'),
        ('+15551111111', 'Carol', 'The weather is nice today', 1700004000000, 2, 'hash5'),
    ]

    for msg in messages:
        cursor.execute('''
            INSERT INTO messages (phone_number, contact_name, body, timestamp, message_type, import_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', msg)

    conn.commit()
    conn.close()

    return messages


@pytest.fixture
def sample_xml_file():
    """Create a temporary XML file with sample SMS data."""
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<smses count="3">
  <sms address="+15551234567" contact_name="Test User" body="Hello world" date="1700000000000" type="1" />
  <sms address="+15559876543" contact_name="Another User" body="Testing message" date="1700001000000" type="2" />
  <sms address="+15555555555" body="No contact name" date="1700002000000" type="1" />
</smses>
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(xml_content)
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)

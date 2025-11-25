# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Retext is a self-hosted SMS backup search application. It imports SMS Backup & Restore XML exports from Android and provides full-text search across message history.

## Tech Stack

- Python 3.11+ with Flask (only external dependency)
- SQLite with FTS5 for full-text search
- Werkzeug for password hashing and WSGI middleware
- Vanilla JavaScript frontend (no framework)

## Commands

```bash
# Setup
python -m venv venv
./venv/bin/pip install -r requirements.txt

# Run server (development)
./venv/bin/python app.py

# Run with environment variables
export PASSWORD_HASH='...' SECRET_KEY='...' HOST=127.0.0.1 PORT=5000
./venv/bin/python app.py

# Import SMS backup
./venv/bin/python import_sms.py backup.xml

# Initialize database only
./venv/bin/python db.py

# Run tests
./venv/bin/pip install pytest  # first time only
./venv/bin/pytest -v

# Run single test file
./venv/bin/pytest test_app.py -v

# Linting
ruff check .
```

## Architecture

```
app.py          # Flask routes: login, logout, index, /api/search, /api/stats, /health
db.py           # SQLite setup: messages table, FTS5 virtual table, triggers
import_sms.py   # CLI script: streaming XML parser for SMS Backup & Restore format
templates/      # Jinja2 templates: login.html, index.html
```

**Data flow:**
1. `import_sms.py` parses XML → inserts into `messages` table → triggers sync FTS5 index
2. `app.py` serves search UI → queries `messages_fts` with MATCH → returns paginated JSON
3. Frontend fetches `/api/search?q=term&page=1` → displays highlighted results

**Database schema:**
- `messages`: id, phone_number, contact_name, body, timestamp (ms), message_type, import_hash
- `messages_fts`: FTS5 virtual table indexing body column (porter stemming, unicode61)
- `import_jobs`: tracking table for import operations

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| PASSWORD_HASH | Yes | Werkzeug password hash for auth |
| SECRET_KEY | Yes | Flask session secret |
| HOST | No | Bind address (default: 127.0.0.1) |
| PORT | No | Bind port (default: 5000) |
| APPLICATION_ROOT | No | URL prefix for reverse proxy (e.g., /retext) |
| DATA_DIR | No | Directory for messages.db (default: current dir) |

Generate password hash:
```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```

## Reverse Proxy Deployment

For deployment behind a reverse proxy at a subpath (e.g., `/retext`), set `APPLICATION_ROOT`. The app uses Werkzeug's `DispatcherMiddleware` to handle path stripping and `SCRIPT_NAME` setting.

Example for code-server absproxy:
```bash
export APPLICATION_ROOT=/absproxy/8888
```

## Test Data

Sample backup file `sample-backup.xml` contains 15 test messages. Search terms that return results: party, groceries, birthday, meeting.

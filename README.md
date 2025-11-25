# Retext

A self-hosted SMS backup search application. Import your SMS Backup & Restore XML exports and search through years of text message history instantly.

## Features

- **Full-text search** - Find any message using SQLite FTS5 with porter stemming
- **Fast imports** - Streaming XML parser handles large backups (1GB+) without loading into memory
- **Deduplication** - Re-importing the same backup skips duplicate messages
- **Search highlighting** - Matching terms highlighted in results
- **Password protection** - Simple shared password authentication
- **Mobile-friendly** - Responsive design works on any device
- **Reverse proxy support** - Deploy behind nginx, Caddy, or code-server

## Quick Start

```bash
# Clone and setup
git clone https://github.com/ThePharmer/retext.git
cd retext
python -m venv venv
./venv/bin/pip install -r requirements.txt

# Generate a password hash
./venv/bin/python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"

# Configure and run
export PASSWORD_HASH='scrypt:32768:8:1$...'  # paste hash from above
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
./venv/bin/python app.py

# Import your SMS backup
./venv/bin/python import_sms.py /path/to/sms-backup.xml
```

Open http://127.0.0.1:5000 and log in with your password.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PASSWORD_HASH` | Yes | - | Werkzeug password hash |
| `SECRET_KEY` | Yes | - | Flask session secret (32+ hex chars) |
| `HOST` | No | `127.0.0.1` | Bind address |
| `PORT` | No | `5000` | Bind port |
| `APPLICATION_ROOT` | No | - | URL prefix for reverse proxy |
| `DATA_DIR` | No | `.` | Directory for messages.db |

Copy `.env.example` to `.env` and fill in your values.

## Importing SMS Backups

Retext imports XML files from [SMS Backup & Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore) for Android.

```bash
# Import a backup file
./venv/bin/python import_sms.py backup.xml

# Progress is shown for large files
Importing: backup.xml
Counting messages in backup.xml...
Found 247,832 messages
Progress: 50,000 / 247,832 (20.2%)
...
Complete: 247,832 messages imported (0 duplicates skipped)
Time: 45.2 seconds
```

Re-running import on the same file safely skips duplicates.

## Reverse Proxy Deployment

### Behind nginx

```nginx
location /retext/ {
    proxy_pass http://127.0.0.1:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

```bash
export APPLICATION_ROOT=/retext
./venv/bin/python app.py
```

### Behind code-server

```bash
export APPLICATION_ROOT=/absproxy/8888
export PORT=8888
./venv/bin/python app.py
```

Access at `https://your-server/absproxy/8888/`

## Development

```bash
# Run tests
./venv/bin/pip install pytest
./venv/bin/pytest -v

# Run single test file
./venv/bin/pytest test_app.py -v

# Lint
ruff check .
```

## Tech Stack

- Python 3.11+
- Flask (web framework)
- SQLite with FTS5 (full-text search)
- Vanilla JavaScript (no framework)

## License

MIT

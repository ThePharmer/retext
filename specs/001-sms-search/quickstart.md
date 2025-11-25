# Quickstart: Retext SMS Search

## Prerequisites

- Python 3.11 or higher
- SMS Backup & Restore XML export file from your Android device

## Setup

### 1. Clone and Install

```bash
git clone <repository-url>
cd retext
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Password

Generate a password hash and set environment variables:

```bash
# Generate password hash (run in Python)
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password-here'))"

# Create .env file
cp .env.example .env
# Edit .env and set:
# PASSWORD_HASH=<output from above>
# SECRET_KEY=<random string for sessions>
```

Or set environment variables directly:
```bash
export PASSWORD_HASH="pbkdf2:sha256:..."
export SECRET_KEY="your-random-secret-key"
```

### 3. Import Your SMS Backup

Transfer your SMS Backup & Restore XML file to the server, then:

```bash
python import.py /path/to/sms-backup.xml
```

You'll see progress output:
```
Importing: sms-backup.xml
Found 247,832 messages
Progress: 50,000 / 247,832 (20.2%)
...
Complete: 247,832 messages imported
```

### 4. Start the Server

```bash
python app.py
```

Server runs on `http://localhost:5000` by default.

### 5. Access via Cloudflare Tunnel (Optional)

For remote access with HTTPS:

```bash
cloudflared tunnel --url http://localhost:5000
```

## Usage

1. Open `http://localhost:5000` (or your tunnel URL)
2. Enter the shared password to log in
3. Type search terms in the search box
4. Press Enter or click Search
5. Browse results, click "Load more" for additional pages

## Search Tips

- **Basic search**: `dinner` finds all messages containing "dinner"
- **Multiple terms**: `dinner friday` finds messages with both words
- **Phrase search**: `"dinner on friday"` finds exact phrase
- **Prefix search**: `din*` finds dinner, dine, dining, etc.

## File Structure

After setup:
```
retext/
├── app.py           # Flask server (run this)
├── import.py        # Import tool (run once)
├── templates/
│   └── index.html   # Web interface
├── messages.db      # Your messages (auto-created)
├── requirements.txt
└── .env             # Your configuration
```

## Troubleshooting

**"No messages found" after import**
- Verify import completed without errors
- Check `messages.db` file exists and has size > 0

**Login not working**
- Verify PASSWORD_HASH is set correctly in environment
- Ensure hash was generated with same password you're entering

**Import fails with memory error**
- Your XML file may be very large; the streaming parser should handle this
- Check available disk space for database file

**Search is slow**
- First search after startup may be slower (cache warming)
- Subsequent searches should be <2 seconds

# Research: Retext SMS Search

**Date**: 2025-11-24
**Feature**: 001-sms-search

## Technology Decisions

### Language: Python 3.11+

**Decision**: Python 3.11+ with Flask

**Rationale**:
- User-specified choice for simplicity and rapid development
- Excellent XML parsing with iterparse for streaming
- Native SQLite support in standard library
- Flask is minimal and well-understood

**Trade-off acknowledged**: Requires Python runtime on host. Acceptable for this
deployment model (localhost + Cloudflare Tunnel on user's own server).

### Web Framework: Flask

**Decision**: Flask (minimal install)

**Rationale**:
- Single dependency in requirements.txt
- Serves both API and static HTML
- No build step required
- Well-documented, stable

**Dependencies**:
- `flask` (includes Werkzeug, Jinja2, etc.)

### Database: SQLite with FTS5

**Decision**: SQLite via Python's built-in `sqlite3` module

**Rationale**:
- File-based, no separate server (constitution: SQLite default)
- FTS5 provides full-text search for millions of records
- Read-heavy workload, single user - perfect fit
- Standard library, zero additional dependencies

**FTS5 Configuration**:
- External content table to avoid data duplication
- Porter stemmer tokenizer for word stemming
- Triggers to keep FTS index synchronized

### XML Parser: iterparse

**Decision**: `xml.etree.ElementTree.iterparse`

**Rationale**:
- Standard library (zero dependencies)
- Event-driven streaming (constant memory)
- Clear elements after processing to free memory
- Well-documented SMS Backup & Restore format

**Memory Strategy**:
- Process one `<sms>` element at a time
- Call `elem.clear()` after each message
- Batch inserts (1000 records per transaction)

### Frontend: Single HTML + Vanilla JS

**Decision**: Single `index.html` with embedded CSS and vanilla JavaScript

**Rationale**:
- No build step, no npm
- Served directly by Flask
- Fetch API for search requests
- CSS Grid/Flexbox for responsive layout

### Authentication: Session-based with shared password

**Decision**: Flask session with bcrypt password hashing

**Rationale**:
- Simple shared password (spec clarification)
- Flask's built-in session handling
- `bcrypt` or `werkzeug.security` for password hashing
- Cookie-based sessions (HttpOnly, Secure flags)

**Note**: `werkzeug.security.generate_password_hash` and `check_password_hash`
are included with Flask, so no additional dependency needed.

## Architecture Decisions

### File Structure

**Decision**: Flat structure at repository root

```
retext/
├── app.py           # Flask server with search API and auth
├── import.py        # CLI script for XML → SQLite import
├── templates/
│   └── index.html   # Frontend (served by Flask)
├── static/          # CSS/JS if separated from index.html
├── messages.db      # SQLite database (gitignored)
├── requirements.txt # Flask only
└── .env.example     # Environment variable template
```

**Rationale**:
- Minimal files, easy to understand
- CLI import separate from web server
- Templates directory is Flask convention

### Import Process

**Decision**: Separate CLI script (`import.py`)

**Rationale**:
- Run once or occasionally, not part of web server
- Can show progress in terminal
- Simpler than web-based upload for 1GB+ files
- User runs: `python import.py backup.xml`

### Deployment Model

**Decision**: localhost + Cloudflare Tunnel

**Rationale**:
- No containerization for v1 (user preference)
- Cloudflare Tunnel provides HTTPS and remote access
- Application binds to localhost only (security)
- User manages Python environment on their server

## Constitution Compliance Notes

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Simplicity | ✅ Pass | 4 files, minimal dependencies |
| II. Security First | ✅ Pass | Password auth, localhost binding, HTTPS via CF Tunnel |
| III. Performance at Scale | ✅ Pass | iterparse streaming, FTS5 indexing, pagination |
| IV. Accessibility | ✅ Pass | Web UI, guided import via CLI with clear output |
| V. Self-Hosting Friendly | ⚠️ Partial | Requires Python runtime; acceptable per user choice |

**Self-Hosting Note**: The constitution prefers single binary distribution, but
user has explicitly chosen Python for this deployment. The trade-off is accepted
given the deployment model (user's own server with Python already available).

## Dependencies Summary

| Package | Purpose | Notes |
|---------|---------|-------|
| `flask` | Web server | Only external dependency |

**requirements.txt**:
```
flask>=3.0
```

## Performance Targets

| Metric | Target | How Achieved |
|--------|--------|--------------|
| Import 500K messages | < 5 minutes | iterparse streaming, batch inserts |
| Search 1M records | < 2 seconds | FTS5 index, LIMIT clause |
| Memory during import | < 200MB | Streaming XML, element clearing |
| Startup time | < 1 second | Minimal Flask app |

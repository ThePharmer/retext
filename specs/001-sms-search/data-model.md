# Data Model: Retext SMS Search

**Date**: 2025-11-24
**Feature**: 001-sms-search

## Entities

### Message

Represents a single SMS message imported from backup.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal row ID |
| phone_number | TEXT | NOT NULL | Phone number (e.g., "+15551234567") |
| contact_name | TEXT | NULL | Contact name if available |
| body | TEXT | NOT NULL | Message content |
| timestamp | INTEGER | NOT NULL, INDEX | Unix epoch milliseconds |
| message_type | INTEGER | NOT NULL | 1=received, 2=sent |
| import_hash | TEXT | UNIQUE | SHA256(timestamp + phone + body) for dedup |

**Notes**:
- `message_type` matches SMS Backup & Restore `type` attribute
- `import_hash` prevents duplicate imports (FR-013)
- `timestamp` stored as milliseconds for SMS Backup format compatibility

### Message FTS Index

Virtual table for full-text search using FTS5.

```sql
CREATE VIRTUAL TABLE messages_fts USING fts5(
    body,
    content='messages',
    content_rowid='id',
    tokenize='porter unicode61'
);
```

**Configuration**:
- `content='messages'`: External content table (no data duplication)
- `content_rowid='id'`: Maps to messages.id
- `tokenize='porter unicode61'`: Word stemming + Unicode support

### ImportJob

Tracks import operations for progress reporting.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Import job ID |
| file_name | TEXT | NOT NULL | Original XML filename |
| status | TEXT | NOT NULL | pending/running/completed/failed |
| total_messages | INTEGER | DEFAULT 0 | Total messages in file |
| processed_messages | INTEGER | DEFAULT 0 | Messages imported so far |
| started_at | INTEGER | NOT NULL | Unix timestamp |
| completed_at | INTEGER | NULL | Unix timestamp when done |
| error_message | TEXT | NULL | Error details if failed |

## Schema DDL

```sql
-- Main messages table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT NOT NULL,
    contact_name TEXT,
    body TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    message_type INTEGER NOT NULL,
    import_hash TEXT UNIQUE
);

-- Index for date sorting (FR-006: newest first)
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC);

-- Index for deduplication lookups
CREATE INDEX IF NOT EXISTS idx_messages_import_hash ON messages(import_hash);

-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    body,
    content='messages',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Triggers to keep FTS in sync with messages table
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, body) VALUES (new.id, new.body);
END;

CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, body) VALUES('delete', old.id, old.body);
END;

CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, body) VALUES('delete', old.id, old.body);
    INSERT INTO messages_fts(rowid, body) VALUES (new.id, new.body);
END;

-- Import tracking table
CREATE TABLE IF NOT EXISTS import_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_messages INTEGER DEFAULT 0,
    processed_messages INTEGER DEFAULT 0,
    started_at INTEGER NOT NULL,
    completed_at INTEGER,
    error_message TEXT
);
```

## XML Source Format

SMS Backup & Restore XML structure:

```xml
<smses count="12345" backup_set="..." backup_date="1234567890123">
  <sms protocol="0"
       address="+15551234567"
       date="1234567890123"
       type="1"
       body="Message text here"
       read="1"
       contact_name="John Doe"
       ... />
</smses>
```

**Field Mapping**:
| XML Attribute | Database Field | Transformation |
|---------------|----------------|----------------|
| address | phone_number | Direct copy |
| contact_name | contact_name | Direct copy (may be absent) |
| body | body | Direct copy |
| date | timestamp | Direct copy (already milliseconds) |
| type | message_type | Direct copy (1=recv, 2=sent) |
| - | import_hash | SHA256(date + address + body) |

## Queries

### Search (FR-005, FR-006, FR-007)

```sql
SELECT m.id, m.phone_number, m.contact_name, m.body, m.timestamp, m.message_type
FROM messages m
JOIN messages_fts fts ON m.id = fts.rowid
WHERE messages_fts MATCH ?
ORDER BY m.timestamp DESC
LIMIT 50 OFFSET ?;
```

### Message Count (FR-008)

```sql
SELECT COUNT(*) FROM messages;
```

### Duplicate Check (FR-013)

```sql
INSERT OR IGNORE INTO messages (...) VALUES (...);
```

The `UNIQUE` constraint on `import_hash` with `INSERT OR IGNORE` handles
duplicates automatically during import.

## Validation Rules

1. **phone_number**: Must not be empty
2. **body**: Must not be empty
3. **timestamp**: Must be positive integer (Unix milliseconds)
4. **message_type**: Must be 1 (received) or 2 (sent)
5. **import_hash**: Computed as `sha256(f"{timestamp}{phone_number}{body}")`

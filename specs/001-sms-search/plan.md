# Implementation Plan: Retext SMS Search

**Branch**: `001-sms-search` | **Date**: 2025-11-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-sms-search/spec.md`

## Summary

Build a self-hosted SMS backup search application that imports SMS Backup & Restore
XML files into SQLite with FTS5 for full-text search. Users access via a simple
web interface served by Flask, with password protection for security.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Flask (web server, only external dependency)
**Storage**: SQLite with FTS5 (file-based full-text search)
**Testing**: pytest (unit and integration tests)
**Target Platform**: Linux server (localhost + Cloudflare Tunnel)
**Project Type**: Single project (flat structure)
**Performance Goals**: Search <2s for 1M records, import 500K messages <5 min
**Constraints**: <200MB memory during import, <1GB RAM total
**Scale/Scope**: Single user/family, 1M+ messages, 1GB+ XML files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Code Simplicity | ✅ Pass | 4 source files, 1 dependency, no abstractions |
| II. Security First | ✅ Pass | Password auth (FR-015/16), localhost binding, HTTPS via tunnel |
| III. Performance at Scale | ✅ Pass | iterparse streaming (FR-003), FTS5 index (FR-005), pagination (FR-007) |
| IV. Accessibility | ✅ Pass | Web UI primary (FR-009), CLI import with progress (FR-004) |
| V. Self-Hosting Friendly | ⚠️ Accepted | Requires Python runtime; trade-off accepted for simplicity |

**Self-Hosting Exception**: Constitution prefers single binary, but Python was
explicitly chosen by user. Deployment model (user's server + Cloudflare Tunnel)
makes this acceptable - user already has Python available.

## Project Structure

### Documentation (this feature)

```text
specs/001-sms-search/
├── plan.md              # This file
├── research.md          # Technology decisions
├── data-model.md        # Database schema
├── quickstart.md        # Setup and usage guide
├── contracts/           # API specification
│   └── api.md           # REST endpoints
└── tasks.md             # Implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
retext/
├── app.py               # Flask server: routes, auth, search API
├── import.py            # CLI script: XML parsing, SQLite import
├── templates/
│   └── index.html       # Single-page frontend with search UI
├── static/              # Optional: separated CSS/JS assets
├── messages.db          # SQLite database (gitignored)
├── requirements.txt     # flask>=3.0
├── .env.example         # PASSWORD_HASH, SECRET_KEY template
└── tests/
    ├── test_import.py   # Import functionality tests
    └── test_search.py   # Search API tests
```

**Structure Decision**: Flat structure at repository root. No src/ directory
needed for 4 files. Flask convention with templates/ directory. CLI import
separate from web server for simplicity.

## Complexity Tracking

> No violations requiring justification. Design follows constitution principles.

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| No ORM | Direct sqlite3 | Simpler, fewer dependencies, full FTS5 control |
| No frontend framework | Vanilla JS | No build step, constitution simplicity |
| CLI import vs web upload | CLI | Simpler for 1GB+ files, clear progress output |

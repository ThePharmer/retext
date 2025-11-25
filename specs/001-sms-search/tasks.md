# Tasks: Retext SMS Search

**Input**: Design documents from `/specs/001-sms-search/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/api.md

**Tests**: Not explicitly requested in spec. Test tasks omitted per template guidelines.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: Project initialization and configuration

- [x] T001 Create project directory structure per plan.md at repository root
- [x] T002 Create requirements.txt with `flask>=3.0` at requirements.txt
- [x] T003 [P] Create .env.example with PASSWORD_HASH, SECRET_KEY, HOST, PORT, APPLICATION_ROOT, DATA_DIR placeholders at .env.example
- [x] T004 [P] Create .gitignore with messages.db, .env, __pycache__, venv at .gitignore
- [x] T005 [P] Create templates/ directory at templates/
- [x] T005a [P] Document APPLICATION_ROOT, DATA_DIR in .env.example comments at .env.example

**Checkpoint**: Project scaffolding complete, ready for database setup

---

## Phase 2: Foundational (Database Schema)

**Purpose**: Core database infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create database initialization module with schema DDL and DATA_DIR support at db.py
- [x] T007 Implement messages table creation (id, phone_number, contact_name, body, timestamp, message_type, import_hash) in db.py
- [x] T008 Implement messages_fts FTS5 virtual table creation with porter tokenizer in db.py
- [x] T009 Implement FTS sync triggers (insert, update, delete) in db.py
- [x] T010 Implement import_jobs table creation in db.py
- [x] T011 [P] Add timestamp DESC index for search result ordering in db.py
- [x] T012 [P] Add import_hash UNIQUE index for deduplication in db.py

**Checkpoint**: Database schema complete, can be initialized with `python -c "import db; db.init_db()"`

---

## Phase 3: User Story 1 - Import SMS Backup (Priority: P1)

**Goal**: Users can import SMS Backup & Restore XML files via CLI with progress indication

**Independent Test**: Run `python import.py sample.xml` and verify messages appear in messages.db

### Implementation for User Story 1

- [x] T013 [US1] Create import.py CLI script skeleton with argparse at import_sms.py
- [x] T014 [US1] Implement XML streaming parser using iterparse for `<sms>` elements in import_sms.py
- [x] T015 [US1] Implement message extraction (address→phone_number, body, date→timestamp, type→message_type, contact_name) in import_sms.py
- [x] T016 [US1] Implement import_hash computation using SHA256(timestamp+phone+body) in import_sms.py
- [x] T017 [US1] Implement batch INSERT OR IGNORE with 1000-record transactions in import_sms.py
- [x] T018 [US1] Implement progress output showing count/total and percentage in import_sms.py
- [x] T019 [US1] Implement XML element clearing after processing to bound memory in import_sms.py
- [x] T020 [US1] Implement error handling for malformed XML with clear error messages in import_sms.py
- [x] T021 [US1] Implement import summary showing total imported and duplicates skipped in import_sms.py

**Checkpoint**: User Story 1 complete - can import XML backups via `python import.py backup.xml`

---

## Phase 4: User Story 2 - Search Messages (Priority: P1)

**Goal**: Users can search messages via web UI with paginated results

**Independent Test**: Start Flask server, log in, type search term, see matching messages with highlighting

### Implementation for User Story 2

- [x] T022 [US2] Create app.py Flask application skeleton with config loading at app.py
- [x] T022a [US2] Implement APPLICATION_ROOT config for URL prefix support in app.py
- [x] T023 [US2] Implement session configuration (secret key, cookie flags) in app.py
- [x] T024 [US2] Implement login_required decorator for route protection in app.py
- [x] T025 [US2] Implement GET /login route serving login form in app.py
- [x] T026 [US2] Implement POST /login route with password verification using werkzeug.security in app.py
- [x] T027 [US2] Implement POST /logout route clearing session in app.py
- [x] T028 [US2] Implement GET /api/search route with FTS5 MATCH query in app.py
- [x] T029 [US2] Implement search result pagination (50 per page, offset calculation) in app.py
- [x] T030 [US2] Implement search term highlighting with `<mark>` tags in app.py
- [x] T031 [US2] Implement timestamp to human-readable date formatting in app.py
- [x] T032 [US2] Implement GET / route serving index.html (requires auth) in app.py
- [x] T033 [US2] Create index.html with search input, results container, and login form at templates/index.html
- [x] T034 [US2] Implement search form with Enter key and button submission in templates/index.html
- [x] T035 [US2] Implement fetch-based search API call with JSON response handling in templates/index.html
- [x] T036 [US2] Implement results rendering with contact name, body, date, sent/received styling in templates/index.html
- [x] T037 [US2] Implement "Load more" button for pagination in templates/index.html
- [x] T038 [US2] Implement responsive CSS for mobile/desktop using flexbox/grid in templates/index.html
- [x] T039 [US2] Implement sent vs received visual distinction (different background colors) in templates/index.html
- [x] T040 [US2] Implement "No results found" empty state message in templates/index.html

**Checkpoint**: User Story 2 complete - can search messages via web UI

---

## Phase 5: User Story 3 - View Database Status (Priority: P2)

**Goal**: Users see message count on landing page confirming import success

**Independent Test**: Visit landing page and see "X messages searchable" or import prompt

### Implementation for User Story 3

- [x] T041 [US3] Implement GET /api/stats route returning message_count and has_messages in app.py
- [x] T042 [US3] Add message count display to index.html landing page in templates/index.html
- [x] T043 [US3] Implement conditional UI: show import prompt when has_messages is false in templates/index.html
- [x] T044 [US3] Fetch and display stats on page load in templates/index.html

**Checkpoint**: User Story 3 complete - landing page shows database status

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Security headers, health endpoint, final hardening

- [x] T045 [P] Implement GET /health endpoint returning {"status": "ok"} in app.py
- [x] T046 [P] Add security headers middleware (X-Content-Type-Options, X-Frame-Options, CSP) in app.py
- [x] T047 [P] Implement input sanitization for search query parameter in app.py
- [x] T048 Implement configurable HOST/PORT binding from environment variables (default: 127.0.0.1:5000) in app.py
- [x] T048a Implement SIGTERM signal handler for graceful shutdown in app.py
- [x] T049 [P] Add error handlers for 400, 401, 500 returning JSON (no message content) in app.py
- [x] T049a [P] Implement authentication logging (timestamp, IP, success/failure) in app.py
- [x] T049b [P] Audit all error handlers to ensure no message content leakage in app.py
- [ ] T050 Manual verification: test import with large XML file (>100MB)
- [ ] T051 Manual verification: test search performance with >100K messages

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - can start after Phase 2
- **User Story 2 (Phase 4)**: Depends on Foundational - can run parallel with US1 if needed
- **User Story 3 (Phase 5)**: Depends on User Story 2 (extends app.py and index.html)
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (db.py)
    ↓
    ├── Phase 3: US1 - Import (import.py) ──────┐
    │                                            │
    └── Phase 4: US2 - Search (app.py, index.html)
                        ↓
                 Phase 5: US3 - Status (extends app.py, index.html)
                        ↓
                 Phase 6: Polish
```

### Parallel Opportunities

**Phase 1 (Setup)**:
```
T003, T004, T005 can run in parallel (different files)
```

**Phase 2 (Foundational)**:
```
T011, T012 can run in parallel (both modify db.py but different indexes)
```

**Phase 6 (Polish)**:
```
T045, T046, T047, T049 can run in parallel (different concerns in app.py)
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup (~5 tasks)
2. Complete Phase 2: Foundational (~7 tasks)
3. Complete Phase 3: User Story 1 - Import (~9 tasks)
4. Complete Phase 4: User Story 2 - Search (~19 tasks)
5. **STOP and VALIDATE**: Can import XML and search messages
6. Deploy/demo MVP

### Incremental Delivery

After MVP:
1. Add User Story 3 - Status (~4 tasks) → shows import confirmation
2. Add Polish phase (~7 tasks) → security hardening
3. Each addition is independently deployable

### Suggested MVP Scope

**Minimum viable**: Phase 1 + Phase 2 + Phase 3 + Phase 4 = 40 tasks

This delivers:
- XML import with progress (US1)
- Web search with pagination (US2)
- Password authentication
- Mobile-responsive UI

---

## Notes

- All file paths are relative to repository root
- db.py is a new module for database initialization (not in original plan but needed)
- No test tasks included (not explicitly requested in spec)
- Tasks T050, T051 are manual verification steps, not code tasks
- Constitution compliance verified in each task (no abstractions, direct code)

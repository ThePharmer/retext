# Feature Specification: Retext SMS Search

**Feature Branch**: `001-sms-search`
**Created**: 2025-11-24
**Status**: Draft
**Input**: User description: "Build Retext, a self-hosted SMS backup search application"

## Clarifications

### Session 2025-11-24

- Q: What should the V1 authentication approach be? → A: Simple password protection (single shared password for all users)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import SMS Backup (Priority: P1)

A user wants to import their SMS Backup & Restore XML export file so their messages become searchable. This is a one-time setup step before search becomes available.

**Why this priority**: Without imported data, there is nothing to search. This is the foundational capability that enables all other features.

**Independent Test**: Upload a sample XML backup file and verify messages appear in the database with correct contact names, phone numbers, timestamps, and message bodies.

**Acceptance Scenarios**:

1. **Given** the application is running with no imported data, **When** the user uploads an XML backup file, **Then** the system parses all messages and stores them in the database with progress indication.
2. **Given** a 1GB XML file with 500,000 messages, **When** the user initiates import, **Then** the import completes without running out of memory and provides progress feedback.
3. **Given** an import is in progress, **When** the user views the import page, **Then** they see a progress indicator showing approximate completion percentage.

---

### User Story 2 - Search Messages (Priority: P1)

A user wants to search their entire SMS history by typing keywords and viewing matching messages with context about who sent them and when.

**Why this priority**: This is the core value proposition of the application. Users need to find specific messages from years of conversation history.

**Independent Test**: Type a search term, press Enter, and see a list of matching messages showing contact name, message text, timestamp, and sent/received indicator.

**Acceptance Scenarios**:

1. **Given** messages have been imported, **When** the user types a search term and presses Enter (or clicks search), **Then** matching messages appear sorted by date (newest first).
2. **Given** search results exist, **When** the user views a result, **Then** they see: contact name, message body with highlighted search term, date/time, phone number, and whether it was sent or received.
3. **Given** the search matches 500 messages, **When** results load, **Then** only the first 50 appear with a "Load more" button to fetch additional pages.
4. **Given** the user is on a mobile device, **When** they perform a search, **Then** the interface remains usable with appropriately sized touch targets and readable text.

---

### User Story 3 - View Database Status (Priority: P2)

A user wants to see how many messages are in their database to confirm import succeeded and understand the scope of their searchable history.

**Why this priority**: Provides confidence that import worked and gives context for search results. Secondary to core import/search functionality.

**Independent Test**: View the landing page and see the total message count displayed prominently.

**Acceptance Scenarios**:

1. **Given** messages have been imported, **When** the user visits the landing page, **Then** they see the total message count (e.g., "247,832 messages searchable").
2. **Given** no messages have been imported, **When** the user visits the landing page, **Then** they see a prompt to import their backup file.

---

### Edge Cases

- What happens when a search returns no results? Display a friendly "No messages found" message with suggestion to try different terms.
- What happens when the XML file is malformed or from a different app? Display a clear error message explaining the file format is not supported.
- What happens if the user uploads a second backup file? New messages are added; duplicate messages (same timestamp + phone number + body) are skipped.
- What happens if a message has no contact name (just phone number)? Display the phone number in place of contact name.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST parse SMS Backup & Restore Android app XML format
- **FR-002**: System MUST extract and store: phone number, contact name (if present), message body, timestamp (as Unix epoch), sent/received type indicator
- **FR-003**: System MUST use streaming XML parsing to handle 1GB+ files without loading entire file into memory
- **FR-004**: System MUST provide visual progress indication during import
- **FR-005**: System MUST support full-text search across all message bodies
- **FR-006**: System MUST return search results sorted by date, newest first
- **FR-007**: System MUST paginate results with 50 messages per page and "Load more" functionality
- **FR-008**: System MUST display total message count in database on landing page
- **FR-009**: System MUST provide single search input on landing page
- **FR-010**: System MUST execute search on Enter key press or search button click
- **FR-011**: System MUST visually distinguish sent messages from received messages
- **FR-012**: System MUST work responsively on mobile and desktop browsers
- **FR-013**: System MUST skip duplicate messages during subsequent imports (matching on timestamp + phone number + body)
- **FR-014**: System MUST display phone number when contact name is not available
- **FR-015**: System MUST require password authentication before accessing any data or functionality
- **FR-016**: System MUST use a single shared password configured by the administrator
- **FR-017**: System MUST log authentication attempts (success/failure with timestamp and IP) without exposing passwords
- **FR-018**: System MUST NOT include message content in any log output (error messages, access logs, debug logs)
- **FR-019**: System MUST support APPLICATION_ROOT environment variable for deployment at non-root URL paths (e.g., /retext/)
- **FR-020**: System MUST support HOST and PORT environment variables for bind address configuration
- **FR-021**: System MUST support DATA_DIR environment variable for database file location (default: current directory)

### Key Entities

- **Message**: Represents a single SMS message with attributes: phone_number (string), contact_name (string, nullable), body (text), timestamp (Unix epoch integer), message_type (sent/received enum)
- **ImportJob**: Represents an import operation with attributes: file_name (string), status (pending/running/completed/failed), total_messages (integer), processed_messages (integer), started_at (timestamp), completed_at (timestamp, nullable)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can import a 1GB XML backup file containing 500,000 messages without the application crashing or running out of memory
- **SC-002**: Users see search results within 2 seconds for any query against a database of 1 million messages
- **SC-003**: 90% of family members with no technical background can successfully import a backup and search for a message on first attempt without assistance
- **SC-004**: Application runs successfully on a home server with 1GB RAM available
- **SC-005**: Users can access and use all features from mobile browsers without horizontal scrolling or unusable touch targets

## Assumptions

- Users have already created SMS Backup & Restore XML exports from their Android device
- Application uses simple shared password authentication (administrator sets password, all family members use same password)
- Users have a web browser on the device they want to search from
- Import is a batch operation performed occasionally (not continuous sync)
- Single user or small family use case; no concurrent import operations needed

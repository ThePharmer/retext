<!--
Sync Impact Report
==================
Version change: 0.0.0 → 1.0.0 (initial ratification)
Modified principles: N/A (initial version)
Added sections:
  - Core Principles (5 principles)
  - Self-Hosting Requirements
  - Development Workflow
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (generic, compatible)
  - .specify/templates/spec-template.md ✅ (generic, compatible)
  - .specify/templates/tasks-template.md ✅ (generic, compatible)
Follow-up TODOs: None
-->

# Retext Constitution

## Core Principles

### I. Code Simplicity

Retext is a single-purpose SMS search tool. Code MUST remain simple and direct.

- **No premature abstraction**: Solve the immediate problem; do not build frameworks
- **Flat is better than nested**: Prefer linear code flow over deep hierarchies
- **One way to do things**: Avoid multiple approaches to the same problem
- **Delete over deprecate**: Remove unused code rather than marking it obsolete
- **YAGNI**: Features not explicitly required MUST NOT be implemented

Rationale: A search tool succeeds through reliability and maintainability, not
architectural elegance. Every abstraction adds cognitive load and maintenance burden.

### II. Security First

Retext exposes personal SMS data over network connections. Security is non-negotiable.

- **Zero trust by default**: All network interfaces MUST require authentication
- **No data leakage**: Error messages and logs MUST NOT expose message content
- **Encryption in transit**: HTTPS MUST be supported and recommended as default
- **Input sanitization**: All user-supplied search queries MUST be sanitized
- **Minimal permissions**: Application MUST request only necessary filesystem access
- **Audit logging**: Authentication attempts and data access MUST be logged

Rationale: SMS messages contain sensitive personal, financial, and authentication data.
A security breach exposes the user's entire communication history.

### III. Performance at Scale

Retext MUST handle large datasets efficiently: 1GB+ XML imports and millions of records.

- **Streaming imports**: XML parsing MUST use streaming (not DOM) for imports
- **Indexed search**: Search queries MUST use database indexes, not table scans
- **Memory bounded**: Memory usage MUST remain constant regardless of dataset size
- **Progress feedback**: Long operations MUST provide progress indication to users
- **Pagination required**: All result sets MUST be paginated, no unbounded queries

Rationale: Users with years of SMS history will have massive datasets. The tool is
useless if import takes hours or search freezes the browser.

### IV. Accessibility for Non-Technical Users

Retext MUST be usable by people with no technical background.

- **No command-line required**: Primary interface MUST be graphical (web UI)
- **Clear error messages**: Errors MUST explain what went wrong in plain language
- **Sensible defaults**: Application MUST work without configuration file editing
- **Guided setup**: First-run experience MUST guide users through import process
- **No jargon**: UI text MUST avoid technical terminology where possible

Rationale: The target user is someone who wants to search their SMS history, not
someone who wants to administer a server.

### V. Self-Hosting Friendly

Retext MUST deploy easily in self-hosted environments without external dependencies.

- **Single binary or container**: Distribution MUST NOT require runtime installation
- **No external services**: Application MUST NOT require external APIs or SaaS
- **Reverse proxy compatible**: MUST work behind nginx, Caddy, Cloudflare Tunnel
- **Configurable base path**: MUST support deployment at non-root URL paths
- **Offline capable**: All functionality MUST work without internet access
- **SQLite default**: Database MUST be file-based by default, no separate server

Rationale: Self-hosters run diverse environments. External dependencies create
fragility, privacy concerns, and operational complexity.

## Self-Hosting Requirements

Technical requirements ensuring deployment flexibility:

- **Port configuration**: Bind address and port MUST be configurable via environment
- **TLS termination**: Application SHOULD support external TLS termination
- **Health endpoint**: MUST expose /health for reverse proxy health checks
- **Graceful shutdown**: MUST handle SIGTERM for container orchestration
- **Data persistence**: All state MUST be in a single, configurable directory

## Development Workflow

- **Test before merge**: All changes MUST pass existing tests before merge
- **Security review**: Changes to authentication or data access require explicit review
- **Performance regression**: Import and search benchmarks MUST NOT regress
- **Accessibility check**: UI changes MUST be tested for usability
- **Single-file changes preferred**: When possible, changes should be isolated

## Governance

This constitution defines the non-negotiable principles for Retext development.

- **Constitution authority**: This document supersedes other guidance when conflicts arise
- **Amendment process**: Changes require documented rationale and review
- **Compliance verification**: PRs MUST reference which principles were considered
- **Complexity justification**: Violations MUST be documented with alternatives rejected

**Version**: 1.0.0 | **Ratified**: 2025-11-24 | **Last Amended**: 2025-11-24

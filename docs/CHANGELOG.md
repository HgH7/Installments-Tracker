# Changelog

## [4.0.0] — 2026-06-27

### Added
- Structured logging system (app/logging/) with rotating handlers for app, errors, migrations, and backups
- Settings system (settings.db) with persistent user preferences (theme, window size, backup config)
- ValidationService (app/validation.py) — centralized input validation with specific error messages
- Startup recovery checks (app/recovery.py) — database integrity, missing tables, migration state
- Backup rotation (keep latest N, configurable via settings)
- Backup compression (gzip) with metadata JSON files
- Backup verification method
- 61 automated tests across validation, serialization, installments, database, repository, settings, and recovery
- Documentation (docs/ARCHITECTURE.md, DATABASE.md, CHANGELOG.md, ROADMAP.md, CONTRIBUTING.md)

### Changed
- The-Project.py reduced from ~1028 to ~190 lines
- Extracted DatePicker → app/ui/date_picker.py
- Extracted export_to_excel → app/export.py
- Extracted refresh_treeview → app/ui/treeview_helpers.py
- Extracted show_frame, keyboard shortcuts, nav button → app/ui/window_helpers.py
- Extracted show_payment_history → app/ui/payment_history.py
- Extracted EditInstallmentDialog, RestoreBackupDialog → app/ui/dialogs.py
- SQLiteRepository: transactional safety, specific exception handling, backup improvements
- CustomerService: uses ValidationService through validate_and_save

### Fixed
- append_record now reads data before transaction (was reading after delete)
- SQLiteRepository uses specific exceptions (sqlite3.Error, OSError, csv.Error)
- Phone normalization centralized in ValidationService

## [3.0.0] — 2026-06-27

### Added
- SQLite migration phase: schema redesign, SQLiteRepository, DatabaseManager
- app/repositories/sqlite_repository.py with full CRUD
- Normalized database schema with migrations

## [2.0.0] — 2026-06-25

### Added
- Architecture refactor: service layer, repository layer, UI modernization
- Phase 1 critical safety fixes: rename data loss, auto-WhatsApp, wildcard imports, bare excepts
- Phase 2 SQLite database design (pre-migration)

## [1.0.0] — 2026-06-20

### Initial
- Tkinter-based installment tracking desktop application
- CSV file storage
- WhatsApp notification integration

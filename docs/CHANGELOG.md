# Changelog

## v2.0.0-RC1 (2026-07-02)

### Added
- **Phase I (Contracts)**: Full contract workflow — detail/edit dialog, status transitions (Draft→Pending→Sent→Signed→Completed), template management (CRUD + duplicate + preview), customer name lookup, document generation integration, multi-criteria search/filtering
- **Phase J (Documents)**: Full document workflow — generate (receipt, invoice, contract, statement, etc.), list with customer name, type/customer filtering, detail dialog, open/delete, customer→documents navigation
- **Phase K (Tasks)**: Full task workflow — create with customer lookup, edit dialog, complete/reopen toggle, delete, overdue highlighting, today filter, empty state, customer→tasks navigation, activity logging
- **Phase L (Finance & Analytics)**: Expense CRUD with edit/filters, financial dashboard with 8 analytics metrics, per-customer financial summary
- **Phase M (Architecture Enforcement)**: Centralized path module (`app/utils/paths.py`), removed UI leak in service layer, 38 regression tests
- **Phase N (Notifications & Reminders)**: Reminder management page — search/filter, detail/edit, delete, resend via WhatsApp, status workflow (Draft→Scheduled→Sent→Failed/Cancelled)
- **Phase O (Global Search)**: Unified search across customers, contracts, documents, tasks, expenses, reminders — category filter, detail dialog, page navigation
- **Phase P (Production Hardening)**: Graceful shutdown, atomic writes, settings deep-copy fix, silent exception removal, raw exception dialog cleanup, PyInstaller packaging support, 10 regression tests

### Changed
- Version string now includes build tag: `v2.0.0-RC1`
- Centralized path computation supports `sys.frozen` for packaged builds
- ReminderService row_factory swap guaranteed safe via try/finally
- Telemetry persistence debounced (saves every 5s instead of on every event)

### Fixed
- Settings shallow copy corruption — `reset_to_defaults()` no longer mutates global defaults
- 3 silent `except Exception: pass` blocks — now log failures
- 15+ dialog calls leaking raw exception strings to users
- Settings.set()/set_many()/get_all() crash on DB errors — now caught and logged
- Updater temp file leaks — cleaned up in `finally` blocks
- Global search reminders double-query — removed redundant fallback
- CWD-relative `logs/`/`data/` paths — use centralized path module
- PyInstaller spec: fixed hiddenimports, urllib exclusion, datas filter

### Tests
- **324 tests** (0 failing), up from 250 after Phase L
- 10 new regression tests for production hardening fixes

## v2.0.0 (2026-06-27)

### Added
- Version system with `app/version.py` — single source of truth for version metadata
- Branding module with splash screen, about dialog, and consistent app naming
- Global crash recovery with exception hooks, session save/restore, and crash logging
- Auto-update mechanism via GitHub releases (check, download, apply, rollback)
- Application settings with persistent JSON config and UI editor
- Payment history dialog with per-customer installment timeline
- Backup manager with scheduled and on-demand backups, restore, and cleanup
- Activity log with search, date range filtering, and CSV export
- Import/export (CSV/Excel) with field mapping and validation
- Send notification page with reminder management and force-check
- Date picker widget for easier date input
- File manager for attaching files to customers
- Excel export with styled sheets
- Responsive layout with scrollable frames throughout all pages
- Keyboard shortcuts: Ctrl+N (new customer), Ctrl+F (search), Ctrl+Q (quit)
- Sidebar navigation with active state highlighting

### Changed
- Complete UI overhaul using customtkinter with dark/light theme support
- Replaced file-based CSV storage with SQLite for customers, activities, reminders
- Enhanced validation service returning structured `ValidationResult` objects
- Unified style system via `StyleManager` class with color palette
- Consolidated backup system — old `backup_restore.py` superseded by `backup_manager.py`
- Modular page architecture — each page is a self-contained `setup_*` function
- Improved error handling and logging throughout

### Fixed
- Treeview refresh on data changes across all pages
- Date parsing robustness with multiple format fallbacks
- Window centering on multi-monitor setups
- Graceful handling of missing data directories

### Removed
- Legacy CSV-based repository (replaced by SQLite + CSV export)
- `ui/tabs.py` — functionality moved into page modules
- Individual `*.csv` customer files (consolidated into SQLite)

## v1.0.0 (2026-01-15)

### Added
- Initial release with basic customer management
- CSV-based storage for customers and installments
- Simple UI with Tkinter
- Add, view, and manage installment records
- Basic backup and restore functionality

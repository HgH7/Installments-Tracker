# Changelog

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

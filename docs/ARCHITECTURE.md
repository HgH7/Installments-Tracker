# Architecture

## Overview

Installment Tracker is a desktop application built with CustomTkinter (tkinter) and SQLite. It follows a layered architecture:

```
The-Project.py (entry point)
    |
    +-- app/ui/pages/     (presentation layer)
    +-- app/services/     (business logic)
    +-- app/repositories/ (data access)
    +-- app/database/     (persistence)
    +-- app/utils/        (utilities)
```

## Layers

### Presentation (app/ui/)
- `pages/` — Page setup functions (home, add, view, manage, backup_restore, send_notification)
- `style.py` — StyleManager: central theme, fonts, UI primitive creators
- `date_picker.py` — Reusable date picker dialog
- `dialogs.py` — Shared dialog builders (EditInstallment, RestoreBackup, ModalDialog)
- `file_manager.py` — File CRUD for customer attachments
- `treeview_helpers.py` — Shared Treeview refresh utilities
- `window_helpers.py` — Frame navigation, keyboard shortcuts, nav button factory
- `payment_history.py` — Payment history dialog

### Business Logic (app/services/)
- `customer_service.py` — CustomerService: CRUD operations, installment marking, search
- `notification_service.py` — NotificationService: WhatsApp Web opener

### Data Access (app/repositories/)
- `sqlite_repository.py` — SQLiteRepository: primary data store, CSV-compatible dict interface
- `csv_repository.py` — CSVRepository: legacy CSV storage (kept for compatibility)

### Persistence (app/database/)
- `database.py` — DatabaseManager: connection lifecycle, WAL mode, FK enforcement, transactions
- `schema.py` — DDL statements and schema constants
- `migrations.py` — Version-aware schema migration runner
- `models.py` — Dataclasses: Customer, Installment, Attachment, Backup

### Cross-cutting
- `app/validation.py` — ValidationService: centralized input validation
- `app/settings.py` — Settings: persistent user preferences (settings.db)
- `app/logging/logger.py` — AppLogger: structured logging with rotation
- `app/recovery.py` — Startup integrity checks and recovery
- `app/export.py` — Excel export utility

## Key Design Decisions

- **Repository pattern**: CustomerService never knows whether data comes from SQLite or CSV
- **CSV-compatible dicts**: SQLiteRepository.read_data() returns same dict format as CSVRepository
- **Transactions**: All writes go through DatabaseManager.transaction() context manager
- **Backup as CSV**: Backups export SQLite data to timestamped CSV files (optionally gzip-compressed)
- **Settings as SQLite**: User preferences stored in settings.db, key-value format

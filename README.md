# Installments Tracker

A desktop application for tracking customer installment payments, built with Python and customtkinter.

## Features

- **Customer Management** — Add, edit, view, and search customer records
- **Installment Tracking** — Track payment schedules, due dates, and amounts
- **Payment History** — Per-customer payment timeline with filtering
- **Notifications & Reminders** — Automatic reminders for upcoming/overdue payments
- **Backup Manager** — Scheduled backups, manual backup, restore, and cleanup
- **Activity Log** — Full audit trail with search, date filtering, and CSV export
- **Import / Export** — CSV and Excel import/export with field mapping
- **File Attachments** — Attach files to customer records
- **Analytics Dashboard** — Charts and metrics for revenue, arrears, trends
- **Auto-Update** — Checks GitHub for new releases, downloads and installs
- **Crash Recovery** — Global exception handling with session save/restore
- **Settings** — Persistent configuration via UI editor
- **REST API** — Lightweight HTTP API (localhost:8765) for programmatic access to customers, installments, reports, events, settings, and system info

## Installation

### Prerequisites

- Python 3.9+
- pip

### Quick Start

```bash
git clone https://github.com/otman-22-git/Installments-Tracker.git
cd Installments-Tracker
pip install -r requirements.txt
python The-Project.py
```

### Build Standalone Executable

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller Installments-Tracker.spec
```

The executable will be in the `dist/` directory.

## Usage

### Navigation

The sidebar on the left provides access to all pages:

| Page | Description |
|------|-------------|
| **Home** | Dashboard with analytics, recent activity, and quick stats |
| **Add Customer** | Register a new customer with installment plan |
| **Customers** | Browse, search, and manage all customers |
| **Installments** | Manage installment records per customer |
| **Notifications** | View and manage reminders |
| **Backup Manager** | Schedule, create, and restore backups |
| **Activity Log** | Searchable audit trail |
| **Import/Export** | CSV/Excel import and export |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New customer |
| `Ctrl+F` | Focus search bar |
| `Ctrl+Q` | Quit application |

## Project Structure

```
Installments-Tracker/
├── The-Project.py            # Main entry point
├── app/
│   ├── version.py            # Version metadata
│   ├── branding.py           # Splash screen, about dialog
│   ├── settings.py           # Persistent settings
│   ├── crash_recovery.py     # Exception hooks, session save/restore
│   ├── updater.py            # Auto-update mechanism
│   ├── validation.py         # Input validation service
│   ├── export.py             # Excel/CSV export
│   ├── database/
│   │   └── database.py       # SQLite manager
│   ├── repositories/
│   │   └── sqlite_repository.py
│   ├── services/
│   │   ├── customer_service.py
│   │   ├── activity_service.py
│   │   ├── analytics_service.py
│   │   └── reminder_service.py
│   └── ui/
│       ├── style.py          # Theme and style manager
│       ├── pages/            # Page setup modules
│       ├── window_helpers.py
│       ├── file_manager.py
│       ├── date_picker.py
│       └── payment_history.py
├── data/                     # Runtime data (auto-created)
├── logs/                     # Application logs (auto-created)
├── backups/                  # Backup files (auto-created)
├── tests/                    # Unit tests
├── requirements.txt
├── pyproject.toml
└── CHANGELOG.md
```

## Configuration

Settings are stored in `data/settings.json` and can be modified through the Settings page in the application or by editing the file directly.

Key settings:
- **Theme**: dark, light, or system
- **Notification days**: configure reminder lead time
- **Backup interval**: automatic backup frequency
- **Auto-update**: enable/disable version checks

## Development

### Running Tests

```bash
python -m pytest tests/ -v
```

### Code Style

```bash
pip install ruff
ruff check app/ tests/
```

### Building Documentation

All documentation is in Markdown format in the project root.

## License

MIT — see [LICENSE](LICENSE) for details.

## Support

- Report issues: https://github.com/otman-22-git/Installments-Tracker/issues
- Source code: https://github.com/otman-22-git/Installments-Tracker

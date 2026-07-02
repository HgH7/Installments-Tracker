# Contributing

## Setup

```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

## Running Tests

```bash
pytest tests/ -v
pytest tests/ --cov=app --cov-report=term-missing
```

## Code Style

- Follow existing patterns (service layer → repository → UI)
- No bare `except:` — always catch specific exceptions
- All user-facing strings in messagebox calls
- Use ValidationService for input validation (no inline regex)
- Use AppLogger for logging (not print())
- Every write operation must use transactions

## Project Structure

```
The-Project.py       — Entry point (<300 lines)
app/
  database/          — SQLite schema, migration, models
  logging/           — Structured logging
  repositories/      — Data access (SQLite, CSV)
  services/          — Business logic
  ui/                — Presentation layer
    pages/           — Page setup functions
  utils/             — Utilities
  validation.py      — Centralized validation
  settings.py        — User preferences
  recovery.py        — Startup checks
  export.py          — Excel export
tests/               — Pytest test suite
```

## Commit Messages

Format: `type(scope): description`

Types: feat, fix, refactor, test, docs, chore

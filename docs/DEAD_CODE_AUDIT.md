# Dead Code Audit — Phase S (2026-07-03)

**Scope**: Evidence-based audit of Installments Tracker for dead code, unused files, orphaned dependencies, and safe-to-archive components. No deletions — classification only.

---

## 1. Repository Inventory

### 1.1 File Counts
- **Python source files** (`app/`): ~70
- **Test files** (`tests/`): ~25
- **Documentation** (`docs/`): 9 files
- **Data/Config**: ~10 files (`.db`, `.csv`, `.spec`, `pyproject.toml`, etc.)
- **Total tracked**: ~115 files

### 1.2 Dependency Audit

**Runtime (requirements.txt)**:
| Package | Size | Status |
|---|---|---|
| customtkinter | ~14 MB | Core UI dependency — REQUIRED |
| Pillow | ~8 MB | Image handling — REQUIRED |
| pandas | ~12 MB | Only used by `export_service.py` for Excel export — COULD BE OPTIONAL |
| pyinstaller | ~20 MB (install) | Build-time only — COULD BE MOVED TO optional deps |
| darkdetect | ~0.1 MB | Theme detection — REQUIRED |
| packaging | ~0.1 MB | Version parsing — REQUIRED |
| requests | ~2 MB | Telemetry (dead) + potential API use — REDUCIBLE |
| ttkbootstrap | ~5 MB | **UNUSED** — was imported once, never instantiated |
| tkcalendar | ~1 MB | **UNUSED** — no DateEntry/Dialog import found anywhere |
| pillow-heif | ~0.5 MB | **UNUSED** — HEIF plugin never imported |

**Build-time (pyproject.toml)**:
- pytest, pytest-cov — REQUIRED
- ruff — REQUIRED (linting)
- build, setuptools — REQUIRED (packaging)

### 1.3 Dead Top-Level Files
| File | Reason |
|---|---|
| `simple_build.bat` | Windows-only build script; developer uses macOS |
| `customers.csv` | Stale export; `test.csv` also present |
| `backups/` directory | Contains old DB snapshots; not referenced by code |
| `logs/` directory | Runtime logs; belongs in `.gitignore` |

---

## 2. Dead Functions & Methods

### 2.1 Never Called (0 references except definition)
| Location | Function/Method | Notes |
|---|---|---|
| `app/core/validation.py` | `validate_customer()` | Only used by REST API (Phase R) — was technically dead before Phase R; now alive |
| `app/utils/paths.py` | `get_export_path()`, `get_backup_path()` | Defined but never imported anywhere |
| `app/services/telemetry_service.py` | `TelemetryService.send_event()`, `TelemetryService.flush()` | Service never instantiated |
| `app/extensions/events/hooks.py` | `HookRegistry.register()`, `HookRegistry.trigger()` | Module never imported |
| `app/extensions/scripting/*` | `Sandbox.execute()`, `DeveloperConsole.*` | DeveloperConsole never instantiated; Sandbox only used by DeveloperConsole |
| `app/extensions/ocr/*` | `OCRProcessor.*` | Module never imported |
| `app/ui/components/modal_manager.py` | `ModalManager.*` | Never imported in any UI page |

### 2.2 Exception Silencers (except BaseException / except Exception: pass)
| Location | Line | Risk |
|---|---|---|
| `app/services/backup_service.py` | ~45 | `except Exception: pass` — silent failure on backup |
| `app/services/reminder_service.py` | ~120 | `except Exception: pass` — silent failure on reminder scheduling |
| `app/extensions/telemetry/telemetry_service.py` | ~30 | `except Exception: pass` — silent failure on telemetry send |

### 2.3 Redundant / Dead Parameters
| Location | Parameter | Status |
|---|---|---|
| `app/services/customer_service.py` | `search_customers(..., db_path=None)` | `db_path` never passed |
| `app/repositories/customer_repository.py` | `__init__(self, db_path)` | Always receives default |

---

## 3. Dead Classes

| Class | File | Status |
|---|---|---|
| `TelemetryService` | `app/extensions/telemetry/telemetry_service.py` | Never instantiated. Initialization call was removed. Safe to archive. |
| `ModalManager` | `app/ui/components/modal_manager.py` | Never imported by any UI page. |
| `EventBus` | `app/extensions/events/hooks.py` | HookRegistry defined but never imported. |
| `Guard`, `PermissionManager` | `app/extensions/auth/` | Module structure exists but never imported. |
| `PluginManager`, `PluginBase`, `PluginLoader` | `app/extensions/plugins/` | Initialized in The-Project.py but no plugins ever loaded. |
| `Sandbox`, `DeveloperConsole` | `app/extensions/scripting/` | DeveloperConsole never instantiated. Sandbox only internal. |
| `OCRProcessor` | `app/extensions/ocr/` | Prototype, never imported. |
| `ExportWorker` | `app/services/export_service.py` | Thread subclass defined but `threading.Thread` used directly instead. |

---

## 4. Dead UI Components

| Component | File | Status |
|---|---|---|
| `show_customer_view_bare()` | `app/ui/components/customer_view.py` | Not called anywhere (view page uses `show_customer_view()` wrapper). |
| `AdvancedSearchDialog` | (removed in earlier cleanup) | Was in `search_page.py` — deleted. |
| DevTools: `db_explorer`, `log_viewer`, `plugin_debugger`, `profiler` | `app/extensions/devtools/` | Never imported in production. Not wired in The-Project.py. |

---

## 5. Dead / Orphaned Services

| Service | File | Status |
|---|---|---|
| `telemetry_service.py` | `app/extensions/telemetry/` | Full file. Safe to archive entire directory. |
| `search_service.py` | (previously deleted) | Confirmed deleted. |
| `ai_service.py` | (previously deleted) | Confirmed deleted. |
| `custom_field_service.py` | (previously deleted) | Confirmed deleted. |

---

## 6. Dead Database / Storage Artifacts

| Artifact | Location | Status |
|---|---|---|
| `.db-shm`, `.db-wal` | Root | SQLite WAL leftovers; safe to delete when DB not in use. |
| `customers.csv` | Root | Stale export; not referenced. |
| `test.csv` | Root | Stale export; not referenced. |
| `backups/` | Root | Contains `installment_tracker_backup_*.db` files; manual backups, not code-managed. |
| `logs/` | Root | Runtime log files; should be in `.gitignore`. |

---

## 7. Dead Assets / Orphaned Directories

| Directory | Status |
|---|---|
| `stitch_installment_manager/` | Old standalone tool; unrelated Python project shipped in-tree. |
| `app/extensions/auth/` | Module scaffold: `__init__.py`, `guard.py`, `permissions.py`, `roles.py`. Unwired. |
| `app/extensions/plugins/` | Module: `__init__.py`, `plugin_base.py`, `plugin_loader.py`, `plugin_manager.py`. Never used. |
| `app/extensions/scripting/` | Module: `sandbox.py`, `developer_console.py`. Never wired. |
| `app/extensions/ocr/` | Module: 3 prototype files. Never imported. |
| `app/extensions/devtools/` | Module: 4 tools. Never imported in production. |

---

## 8. Dead / Outdated Documentation

| File | Status |
|---|---|
| `docs/CLEANUP_AUDIT.md` | Historical record of July 2 cleanup. Superseded by this audit. |
| `docs/CHANGELOG.md` | Maintained but duplicative of Phase docs in PROJECT_STATUS.md. |
| `docs/PROJECT_REFACTOR.md` | Roadmap document; planning content, not operational. |

---

## 9. Dead / Orphaned Imports

| File | Dead Import |
|---|---|
| `app/services/export_service.py` | `import pandas` — only dead import? (Actually used for Excel) |
| `app/extensions/api/rest_api.py` | `from app.services.activity_service import ActivityService` — checked, it IS used (Phase R) |
| `app/ui/pages/contracts_page.py` | Various unused CTk imports |
| Multiple files | Unused imports cleaned up in Phase M |

---

## 10. Dead Extension Modules

| Extension | Status | Recommendation |
|---|---|---|
| `app/extensions/auth/` | 4 files, fully scaffolded, never wired | SAFE TO ARCHIVE |
| `app/extensions/plugins/` | 5 files, initialized but no loaders | SAFE TO ARCHIVE |
| `app/extensions/scripting/` | 2 files, DeveloperConsole never created | SAFE TO ARCHIVE |
| `app/extensions/ocr/` | 3 files, prototype, never imported | SAFE TO ARCHIVE |
| `app/extensions/devtools/` | 4 files, never imported in production | SAFE TO ARCHIVE |
| `app/extensions/events/` | hooks.py + __init__.py, never imported | SAFE TO ARCHIVE |
| `app/extensions/telemetry/` | telemetry_service.py, initialization removed | SAFE TO ARCHIVE |
| `app/extensions/api/` | rest_api.py + __init__.py — **ACTIVELY USED** (Phase R) | KEEP |

---

## 11. Duplicate Code

| Pattern | Locations | Notes |
|---|---|---|
| `dict_factory` lambda | `app/database/connection.py`, `app/extensions/api/rest_api.py` | Inline lambda duplicated; could be shared constant |
| `row_factory = sqlite3.Row` | `app/repositories/*.py` (multiple) | Set in every repository __init__; could be centralized |
| Customer lookup SQL | `app/services/customer_notes_service.py` and `app/services/customer_tags_service.py` | Same `SELECT id, name FROM customers WHERE id = ?` pattern |
| Validation patterns | `app/core/validation.py` vs `app/extensions/api/rest_api.py` | ValidationService reused in Phase R, but some inline checks remain |

---

## 12. Legacy / Compatibility Shims

| Location | Pattern | Status |
|---|---|---|
| `app/data/migrations/` | Migration scripts | Historical; last migration is from Phase J. Keep for reference. |
| Root `customers.csv` | CSV export format | Pre-database legacy artifact. |
| `simple_build.bat` | Windows build script | No Windows CI/CD. Could be removed. |
| `data/` directory | Additional data folder | Not referenced by code (uses root-level DB). |

---

## 13. Final Classification Summary

### Safe to Archive (Delete from main branch, keep in git history)
| Component | Size Impact | Effort |
|---|---|---|
| `app/extensions/auth/` | 4 files, ~200 lines | Low |
| `app/extensions/plugins/` | 5 files, ~300 lines | Low |
| `app/extensions/scripting/` | 2 files, ~180 lines | Low |
| `app/extensions/ocr/` | 3 files, ~120 lines | Low |
| `app/extensions/devtools/` | 4 files, ~250 lines | Low |
| `app/extensions/events/` | 2 files, ~80 lines | Low |
| `app/extensions/telemetry/` | 1 file, ~60 lines | Low |
| `stitch_installment_manager/` | ~20 files, 2000+ lines | Medium (separate project) |
| `simple_build.bat` | 1 file | Trivial |
| `data/` directory | Empty/unused | Trivial |

### Keep But Monitor
| Component | Reason |
|---|---|
| `ttkbootstrap` in requirements | Listed but never imported in source — safe to remove from deps |
| `tkcalendar` in requirements | Listed but never imported — safe to remove |
| `pillow-heif` in requirements | Listed but never imported — safe to remove |
| `requests` in requirements | Only used by dead telemetry — could be removed if telemetry archived |
| `pandas` in requirements | Used by export_service.py for Excel export only — could make optional |

### Keep (Actively Used)
- All services under `app/services/` (customer, contract, document, task, finance, reminder, notes, tags, export, backup, activity, notification, global_search)
- All repositories under `app/repositories/`
- All UI under `app/ui/pages/`
- Database layer (`app/database/`, `app/data/`)
- Core (`app/core/`)
- Utils (`app/utils/`)
- REST API (`app/extensions/api/`)
- All tests
- `The-Project.py`, `pyproject.toml`

---

## 14. Recommended Actions (Priority Order)

1. **Archive dead extensions** (auth, plugins, scripting, ocr, devtools, events, telemetry) — move to `archive/` or delete
2. **Remove unused dependencies** from requirements.txt: `ttkbootstrap`, `tkcalendar`, `pillow-heif`
3. **Make pandas optional** — only needed for Excel export; guard import
4. **Gitignore** `logs/`, `*.db-shm`, `*.db-wal`, `backups/`, `__pycache__/`
5. **Delete stale artifacts**: `customers.csv`, `test.csv`, `simple_build.bat`, `data/`
6. **Remove `stitch_installment_manager/`** — unrelated project shipped in-tree
7. **Consolidate duplicate code**: `dict_factory` constant, centralized `row_factory` setting
8. **Fix exception silencers** in telemetry, backup, reminder services

---

*End of Phase S — Dead Code Audit. Evidence-based; no deletions performed.*

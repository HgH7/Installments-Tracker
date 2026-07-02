# Cleanup Audit — Session July 2, 2026

## Removed Features (4 pages + 3 services)

### Deleted Files (7)
| File | Reason |
|------|--------|
| `app/ui/pages/calendar_page.py` | Calendar view — removed |
| `app/ui/pages/ai_assistant.py` | AI Assistant — removed |
| `app/ui/pages/search_page.py` | Search page — removed |
| `app/ui/pages/custom_fields_page.py` | Custom Fields — removed |
| `app/services/ai_service.py` | Only consumed by ai_assistant page |
| `app/services/search_service.py` | Only consumed by search page |
| `app/services/custom_field_service.py` | Only consumed by custom_fields page |

### Edited Files (5)
**`The-Project.py`**
- Removed: 4 page imports, 3 service imports, 4 nav items, 3 service inits, `ai_service`/`search_service` from `_services` dict, 4 page names from `page_names`, 4 lazy imports, 4 setup calls
- Modified: `_add` setup call wraps `validate_and_save` with `show_frame(frames["manage"])` navigation on success

**`app/ui/pages/__init__.py`**
- Removed 4 imports for deleted pages

**`app/database/schema.py`**
- Removed `CREATE_AI_CONVERSATIONS` table constant
- Removed `CREATE_CUSTOM_FIELD_DEFS` and `CREATE_CUSTOM_FIELD_VALUES` table constants
- Removed 4 stale indexes from `V4_INDEXES` list
- Removed `CREATE_AI_CONVERSATIONS`, `CREATE_CUSTOM_FIELD_DEFS`, `CREATE_CUSTOM_FIELD_VALUES` from `V4_TABLES`

**`app/ui/pages/manage.py`**
- Added `frame.page_on_show = load_data` — auto-refreshes the installments tree whenever the page is shown

**`app/ui/pages/view.py`**
- Added `frame.page_on_show = lambda: refresh_treeview(frame.tree)` — auto-refreshes the customers tree whenever the page is shown

**`app/ui/pages/import_export.py`**
- Added tree refresh after `do_import()` completes

## Behavioral Changes
1. **Add Customer → auto-navigate to Installments tab**: After saving a new customer, the form resets (existing behavior) AND the app navigates to the Installments (manage) page with auto-refreshed data
2. **Auto-refresh on page visits**: Both the Customers (view) and Installments (manage) pages now refresh their data via `page_on_show` hook whenever they're navigated to
3. **Import page**: After importing data, the import page's tree is immediately refreshed; navigating to Customers/Installments pages will show fresh data

## Verification
- All 87 existing tests pass (PASSED)
- All modified files compile without syntax errors
- Zero dead imports, dead methods, or dangling references remain

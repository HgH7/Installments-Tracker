SCHEMA_VERSION = 5

# ── Existing tables (v1/v2/v3) ──────────────────────────────────────────────

CREATE_CUSTOMERS = """
CREATE TABLE IF NOT EXISTS customers (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name     TEXT    NOT NULL,
    phone_number      TEXT    NOT NULL DEFAULT '',
    total_amount      REAL   NOT NULL DEFAULT 0,
    installment_count INTEGER NOT NULL DEFAULT 0,
    start_date        TEXT    NOT NULL DEFAULT '',
    notes             TEXT    DEFAULT '',
    created_at        TEXT    NOT NULL,
    updated_at        TEXT    NOT NULL
);
"""

CREATE_INSTALLMENTS = """
CREATE TABLE IF NOT EXISTS installments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id         INTEGER NOT NULL,
    installment_number  INTEGER NOT NULL,
    due_date            TEXT    NOT NULL,
    amount              REAL    NOT NULL DEFAULT 0,
    status              TEXT    NOT NULL DEFAULT 'pending',
    notified            INTEGER NOT NULL DEFAULT 0,
    paid_date           TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
"""

CREATE_ATTACHMENTS = """
CREATE TABLE IF NOT EXISTS attachments (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id       INTEGER NOT NULL,
    file_name         TEXT    NOT NULL,
    original_path     TEXT    NOT NULL DEFAULT '',
    stored_path       TEXT    NOT NULL DEFAULT '',
    created_at        TEXT    NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
"""

CREATE_BACKUPS = """
CREATE TABLE IF NOT EXISTS backups (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name   TEXT    NOT NULL,
    file_size   INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL
);
"""

CREATE_ACTIVITY_LOG = """
CREATE TABLE IF NOT EXISTS activity_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    action      TEXT    NOT NULL,
    detail      TEXT    DEFAULT '',
    created_at  TEXT    NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);
"""

CREATE_REMINDER_HISTORY = """
CREATE TABLE IF NOT EXISTS reminder_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL,
    customer_name   TEXT    NOT NULL,
    phone           TEXT    NOT NULL DEFAULT '',
    installment_date TEXT   NOT NULL DEFAULT '',
    amount          REAL    NOT NULL DEFAULT 0,
    message         TEXT    DEFAULT '',
    status          TEXT    NOT NULL DEFAULT 'draft',
    sent_at         TEXT,
    created_at      TEXT    NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
"""

# ── MODULE 1: Financial Management ────────────────────────────────────────

CREATE_EXPENSES = """
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL DEFAULT 'other',
    description TEXT    DEFAULT '',
    expense_date TEXT   NOT NULL,
    created_at  TEXT    NOT NULL
);
"""

CREATE_FINANCIAL_METRICS = """
CREATE TABLE IF NOT EXISTS financial_metrics (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type  TEXT    NOT NULL,
    metric_value REAL    NOT NULL,
    period_start TEXT    NOT NULL,
    period_end   TEXT    NOT NULL,
    created_at   TEXT    NOT NULL
);
"""

# ── MODULE 2: Contract Management ─────────────────────────────────────────

CREATE_CONTRACT_TEMPLATES = """
CREATE TABLE IF NOT EXISTS contract_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    content     TEXT    NOT NULL DEFAULT '',
    fields_json TEXT    DEFAULT '[]',
    is_default  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);
"""

CREATE_CONTRACTS = """
CREATE TABLE IF NOT EXISTS contracts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL,
    contract_number TEXT    NOT NULL UNIQUE,
    template_id     INTEGER,
    status          TEXT    NOT NULL DEFAULT 'draft',
    content_json    TEXT    DEFAULT '{}',
    pdf_path        TEXT    DEFAULT '',
    signed_date     TEXT,
    notes           TEXT    DEFAULT '',
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES contract_templates(id) ON DELETE SET NULL
);
"""

# ── MODULE 3: Customer Experience ─────────────────────────────────────────

CREATE_CUSTOMER_NOTES = """
CREATE TABLE IF NOT EXISTS customer_notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    content     TEXT    NOT NULL,
    category    TEXT    DEFAULT 'general',
    is_pinned   INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
"""

CREATE_CUSTOMER_TAGS = """
CREATE TABLE IF NOT EXISTS customer_tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    tag         TEXT    NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
"""

# ── MODULE 4: Productivity ─────────────────────────────────────────────────

CREATE_TASKS = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    title       TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    due_date    TEXT,
    status      TEXT    NOT NULL DEFAULT 'pending',
    priority    TEXT    NOT NULL DEFAULT 'medium',
    task_type   TEXT    DEFAULT 'general',
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);
"""

# ── MODULE 7: OCR ──────────────────────────────────────────────────────────

CREATE_OCR_DOCUMENTS = """
CREATE TABLE IF NOT EXISTS ocr_documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER,
    file_path       TEXT    NOT NULL,
    ocr_text        TEXT    DEFAULT '',
    extracted_data_json TEXT DEFAULT '{}',
    status          TEXT    NOT NULL DEFAULT 'pending',
    created_at      TEXT    NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);
"""

# ── MODULE 8: Document Generator ──────────────────────────────────────────

CREATE_DOCUMENTS = """
CREATE TABLE IF NOT EXISTS generated_documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER,
    document_type   TEXT    NOT NULL,
    title           TEXT    NOT NULL,
    file_path       TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);
"""

# ── Phase 8: Performance Indexes ─────────────────────────────────────────

V5_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_customers_created ON customers(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_installments_paid_date ON installments(paid_date);",
    "CREATE INDEX IF NOT EXISTS idx_backups_created ON backups(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_activity_log_action_created ON activity_log(action, created_at);",
    "CREATE INDEX IF NOT EXISTS idx_installments_customer_status ON installments(customer_id, status);",
    "CREATE INDEX IF NOT EXISTS idx_customers_name_phone ON customers(customer_name, phone_number);",
]

V5_TABLES = [
    "CREATE TABLE IF NOT EXISTS search_history ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  query TEXT NOT NULL,"
    "  result_count INTEGER DEFAULT 0,"
    "  created_at TEXT NOT NULL"
    ");",
    "CREATE TABLE IF NOT EXISTS saved_searches ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  name TEXT NOT NULL,"
    "  query TEXT NOT NULL,"
    "  entity_type TEXT DEFAULT '',"
    "  created_at TEXT NOT NULL"
    ");",
    "CREATE TABLE IF NOT EXISTS telemetry_events ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  category TEXT NOT NULL,"
    "  data_json TEXT DEFAULT '{}',"
    "  created_at TEXT NOT NULL"
    ");",
    "CREATE TABLE IF NOT EXISTS plugin_registry ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  plugin_id TEXT NOT NULL UNIQUE,"
    "  name TEXT NOT NULL,"
    "  version TEXT NOT NULL,"
    "  enabled INTEGER NOT NULL DEFAULT 1,"
    "  installed_at TEXT NOT NULL"
    ");",
    "CREATE TABLE IF NOT EXISTS automation_rules ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  name TEXT NOT NULL,"
    "  event TEXT NOT NULL,"
    "  conditions_json TEXT DEFAULT '[]',"
    "  actions_json TEXT DEFAULT '[]',"
    "  enabled INTEGER NOT NULL DEFAULT 1,"
    "  created_at TEXT NOT NULL,"
    "  updated_at TEXT NOT NULL"
    ");",
    "CREATE TABLE IF NOT EXISTS automation_workflows ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  name TEXT NOT NULL,"
    "  trigger_event TEXT NOT NULL,"
    "  steps_json TEXT DEFAULT '[]',"
    "  enabled INTEGER NOT NULL DEFAULT 1,"
    "  created_at TEXT NOT NULL"
    ");",
    "CREATE TABLE IF NOT EXISTS api_keys ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  name TEXT NOT NULL,"
    "  key TEXT NOT NULL UNIQUE,"
    "  role TEXT NOT NULL DEFAULT 'readonly',"
    "  enabled INTEGER NOT NULL DEFAULT 1,"
    "  created_at TEXT NOT NULL"
    ");",
]

V4_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);",
    "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);",
    "CREATE INDEX IF NOT EXISTS idx_financial_metrics_type ON financial_metrics(metric_type);",
    "CREATE INDEX IF NOT EXISTS idx_contracts_customer ON contracts(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_contracts_number ON contracts(contract_number);",
    "CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);",
    "CREATE INDEX IF NOT EXISTS idx_customer_notes_customer ON customer_notes(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_customer_tags_customer ON customer_tags(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_customer_tags_tag ON customer_tags(tag);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_customer ON tasks(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);",
    "CREATE INDEX IF NOT EXISTS idx_ocr_documents_customer ON ocr_documents(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_ocr_documents_status ON ocr_documents(status);",
    "CREATE INDEX IF NOT EXISTS idx_generated_docs_customer ON generated_documents(customer_id);",

]

EXISTING_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_customers_customer_name ON customers(customer_name);",
    "CREATE INDEX IF NOT EXISTS idx_customers_phone_number ON customers(phone_number);",
    "CREATE INDEX IF NOT EXISTS idx_installments_customer_id ON installments(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_installments_due_date ON installments(due_date);",
    "CREATE INDEX IF NOT EXISTS idx_installments_status ON installments(status);",
    "CREATE INDEX IF NOT EXISTS idx_attachments_customer_id ON attachments(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_activity_log_customer_id ON activity_log(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON activity_log(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_activity_log_action ON activity_log(action);",
    "CREATE INDEX IF NOT EXISTS idx_reminder_history_customer_id ON reminder_history(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_reminder_history_status ON reminder_history(status);",
]

V4_TABLES = [
    CREATE_EXPENSES,
    CREATE_FINANCIAL_METRICS,
    CREATE_CONTRACT_TEMPLATES,
    CREATE_CONTRACTS,
    CREATE_CUSTOMER_NOTES,
    CREATE_CUSTOMER_TAGS,
    CREATE_TASKS,
    CREATE_OCR_DOCUMENTS,
    CREATE_DOCUMENTS,
]

ALL_TABLES = [
    CREATE_CUSTOMERS,
    CREATE_INSTALLMENTS,
    CREATE_ATTACHMENTS,
    CREATE_BACKUPS,
    CREATE_ACTIVITY_LOG,
    CREATE_REMINDER_HISTORY,
] + V4_TABLES + V5_TABLES

SCHEMA_TABLE = """
CREATE TABLE IF NOT EXISTS _schema_version (
    version INTEGER NOT NULL,
    applied_at TEXT NOT NULL
);
"""

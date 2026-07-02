from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── Existing models ────────────────────────────────────────────────────────


@dataclass
class Customer:
    id: Optional[int] = None
    customer_name: str = ""
    phone_number: str = ""
    total_amount: float = 0.0
    installment_count: int = 0
    start_date: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()
        if not self.updated_at:
            self.updated_at = _now()


@dataclass
class Installment:
    id: Optional[int] = None
    customer_id: int = 0
    installment_number: int = 0
    due_date: str = ""
    amount: float = 0.0
    status: str = "pending"
    notified: int = 0
    paid_date: Optional[str] = None


@dataclass
class Attachment:
    id: Optional[int] = None
    customer_id: int = 0
    file_name: str = ""
    original_path: str = ""
    stored_path: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()


@dataclass
class Backup:
    id: Optional[int] = None
    file_name: str = ""
    file_size: int = 0
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()


# ── MODULE 1: Financial Management ─────────────────────────────────────────


@dataclass
class Expense:
    id: Optional[int] = None
    amount: float = 0.0
    category: str = "other"
    description: str = ""
    expense_date: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()


@dataclass
class FinancialMetric:
    id: Optional[int] = None
    metric_type: str = ""
    metric_value: float = 0.0
    period_start: str = ""
    period_end: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()


# ── MODULE 2: Contract Management ─────────────────────────────────────────


@dataclass
class ContractTemplate:
    id: Optional[int] = None
    name: str = ""
    content: str = ""
    fields_json: str = "[]"
    is_default: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()
        if not self.updated_at:
            self.updated_at = _now()


@dataclass
class Contract:
    id: Optional[int] = None
    customer_id: int = 0
    contract_number: str = ""
    template_id: Optional[int] = None
    status: str = "draft"
    content_json: str = "{}"
    pdf_path: str = ""
    signed_date: Optional[str] = None
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()
        if not self.updated_at:
            self.updated_at = _now()


# ── MODULE 3: Customer Experience ──────────────────────────────────────────


@dataclass
class CustomerNote:
    id: Optional[int] = None
    customer_id: int = 0
    content: str = ""
    category: str = "general"
    is_pinned: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()
        if not self.updated_at:
            self.updated_at = _now()


@dataclass
class CustomerTag:
    id: Optional[int] = None
    customer_id: int = 0
    tag: str = ""


# ── MODULE 4: Productivity ─────────────────────────────────────────────────


@dataclass
class Task:
    id: Optional[int] = None
    customer_id: Optional[int] = None
    title: str = ""
    description: str = ""
    due_date: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    task_type: str = "general"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()
        if not self.updated_at:
            self.updated_at = _now()


# ── MODULE 6: AI Assistant ─────────────────────────────────────────────────


@dataclass
class AIConversation:
    id: Optional[int] = None
    session_id: str = ""
    role: str = ""
    content: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()


# ── MODULE 7: OCR ──────────────────────────────────────────────────────────


@dataclass
class OCRDocument:
    id: Optional[int] = None
    customer_id: Optional[int] = None
    file_path: str = ""
    ocr_text: str = ""
    extracted_data_json: str = "{}"
    status: str = "pending"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()


# ── MODULE 8: Document Generator ───────────────────────────────────────────


@dataclass
class GeneratedDocument:
    id: Optional[int] = None
    customer_id: Optional[int] = None
    document_type: str = ""
    title: str = ""
    file_path: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()


# ── MODULE 10: Custom Fields ───────────────────────────────────────────────


@dataclass
class CustomFieldDefinition:
    id: Optional[int] = None
    entity_type: str = ""
    field_name: str = ""
    field_type: str = "text"
    is_required: int = 0
    options_json: str = "[]"
    sort_order: int = 0
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _now()


@dataclass
class CustomFieldValue:
    id: Optional[int] = None
    field_definition_id: int = 0
    entity_id: int = 0
    value: str = ""

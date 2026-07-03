"""Unified search across all entity types, delegating to existing service methods."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GlobalSearchService:
    def __init__(self, customer_service=None, contract_service=None,
                 document_service=None, task_service=None,
                 finance_service=None, reminder_service=None,
                 notes_service=None):
        self.customer_service = customer_service
        self.contract_service = contract_service
        self.document_service = document_service
        self.task_service = task_service
        self.finance_service = finance_service
        self.reminder_service = reminder_service
        self.notes_service = notes_service

    def search(self, query: str, category: Optional[str] = None) -> List[Dict]:
        if not query or not query.strip():
            return []
        q = query.strip().lower()
        results = []

        categories = ["customers", "contracts", "documents", "tasks", "expenses", "reminders", "notes"]
        if category and category != "all":
            categories = [c for c in categories if c == category]

        for cat in categories:
            method = getattr(self, f"_search_{cat}", None)
            if method:
                try:
                    results.extend(method(q, query.strip()))
                except Exception:
                    logger.exception("Global search error in category '%s'", cat)

        results.sort(key=lambda r: r.get("date", ""), reverse=True)
        return results

    def _search_customers(self, q: str, raw: str) -> List[Dict]:
        if not self.customer_service:
            return []
        customers = self.customer_service.get_all_customers()
        matched = []
        for c in customers:
            if any(str(v).lower().find(q) != -1 for v in c.values()):
                matched.append({
                    "type": "customer",
                    "id": str(c.get("Name", "")),
                    "title": c.get("Name", ""),
                    "customer_name": c.get("Name", ""),
                    "status": "",
                    "date": c.get("Start Date", ""),
                    "detail": f"Phone: {c.get('Phone', '')} | Amount: {c.get('Amount', 0)}",
                })
        return matched

    def _search_contracts(self, q: str, raw: str) -> List[Dict]:
        if not self.contract_service:
            return []
        contracts = self.contract_service.find_contract(query=raw)
        results = []
        for c in contracts:
            results.append({
                "type": "contract",
                "id": c.get("id"),
                "title": f"{c.get('contract_number', '')} — {c.get('customer_name', '')}",
                "customer_name": c.get("customer_name", ""),
                "status": c.get("status", ""),
                "date": (c.get("created_at") or "")[:10],
                "detail": f"Number: {c.get('contract_number', '')} | Status: {c.get('status', '')}",
            })
        return results

    def _search_documents(self, q: str, raw: str) -> List[Dict]:
        if not self.document_service:
            return []
        documents = self.document_service.get_documents()
        results = []
        for d in documents:
            title = (d.get("title") or "").lower()
            doc_type = (d.get("document_type") or "").lower()
            customer_name = self.document_service.get_customer_name_for_doc(d.get("customer_id") or 0)
            customer_match = customer_name.lower().find(q) != -1
            if title.find(q) == -1 and doc_type.find(q) == -1 and not customer_match:
                continue
            results.append({
                "type": "document",
                "id": d.get("id"),
                "title": d.get("title", ""),
                "customer_name": customer_name,
                "status": d.get("document_type", ""),
                "date": (d.get("created_at") or "")[:10],
                "detail": f"Type: {d.get('document_type', '')}",
            })
        return results

    def _search_tasks(self, q: str, raw: str) -> List[Dict]:
        if not self.task_service:
            return []
        tasks = self.task_service.get_tasks()
        results = []
        for t in tasks:
            title = (t.get("title") or "").lower()
            desc = (t.get("description") or "").lower()
            customer = (t.get("customer_name") or "").lower()
            if title.find(q) == -1 and desc.find(q) == -1 and customer.find(q) == -1:
                continue
            results.append({
                "type": "task",
                "id": t.get("id"),
                "title": t.get("title", ""),
                "customer_name": t.get("customer_name", ""),
                "status": t.get("status", ""),
                "date": (t.get("due_date") or "")[:10],
                "detail": f"Priority: {t.get('priority', '')} | Type: {t.get('task_type', '')}",
            })
        return results

    def _search_expenses(self, q: str, raw: str) -> List[Dict]:
        if not self.finance_service:
            return []
        expenses = self.finance_service.get_expenses()
        results = []
        for e in expenses:
            cat = (e.get("category") or "").lower()
            desc = (e.get("description") or "").lower()
            if cat.find(q) == -1 and desc.find(q) == -1:
                continue
            results.append({
                "type": "expense",
                "id": e.get("id"),
                "title": f"{e.get('category', '')} — {e.get('description', '')[:50]}",
                "customer_name": "",
                "status": e.get("category", ""),
                "date": e.get("expense_date", ""),
                "detail": f"Amount: {e.get('amount', 0):.2f}",
            })
        return results

    def _search_reminders(self, q: str, raw: str) -> List[Dict]:
        if not self.reminder_service:
            return []
        seen = set()
        results = []
        for search_kwargs in [{"customer_name": raw}, {"phone": raw}]:
            reminders = self.reminder_service.search_reminders(**search_kwargs)
            for r in reminders:
                rid = r.get("id")
                if rid in seen:
                    continue
                seen.add(rid)
                results.append({
                    "type": "reminder",
                    "id": rid,
                    "title": f"Reminder for {r.get('customer_name', '')}",
                    "customer_name": r.get("customer_name", ""),
                    "status": r.get("status", ""),
                    "date": r.get("installment_date", ""),
                    "detail": f"Phone: {r.get('phone', '')} | Amount: {r.get('amount', 0):.2f}",
                })
        results.sort(key=lambda r: r.get("date", "") or "", reverse=True)
        return results

    def _search_notes(self, q: str, raw: str) -> List[Dict]:
        if not self.notes_service:
            return []
        notes = self.notes_service.search_notes(raw)
        results = []
        for n in notes:
            results.append({
                "type": "note",
                "id": n.get("id"),
                "title": (n.get("content") or "")[:80],
                "customer_name": n.get("customer_name", ""),
                "status": n.get("category", ""),
                "date": (n.get("created_at") or "")[:10],
                "detail": f"Customer: {n.get('customer_name', '')} | Category: {n.get('category', '')}",
            })
        return results

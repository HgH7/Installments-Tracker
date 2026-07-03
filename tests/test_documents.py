import os
import tempfile

from app.database.database import DatabaseManager
from app.services.document_service import DocumentService


def _setup_db(db_path):
    db = DatabaseManager(db_path)
    db.initialize()
    conn = db.connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
        ("Alice", "+971500000000", 1000.0, 1, "2026-01-01", ""),
    )
    cid = cur.lastrowid
    cur.execute(
        "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
        ("Bob", "+971500000001", 2000.0, 2, "2026-02-01", ""),
    )
    bob_id = cur.lastrowid
    conn.commit()
    return db, cid, bob_id


def _insert_doc(conn, customer_id, doc_type="receipt", title="TestDoc", file_path="/tmp/test.pdf", created_at="2026-06-01"):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO generated_documents (customer_id, document_type, title, file_path, created_at) VALUES (?, ?, ?, ?, ?)",
        (customer_id, doc_type, title, file_path, created_at),
    )
    conn.commit()
    return cur.lastrowid


class TestDocumentService:
    def test_get_documents_empty(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = DocumentService(db)
            assert service.get_documents() == []
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_document_by_id(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            conn = db.connect()
            doc_id = _insert_doc(conn, cid)
            service = DocumentService(db)
            doc = service.get_document(doc_id)
            assert doc is not None
            assert doc["id"] == doc_id
            assert doc["customer_id"] == cid
            assert doc["document_type"] == "receipt"
            assert doc["title"] == "TestDoc"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_document_not_found(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = DocumentService(db)
            assert service.get_document(999) is None
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_documents_filters_by_customer_id(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, alice_id, bob_id = _setup_db(tmp.name)
            conn = db.connect()
            _insert_doc(conn, alice_id)
            _insert_doc(conn, bob_id, doc_type="invoice", title="BobInvoice")
            service = DocumentService(db)
            alice_docs = service.get_documents(customer_id=alice_id)
            assert len(alice_docs) == 1
            assert alice_docs[0]["customer_id"] == alice_id
            bob_docs = service.get_documents(customer_id=bob_id)
            assert len(bob_docs) == 1
            assert bob_docs[0]["customer_id"] == bob_id
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_documents_filters_by_doc_type(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            conn = db.connect()
            _insert_doc(conn, cid, doc_type="receipt", title="Receipt1")
            _insert_doc(conn, cid, doc_type="invoice", title="Invoice1")
            _insert_doc(conn, cid, doc_type="receipt", title="Receipt2")
            service = DocumentService(db)
            receipts = service.get_documents(doc_type="receipt")
            assert len(receipts) == 2
            invoices = service.get_documents(doc_type="invoice")
            assert len(invoices) == 1
            statements = service.get_documents(doc_type="statement")
            assert len(statements) == 0
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_documents_combined_filters(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, alice_id, bob_id = _setup_db(tmp.name)
            conn = db.connect()
            _insert_doc(conn, alice_id, doc_type="receipt", title="AliceReceipt")
            _insert_doc(conn, bob_id, doc_type="receipt", title="BobReceipt")
            _insert_doc(conn, alice_id, doc_type="invoice", title="AliceInvoice")
            service = DocumentService(db)
            result = service.get_documents(customer_id=alice_id, doc_type="receipt")
            assert len(result) == 1
            assert result[0]["title"] == "AliceReceipt"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_delete_document_existing(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            conn = db.connect()
            doc_id = _insert_doc(conn, cid)
            service = DocumentService(db)
            assert service.get_document(doc_id) is not None
            assert service.delete_document(doc_id) is True
            assert service.get_document(doc_id) is None
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_delete_document_non_existing(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = DocumentService(db)
            assert service.delete_document(999) is False
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_customer_name_for_doc_valid(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = DocumentService(db)
            name = service.get_customer_name_for_doc(cid)
            assert name == "Alice"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_customer_name_for_doc_invalid(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = DocumentService(db)
            name = service.get_customer_name_for_doc(999)
            assert name == "ID:999"
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_customer_id_by_name_valid(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            service = DocumentService(db)
            found = service.get_customer_id_by_name("Alice")
            assert found == cid
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_get_customer_id_by_name_not_found(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db = DatabaseManager(tmp.name)
            db.initialize()
            service = DocumentService(db)
            assert service.get_customer_id_by_name("NonExistent") is None
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_documents_ordered_by_created_at_desc(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            db, cid, _ = _setup_db(tmp.name)
            conn = db.connect()
            _insert_doc(conn, cid, created_at="2026-01-01")
            _insert_doc(conn, cid, created_at="2026-06-01")
            _insert_doc(conn, cid, created_at="2026-03-01")
            service = DocumentService(db)
            docs = service.get_documents()
            dates = [d["created_at"][:10] for d in docs]
            assert dates == ["2026-06-01", "2026-03-01", "2026-01-01"]
        finally:
            db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

import os
import shutil
import tempfile

import pytest

from app.database.database import DatabaseManager
from app.services.customer_notes_service import CustomerNotesService, CustomerTagsService


def _make_db(tmpdir):
    db_path = os.path.join(tmpdir, "installment_tracker.db")
    db = DatabaseManager(db_path)
    db.initialize()
    with db.transaction() as cur:
        cur.execute(
            "INSERT INTO customers (customer_name, phone_number, total_amount, installment_count, start_date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("Alice", "+971500000000", 1000.0, 1, "2026-01-01", "", "2026-01-01", "2026-01-01"),
        )
        customer_id = cur.lastrowid
    return db, customer_id


def test_notes_and_tags_round_trip():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db, customer_id = _make_db(tmpdir)
        notes_service = CustomerNotesService(db)
        tags_service = CustomerTagsService(db)

        note_id = notes_service.add_note(customer_id, "Follow up on payment", "follow-up")
        assert note_id > 0

        notes = notes_service.get_notes(customer_id)
        assert len(notes) == 1
        assert notes[0]["content"] == "Follow up on payment"
        assert notes[0]["category"] == "follow-up"

        assert notes_service.toggle_pin(note_id)
        assert notes_service.get_notes(customer_id)[0]["is_pinned"] == 1

        assert notes_service.update_note(note_id, content="Updated follow-up", category="payment")
        updated_notes = notes_service.get_notes(customer_id)
        assert updated_notes[0]["content"] == "Updated follow-up"
        assert updated_notes[0]["category"] == "payment"

        tag_id = tags_service.add_tag(customer_id, " VIP ")
        assert tag_id > 0
        assert tags_service.get_tags(customer_id) == ["vip"]
        assert tags_service.remove_tag(customer_id, "vip")
        assert tags_service.get_tags(customer_id) == []

        assert notes_service.delete_note(note_id)
        assert notes_service.get_notes(customer_id) == []
    finally:
        shutil.rmtree(tmpdir)


def test_search_notes_empty_db():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db_path = os.path.join(tmpdir, "installment_tracker.db")
        db = DatabaseManager(db_path)
        db.initialize()
        notes_service = CustomerNotesService(db)
        assert notes_service.search_notes("test") == []
    finally:
        shutil.rmtree(tmpdir)


def test_search_notes_finds_content():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db, customer_id = _make_db(tmpdir)
        notes_service = CustomerNotesService(db)
        notes_service.add_note(customer_id, "Follow up on payment", "follow-up")
        notes_service.add_note(customer_id, "Call about contract renewal", "call")

        results = notes_service.search_notes("Follow")
        assert len(results) == 1
        assert results[0]["content"] == "Follow up on payment"

        results = notes_service.search_notes("contract")
        assert len(results) == 1
        assert results[0]["content"] == "Call about contract renewal"
    finally:
        shutil.rmtree(tmpdir)


def test_search_notes_no_match():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db, customer_id = _make_db(tmpdir)
        notes_service = CustomerNotesService(db)
        notes_service.add_note(customer_id, "General note", "general")
        results = notes_service.search_notes("NonexistentWordXYZ")
        assert results == []
    finally:
        shutil.rmtree(tmpdir)


def test_search_notes_empty_query_returns_all():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db, customer_id = _make_db(tmpdir)
        notes_service = CustomerNotesService(db)
        notes_service.add_note(customer_id, "Note one", "general")
        notes_service.add_note(customer_id, "Note two", "follow-up")
        results = notes_service.search_notes("")
        assert len(results) == 2
    finally:
        shutil.rmtree(tmpdir)


def test_get_notes_nonexistent_customer():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db, _ = _make_db(tmpdir)
        notes_service = CustomerNotesService(db)
        assert notes_service.get_notes(99999) == []
    finally:
        shutil.rmtree(tmpdir)


def test_add_note_invalid_customer():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db_path = os.path.join(tmpdir, "installment_tracker.db")
        db = DatabaseManager(db_path)
        db.initialize()
        notes_service = CustomerNotesService(db)
        with pytest.raises(Exception):
            notes_service.add_note(-1, "test")
    finally:
        shutil.rmtree(tmpdir)


def test_update_note_invalid_id():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db, _ = _make_db(tmpdir)
        notes_service = CustomerNotesService(db)
        assert not notes_service.update_note(99999, content="updated")
    finally:
        shutil.rmtree(tmpdir)


def test_delete_note_invalid_id():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db, _ = _make_db(tmpdir)
        notes_service = CustomerNotesService(db)
        assert not notes_service.delete_note(99999)
    finally:
        shutil.rmtree(tmpdir)


def test_toggle_pin_invalid_id():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db, _ = _make_db(tmpdir)
        notes_service = CustomerNotesService(db)
        assert not notes_service.toggle_pin(99999)
    finally:
        shutil.rmtree(tmpdir)


def test_multiple_notes_per_customer():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db, customer_id = _make_db(tmpdir)
        notes_service = CustomerNotesService(db)
        id1 = notes_service.add_note(customer_id, "First", "general")
        id2 = notes_service.add_note(customer_id, "Second", "follow-up")
        id3 = notes_service.add_note(customer_id, "Third", "payment")
        assert id1 and id2 and id3
        notes = notes_service.get_notes(customer_id)
        assert len(notes) == 3
    finally:
        shutil.rmtree(tmpdir)


def test_get_customers_by_tag():
    tmpdir = tempfile.mkdtemp(prefix="notes_test_")
    try:
        db, customer_id = _make_db(tmpdir)
        tags_service = CustomerTagsService(db)
        tags_service.add_tag(customer_id, "important")
        customers = tags_service.get_customers_by_tag("important")
        assert any(c["id"] == customer_id for c in customers)
        customers = tags_service.get_customers_by_tag("nonexistent")
        assert customers == []
    finally:
        shutil.rmtree(tmpdir)

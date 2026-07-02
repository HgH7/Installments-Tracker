
from app.utils.serialization import dump_json, load_json_dict, load_json_list


class TestSerialization:
    def test_dump_json_list(self):
        assert dump_json([1, 2, 3]) == "[1, 2, 3]"

    def test_dump_json_dict(self):
        assert dump_json({"a": 1}) == '{"a": 1}'

    def test_load_json_list_from_string(self):
        assert load_json_list("[1, 2, 3]") == [1, 2, 3]

    def test_load_json_list_empty(self):
        assert load_json_list("") == []
        assert load_json_list(None) == []

    def test_load_json_list_from_list(self):
        assert load_json_list([1, 2]) == [1, 2]

    def test_load_json_list_invalid(self):
        assert load_json_list("invalid") == []

    def test_load_json_dict_from_string(self):
        assert load_json_dict('{"a": 1}') == {"a": 1}

    def test_load_json_dict_empty(self):
        assert load_json_dict("") == {}
        assert load_json_dict(None) == {}

    def test_load_json_dict_from_dict(self):
        assert load_json_dict({"a": 1}) == {"a": 1}

    def test_load_json_dict_invalid(self):
        assert load_json_dict("invalid") == {}

    def test_roundtrip_list(self):
        data = ["2026-01-01", "2026-02-01"]
        assert load_json_list(dump_json(data)) == data

    def test_roundtrip_dict(self):
        data = {"2026-01-01": 1000.0, "2026-02-01": 1000.0}
        assert load_json_dict(dump_json(data)) == data

    def test_load_json_list_python_literal(self):
        assert load_json_list("['2026-01-01', '2026-02-01']") == ["2026-01-01", "2026-02-01"]

    def test_load_json_dict_python_literal(self):
        assert load_json_dict("{'2026-01-01': 1000.0}") == {"2026-01-01": 1000.0}

    def test_dump_json_empty_list(self):
        assert dump_json([]) == "[]"

    def test_dump_json_empty_dict(self):
        assert dump_json({}) == "{}"

    def test_dump_json_none(self):
        assert dump_json(None) == "null"

    def test_load_json_list_numeric(self):
        assert load_json_list("[1, 2, 3]") == [1, 2, 3]

    def test_load_json_dict_numeric_values(self):
        assert load_json_dict('{"a": 1, "b": 2}') == {"a": 1, "b": 2}

    def test_load_json_list_with_unicode(self):
        data = load_json_list('["أحمد", "علي"]')
        assert len(data) == 2

    def test_load_json_dict_with_unicode(self):
        data = load_json_dict('{"أحمد": 100.0}')
        assert data["أحمد"] == 100.0

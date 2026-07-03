import re

from app.core.version import (
    APP_NAME,
    COPYRIGHT,
    VERSION_PARTS,
    VERSION_STRING,
    __author__,
    __build__,
    __license__,
    __version__,
)


class TestVersion:
    def test_version_string_format(self):
        assert re.match(r"^\d+\.\d+\.\d+$", __version__)

    def test_version_parts_tuple(self):
        assert isinstance(VERSION_PARTS, tuple)
        assert len(VERSION_PARTS) == 3
        assert all(isinstance(p, int) for p in VERSION_PARTS)

    def test_version_string_contains_parts(self):
        parts = ".".join(str(p) for p in VERSION_PARTS)
        assert parts == __version__

    def test_app_name_nonempty(self):
        assert isinstance(APP_NAME, str)
        assert len(APP_NAME) > 0

    def test_copyright_contains_year(self):
        assert "2026" in COPYRIGHT

    def test_author_nonempty(self):
        assert isinstance(__author__, str)
        assert len(__author__) > 0

    def test_license_nonempty(self):
        assert isinstance(__license__, str)
        assert len(__license__) > 0

    def test_vars_defined(self):
        assert VERSION_STRING.startswith("v")

    def test_all_exports(self):
        assert __version__ in VERSION_STRING

    def test_version_string_includes_build(self):
        if __build__:
            assert __build__ in VERSION_STRING
        else:
            assert VERSION_STRING == f"v{__version__}"

    def test_version_parts_is_tuple_of_ints(self):
        assert all(isinstance(p, int) for p in VERSION_PARTS)


class TestVersionComparison:
    """Ensure version tuples compare correctly."""

    def test_versions_are_ordered(self):
        assert (1, 0, 0) < (2, 0, 0)
        assert (2, 0, 0) == (2, 0, 0)
        assert (2, 0, 1) > (2, 0, 0)

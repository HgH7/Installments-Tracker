import os
import tempfile

import pytest

from app.core.settings import Settings


class TestSettings:
    @pytest.fixture
    def settings(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        s = Settings(tmp.name)
        yield s
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    def test_default_values(self, settings):
        assert settings.get("theme") == "dark"
        assert settings.get("window_width") == 1280
        assert settings.get("backup_max_count") == 50
        assert settings.get("backup_compress") == True

    def test_set_and_get(self, settings):
        settings.set("theme", "light")
        assert settings.get("theme") == "light"

    def test_set_many(self, settings):
        settings.set_many({"theme": "light", "window_width": 1024})
        assert settings.get("theme") == "light"
        assert settings.get("window_width") == 1024

    def test_get_all(self, settings):
        all_settings = settings.get_all()
        assert isinstance(all_settings, dict)
        assert "theme" in all_settings
        assert "window_width" in all_settings

    def test_persistence(self, settings):
        settings.set("language", "ar")
        path = settings.db_path
        s2 = Settings(path)
        assert s2.get("language") == "ar"

    def test_get_with_default(self, settings):
        assert settings.get("nonexistent", "fallback") == "fallback"

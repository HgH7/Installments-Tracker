import copy
import os
import tempfile

import pytest

from app.core.settings import DEFAULT_SETTINGS, Settings, SettingsManager


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


class TestSettingsManager:
    def test_defaults_not_mutated_after_set(self):
        """Verify shallow copy bug is fixed: modifying settings via
        SettingsManager must not mutate DEFAULT_SETTINGS."""
        expected = copy.deepcopy(DEFAULT_SETTINGS)
        mgr = SettingsManager()
        mgr.set("general", "language", "fr")
        # DEFAULT_SETTINGS must be unchanged
        assert DEFAULT_SETTINGS == expected
        mgr.set_section("display", {"theme": "light"})
        # DEFAULT_SETTINGS must still be unchanged after section update
        assert DEFAULT_SETTINGS == expected

    def test_reset_to_defaults(self):
        mgr = SettingsManager()
        mgr.set("general", "language", "fr")
        mgr.reset_to_defaults()
        assert mgr.get("general", "language") == "en"
        assert DEFAULT_SETTINGS["general"]["language"] == "en"

    def test_set_section_updates_only_target_section(self):
        mgr = SettingsManager()
        backup_display = dict(mgr.get_section("display"))
        mgr.set_section("general", {"language": "ar"})
        assert mgr.get("general", "language") == "ar"
        assert mgr.get_section("display") == backup_display

from app.core.updater import UpdateChecker, UpdateInfo


class TestUpdateChecker:
    def test_init(self):
        checker = UpdateChecker("1.0.0")
        assert checker.current_version == "1.0.0"

    def test_parse_version(self):
        checker = UpdateChecker("2.0.0")
        assert checker._parse_version("1.2.3") == (1, 2, 3)
        assert checker._parse_version("v3.4.5") == (3, 4, 5)

    def test_parse_version_with_prerelease(self):
        checker = UpdateChecker("2.0.0")
        parts = checker._parse_version("v10.0.0-beta")
        assert parts[0] > 0  # the numeric part should parse

    def test_parse_version_invalid(self):
        checker = UpdateChecker("1.0.0")
        assert checker._parse_version("not.a.version") == (0, 0, 0)

    def test_no_update_available(self):
        info = UpdateInfo(available=False, latest_version="2.0.0")
        assert not info.available
        assert info.latest_version == "2.0.0"

    def test_update_available(self):
        info = UpdateInfo(available=True, latest_version="2.0.0")
        assert info.available
        assert info.latest_version == "2.0.0"

    def test_error_handling(self):
        info = UpdateInfo(error="Network error")
        assert info.error == "Network error"
        assert not info.available

    def test_info_defaults(self):
        info = UpdateInfo()
        assert not info.available
        assert info.latest_version == ""
        assert info.download_url == ""
        assert info.release_notes == ""

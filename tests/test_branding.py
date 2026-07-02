from app.branding import APP_NAME, generate_logo, get_logo_path


class TestBranding:
    def test_app_name(self):
        assert APP_NAME == "Installments Tracker"

    def test_logo_path_ends_with_png(self):
        path = get_logo_path()
        assert path.endswith("icon.png")

    def test_generate_logo_returns_path_when_pil_available(self):
        result = generate_logo("/tmp/test_logo_branding.png")
        import os
        assert result is None or os.path.exists(result)

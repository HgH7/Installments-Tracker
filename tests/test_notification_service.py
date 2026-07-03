from unittest.mock import patch, MagicMock

from app.services.notification_service import NotificationService


class TestNotificationService:
    def test_open_whatsapp_adds_plus_prefix(self):
        with patch("app.services.notification_service.webbrowser.open", return_value=True) as mock_open:
            result = NotificationService.open_whatsapp("971500000000", "Hello")
            assert result is True
            args, _ = mock_open.call_args
            url = args[0]
            assert "wa.me/+971500000000" in url

    def test_open_whatsapp_keeps_existing_plus(self):
        with patch("app.services.notification_service.webbrowser.open", return_value=True) as mock_open:
            result = NotificationService.open_whatsapp("+971500000000", "Hello")
            assert result is True
            args, _ = mock_open.call_args
            url = args[0]
            assert "wa.me/+971500000000" in url

    def test_open_whatsapp_url_encodes_message(self):
        with patch("app.services.notification_service.webbrowser.open", return_value=True) as mock_open:
            NotificationService.open_whatsapp("+971500000000", "Hello world & thanks")
            args, _ = mock_open.call_args
            url = args[0]
            assert "Hello%20world%20%26%20thanks" in url

    def test_open_whatsapp_returns_false_on_exception(self):
        with patch("app.services.notification_service.webbrowser.open", side_effect=Exception("No browser")):
            result = NotificationService.open_whatsapp("+971500000000", "Hi")
            assert result is False

    def test_open_whatsapp_very_long_message(self):
        with patch("app.services.notification_service.webbrowser.open", return_value=True) as mock_open:
            long_msg = "A" * 5000
            result = NotificationService.open_whatsapp("+971500000000", long_msg)
            assert result is True
            args, _ = mock_open.call_args
            assert len(args[0]) > 0

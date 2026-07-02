import logging
import webbrowser
from urllib.parse import quote


class NotificationService:
    """Handles notification generation and opens WhatsApp Web with pre-filled messages.
    
    The application never sends messages automatically.
    WhatsApp Web is opened with the message pre-filled; the user presses Send manually.
    """

    @staticmethod
    def open_whatsapp(phone: str, message: str) -> bool:
        """Open WhatsApp Web with a pre-filled message for the given phone number.
        
        The user must press Send manually.
        """
        try:
            if not phone.startswith("+"):
                phone = "+" + phone
            encoded = quote(message)
            url = f"https://wa.me/{phone}?text={encoded}"
            webbrowser.open(url)
            logging.info(f"Opened WhatsApp Web for {phone}")
            return True
        except Exception as e:
            logging.error(f"Error opening WhatsApp Web: {str(e)}")
            return False

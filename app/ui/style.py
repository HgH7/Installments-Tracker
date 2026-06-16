import customtkinter
import logging
from tkinter import ttk


class StyleManager:
    """Manages application-wide styling"""

    COLORS = {
        "primary": "#2B7DE9",
        "secondary": "#23B0FF",
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "background": "#1a1a1a",
        "surface": "#2d2d2d",
        "text": "#ffffff",
        "text_secondary": "#b3b3b3",
        "border": "#404040",
    }

    FONTS = {
        "heading": ("Arial", 24, "bold"),
        "subheading": ("Arial", 18, "bold"),
        "body": ("Arial", 14),
        "body_bold": ("Arial", 14, "bold"),
        "small": ("Arial", 12),
        "button": ("Arial", 16, "bold"),
    }

    BUTTON_STYLES = {
        "primary": {
            "fg_color": COLORS["primary"],
            "hover_color": COLORS["secondary"],
            "text_color": COLORS["text"],
            "font": ("Arial", 18, "bold"),
            "corner_radius": 12,
            "border_width": 0,
            "height": 45,
        },
        "secondary": {
            "fg_color": "transparent",
            "hover_color": COLORS["surface"],
            "text_color": COLORS["text"],
            "font": ("Arial", 18, "bold"),
            "corner_radius": 12,
            "border_width": 2,
            "border_color": COLORS["primary"],
            "height": 45,
        },
        "danger": {
            "fg_color": COLORS["danger"],
            "hover_color": "#c82333",
            "text_color": COLORS["text"],
            "font": ("Arial", 18, "bold"),
            "corner_radius": 12,
            "border_width": 0,
            "height": 45,
        },
    }

    @classmethod
    def setup_theme(cls):
        """Configure the global theme settings"""
        try:
            customtkinter.set_appearance_mode("dark")
            customtkinter.set_default_color_theme("blue")
            style = ttk.Style()
            style.theme_use("default")
            style.configure(
                "Treeview",
                background=cls.COLORS["surface"],
                foreground=cls.COLORS["text"],
                fieldbackground=cls.COLORS["surface"],
                font=cls.FONTS["body"],
            )
            style.map(
                "Treeview",
                background=[("selected", cls.COLORS["primary"])],
                foreground=[("selected", cls.COLORS["text"])],
            )
            style.configure(
                "Treeview.Heading",
                background=cls.COLORS["primary"],
                foreground=cls.COLORS["text"],
                font=cls.FONTS["body_bold"],
            )
            logging.info("Theme setup completed successfully")
        except Exception as e:
            logging.error(f"Error setting up theme: {str(e)}")
            raise

    @classmethod
    def create_frame(cls, master, **kwargs):
        """Create a styled frame"""
        try:
            frame_config = {"corner_radius": 15, "border_width": 0}
            if "fg_color" not in kwargs:
                frame_config["fg_color"] = cls.COLORS["surface"]
            frame_config.update(kwargs)
            return customtkinter.CTkFrame(master, **frame_config)
        except Exception as e:
            logging.error(f"Error creating frame: {str(e)}")
            raise

    @classmethod
    def create_button(cls, master, text: str, style: str = "primary", **kwargs):
        """Create a styled button"""
        try:
            button_style = cls.BUTTON_STYLES[style].copy()
            button_style.update(kwargs)
            return customtkinter.CTkButton(master, text=text, **button_style)
        except Exception as e:
            logging.error(f"Error creating button: {str(e)}")
            raise

    @classmethod
    def create_label(cls, master, text: str, font_style: str = "body", **kwargs):
        """Create a styled label"""
        try:
            if "text_color" not in kwargs:
                kwargs["text_color"] = cls.COLORS["text"]
            if "font" not in kwargs:
                kwargs["font"] = cls.FONTS[font_style]
            return customtkinter.CTkLabel(master, text=text, **kwargs)
        except Exception as e:
            logging.error(f"Error creating label: {str(e)}")
            raise

    @classmethod
    def create_entry(cls, master, **kwargs):
        """Create a styled entry"""
        try:
            entry_config = {
                "fg_color": cls.COLORS["background"],
                "text_color": cls.COLORS["text"],
                "border_color": cls.COLORS["primary"],
                "corner_radius": 8,
                "font": cls.FONTS["body"],
            }
            entry_config.update(kwargs)
            return customtkinter.CTkEntry(master, **entry_config)
        except Exception as e:
            logging.error(f"Error creating entry: {str(e)}")
            raise

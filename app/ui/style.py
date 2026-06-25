import customtkinter
import logging
from tkinter import ttk


class StyleManager:
    """Manages application-wide styling"""

    COLORS = {
        "primary": "#b4c5ff",
        "primary_action": "#2563eb",
        "primary_hover": "#1d4ed8",
        "success": "#4ae176",
        "warning": "#ffb95f",
        "danger": "#ffb4ab",
        "background": "#101415",
        "surface": "#1d2022",
        "surface_low": "#191c1e",
        "surface_high": "#272a2c",
        "surface_highest": "#323537",
        "text": "#e0e3e5",
        "text_secondary": "#c3c6d7",
        "text_muted": "#94a3b8",
        "border": "#434655",
        "border_soft": "#323537",
        "on_primary": "#eeefff",
        "error_container": "#3a1719",
        "success_container": "#12351f",
        "warning_container": "#3d2a0b",
    }

    FONTS = {
        "heading": ("Segoe UI", 20, "bold"),
        "subheading": ("Segoe UI", 15, "bold"),
        "section": ("Segoe UI", 14, "bold"),
        "body": ("Segoe UI", 13),
        "body_bold": ("Segoe UI", 13, "bold"),
        "small": ("Segoe UI", 11),
        "label": ("Segoe UI", 11, "bold"),
        "data": ("Courier New", 12),
        "button": ("Segoe UI", 13, "bold"),
    }

    BUTTON_STYLES = {
        "primary": {
            "fg_color": COLORS["primary_action"],
            "hover_color": COLORS["primary_hover"],
            "text_color": COLORS["on_primary"],
            "font": FONTS["button"],
            "corner_radius": 6,
            "border_width": 0,
            "height": 36,
        },
        "secondary": {
            "fg_color": COLORS["surface_high"],
            "hover_color": COLORS["surface_highest"],
            "text_color": COLORS["text"],
            "font": FONTS["button"],
            "corner_radius": 6,
            "border_width": 1,
            "border_color": COLORS["border"],
            "height": 36,
        },
        "danger": {
            "fg_color": COLORS["error_container"],
            "hover_color": "#512124",
            "text_color": COLORS["danger"],
            "font": FONTS["button"],
            "corner_radius": 6,
            "border_width": 0,
            "height": 36,
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
                borderwidth=0,
                rowheight=32,
                font=cls.FONTS["data"],
            )
            style.map(
                "Treeview",
                background=[("selected", cls.COLORS["surface_highest"])],
                foreground=[("selected", cls.COLORS["text"])],
            )
            style.configure(
                "Treeview.Heading",
                background=cls.COLORS["surface_high"],
                foreground=cls.COLORS["text_secondary"],
                borderwidth=0,
                relief="flat",
                font=cls.FONTS["section"],
            )
            style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
            logging.info("Theme setup completed successfully")
        except Exception as e:
            logging.error(f"Error setting up theme: {str(e)}")
            raise

    @classmethod
    def create_frame(cls, master, **kwargs):
        """Create a styled frame"""
        try:
            frame_config = {
                "corner_radius": 8,
                "border_width": 1,
                "border_color": cls.COLORS["border"],
            }
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
                "fg_color": cls.COLORS["surface_high"],
                "text_color": cls.COLORS["text"],
                "border_color": cls.COLORS["border"],
                "corner_radius": 4,
                "border_width": 1,
                "font": cls.FONTS["body"],
                "height": 34,
            }
            entry_config.update(kwargs)
            return customtkinter.CTkEntry(master, **entry_config)
        except Exception as e:
            logging.error(f"Error creating entry: {str(e)}")
            raise

    @classmethod
    def create_section_header(cls, master, title: str, subtitle: str = "", **kwargs):
        frame = cls.create_frame(master, fg_color="transparent", border_width=0, **kwargs)
        frame.grid_columnconfigure(0, weight=1)
        cls.create_label(frame, text=title, font_style="heading").grid(row=0, column=0, sticky="w")
        if subtitle:
            cls.create_label(
                frame,
                text=subtitle,
                font_style="small",
                text_color=cls.COLORS["text_muted"],
            ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        return frame

    @classmethod
    def create_badge(cls, master, text: str, tone: str = "neutral", **kwargs):
        tone_styles = {
            "success": (cls.COLORS["success_container"], cls.COLORS["success"]),
            "warning": (cls.COLORS["warning_container"], cls.COLORS["warning"]),
            "danger": (cls.COLORS["error_container"], cls.COLORS["danger"]),
            "neutral": (cls.COLORS["surface_high"], cls.COLORS["text_secondary"]),
        }
        fg_color, text_color = tone_styles.get(tone, tone_styles["neutral"])
        badge_config = {
            "text": text,
            "fg_color": fg_color,
            "text_color": text_color,
            "corner_radius": 2,
            "font": cls.FONTS["label"],
            "width": 72,
            "height": 24,
        }
        badge_config.update(kwargs)
        return customtkinter.CTkLabel(master, **badge_config)

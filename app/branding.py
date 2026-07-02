"""Application branding — splash screen, about dialog, and logo."""

import os
import tkinter as tk

from app.version import (
    APP_DESCRIPTION,
    APP_NAME,
    COMPANY_NAME,
    COMPANY_URL,
    COPYRIGHT,
    VERSION_STRING,
    __release_date__,
)


def get_logo_path() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", "icon.png")


from typing import Optional


def generate_logo(output_path: Optional[str] = None) -> Optional[str]:
    """Generate a simple application logo using PIL. Returns the path."""
    if output_path is None:
        output_path = get_logo_path()
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([8, 8, size - 8, size - 8], radius=40, fill="#1d2022", outline="#b4c5ff", width=4)

    draw.rounded_rectangle([48, 120, 208, 200], radius=12, fill="#2563eb")
    draw.rounded_rectangle([56, 60, 136, 200], radius=10, fill="#1d4ed8")
    draw.rounded_rectangle([120, 30, 200, 200], radius=10, fill="#b4c5ff")

    draw.rectangle([100, 130, 156, 140], fill="#ffffff")
    draw.rectangle([100, 150, 180, 160], fill="#ffffff")
    draw.rectangle([100, 170, 140, 180], fill="#ffffff")

    img.save(output_path, "PNG")
    return output_path


def show_splash_screen(parent, StyleManager, duration_ms: int = 2500):
    """Display a splash screen that auto-closes after duration_ms."""
    splash = tk.Toplevel(parent)
    splash.overrideredirect(True)
    splash.attributes("-topmost", True)

    sw = parent.winfo_screenwidth()
    sh = parent.winfo_screenheight()
    w, h = 480, 300
    x = (sw - w) // 2
    y = (sh - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")

    bg = StyleManager.COLORS["background"]
    frame = tk.Frame(splash, bg=bg, highlightthickness=0)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text=APP_NAME, font=("Segoe UI", 24, "bold"),
             fg=StyleManager.COLORS["primary"], bg=bg).pack(pady=(60, 8))
    tk.Label(frame, text=VERSION_STRING, font=("Segoe UI", 12),
             fg=StyleManager.COLORS["text_muted"], bg=bg).pack()
    tk.Label(frame, text="Loading...", font=("Segoe UI", 10),
             fg=StyleManager.COLORS["text_secondary"], bg=bg).pack(pady=(30, 0))
    tk.Label(frame, text=COPYRIGHT, font=("Segoe UI", 8),
             fg=StyleManager.COLORS["text_secondary"], bg=bg).pack(side="bottom", pady=16)

    splash.update()
    splash.after(duration_ms, splash.destroy)
    return splash


def show_about_dialog(parent, StyleManager):
    """Display the About dialog."""
    from customtkinter import CTkToplevel
    dialog = CTkToplevel(parent)
    dialog.geometry("440x380")
    dialog.title(f"About {APP_NAME}")
    dialog.transient(parent)
    dialog.grab_set()

    main = StyleManager.create_frame(dialog, fg_color=StyleManager.COLORS["background"])
    main.pack(fill="both", expand=True, padx=24, pady=24)

    StyleManager.create_label(main, text=APP_NAME, font_style="heading",
                              text_color=StyleManager.COLORS["primary"]).pack(pady=(0, 4))
    StyleManager.create_label(main, text=VERSION_STRING, font_style="subheading",
                              text_color=StyleManager.COLORS["text_muted"]).pack(pady=(0, 2))
    StyleManager.create_label(main, text=f"Released: {__release_date__}", font_style="small",
                              text_color=StyleManager.COLORS["text_secondary"]).pack(pady=(0, 16))

    desc = StyleManager.create_textbox(main, height=80, readonly=True,
                                       fg_color=StyleManager.COLORS["surface_low"])
    desc.pack(fill="x", pady=(0, 16))
    desc.insert("end", APP_DESCRIPTION)
    desc.configure(state="disabled")

    info_frame = StyleManager.create_frame(main, fg_color="transparent", border_width=0)
    info_frame.pack(fill="x", pady=(0, 16))

    for label, value in [
        ("Company:", COMPANY_NAME),
        ("Website:", COMPANY_URL),
        ("Copyright:", COPYRIGHT),
        ("Python:", __import__("sys").version),
    ]:
        row = StyleManager.create_frame(info_frame, fg_color="transparent", border_width=0)
        row.pack(fill="x", pady=2)
        StyleManager.create_label(row, text=label, font_style="label",
                                  text_color=StyleManager.COLORS["text_muted"], anchor="w").pack(side="left")
        StyleManager.create_label(row, text=value, font_style="small",
                                  text_color=StyleManager.COLORS["text"], anchor="w").pack(side="right")

    btn_frame = StyleManager.create_frame(main, fg_color="transparent", border_width=0)
    btn_frame.pack(fill="x")
    StyleManager.create_button(btn_frame, text="Close", width=100, style="secondary",
                               command=dialog.destroy).pack(side="right")

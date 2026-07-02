from app.ui.styles.style import StyleManager

nav_buttons = {}


def create_nav_button(parent, text, command):
    btn = StyleManager.create_button(parent, text=text, command=command, anchor="w")
    btn.configure(height=40)
    return btn


def show_frame(frame, frames=None):
    for child in frame.master.winfo_children():
        if hasattr(child, "grid_remove"):
            child.grid_remove()
    frame.grid()
    on_show = getattr(frame, "page_on_show", None)
    if on_show:
        on_show()
    active_page = getattr(frame, "page_name", None)
    for page_name, button in nav_buttons.items():
        if page_name == active_page:
            button.configure(
                fg_color=StyleManager.COLORS["surface_highest"],
                text_color=StyleManager.COLORS["primary"],
            )
        else:
            button.configure(
                fg_color="transparent",
                text_color=StyleManager.COLORS["text_secondary"],
            )


def setup_keyboard_shortcuts(app, frames, show_frame_fn):
    bindings = [
        ("<Control-h>", "home"),
        ("<Control-n>", "add"),
        ("<Control-f>", "view"),
        ("<Control-i>", "manage"),
        ("<Control-b>", "backup_manager"),
        ("<Control-N>", "notifications"),
        ("<Control-a>", "activity"),
        ("<Control-e>", "import_export"),
    ]

    def navigate(e, page_name):
        show_frame_fn(frames[page_name])

    for sequence, page_name in bindings:
        app.bind_all(sequence, lambda e, p=page_name: navigate(e, p))
    app.bind_all("<Control-q>", lambda e: app.quit())
    app.bind_all("<Control-w>", lambda e: app.quit() if hasattr(app, "quit") else None)
    app.bind_all("<Escape>", lambda e: close_active_dialog(app))
    app.bind_all("<Control-r>", lambda e: refresh_active_page(frames, show_frame_fn))
    app.bind_all("<Control-s>", lambda e: trigger_save(app))


def close_active_dialog(app):
    for w in app.winfo_children():
        if hasattr(w, "grab_current") and w.grab_current():
            w.destroy()
            break


def refresh_active_page(frames, show_frame_fn):
    import customtkinter as ctk
    top = None
    for w in ctk.CTk.winfo_children(ctk.CTk):
        if hasattr(w, "page_on_show"):
            top = w
            break
    if top:
        on_show = getattr(top, "page_on_show", None)
        if on_show:
            on_show()


def trigger_save(app):
    for w in app.winfo_children():
        if isinstance(w, type(app)):
            continue
        if hasattr(w, "winfo_children"):
            for child in w.winfo_children():
                if hasattr(child, "invoke"):
                    if "save" in str(child.cget("text")).lower():
                        child.invoke()
                        return

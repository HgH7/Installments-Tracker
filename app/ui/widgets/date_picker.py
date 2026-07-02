from customtkinter import CTkToplevel
from tkcalendar import Calendar

from app.ui.styles.style import StyleManager


class DatePicker(CTkToplevel):
    """Popup calendar to select a date."""
    def __init__(self, parent, entry_widget):
        super().__init__(parent)
        self.entry_widget = entry_widget
        self.geometry("380x420")
        self.title("Select Date")

        main_frame = StyleManager.create_frame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        StyleManager.create_label(
            main_frame,
            text="Select installment start date",
            font_style="subheading"
        ).pack(pady=(0, 20))

        self.cal = Calendar(
            main_frame,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            background=StyleManager.COLORS["surface"],
            foreground=StyleManager.COLORS["text"],
            headersbackground=StyleManager.COLORS["surface_highest"],
            headersforeground=StyleManager.COLORS["text"],
            selectbackground=StyleManager.COLORS["primary_action"],
            selectforeground=StyleManager.COLORS["on_primary"],
            normalbackground=StyleManager.COLORS["surface_low"],
            normalforeground=StyleManager.COLORS["text"],
            weekendbackground=StyleManager.COLORS["surface_low"],
            weekendforeground=StyleManager.COLORS["text_secondary"],
            othermonthbackground=StyleManager.COLORS["background"],
            othermonthforeground=StyleManager.COLORS["text_muted"]
        )
        self.cal.pack(pady=20, padx=20, fill="both", expand=True)

        buttons_frame = StyleManager.create_frame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(20, 0))
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        left_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
        left_side.grid(row=0, column=0, sticky="w")
        right_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
        right_side.grid(row=0, column=1, sticky="e")

        StyleManager.create_button(
            left_side,
            text="Select",
            width=140,
            command=self.select_date
        ).pack(side="left", pady=10)

        StyleManager.create_button(
            right_side,
            text="Cancel",
            style="secondary",
            width=120,
            command=self.destroy
        ).pack(side="right", pady=10)

        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def select_date(self):
        self.entry_widget.delete(0, "end")
        self.entry_widget.insert(0, self.cal.get_date())
        self.destroy()

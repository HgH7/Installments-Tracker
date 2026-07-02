from tkinter import messagebox
from typing import Callable

from customtkinter import CTkToplevel

from app.ui.styles.style import StyleManager
from app.core.validation import ValidationService


class ModalDialog:
    """Base builder for common modal dialog patterns."""

    @staticmethod
    def button_row(parent, left_text="", left_cmd=None, right_text="", right_cmd=None):
        buttons_frame = StyleManager.create_frame(parent)
        buttons_frame.pack(fill="x", pady=(20, 0))
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        left_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
        left_side.grid(row=0, column=0, sticky="w")
        right_side = StyleManager.create_frame(buttons_frame, fg_color="transparent")
        right_side.grid(row=0, column=1, sticky="e")

        if left_cmd:
            StyleManager.create_button(
                left_side, text=left_text, width=160, command=left_cmd
            ).pack(side="left", pady=10)
        if right_cmd:
            StyleManager.create_button(
                right_side, text=right_text, width=120, style="secondary", command=right_cmd
            ).pack(side="right", pady=10)
        return buttons_frame


class EditInstallmentDialog:
    """Shared Edit Installment dialog used from both Manage and Payment History pages."""

    def __init__(self, parent, customer_name: str, installment_date: str,
                 installment_value: float, is_paid: bool,
                 on_save: Callable):
        self.parent = parent
        self.customer_name = customer_name
        self.installment_date = installment_date
        self.installment_value = installment_value
        self.is_paid = is_paid
        self.on_save = on_save
        self.window = None
        self.date_entry = None
        self.amount_entry = None
        self.paid_status = None

    def show(self):
        self.window = CTkToplevel(self.parent)
        self.window.geometry("480x460")
        self.window.title("Edit Installment")
        self.window.transient(self.parent)
        self.window.grab_set()

        main_frame = StyleManager.create_frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        StyleManager.create_label(
            main_frame, text="Edit Installment Details", font_style="subheading"
        ).pack(pady=(0, 12))

        StyleManager.create_label(
            main_frame,
            text=f"Customer: {self.customer_name}",
            font_style="body_bold",
            text_color=StyleManager.COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 16))

        fields_frame = StyleManager.create_frame(main_frame, border_width=0)
        fields_frame.pack(fill="x", pady=(0, 16))

        StyleManager.create_label(
            fields_frame, text="Installment Date:", font_style="label",
        ).pack(anchor="w", pady=(0, 4))

        date_row = StyleManager.create_frame(fields_frame, fg_color="transparent", border_width=0)
        date_row.pack(fill="x", pady=(0, 12))
        date_row.grid_columnconfigure(0, weight=1)

        self.date_entry = StyleManager.create_entry(date_row)
        self.date_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.date_entry.insert(0, self.installment_date)

        from app.ui.widgets.date_picker import DatePicker

        def open_dp():
            DatePicker(self.window, self.date_entry)

        StyleManager.create_button(
            date_row, text="Date", width=60, command=open_dp
        ).grid(row=0, column=1)

        StyleManager.create_label(
            fields_frame, text="Installment Value:", font_style="label",
        ).pack(anchor="w", pady=(0, 4))

        self.amount_entry = StyleManager.create_entry(fields_frame)
        self.amount_entry.pack(fill="x", pady=(0, 12))
        self.amount_entry.insert(0, str(self.installment_value))

        import tkinter as tk
        self.paid_status = tk.BooleanVar(value=self.is_paid)
        StyleManager.create_checkbox(
            fields_frame, text="Paid", variable=self.paid_status,
        ).pack(anchor="w")

        def save():
            new_date = self.date_entry.get().strip()
            new_value_str = self.amount_entry.get().strip()
            new_paid = self.paid_status.get()

            date_result = ValidationService.validate_date(new_date)
            if not date_result:
                messagebox.showerror("Error", date_result.errors[0])
                return

            value_result = ValidationService.validate_installment_value(new_value_str)
            if not value_result:
                messagebox.showerror("Error", value_result.errors[0])
                return

            self.on_save(
                old_date=self.installment_date,
                new_date=new_date,
                new_value=float(new_value_str),
                new_paid_status=new_paid,
                old_paid_status=self.is_paid,
                dialog=self.window,
            )

        ModalDialog.button_row(
            main_frame,
            left_text="Save Changes", left_cmd=save,
            right_text="Cancel", right_cmd=self.window.destroy,
        )



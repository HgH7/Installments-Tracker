import customtkinter
from customtkinter import *
from tkinter import messagebox, ttk, StringVar, BooleanVar, filedialog
import tkinter as tk
from tkinter import TclError
import re
import csv
import os
import pandas as pd
from datetime import datetime
from tkcalendar import Calendar
import shutil
import threading
import pywhatkit as kit
import logging
from typing import List, Dict, Optional, Union
import time
import sys
import traceback

from app.repositories.csv_repository import CSVRepository
from app.services.customer_service import CustomerService
from app.ui.style import StyleManager
from app.ui.file_manager import FileManager
from app.ui.pages.add import setup_add_page as setup_add_page_module
from app.ui.pages.home import setup_home_page as setup_home_page_module
from app.ui.pages.view import setup_view_page as setup_view_page_module
from app.ui.pages.manage import setup_manage_installments_page as setup_manage_installments_page_module
from app.ui.pages.backup_restore import setup_backup_restore_page as setup_backup_restore_page_module
from app.ui.pages.send_notification import setup_send_notification_page as setup_send_notification_page_module
from app.utils.serialization import dump_json, load_json_dict, load_json_list

# Ensure logs directory exists
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Set up logging with more detailed format
logging.basicConfig(
    filename=os.path.join(logs_dir, 'app.log'),
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

# Add console logging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# Global variables
frames = {}
nav_buttons = {}


# Initialize file manager
file_manager = FileManager(os.path.join(os.path.dirname(os.path.abspath(__file__)), "customer_files"))

def initialize_app():
    """Initialize the main application window with error handling"""
    try:
        logging.info("Starting application initialization...")
        
        # Initialize the main window
        app_window = CTk()
        if not app_window:
            raise Exception("Failed to create main window")
            
        app_window.geometry("1280x800")
        app_window.title("Installment Tracker")
        
        # Try setting appearance mode
        try:
            app_window._set_appearance_mode("dark")
            logging.info("Appearance mode set successfully")
        except Exception as e:
            logging.error(f"Failed to set appearance mode: {str(e)}")
            # Continue anyway as this is not critical
        
        # Center the window on screen
        try:
            screen_width = app_window.winfo_screenwidth()
            screen_height = app_window.winfo_screenheight()
            x = (screen_width - 1280) // 2
            y = (screen_height - 800) // 2
            app_window.geometry(f"1280x800+{x}+{y}")
            logging.info("Window centered successfully")
        except Exception as e:
            logging.error(f"Failed to center window: {str(e)}")
            # Continue anyway as this is not critical
        
        return app_window
    except Exception as e:
        logging.critical(f"Failed to initialize application: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("Critical Error", "Failed to start the application. Please review the log file for details.")
        sys.exit(1)

def main(app_window):
    """Main application entry point with error handling"""
    try:
        logging.info("Application starting...")
        app_window.mainloop()
    except Exception as e:
        logging.critical(f"Critical error in main: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("Critical Error", f"An unexpected error occurred: {str(e)}\nPlease review the log file for details.")
        sys.exit(1)

def show_frame(frame):
    """Show the specified frame and hide sibling pages."""
    for child in frame.master.winfo_children():
        if hasattr(child, "grid_remove"):
            child.grid_remove()
    frame.grid()
    active_page = getattr(frame, "page_name", None)
    for page_name, button in nav_buttons.items():
        if page_name == active_page:
            button.configure(
                fg_color=StyleManager.COLORS["surface_high"],
                text_color=StyleManager.COLORS["primary"],
            )
        else:
            button.configure(
                fg_color="transparent",
                text_color=StyleManager.COLORS["text_secondary"],
            )


def create_app_shell(app):
    """Create the fixed sidebar and page canvas."""
    shell = StyleManager.create_frame(
        app,
        fg_color=StyleManager.COLORS["background"],
        border_width=0,
        corner_radius=0,
    )
    shell.pack(fill="both", expand=True)
    shell.grid_columnconfigure(0, weight=0, minsize=220)
    shell.grid_columnconfigure(1, weight=1)
    shell.grid_rowconfigure(0, weight=1)

    sidebar = StyleManager.create_frame(
        shell,
        fg_color=StyleManager.COLORS["surface_low"],
        border_width=0,
        corner_radius=0,
    )
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_rowconfigure(1, weight=1)

    brand_frame = StyleManager.create_frame(sidebar, fg_color="transparent", border_width=0)
    brand_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(24, 28))
    StyleManager.create_label(
        brand_frame,
        text="Installments Tracker",
        font_style="heading",
        text_color=StyleManager.COLORS["primary"],
        anchor="w",
    ).pack(anchor="w")
    StyleManager.create_label(
        brand_frame,
        text="Desktop Management",
        font_style="small",
        text_color=StyleManager.COLORS["text_muted"],
        anchor="w",
    ).pack(anchor="w", pady=(2, 0))

    nav_frame = StyleManager.create_frame(sidebar, fg_color="transparent", border_width=0)
    nav_frame.grid(row=1, column=0, sticky="new", padx=8)
    nav_frame.grid_columnconfigure(0, weight=1)

    nav_items = [
        ("home", "Home", "", lambda: show_frame(frames["home"])),
        ("add", "Add Customer", "+", lambda: show_frame(frames["add"])),
        ("view", "Customers", "", lambda: show_frame(frames["view"])),
        ("manage", "Installments", "$", lambda: show_frame(frames["manage"])),
        ("backup_restore", "Backup & Restore", "", lambda: show_frame(frames["backup_restore"])),
        ("send_notification", "Notifications", "!", lambda: show_frame(frames["send_notification"])),
    ]

    nav_buttons.clear()
    for index, (page_name, label, icon, command) in enumerate(nav_items):
        button = StyleManager.create_button(
            nav_frame,
            text=label,
            style="secondary",
            command=command,
            anchor="w",
            width=196,
            height=38,
            fg_color="transparent",
            hover_color=StyleManager.COLORS["surface_high"],
            text_color=StyleManager.COLORS["text_secondary"],
            border_width=0,
            corner_radius=4,
        )
        button.grid(row=index, column=0, sticky="ew", pady=2)
        nav_buttons[page_name] = button

    footer = StyleManager.create_frame(sidebar, fg_color="transparent", border_width=0)
    footer.grid(row=2, column=0, sticky="ew", padx=16, pady=20)
    StyleManager.create_label(
        footer,
        text="Local CSV Workspace",
        font_style="label",
        text_color=StyleManager.COLORS["text_secondary"],
        anchor="w",
    ).pack(anchor="w")
    StyleManager.create_label(
        footer,
        text="Production refactor",
        font_style="small",
        text_color=StyleManager.COLORS["text_muted"],
        anchor="w",
    ).pack(anchor="w", pady=(2, 0))

    content = StyleManager.create_frame(
        shell,
        fg_color=StyleManager.COLORS["background"],
        border_width=0,
        corner_radius=0,
    )
    content.grid(row=0, column=1, sticky="nsew")
    content.grid_columnconfigure(0, weight=1)
    content.grid_rowconfigure(0, weight=1)
    return content

def refresh_treeview(tree, data=None):
    """Refresh the treeview with data."""
    # Clear existing items
    for item in tree.get_children():
        tree.delete(item)
        
    # If no data provided, read from CSV
    if data is None:
        data = csv_repository.read_data()
    
    # Get column names
    columns = tree["columns"]
    
    # Insert data into treeview with proper status handling
    for customer in data:
        values = []
        for col in columns:
            if col == "Paid":
                # Get the first installment date and check if it's paid
                installment_dates = customer.get("Installment Dates", "").split(";")
                first_date = installment_dates[0] if installment_dates else ""
                paid_installments = load_json_list(customer.get("Paid_Installments", "[]"))
                is_paid = first_date in paid_installments
                values.append("Yes" if is_paid else "No")
            else:
                values.append(customer.get(col, ""))
        
        item = tree.insert("", "end", values=values)
        
        # Add color coding for paid status if applicable
        if "Paid" in columns:
            if values[columns.index("Paid")] == "Yes":
                tree.item(item, tags=("paid",))
            else:
                tree.item(item, tags=("unpaid",))
    
    # Configure payment status styles if needed
    if "Paid" in columns:
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])


# Initialize CSV repository and customer service
csv_filename = "customers.csv"
backup_folder = "backups"
csv_repository = CSVRepository(csv_filename, backup_folder)
customer_service = CustomerService(csv_repository)

def validate_and_save(name_entry, phone_entry, amount_entry, installments_entry, start_date_entry, file_list=None):
    """Validate and save customer data"""
    try:
        # Get values from entries
        name = name_entry.get().strip()
        phone = phone_entry.get().strip()
        amount = amount_entry.get().strip()
        installments = installments_entry.get().strip()
        start_date = start_date_entry.get().strip()

        # Validate all fields are filled
        if not all([name, phone, amount, installments, start_date]):
            messagebox.showerror("Error", "All fields are required.")
            return False

        # Validate phone number
        if not re.match(r"^\+?\d{10,15}$", phone):
            messagebox.showerror("Error", "Invalid phone number.")
            return False

        # Validate amount
        if not re.match(r"^\d+(\.\d{1,2})?$", amount):
            messagebox.showerror("Error", "Amount must be a valid number.")
            return False

        # Validate installments
        if not installments.isdigit() or int(installments) <= 0:
            messagebox.showerror("Error", "Installments must be a whole number greater than zero.")
            return False

        # Validate date format
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
            return False

        customer_data = customer_service.build_customer_record(
            name,
            phone,
            amount,
            installments,
            start_date,
            date_strategy="calendar_month",
        )

        # Save customer data
        if customer_service.append_customer(customer_data):
            # Save files if provided
            if file_list and hasattr(file_list, 'files') and file_list.files:
                if file_manager.add_files(name, file_list.files):
                    logging.info(f"Successfully saved files for customer {name}")
                else:
                    logging.error(f"Failed to save files for customer {name}")
                    messagebox.showwarning("Warning", "Customer data was saved, but attached files could not be saved.")
            
            # Clear all entry fields
            name_entry.delete(0, "end")
            phone_entry.delete(0, "end")
            amount_entry.delete(0, "end")
            installments_entry.delete(0, "end")
            start_date_entry.delete(0, "end")
            
            # Clear file list but preserve the widget
            if file_list:
                file_list.files = []
                file_list.configure(state="normal")
                file_list.delete("1.0", "end")
                file_list.configure(state="disabled")
            
            messagebox.showinfo("Success", "Customer added successfully.")
            return True
        else:
            return False
            
    except Exception as e:
        logging.error(f"Error saving customer data: {str(e)}")
        messagebox.showerror("Error", f"An error occurred while saving data: {str(e)}")
        return False

class DatePicker(CTkToplevel):
    """Popup calendar to select a date."""
    def __init__(self, parent, entry_widget):
        super().__init__(parent)
        self.entry_widget = entry_widget
        self.geometry("400x450")
        self.title("Select Date")
        
        # Create main frame
        main_frame = StyleManager.create_frame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add title
        StyleManager.create_label(
            main_frame,
            text="Select installment start date",
            font_style="subheading"
        ).pack(pady=(0, 20))
        
        # Calendar widget with custom colors
        self.cal = Calendar(
            main_frame,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            background=StyleManager.COLORS["surface"],
            foreground=StyleManager.COLORS["text"],
            headersbackground=StyleManager.COLORS["primary"],
            headersforeground=StyleManager.COLORS["text"],
            selectbackground=StyleManager.COLORS["secondary"],
            selectforeground=StyleManager.COLORS["text"],
            normalbackground=StyleManager.COLORS["background"],
            normalforeground=StyleManager.COLORS["text"],
            weekendbackground=StyleManager.COLORS["background"],
            weekendforeground=StyleManager.COLORS["text"],
            othermonthbackground=StyleManager.COLORS["background"],
            othermonthforeground=StyleManager.COLORS["text_secondary"]
        )
        self.cal.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Buttons frame
        buttons_frame = StyleManager.create_frame(main_frame)
        buttons_frame.pack(fill="x", pady=(20, 0))
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Select button
        StyleManager.create_button(
            buttons_frame,
            text="Select",
            width=150,
            command=self.select_date
        ).grid(row=0, column=0, padx=5)
        
        # Cancel button
        StyleManager.create_button(
            buttons_frame,
            text="Cancel",
            style="secondary",
            width=150,
            command=self.destroy
        ).grid(row=0, column=1, padx=5)
        
        # Make the window modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()
    
    def select_date(self):
        """Set the selected date and close the window."""
        self.entry_widget.delete(0, "end")
        self.entry_widget.insert(0, self.cal.get_date())
        self.destroy()

def show_payment_history():
    """Show payment history for selected customer."""
    # Get the current frame's treeview
    current_frame = None
    for frame in frames.values():
        if frame.winfo_ismapped():  # Check if frame is visible
            current_frame = frame
            break
            
    if not current_frame or not hasattr(current_frame, 'tree'):
        messagebox.showerror("Error", "Customer list was not found.")
        return
        
    tree = current_frame.tree
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showerror("Error", "Select a customer to view payment history.")
        return
        
    if len(selected_items) > 1:
        messagebox.showerror("Error", "Select only one customer.")
        return
        
    try:
        item = selected_items[0]
        customer_name = tree.item(item)["values"][0]
        
        # Get customer data
        data = csv_repository.read_data()
        customer_data = None
        for customer in data:
            if customer["Name"] == customer_name:
                customer_data = customer
                break
                
        if not customer_data:
            messagebox.showerror("Error", "Customer data was not found.")
            return
            
        # Create payment history window
        history_window = CTkToplevel(app)
        history_window.geometry("800x760")
        history_window.title(f"Payment History - {customer_name}")
        
        # Make window modal
        history_window.transient(app)
        history_window.grab_set()
        
        # Create main frame
        main_frame = StyleManager.create_frame(history_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add title
        StyleManager.create_label(
            main_frame,
            text=f"Payment History - {customer_name}",
            font_style="subheading"
        ).pack(pady=(0, 20))
        
        # Create table container
        table_frame = StyleManager.create_frame(main_frame)
        table_frame.pack(fill="both", expand=True, pady=10)
        
        # Create a Treeview widget
        columns = ("Date", "Value", "Status", "Action")
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Custom.Treeview"
        )
        
        # Set column widths and headings
        column_widths = {
            "Date": 150,
            "Value": 150,
            "Status": 150,
            "Action": 150
        }
        
        column_headers = {
            "Date": "Installment Date",
            "Value": "Installment Value",
            "Status": "Status",
            "Action": "Action"
        }
        
        for col in columns:
            tree.column(col, width=column_widths[col], anchor="center")
            tree.heading(col, text=column_headers[col])
            
        if customer_data:
            installment_dates = customer_data["Installment Dates"].split(";")
            default_value = float(customer_data["Installment Value"])
            paid_installments = load_json_list(customer_data.get("Paid_Installments", "[]"))
            
            # Get installment values if they exist
            try:
                installment_values = load_json_dict(customer_data.get("Installment_Values", "{}"))
            except:
                installment_values = {}
            
            # Create a dictionary to store row IDs for each installment date
            date_to_row_map = {}
            today = datetime.now().strftime("%Y-%m-%d")
            
            for date in installment_dates:
                is_paid = date in paid_installments
                status = "Paid" if is_paid else "Unpaid"
                status_tags = ("paid",) if is_paid else ("unpaid",)
                
                # Get the installment value, using the specific value if it exists
                value = installment_values.get(date, default_value)
                
                # Determine if this installment date is in the future
                is_future = date > today
                
                # For unpaid installments, add a "Mark as Paid" button, unless it's in the future
                action = "" if is_paid else "Mark as Paid" if not is_future else "Future Due Date"
                
                # Insert row and store the row ID
                row_id = tree.insert("", "end", values=(date, f"{value:.2f}", status, action), tags=status_tags)
                date_to_row_map[date] = row_id
        
        # Configure tags
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(fill="both", expand=True)
        
        # Function to mark installment as paid
        def mark_as_paid(event):
            try:
                item = tree.identify_row(event.y)
                if not item:
                    return
                    
                values = tree.item(item)["values"]
                date = values[0]
                
                if values[3] == "Mark as Paid":  # Only if action is "Mark as Paid"
                    if customer_service.mark_installment_as_paid(customer_name, date):
                        # Update the row
                        tree.item(item, values=(date, values[1], "Paid", ""), tags=("paid",))
                        messagebox.showinfo("Success", "Installment marked as paid successfully.")
                    else:
                        messagebox.showerror("Error", "Failed to mark installment as paid.")
                        
            except Exception as e:
                logging.error(f"Error marking installment as paid: {str(e)}")
                messagebox.showerror("Error", f"An error occurred while marking the installment: {str(e)}")
                
        # Function to edit installment
        def edit_installment(event):
            try:
                item = tree.identify_row(event.y)
                if not item:
                    return
                    
                values = tree.item(item)["values"]
                date = values[0]
                value = values[1]
                is_paid = values[2] == "Paid"
                
                # Create edit installment window
                edit_window = CTkToplevel(history_window)
                edit_window.geometry("500x450")
                edit_window.title("Edit Installment")
                
                # Make window modal
                edit_window.transient(history_window)
                edit_window.grab_set()
                
                # Create main frame
                main_frame = StyleManager.create_frame(edit_window)
                main_frame.pack(fill="both", expand=True, padx=20, pady=20)
                
                # Add title
                StyleManager.create_label(
                    main_frame,
                    text="Edit Installment Details",
                    font_style="subheading"
                ).pack(pady=(0, 20))
                
                # Customer info (non-editable)
                info_frame = StyleManager.create_frame(main_frame)
                info_frame.pack(fill="x", pady=10)
                
                StyleManager.create_label(
                    info_frame,
                    text=f"Customer: {customer_name}",
                    font_style="body_bold"
                ).pack(anchor="w")
                
                # Editable fields
                fields_frame = StyleManager.create_frame(main_frame)
                fields_frame.pack(fill="x", pady=20)
                
                # Date field
                date_frame = StyleManager.create_frame(fields_frame)
                date_frame.pack(fill="x", pady=10)
                
                StyleManager.create_label(
                    date_frame,
                    text="Installment Date:",
                    font_style="body"
                ).pack(side="left", padx=(0, 10))
                
                date_entry = StyleManager.create_entry(date_frame)
                date_entry.pack(side="left", fill="x", expand=True)
                date_entry.insert(0, date)
                
                # Date picker button
                def open_date_picker():
                    DatePicker(edit_window, date_entry)
                    
                date_picker_btn = StyleManager.create_button(
                    date_frame,
                    text="Date",
                    width=40,
                    command=open_date_picker
                )
                date_picker_btn.pack(side="left", padx=(10, 0))
                
                # Amount field
                amount_frame = StyleManager.create_frame(fields_frame)
                amount_frame.pack(fill="x", pady=10)
                
                StyleManager.create_label(
                    amount_frame,
                    text="Installment Value:",
                    font_style="body"
                ).pack(side="left", padx=(0, 10))
                
                amount_entry = StyleManager.create_entry(amount_frame)
                amount_entry.pack(side="left", fill="x", expand=True)
                amount_entry.insert(0, str(value))
                
                # Paid status
                paid_frame = StyleManager.create_frame(fields_frame)
                paid_frame.pack(fill="x", pady=10)
                
                paid_status = tk.BooleanVar(value=is_paid)
                
                paid_checkbox = CTkCheckBox(
                    paid_frame,
                    text="Paid",
                    variable=paid_status,
                    onvalue=True,
                    offvalue=False,
                    checkbox_width=24,
                    checkbox_height=24,
                    corner_radius=5,
                    border_width=2,
                    fg_color=StyleManager.COLORS["primary"],
                    hover_color=StyleManager.COLORS["secondary"],
                    checkmark_color=StyleManager.COLORS["text"]
                )
                paid_checkbox.pack(anchor="w")
                
                # Action buttons
                buttons_frame = StyleManager.create_frame(main_frame)
                buttons_frame.pack(fill="x", pady=(20, 10))
                buttons_frame.grid_columnconfigure(0, weight=1)
                buttons_frame.grid_columnconfigure(1, weight=1)
                
                # Save changes
                def save_changes():
                    try:
                        new_date = date_entry.get().strip()
                        new_value_str = amount_entry.get().strip()
                        new_paid_status = paid_status.get()
                        
                        # Validate date format
                        try:
                            datetime.strptime(new_date, "%Y-%m-%d")
                        except ValueError:
                            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
                            return
                        
                        # Validate amount
                        if not re.match(r"^\d+(\.\d{1,2})?$", new_value_str):
                            messagebox.showerror("Error", "Installment value must be a valid number.")
                            return
                            
                        new_value = float(new_value_str)
                        
                        # Update installment in database
                        if customer_service.update_installment(customer_name, date, new_date, new_value):
                            # Update paid status if needed
                            if is_paid != new_paid_status:
                                if new_paid_status:
                                    customer_service.mark_installment_as_paid(customer_name, new_date)
                                else:
                                    customer_service.unmark_installment_as_paid(customer_name, new_date)
                                
                            messagebox.showinfo("Success", "Installment updated successfully.")
                            edit_window.destroy()
                            # Refresh the payment history view
                            history_window.destroy()
                            show_payment_history()
                        else:
                            messagebox.showerror("Error", "Failed to update installment.")
                            
                    except Exception as e:
                        logging.error(f"Error saving installment changes: {str(e)}")
                        messagebox.showerror("Error", f"An error occurred while saving changes: {str(e)}")
                    
                StyleManager.create_button(
                    buttons_frame,
                    text="Save Changes",
                    width=200,
                    command=save_changes
                ).grid(row=0, column=0, padx=5, pady=5)
                
                # Cancel button
                StyleManager.create_button(
                    buttons_frame,
                    text="Cancel",
                    width=200,
                    style="secondary",
                    command=edit_window.destroy
                ).grid(row=0, column=1, padx=5, pady=5)
                
            except Exception as e:
                logging.error(f"Error opening edit installment window: {str(e)}")
                messagebox.showerror("Error", f"An error occurred while opening the edit window: {str(e)}")
        
        # Bind double-click event for marking as paid
        tree.bind("<Double-1>", mark_as_paid)
        
        # Bind right-click event for editing
        tree.bind("<Button-3>", edit_installment)
        
        # Calculate payment summary
        if customer_data:
            total_installments = len(installment_dates)
            paid_count = len(paid_installments)
            remaining_count = total_installments - paid_count
            
            # Calculate total amounts
            total_amount = sum(float(installment_values.get(date, default_value)) for date in installment_dates)
            paid_amount = sum(float(installment_values.get(date, default_value)) for date in paid_installments)
            remaining_amount = total_amount - paid_amount
            
            # Create summary frame
            summary_frame = StyleManager.create_frame(main_frame)
            summary_frame.pack(fill="x", padx=20, pady=(0, 20))
            
            # Add summary information
            StyleManager.create_label(
                summary_frame,
                text=f"Paid installments: {paid_count} of {total_installments}",
                font_style="body_bold"
            ).pack(pady=5)
            
            StyleManager.create_label(
                summary_frame,
                text=f"Paid amount: {paid_amount:.2f} of {total_amount:.2f} ({round(paid_amount/total_amount*100, 1)}%)",
                font_style="body_bold"
            ).pack(pady=5)
            
            StyleManager.create_label(
                summary_frame,
                text=f"Remaining amount: {remaining_amount:.2f}",
                font_style="body_bold"
            ).pack(pady=5)
        
        # Close button
        StyleManager.create_button(
            main_frame,
            text="Close",
            style="secondary",
            width=200,
            command=history_window.destroy
        ).pack(side="bottom", pady=20)
        
    except Exception as e:
        logging.error(f"Error showing payment history: {str(e)}")
        messagebox.showerror("Error", f"An error occurred while showing payment history: {str(e)}")

def export_to_excel():
    """Export customer data to Excel file with enhanced formatting."""
    try:
        data = csv_repository.read_data()
        if not data:
            messagebox.showerror("Error", "There is no data to export.")
            return
            
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"customers_export_{timestamp}.xlsx"
        
        # Convert data to DataFrame with Arabic column names
        arabic_columns = {
            "Name": "Customer Name",
            "Phone": "Phone",
            "Amount": "Total Amount",
            "Installments": "Installments",
            "Installment Value": "Installment Value",
            "Start Date": "Start Date",
            "Installment Dates": "Installment Dates",
            "Notification Sent": "Sent"
        }
        
        # Clean and prepare data
        cleaned_data = []
        for row in data:
            cleaned_row = row.copy()
            # Convert boolean to Arabic text
            cleaned_row["Notification Sent"] = "Yes" if row["Notification Sent"] else "No"
            # Ensure numeric values are properly formatted
            try:
                cleaned_row["Amount"] = float(row["Amount"])
                cleaned_row["Installment Value"] = float(row["Installment Value"])
                cleaned_row["Installments"] = int(row["Installments"])
            except (ValueError, TypeError):
                pass
            cleaned_data.append(cleaned_row)
        
        df = pd.DataFrame(cleaned_data)
        df = df.rename(columns=arabic_columns)
        
        # Create Excel writer with xlsxwriter engine
        with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Customer Data', index=False)
            
            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Customer Data']
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'font_name': 'Arial',
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#2B7DE9',
                'font_color': 'white',
                'border': 2,
                'text_wrap': True,
                'border_color': '#1a5fb4'
            })
            
            cell_format = workbook.add_format({
                'font_size': 14,
                'font_name': 'Arial',
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'text_wrap': True,
                'border_color': '#666666'
            })
            
            # Predefined column widths for specific columns
            column_widths = {
                "Customer Name": 25,
                "Phone": 20,
                "Total Amount": 20,
                "Installments": 15,
                "Installment Value": 20,
                "Start Date": 20,
                "Installment Dates": 40,
                "Sent": 15
            }
            
            # Set column widths and apply formats
            for idx, col in enumerate(df.columns):
                # Use predefined width or calculate based on content
                if col in column_widths:
                    col_width = column_widths[col]
                else:
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(str(col))
                    )
                    col_width = min(max(max_length + 4, 15), 50)
                
                worksheet.set_column(idx, idx, col_width)
                worksheet.write(0, idx, col, header_format)
                
                # Apply format to entire column
                for row in range(1, len(df) + 1):
                    worksheet.write(row, idx, df.iloc[row-1][col], cell_format)
            
            # Add alternating row colors
            for row_num in range(1, len(df) + 1):
                row_format = workbook.add_format({
                    'font_size': 14,
                    'font_name': 'Arial',
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 1,
                    'border_color': '#666666',
                    'text_wrap': True,
                    'bg_color': '#F5F5F5' if row_num % 2 == 0 else 'white'
                })
                
                for col_num in range(len(df.columns)):
                    worksheet.write(row_num, col_num, df.iloc[row_num-1][df.columns[col_num]], row_format)
            
            # Set larger row height for all rows
            worksheet.set_default_row(45)  # Increased row height
            worksheet.set_row(0, 60)  # Make header row even taller
            
            # Freeze the header row
            worksheet.freeze_panes(1, 0)
            
            # Set RTL direction for the worksheet
            worksheet.right_to_left()
        
        # Show success message
        messagebox.showinfo("Success", f"Data exported to Excel file: {excel_filename}")
        
        # Open the Excel file automatically
        os.startfile(os.path.abspath(excel_filename))
        
    except ImportError:
        messagebox.showerror("Error", "Please make sure the xlsxwriter package is installed.")
        logging.error("xlsxwriter package not installed")
    except Exception as e:
        logging.error(f"Error exporting to Excel: {str(e)}")
        messagebox.showerror("Error", "An error occurred while exporting data.")

    frame = frames["view"]
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=0)  # Header
    frame.grid_rowconfigure(1, weight=0)  # Search bar
    frame.grid_rowconfigure(2, weight=1)  # Table
    frame.grid_rowconfigure(3, weight=0)  # Buttons
    
    # Simplified header with clean design
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 15))
    header_frame.grid_columnconfigure(0, weight=1)
    
    StyleManager.create_label(
        header_frame,
        text="Customers",
        font_style="heading"
    ).grid(row=0, column=0, pady=(5, 5), sticky="w")
    
    # Simplified search area with better spacing
    search_frame = StyleManager.create_frame(frame)
    search_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 15))
    search_frame.grid_columnconfigure(1, weight=1)
    
    # Simple search label
    StyleManager.create_label(
        search_frame,
        text="Search:",
        font_style="body_bold"
    ).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
    
    # Clean search entry
    search_entry = StyleManager.create_entry(
        search_frame,
        width=400,
        font=("Arial", 14),
        height=35,
        placeholder_text="Enter customer name or phone number..."
    )
    search_entry.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ew")
    
    def perform_search():
        query = search_entry.get().strip()
        results = customer_service.search_customers(query)
        refresh_treeview(frame.tree, results)
        
        # Update status message with search results
        result_count = len(results)
        status_label.configure(text=f"Customers: {result_count}")
    
    # Add keyboard binding for Enter key
    search_entry.bind("<Return>", lambda event: perform_search())
    
    search_button = StyleManager.create_button(
        search_frame,
        text="Search",
        width=100,
        height=35,
        command=perform_search
    )
    search_button.grid(row=0, column=2, padx=(0, 0), pady=5)
    
    # Simple status label
    status_label = StyleManager.create_label(
        search_frame,
        text="",
        font_style="small",
        text_color=StyleManager.COLORS["text_secondary"]
    )
    status_label.grid(row=0, column=3, padx=(10, 0), pady=5, sticky="e")
    
    # Clean table container with more breathing room
    table_frame = StyleManager.create_frame(frame)
    table_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 20))
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)
    
    # Configure Treeview style for better visibility and modern look
    style = ttk.Style()
    style.configure(
        "Custom.Treeview",
        rowheight=40,
        font=("Arial", 12),
        background=StyleManager.COLORS["surface"],
        foreground=StyleManager.COLORS["text"],
        fieldbackground=StyleManager.COLORS["surface"]
    )
    style.configure(
        "Custom.Treeview.Heading",
        font=("Arial", 12, "bold"),
        background=StyleManager.COLORS["primary"],
        foreground=StyleManager.COLORS["text"]
    )
    style.map(
        "Custom.Treeview",
        background=[("selected", StyleManager.COLORS["primary"])],
        foreground=[("selected", StyleManager.COLORS["text"])]
    )
    
    # Define column headers mapping - simplified
    column_headers = {
        "Name": "Customer Name",
        "Phone": "Phone",
        "Amount": "Amount",
        "Installments": "Installments",
        "Installment Value": "Installment Value",
        "Start Date": "Start Date"
    }
    
    # Create Treeview with responsive columns
    tree = ttk.Treeview(
        table_frame,
        columns=list(column_headers.keys()),
        show="headings",
        style="Custom.Treeview"
    )
    
    # Configure column proportions
    column_weights = {
        "Name": 25,
        "Phone": 20,
        "Amount": 15,
        "Installments": 15,
        "Installment Value": 15,
        "Start Date": 10
    }
    
    # Set dynamic column widths and headers
    for col in column_headers.keys():
        width = int((column_weights[col] / 100) * 1200)  # Base width of 1200 pixels
        tree.column(col, width=width, minwidth=100)
        tree.heading(col, text=column_headers[col])
    
    tree.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
    
    # Add scrollbars
    y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    y_scrollbar.grid(row=0, column=1, sticky="ns")
    
    x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    x_scrollbar.grid(row=1, column=0, sticky="ew")
    
    tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
    
    # Store the Treeview widget as an attribute of the frame
    frame.tree = tree
    
    # Initial data load
    refresh_treeview(tree)
    
    # Update status label with initial count
    data = csv_repository.read_data()
    status_label.configure(text=f"Customers: {len(data)}")
    
    # Edit customer function - keeping functionality intact
    def edit_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Select a customer to edit.")
            return
            
        # Get selected customer data
        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]
        
        # Get full customer data
        data = csv_repository.read_data()
        customer = next((c for c in data if c["Name"] == customer_name), None)
        
        if not customer:
            messagebox.showerror("Error", "Customer data was not found.")
            return
        
        # Create edit window
        edit_window = CTkToplevel(app)
        edit_window.geometry("800x600")
        edit_window.title(f"Edit Customer Details: {customer_name}")
        
        # Add header
        StyleManager.create_label(
            edit_window,
            text=f"Edit Customer Details: {customer_name}",
            font_style="heading"
        ).pack(pady=(20, 10))
        
        # Create form container
        form_frame = StyleManager.create_frame(edit_window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Form fields with current values
        fields = [
            {"label": "Customer Name:", "key": "Name", "type": "text"},
            {"label": "Phone:", "key": "Phone", "type": "phone"},
            {"label": "Amount:", "key": "Amount", "type": "number"},
            {"label": "Installments:", "key": "Installments", "type": "number"}
        ]
        
        entries = {}
        row = 0
        
        for field in fields:
            # Create field container
            field_frame = StyleManager.create_frame(form_frame)
            field_frame.pack(fill="x", padx=10, pady=10)
            field_frame.grid_columnconfigure(1, weight=1)
            
            # Add label
            StyleManager.create_label(
                field_frame,
                text=field["label"],
                font_style="body_bold"
            ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            # Add entry with current value
            entry = StyleManager.create_entry(field_frame, width=300)
            entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
            entry.insert(0, str(customer.get(field["key"], "")))
            entries[field["key"]] = entry
            
            row += 1
        
        # Date Picker Section
        date_frame = StyleManager.create_frame(form_frame)
        date_frame.pack(fill="x", padx=10, pady=10)
        date_frame.grid_columnconfigure(1, weight=1)
        
        StyleManager.create_label(
            date_frame,
            text="Installment Start Date:",
            font_style="body_bold"
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        start_date_entry = StyleManager.create_entry(date_frame, width=200)
        start_date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        start_date_entry.insert(0, str(customer.get("Start Date", "")))
        entries["Start Date"] = start_date_entry
        
        date_picker_btn = StyleManager.create_button(
            date_frame,
            text="Select Date",
            style="secondary",
            command=lambda: DatePicker(edit_window, start_date_entry)
        )
        date_picker_btn.grid(row=0, column=2, padx=10, pady=5)
        
        # Buttons container
        buttons_frame = StyleManager.create_frame(edit_window)
        buttons_frame.pack(fill="x", padx=20, pady=20)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        def save_changes():
            # Validation patterns
            name_pattern = r"^[A-Za-z\u0600-\u06FF\s]+$"
            phone_pattern = r"^\+?\d{10,15}$"
            amount_pattern = r"^\d+(\.\d{1,2})?$"
            installments_pattern = r"^\d+$"
            
            # Get values from entries
            name = entries["Name"].get().strip()
            phone = entries["Phone"].get().strip()
            amount = entries["Amount"].get().strip()
            installments = entries["Installments"].get().strip()
            start_date = entries["Start Date"].get().strip()
            
            # Validate inputs
            if not re.fullmatch(name_pattern, name):
                messagebox.showerror("Error", "Name can contain only letters and spaces.")
                return
                
            if not re.fullmatch(phone_pattern, phone):
                messagebox.showerror("Error", "Phone number must contain digits only and may start with +.")
                return
                
            if not re.fullmatch(amount_pattern, amount):
                messagebox.showerror("Error", "Amount must be a valid number.")
                return
                
            if not re.fullmatch(installments_pattern, installments):
                messagebox.showerror("Error", "Installments must be a whole number.")
                return
            
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
                return
            
            try:
                updated_data = customer_service.build_customer_record(
                    name,
                    phone,
                    amount,
                    installments,
                    start_date,
                    date_strategy="thirty_day",
                    include_tracking_fields=False,
                )
                
                # If name changed, delete old record and create new one
                if customer_name != name:
                    if customer_service.delete_customer(customer_name) and customer_service.append_customer({
                        **updated_data,
                        "Notification Sent": customer.get("Notification Sent", False),
                        "Paid_Installments": customer.get("Paid_Installments", "[]"),
                        "Notified_Installments": customer.get("Notified_Installments", "[]"),
                        "Installment_Values": customer.get("Installment_Values", "{}"),
                    }):
                        messagebox.showinfo("Success", "Customer updated successfully.")
                        edit_window.destroy()
                        refresh_treeview(tree)
                        refresh_payment_history_views()  # Refresh payment history views
                    else:
                        messagebox.showerror("Error", "Failed to update customer.")
                else:
                    # Update existing record
                    if customer_service.update_customer(customer_name, updated_data):
                        messagebox.showinfo("Success", "Customer updated successfully.")
                        edit_window.destroy()
                        refresh_treeview(tree)
                        refresh_payment_history_views()  # Refresh payment history views
                    else:
                        messagebox.showerror("Error", "Failed to update customer.")
                
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input data: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            
        # Save Button
        StyleManager.create_button(
            buttons_frame,
            text="Save Changes",
            width=200,
            command=save_changes
        ).grid(row=0, column=0, padx=10, pady=10)
        
        # Cancel Button
        StyleManager.create_button(
            buttons_frame,
            text="Cancel",
            style="secondary",
            width=200,
            command=edit_window.destroy
        ).grid(row=0, column=1, padx=10, pady=10)
        
        # Make the window modal
        edit_window.transient(app)
        edit_window.grab_set()
        edit_window.focus_set()
    
    # Delete customer function
    def delete_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Select a customer to delete.")
            return
            
        # Get selected customer data
        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete customer {customer_name}?\nThis action cannot be undone."):
            if customer_service.delete_customer(customer_name):
                messagebox.showinfo("Success", f"Deleted customer {customer_name} successfully.")
                refresh_treeview(tree)
            else:
                messagebox.showerror("Error", "Failed to delete customer.")
    
    # Action buttons with simplified design
    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 30))
    
    # Create two columns for better spacing
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)
    
    # Left buttons container
    left_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    left_buttons.grid(row=0, column=0, sticky="w")
    
    # Right buttons container
    right_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    right_buttons.grid(row=0, column=1, sticky="e")
    
    # Left side buttons - operations
    refresh_btn = StyleManager.create_button(
        left_buttons,
        text="Refresh",
        width=120,
        command=lambda: refresh_treeview(tree)
    )
    refresh_btn.pack(side="left", padx=(0, 10), pady=10)
    
    history_btn = StyleManager.create_button(
        left_buttons,
        text="Payment History",
        width=120,
        command=show_payment_history
    )
    history_btn.pack(side="left", padx=(0, 10), pady=10)

    export_btn = StyleManager.create_button(
        left_buttons,
        text="Export Excel",
        width=120,
        command=export_to_excel
    )
    export_btn.pack(side="left", padx=(0, 10), pady=10)
    
    # Right side buttons - customer management
    back_btn = StyleManager.create_button(
        right_buttons,
        text="Back",
        style="secondary",
        width=120,
        command=lambda: show_frame(frames["home"])
    )
    back_btn.pack(side="right", padx=(0, 0), pady=10)
    
    delete_btn = StyleManager.create_button(
        right_buttons,
        text="Delete Customer",
        style="danger",
        width=120,
        command=delete_customer
    )
    delete_btn.pack(side="right", padx=(0, 10), pady=10)
    
    edit_btn = StyleManager.create_button(
        right_buttons,
        text="Edit Customer",
        width=120,
        command=edit_customer
    )
    edit_btn.pack(side="right", padx=(0, 10), pady=10)

def check_due_installments():
    """Check for installments due in 3 days and send notifications."""
    while True:
        try:
            logging.info("Starting automatic installment check")
            
            # Read customer data
            data = csv_repository.read_data()
            if not data:
                logging.info("No customer data found for notifications")
                time.sleep(60 * 60)  # Check again in 1 hour
                continue
                
            # Get current date
            today = datetime.now()
            notification_window = 3  # days before payment to send notification
            
            # Track notification results
            success_count = 0
            fail_count = 0
            skip_count = 0
            
            logging.info(f"Checking notifications for {len(data)} customers")
            
            # Check each customer
            for customer in data:
                try:
                    # Get installment dates
                    dates_str = customer.get("Installment Dates", "")
                    if not dates_str:
                        logging.warning(f"Customer {customer['Name']} has no installment dates")
                        continue
                        
                    # Get paid installments to skip them
                    try:
                        paid_installments = load_json_list(customer.get("Paid_Installments", "[]"))
                    except:
                        paid_installments = []
                        
                    # Get notified installments
                    try:
                        notified_installments = load_json_list(customer.get("Notified_Installments", "[]"))
                    except:
                        notified_installments = []
                        
                    installment_dates = dates_str.split(";")
                    
                    # Check each installment date
                    for date_str in installment_dates:
                        try:
                            # Skip if already paid or notified
                            if date_str in paid_installments or date_str in notified_installments:
                                continue
                                
                            date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
                            days_until_due = (date - today).days
                            
                            # Send notification if due within notification window
                            if 0 <= days_until_due <= notification_window:
                                logging.info(f"Found upcoming payment for {customer['Name']} due in {days_until_due} days")
                                
                                message = (
                                    f"Hello {customer['Name']},\n"
                                    f"This is a reminder for an installment payment of {customer['Installment Value']} SAR "
                                    f"due on {date_str}.\n"
                                    f"Thank you for your business."
                                )
                                
                                # Prepare phone number
                                phone = customer["Phone"]
                                if not phone.startswith("+"):
                                    phone = "+" + phone
                                
                                # Add a small delay to prevent rate limiting
                                time.sleep(2)
                                
                                max_retries = 2
                                retry_count = 0
                                success = False
                                last_error = None
                                
                                # Try sending with retries
                                while retry_count < max_retries and not success:
                                    retry_count += 1
                                    try:
                                        logging.info(f"Attempt {retry_count} to send notification to {customer['Name']} at {phone}")
                                        
                                        # Send WhatsApp message with increased delays
                                        kit.sendwhatmsg_instantly(
                                            phone_no=phone,
                                            message=message,
                                            wait_time=30,  # Increased wait time to 30 seconds
                                            tab_close=True,
                                            close_time=20  # Increased close time to 20 seconds
                                        )
                                        
                                        # Add additional delay after sending
                                        time.sleep(5)
                                        
                                        # Update notification status for this installment
                                        notified_installments.append(date_str)
                                        customer["Notified_Installments"] = dump_json(notified_installments)
                                        csv_repository.save_data(data)
                                        logging.info(f"Automatic notification sent to {customer['Name']} at {phone} for installment {date_str}")
                                        success = True
                                        success_count += 1
                                        
                                    except Exception as e:
                                        last_error = str(e)
                                        logging.error(f"Error sending WhatsApp message to {customer['Name']} at {phone} (Attempt {retry_count}): {last_error}")
                                        
                                        # Wait before retry
                                        if retry_count < max_retries:
                                            time.sleep(10)  # Increased retry delay to 10 seconds
                                
                                if not success:
                                    fail_count += 1
                                    logging.error(f"Failed to send notification to {customer['Name']} after {max_retries} attempts. Last error: {last_error}")
                                    
                        except ValueError as e:
                            logging.error(f"Error parsing date {date_str} for customer {customer['Name']}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logging.error(f"Error processing customer {customer.get('Name', 'unknown')}: {str(e)}")
                    
            # Log summary of notification attempts
            logging.info(f"Notification check completed. Success: {success_count}, Failed: {fail_count}, Skipped: {skip_count}")
                
        except Exception as e:
            logging.error(f"Error in automatic notification check: {str(e)}")
            
        # Sleep for 1 hour before next check
        time.sleep(60 * 60)

def start_notification_thread():
    """Start a background thread to check for due installments."""
    notification_thread = threading.Thread(target=check_due_installments, daemon=True)
    notification_thread.start()
    logging.info("Notification thread started")

def refresh_payment_history_views():
    """Refresh all open payment history windows."""
    for widget in app.winfo_children():
        if isinstance(widget, CTkToplevel) and "Payment History" in widget.title():
            widget.destroy()

def load_installments_data():
    """Load data into the installments management treeview"""
    try:
        frame = frames["manage"]
        tree = frame.tree
        
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Get customer data
        data = csv_repository.read_data()
        
        for customer in data:
            try:
                # Get paid and total installments
                paid_installments = load_json_list(customer.get("Paid_Installments", "[]"))
                total_installments = int(customer.get("Installments", 0))
                
                # Get next due date
                installment_dates = customer.get("Installment Dates", "").split(";")
                next_due = ""
                for date in installment_dates:
                    if date not in paid_installments:
                        next_due = date
                        break
                
                # Format amount with two decimal places
                amount = float(customer.get("Amount", 0))
                formatted_amount = f"{amount:.2f}"
                
                # Insert into tree
                item = tree.insert("", "end", values=(
                    customer.get("Name", ""),
                    customer.get("Phone", ""),
                    formatted_amount,
                    total_installments,
                    f"{len(paid_installments)}/{total_installments}",
                    next_due
                ))
                
                # Add color coding based on payment status
                if len(paid_installments) == total_installments:
                    tree.item(item, tags=("paid",))
                else:
                    tree.item(item, tags=("unpaid",))
                
            except Exception as e:
                logging.error(f"Error processing customer in load_installments_data: {str(e)}")
                continue
        
        # Configure payment status styles
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
                
    except Exception as e:
        logging.error(f"Error loading installments data: {str(e)}")
        messagebox.showerror("Error", "An error occurred while loading data.")

def show_installment_details(event):
    """Show details of a selected installment"""
    try:
        # Get the selected item
        tree = frames["manage"].tree
        selection = tree.selection()
        if not selection:
            return
            
        # Get customer data
        item = selection[0]
        values = tree.item(item, "values")
        customer_name = values[0]
        phone = values[1]
        
        # Get customer data from CSV
        data = csv_repository.read_data()
        customer = next((c for c in data if c["Name"] == customer_name and c["Phone"] == phone), None)
        if not customer:
            messagebox.showerror("Error", "Customer data was not found.")
            return
            
        # Create details window
        details_window = CTkToplevel(app)
        details_window.title(f"Installment Details - {customer_name}")
        details_window.geometry("600x400")
        details_window.resizable(False, False)
        
        # Create main frame
        main_frame = StyleManager.create_frame(details_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create header
        header_frame = StyleManager.create_frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        StyleManager.create_label(
            header_frame,
            text=f"Customer Installment Details: {customer_name}",
            font_style="subheading"
        ).pack()
        
        # Create treeview
        tree_frame = StyleManager.create_frame(main_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Create treeview
        tree = ttk.Treeview(
            tree_frame,
            columns=("date", "amount", "status"),
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )
        
        # Configure columns
        tree.heading("date", text="Installment Date")
        tree.heading("amount", text="Amount")
        tree.heading("status", text="Status")
        
        tree.column("date", width=150, anchor="center")
        tree.column("amount", width=150, anchor="center")
        tree.column("status", width=150, anchor="center")
        
        # Pack tree and scrollbars
        tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        
        y_scroll.config(command=tree.yview)
        x_scroll.config(command=tree.xview)
        
        # Get installment data
        total_amount = float(customer.get("Amount", 0))
        total_installments = int(customer.get("Installments", 0))
        installment_amount = total_amount / total_installments
        paid_installments = load_json_list(customer.get("Paid_Installments", "[]"))
        installment_dates = customer.get("Installment Dates", "").split(";")
        
        # Add installments to tree
        for date in installment_dates:
            if date:
                status = "Paid" if date in paid_installments else "Unpaid"
                tree.insert("", "end", values=(
                    date,
                    f"{installment_amount:.2f}",
                    status
                ))
        
        # Configure styles
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
        
        # Add buttons frame
        buttons_frame = StyleManager.create_frame(main_frame)
        buttons_frame.pack(fill="x", pady=(20, 0))
        
        # Add mark as paid button
        def mark_as_paid():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Notice", "Please select an installment.")
                return
                
            item = selection[0]
            values = tree.item(item, "values")
            date = values[0]
            
            if date in paid_installments:
                messagebox.showinfo("Information", "This installment is already paid.")
                return
                
            if customer_service.mark_installment_as_paid(customer_name, date):
                tree.item(item, values=(date, values[1], "Paid"), tags=("paid",))
                messagebox.showinfo("Success", "Installment marked as paid.")
                load_installments_data()  # Refresh main view
            else:
                messagebox.showerror("Error", "Failed to mark installment as paid.")
        
        StyleManager.create_button(
            buttons_frame,
            text="Mark as Paid",
            command=mark_as_paid
        ).pack(side="right", padx=5)
        
        # Add unmark as paid button
        def unmark_as_paid():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Notice", "Please select an installment.")
                return
                
            item = selection[0]
            values = tree.item(item, "values")
            date = values[0]
            
            if date not in paid_installments:
                messagebox.showinfo("Information", "This installment is not paid.")
                return
                
            if customer_service.unmark_installment_as_paid(customer_name, date):
                tree.item(item, values=(date, values[1], "Unpaid"), tags=("unpaid",))
                messagebox.showinfo("Success", "Installment payment mark removed.")
                load_installments_data()  # Refresh main view
            else:
                messagebox.showerror("Error", "Failed to unmark installment as paid.")
        
        StyleManager.create_button(
            buttons_frame,
            text="Unmark Payment",
            command=unmark_as_paid
        ).pack(side="right", padx=5)
        
        # Add close button
        StyleManager.create_button(
            buttons_frame,
            text="Close",
            command=details_window.destroy
        ).pack(side="left")
        
    except Exception as e:
        logging.error(f"Error showing installment details: {str(e)}")
        messagebox.showerror("Error", "An error occurred while showing installment details.")

def perform_installment_search():
    """Search for installments based on the search query"""
    try:
        frame = frames["manage"]
        search_query = frame.search_entry.get().strip().lower()
        tree = frame.tree
        
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Get customer data
        data = csv_repository.read_data()
        
        for customer in data:
            try:
                # Check if customer matches search query
                if (search_query in customer.get("Name", "").lower() or 
                    search_query in customer.get("Phone", "").lower()):
                    
                    # Get paid and total installments
                    paid_installments = load_json_list(customer.get("Paid_Installments", "[]"))
                    total_installments = int(customer.get("Installments", 0))
                    
                    # Get next due date
                    installment_dates = customer.get("Installment Dates", "").split(";")
                    next_due = ""
                    for date in installment_dates:
                        if date not in paid_installments:
                            next_due = date
                            break
                    
                    # Format amount with two decimal places
                    amount = float(customer.get("Amount", 0))
                    formatted_amount = f"{amount:.2f}"
                    
                    # Insert into tree
                    item = tree.insert("", "end", values=(
                        customer.get("Name", ""),
                        customer.get("Phone", ""),
                        formatted_amount,
                        total_installments,
                        f"{len(paid_installments)}/{total_installments}",
                        next_due
                    ))
                    
                    # Add color coding based on payment status
                    if len(paid_installments) == total_installments:
                        tree.item(item, tags=("paid",))
                    else:
                        tree.item(item, tags=("unpaid",))
                
            except Exception as e:
                logging.error(f"Error processing customer in search: {str(e)}")
                continue
        
        # Configure payment status styles
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
                
    except Exception as e:
        logging.error(f"Error performing installment search: {str(e)}")
        messagebox.showerror("Error", "An error occurred while searching.")

# Initialize the application and create frames
if __name__ == "__main__":
    try:
        # Initialize the application and create frames
        app = initialize_app()
        if not app:
            raise Exception("Failed to initialize application")
            
        # Setup theme
        try:
            StyleManager.setup_theme()
            logging.info("Theme setup completed")
        except Exception as e:
            logging.error(f"Theme setup failed: {str(e)}")
            messagebox.showwarning("Warning", "Failed to load the custom style. The default style will be used.")
        
        # Create fixed sidebar shell and content canvas
        container = create_app_shell(app)
        
        # Create frames
        page_names = ["home", "add", "view", "manage", "backup_restore", "send_notification"]  # Removed manage_installments, using manage instead
        
        for name in page_names:
            try:
                frame = StyleManager.create_frame(container)
                frame.grid(row=0, column=0, sticky="nsew")
                frame.page_name = name
                frames[name] = frame
                frame.grid_columnconfigure(0, weight=1)
                frame.grid_rowconfigure(0, weight=1)
                logging.info(f"Created frame: {name}")
            except Exception as e:
                logging.error(f"Error creating frame {name}: {str(e)}")
                raise
        
        # Setup all pages with error handling
        setup_functions = [
            ("setup_home_page", lambda: setup_home_page_module(frames, StyleManager, show_frame, app)),
            ("setup_add_page", lambda: setup_add_page_module(frames, StyleManager, app, validate_and_save, DatePicker, show_frame)),
            (
                "setup_view_page",
                lambda: setup_view_page_module(
                    frames,
                    StyleManager,
                    customer_service,
                    refresh_treeview,
                    show_frame,
                    app,
                    DatePicker,
                    refresh_payment_history_views,
                    export_to_excel,
                    show_payment_history,
                ),
            ),
            (
                "setup_manage_installments_page",
                lambda: setup_manage_installments_page_module(
                    frames,
                    StyleManager,
                    customer_service,
                    refresh_treeview,
                    show_frame,
                    app,
                    DatePicker,
                    refresh_payment_history_views,
                ),
            ),
            ("setup_backup_restore_page", lambda: setup_backup_restore_page_module(frames, StyleManager, csv_repository, show_frame, app)),
            ("setup_send_notification_page", lambda: setup_send_notification_page_module(frames, StyleManager, csv_repository, show_frame, app))
        ]
        
        for func_name, func in setup_functions:
            try:
                if not callable(func):
                    raise Exception(f"{func_name} is not defined")
                func()
                logging.info(f"{func_name} completed successfully")
            except Exception as e:
                logging.error(f"Error in {func_name}: {str(e)}")
                raise
        
        # Show home frame and start notification thread
        show_frame(frames["home"])
        start_notification_thread()
        
        # Start the main loop
        main(app)
    except Exception as e:
        logging.critical(f"Application failed to start: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("Critical Error", "Failed to start the application. Please make sure all required libraries are installed.")
        sys.exit(1)

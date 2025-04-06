import customtkinter
from customtkinter import *
from tkinter import messagebox, ttk, StringVar, BooleanVar, filedialog
import tkinter as tk
import re
import csv
import os
import pandas as pd
from datetime import datetime, timedelta
from tkcalendar import Calendar
import shutil
import threading
import pywhatkit as kit
import logging
from typing import List, Dict, Optional, Union
import time
import sys
import traceback

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
app = None
frames = {}

class StyleManager:
    """Manages application-wide styling"""
    
    # Color scheme
    COLORS = {
        "primary": "#2B7DE9",      # Blue
        "secondary": "#23B0FF",    # Light Blue
        "success": "#28a745",      # Green
        "warning": "#ffc107",      # Yellow
        "danger": "#dc3545",       # Red
        "background": "#1a1a1a",   # Dark background
        "surface": "#2d2d2d",      # Slightly lighter background
        "text": "#ffffff",         # White text
        "text_secondary": "#b3b3b3", # Gray text
        "border": "#404040"        # Border color
    }
    
    # Font configurations
    FONTS = {
        "heading": ("Arial", 24, "bold"),
        "subheading": ("Arial", 18, "bold"),
        "body": ("Arial", 14),
        "body_bold": ("Arial", 14, "bold"),
        "small": ("Arial", 12),
        "button": ("Arial", 16, "bold")
    }
    
    # Button styles
    BUTTON_STYLES = {
        "primary": {
            "fg_color": COLORS["primary"],
            "hover_color": COLORS["secondary"],
            "text_color": COLORS["text"],
            "font": ("Arial", 18, "bold"),
            "corner_radius": 12,
            "border_width": 0,
            "height": 45
        },
        "secondary": {
            "fg_color": "transparent",
            "hover_color": COLORS["surface"],
            "text_color": COLORS["text"],
            "font": ("Arial", 18, "bold"),
            "corner_radius": 12,
            "border_width": 2,
            "border_color": COLORS["primary"],
            "height": 45
        },
        "danger": {
            "fg_color": COLORS["danger"],
            "hover_color": "#c82333",
            "text_color": COLORS["text"],
            "font": ("Arial", 18, "bold"),
            "corner_radius": 12,
            "border_width": 0,
            "height": 45
        }
    }
    
    @classmethod
    def setup_theme(cls):
        """Configure the global theme settings"""
        try:
            customtkinter.set_appearance_mode("dark")
            customtkinter.set_default_color_theme("blue")
            
            # Configure ttk styles for Treeview
            style = ttk.Style()
            style.theme_use('default')
            
            # Configure Treeview colors
            style.configure("Treeview",
                background=cls.COLORS["surface"],
                foreground=cls.COLORS["text"],
                fieldbackground=cls.COLORS["surface"],
                font=cls.FONTS["body"]
            )
            
            # Configure Treeview selected items
            style.map('Treeview',
                background=[('selected', cls.COLORS["primary"])],
                foreground=[('selected', cls.COLORS["text"])]
            )
            
            # Configure Treeview headers
            style.configure("Treeview.Heading",
                background=cls.COLORS["primary"],
                foreground=cls.COLORS["text"],
                font=cls.FONTS["body_bold"]
            )
            
            logging.info("Theme setup completed successfully")
        except Exception as e:
            logging.error(f"Error setting up theme: {str(e)}")
            raise
    
    @classmethod
    def create_frame(cls, master, **kwargs) -> CTkFrame:
        """Create a styled frame"""
        try:
            # Create base frame configuration
            frame_config = {
                "corner_radius": 15,
                "border_width": 0
            }
            
            # Only set fg_color if not provided in kwargs
            if "fg_color" not in kwargs:
                frame_config["fg_color"] = cls.COLORS["surface"]
            
            # Update with any additional kwargs
            frame_config.update(kwargs)
            
            return CTkFrame(
                master,
                **frame_config
            )
        except Exception as e:
            logging.error(f"Error creating frame: {str(e)}")
            raise
    
    @classmethod
    def create_button(cls, master, text: str, style: str = "primary", **kwargs) -> CTkButton:
        """Create a styled button"""
        try:
            button_style = cls.BUTTON_STYLES[style].copy()
            button_style.update(kwargs)
            return CTkButton(master, text=text, **button_style)
        except Exception as e:
            logging.error(f"Error creating button: {str(e)}")
            raise
    
    @classmethod
    def create_label(cls, master, text: str, font_style: str = "body", **kwargs) -> CTkLabel:
        """Create a styled label"""
        try:
            # Only set text_color and font if not provided in kwargs
            if 'text_color' not in kwargs:
                kwargs['text_color'] = cls.COLORS["text"]
            if 'font' not in kwargs:
                kwargs['font'] = cls.FONTS[font_style]
                
            return CTkLabel(
                master,
                text=text,
                **kwargs
            )
        except Exception as e:
            logging.error(f"Error creating label: {str(e)}")
            raise
    
    @classmethod
    def create_entry(cls, master, **kwargs) -> CTkEntry:
        """Create a styled entry"""
        try:
            entry_config = {
                "fg_color": cls.COLORS["background"],
                "text_color": cls.COLORS["text"],
                "border_color": cls.COLORS["primary"],
                "corner_radius": 8
            }
            
            # Only set font if not provided in kwargs
            if 'font' not in kwargs:
                entry_config['font'] = cls.FONTS["body"]
                
            # Update with any additional kwargs
            entry_config.update(kwargs)
            
            return CTkEntry(
                master,
                **entry_config
            )
        except Exception as e:
            logging.error(f"Error creating entry: {str(e)}")
            raise

class FileManager:
    """Handles all file operations for customer documents"""
    def __init__(self, base_dir: str = "customer_files"):
        self.base_dir = base_dir
        self._ensure_base_directory()
        
    def _ensure_base_directory(self):
        """Ensure the base directory exists"""
        try:
            if not os.path.exists(self.base_dir):
                os.makedirs(self.base_dir)
                logging.info(f"Created base directory: {self.base_dir}")
        except Exception as e:
            logging.error(f"Error creating base directory: {str(e)}")
            raise
            
    def _get_customer_dir(self, customer_name: str) -> str:
        """Get the directory path for a customer's files"""
        # Sanitize customer name for use in file path
        safe_name = "".join(c for c in customer_name if c.isalnum() or c in (' ', '-', '_')).strip()
        customer_dir = os.path.join(self.base_dir, safe_name)
        
        # Create customer directory if it doesn't exist
        if not os.path.exists(customer_dir):
            os.makedirs(customer_dir)
            logging.info(f"Created customer directory: {customer_dir}")
            
        return customer_dir
        
    def add_files(self, customer_name: str, files: List[str]) -> bool:
        """Add files for a customer"""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            success = True
            
            for file_path in files:
                try:
                    # Get file name and create safe version
                    file_name = os.path.basename(file_path)
                    safe_name = "".join(c for c in file_name if c.isalnum() or c in ('.', '-', '_')).strip()
                    
                    # Create unique filename if file already exists
                    base, ext = os.path.splitext(safe_name)
                    counter = 1
                    while os.path.exists(os.path.join(customer_dir, safe_name)):
                        safe_name = f"{base}_{counter}{ext}"
                        counter += 1
                    
                    # Copy file to customer directory
                    dest_path = os.path.join(customer_dir, safe_name)
                    shutil.copy2(file_path, dest_path)
                    logging.info(f"Added file {safe_name} for customer {customer_name}")
                    
                except Exception as e:
                    logging.error(f"Error adding file {file_path} for customer {customer_name}: {str(e)}")
                    success = False
                    
            return success
            
        except Exception as e:
            logging.error(f"Error in add_files for customer {customer_name}: {str(e)}")
            return False
            
    def get_files(self, customer_name: str) -> List[str]:
        """Get list of files for a customer"""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            if not os.path.exists(customer_dir):
                return []
                
            return [f for f in os.listdir(customer_dir) if os.path.isfile(os.path.join(customer_dir, f))]
            
        except Exception as e:
            logging.error(f"Error getting files for customer {customer_name}: {str(e)}")
            return []
            
    def delete_file(self, customer_name: str, file_name: str) -> bool:
        """Delete a specific file for a customer"""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            file_path = os.path.join(customer_dir, file_name)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Deleted file {file_name} for customer {customer_name}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error deleting file {file_name} for customer {customer_name}: {str(e)}")
            return False
            
    def delete_customer_files(self, customer_name: str) -> bool:
        """Delete all files for a customer"""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            if os.path.exists(customer_dir):
                shutil.rmtree(customer_dir)
                logging.info(f"Deleted all files for customer {customer_name}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error deleting files for customer {customer_name}: {str(e)}")
            return False
            
    def open_file(self, customer_name: str, file_name: str) -> bool:
        """Open a file using the system's default application"""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            file_path = os.path.join(customer_dir, file_name)
            
            if os.path.exists(file_path):
                os.startfile(file_path)
                logging.info(f"Opened file {file_name} for customer {customer_name}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error opening file {file_name} for customer {customer_name}: {str(e)}")
            return False

# Initialize file manager
file_manager = FileManager()

def initialize_app():
    """Initialize the main application window with error handling"""
    global app
    try:
        logging.info("Starting application initialization...")
        
        # Initialize the main window
        app = CTk()
        if not app:
            raise Exception("Failed to create main window")
            
        app.geometry("1280x800")
        app.title("نظام إدارة الأقساط")
        
        # Try setting appearance mode
        try:
            app._set_appearance_mode("dark")
            logging.info("Appearance mode set successfully")
        except Exception as e:
            logging.error(f"Failed to set appearance mode: {str(e)}")
            # Continue anyway as this is not critical
        
        # Center the window on screen
        try:
            screen_width = app.winfo_screenwidth()
            screen_height = app.winfo_screenheight()
            x = (screen_width - 1280) // 2
            y = (screen_height - 800) // 2
            app.geometry(f"1280x800+{x}+{y}")
            logging.info("Window centered successfully")
        except Exception as e:
            logging.error(f"Failed to center window: {str(e)}")
            # Continue anyway as this is not critical
        
        return app
    except Exception as e:
        logging.critical(f"Failed to initialize application: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("خطأ حرج", "فشل في بدء التطبيق. يرجى مراجعة ملف السجل للتفاصيل.")
        sys.exit(1)

def main():
    """Main application entry point with error handling"""
    global app
    try:
        logging.info("Application starting...")
        if not app:
            app = initialize_app()
        app.mainloop()
    except Exception as e:
        logging.critical(f"Critical error in main: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("خطأ حرج", f"حدث خطأ غير متوقع: {str(e)}\nيرجى مراجعة ملف السجل للتفاصيل.")
        sys.exit(1)

def show_frame(frame):
    """Show the specified frame and hide others"""
    for f in frames.values():
        f.grid_remove()
    frame.grid()

def refresh_treeview(tree, data=None):
    """Refresh the treeview with data."""
    # Clear existing items
    for item in tree.get_children():
        tree.delete(item)
        
    # If no data provided, read from CSV
    if data is None:
        data = csv_manager.read_data()
    
    # Insert data into treeview with proper status handling
    for customer in data:
        # Handle payment status if viewing payment-related data
        if "Paid" in tree["columns"]:
            values = []
            for col in tree["columns"]:
                if col == "Paid":
                    # Get the installment date from the row
                    date_idx = tree["columns"].index("Installment Date")
                    installment_date = customer.get("Installment Dates", "").split(";")[0]  # Get first date if not found
                    paid_installments = eval(customer.get("Paid_Installments", "[]"))
                    is_paid = installment_date in paid_installments
                    values.append("نعم" if is_paid else "لا")
                else:
                    values.append(customer.get(col, ""))
        else:
            values = [customer.get(col, "") for col in tree["columns"]]
        
        item = tree.insert("", "end", values=values)
        
        # Add color coding for paid status if applicable
        if "Paid" in tree["columns"]:
            if values[tree["columns"].index("Paid")] == "نعم":
                tree.item(item, tags=("paid",))
            else:
                tree.item(item, tags=("unpaid",))
    
    # Configure payment status styles if needed
    if "Paid" in tree["columns"]:
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])

class CSVManager:
    """Handles all CSV file operations with caching and optimized data handling"""
    def __init__(self, csv_file: str, backup_folder: str):
        self.csv_file = csv_file
        self.backup_folder = backup_folder
        self.columns = ["Name", "Phone", "Amount", "Installments", 
                       "Installment Value", "Start Date", "Installment Dates", 
                       "Notification Sent", "Paid_Installments"]
        self._cache = {}
        self._cache_timestamp = None
        self._cache_duration = 60  # Cache duration in seconds
        self._ensure_files_exist()
        
    def _is_cache_valid(self) -> bool:
        """Check if cache is valid"""
        if not self._cache or not self._cache_timestamp:
            return False
        return (datetime.now() - self._cache_timestamp).seconds < self._cache_duration
        
    def _update_cache(self, data: List[Dict]):
        """Update cache with new data"""
        self._cache = data
        self._cache_timestamp = datetime.now()
        
    def read_data(self) -> List[Dict]:
        """Read data from CSV file with caching"""
        try:
            # Return cached data if valid
            if self._is_cache_valid():
                return self._cache.copy()  # Return a copy to prevent cache modification
                
            data = []
            with open(self.csv_file, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Format and validate data
                    cleaned_row = self._clean_row_data(row)
                    data.append(cleaned_row)
                    
            # Update cache with new data
            self._update_cache(data)
            return data
        except FileNotFoundError:
            logging.error(f"CSV file not found: {self.csv_file}")
            self._create_empty_csv()
            return []
        except Exception as e:
            logging.error(f"Error reading CSV file: {str(e)}")
            return []
            
    def _clean_row_data(self, row: Dict) -> Dict:
        """Clean and validate row data"""
        cleaned_row = row.copy()
        
        # Format phone number
        if "Phone" in cleaned_row:
            cleaned_row["Phone"] = f"+{cleaned_row['Phone']}" if not cleaned_row['Phone'].startswith("+") else cleaned_row['Phone']
            
        # Convert numeric values
        try:
            cleaned_row["Amount"] = float(cleaned_row.get("Amount", 0))
            cleaned_row["Installment Value"] = float(cleaned_row.get("Installment Value", 0))
            cleaned_row["Installments"] = int(cleaned_row.get("Installments", 0))
        except (ValueError, TypeError):
            logging.warning(f"Invalid numeric values in row: {row}")
            
        # Ensure boolean fields
        cleaned_row["Notification Sent"] = str(cleaned_row.get("Notification Sent", "")).lower() == "true"
        
        # Initialize Paid_Installments if not present
        if "Paid_Installments" not in cleaned_row:
            cleaned_row["Paid_Installments"] = "[]"
            
        return cleaned_row
        
    def save_data(self, data: List[Dict]) -> bool:
        """Save data to CSV file with backup"""
        try:
            # Validate data before saving
            validated_data = []
            for row in data:
                if self._validate_row(row):
                    validated_data.append(row)
                else:
                    logging.warning(f"Invalid row data skipped: {row}")
            
            # Create backup before saving
            self.create_backup()
            
            with open(self.csv_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.columns)
                writer.writeheader()
                writer.writerows(validated_data)
                
            # Update cache with new data
            self._update_cache(validated_data)
            return True
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            return False
            
    def _validate_row(self, row: Dict) -> bool:
        """Validate row data"""
        required_fields = ["Name", "Phone", "Amount", "Installments"]
        
        # Check required fields
        if not all(field in row for field in required_fields):
            return False
            
        # Validate numeric fields
        try:
            float(row["Amount"])
            float(row["Installment Value"])
            int(row["Installments"])
        except (ValueError, TypeError):
            return False
            
        # Validate phone number format
        phone_pattern = r"^\+?\d{10,15}$"
        if not re.match(phone_pattern, str(row["Phone"])):
            return False
            
        return True
    
    def _ensure_files_exist(self):
        """Ensure necessary files and folders exist."""
        try:
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
                
            if not os.path.exists(self.csv_file):
                self._create_empty_csv()
                
        except Exception as e:
            logging.error(f"Error ensuring files exist: {str(e)}")
            raise
            
    def _create_empty_csv(self):
        """Create empty CSV file with headers."""
        try:
            with open(self.csv_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(self.columns)
        except Exception as e:
            logging.error(f"Error creating empty CSV: {str(e)}")
            raise
            
    def append_customer(self, customer_data: Dict) -> bool:
        """Append a new customer to the CSV file."""
        try:
            # Validate required fields
            missing_fields = [field for field in self.columns if field not in customer_data]
            if missing_fields:
                logging.error(f"Missing required fields: {missing_fields}")
                return False
            
            # Create backup before appending
            self.create_backup()
            
            # Check if file exists and has headers
            file_exists = os.path.exists(self.csv_file) and os.path.getsize(self.csv_file) > 0
            
            with open(self.csv_file, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.columns)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(customer_data)
            
            # Clear cache to force reload
            self._cache = {}
            self._cache_timestamp = None
            return True
        except Exception as e:
            logging.error(f"Error appending customer: {str(e)}")
            return False
            
    def update_customer(self, name: str, updated_data: Dict) -> bool:
        """Update customer data in CSV file."""
        try:
            data = self.read_data()
            customer_found = False
            
            for i, row in enumerate(data):
                if row["Name"] == name:
                    data[i].update(updated_data)
                    customer_found = True
                    break
            
            if not customer_found:
                logging.error(f"Customer not found: {name}")
                return False
                
            return self.save_data(data)
        except Exception as e:
            logging.error(f"Error updating customer: {str(e)}")
            return False
            
    def delete_customer(self, name: str) -> bool:
        """Delete customer from CSV file."""
        try:
            data = self.read_data()
            original_length = len(data)
            data = [row for row in data if row["Name"] != name]
            
            if len(data) == original_length:
                logging.error(f"Customer not found: {name}")
                return False
                
            return self.save_data(data)
        except Exception as e:
            logging.error(f"Error deleting customer: {str(e)}")
            return False
            
    def create_backup(self) -> Optional[str]:
        """Create a backup of the current data."""
        try:
            if not os.path.exists(self.csv_file):
                logging.error("No data file to backup")
                return None
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = os.path.join(self.backup_folder, f"backup_{timestamp}.csv")
            
            # Ensure backup directory exists
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
            
            shutil.copy2(self.csv_file, backup_filename)  # copy2 preserves metadata
            logging.info(f"Backup created: {backup_filename}")
            return backup_filename
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            return None
            
    def restore_backup(self, backup_file: str) -> bool:
        """Restore from a backup file."""
        try:
            # Check if backup file exists
            backup_path = os.path.join(self.backup_folder, backup_file)
            if not os.path.exists(backup_path):
                logging.error(f"Backup file not found: {backup_path}")
                return False
                
            # Backup current file before restoring
            self.create_backup()
            
            # Copy backup to main file
            shutil.copy2(backup_path, self.csv_file)
            
            # Clear cache to force reload
            self._cache = {}
            self._cache_timestamp = None
            
            return True
            
        except Exception as e:
            logging.error(f"Error restoring backup: {str(e)}")
            return False
            
    def get_backup_files(self) -> List[str]:
        """Get list of available backup files."""
        try:
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
            return sorted(
                [f for f in os.listdir(self.backup_folder) if f.endswith(".csv")],
                reverse=True  # Newest first
            )
        except Exception as e:
            logging.error(f"Error getting backup files: {str(e)}")
            return []

    def search_customers(self, query: str) -> List[Dict]:
        """Search customers by any field."""
        try:
            data = self.read_data()
            query = query.lower()
            return [
                row for row in data 
                if any(
                    str(value).lower().find(query) != -1 
                    for value in row.values()
                )
            ]
        except Exception as e:
            logging.error(f"Error searching customers: {str(e)}")
            return []

    def mark_installment_as_paid(self, customer_name: str, installment_date: str) -> bool:
        """Mark a specific installment as paid."""
        try:
            data = self.read_data()
            
            for i, row in enumerate(data):
                if row["Name"] == customer_name:
                    # Get current paid installments
                    try:
                        paid_installments = eval(row.get("Paid_Installments", "[]"))
                        if not isinstance(paid_installments, list):
                            paid_installments = []
                    except:
                        paid_installments = []
                        
                    # Add the installment date if not already paid
                    if installment_date not in paid_installments:
                        paid_installments.append(installment_date)
                        data[i]["Paid_Installments"] = str(paid_installments)
                        # Save updated data
                        return self.save_data(data)
                    else:
                        logging.info(f"Installment already paid: {installment_date}")
                        return True  # Already paid is not an error
            
            logging.warning(f"Customer not found: {customer_name}")
            return False
            
        except Exception as e:
            logging.error(f"Error marking installment as paid: {str(e)}")
            return False

    def get_payment_status(self, customer_name: str, installment_date: str) -> bool:
        """Check if a specific installment has been paid."""
        try:
            data = self.read_data()
            for customer in data:
                if customer["Name"] == customer_name:
                    try:
                        paid_installments = eval(customer.get("Paid_Installments", "[]"))
                        return installment_date in paid_installments
                    except:
                        return False
            return False
        except Exception as e:
            logging.error(f"Error checking payment status: {str(e)}")
            return False
            
    def update_installment(self, customer_name: str, old_date: str, new_date: str, new_value: float) -> bool:
        """Update a specific installment's date and value."""
        try:
            data = self.read_data()
            
            for i, customer in enumerate(data):
                if customer["Name"] == customer_name:
                    # Get current installment dates and values
                    installment_dates = customer["Installment Dates"].split(";")
                    
                    # Find the old date index
                    if old_date not in installment_dates:
                        logging.warning(f"Installment date not found: {old_date}")
                        return False
                    
                    # Update the date
                    date_index = installment_dates.index(old_date)
                    installment_dates[date_index] = new_date
                    
                    # Update the installment value
                    data[i]["Installment Value"] = new_value
                    
                    # Join back the dates
                    data[i]["Installment Dates"] = ";".join(installment_dates)
                    
                    # Update payment status if needed
                    try:
                        paid_installments = eval(customer.get("Paid_Installments", "[]"))
                        if old_date in paid_installments:
                            paid_installments.remove(old_date)
                            paid_installments.append(new_date)
                            data[i]["Paid_Installments"] = str(paid_installments)
                    except Exception as e:
                        logging.error(f"Error updating paid status: {str(e)}")
                    
                    # Save the updated data
                    return self.save_data(data)
            
            logging.warning(f"Customer not found: {customer_name}")
            return False
            
        except Exception as e:
            logging.error(f"Error updating installment: {str(e)}")
            return False
            
    def unmark_installment_as_paid(self, customer_name: str, installment_date: str) -> bool:
        """Remove a specific installment from the paid list."""
        try:
            data = self.read_data()
            
            for i, row in enumerate(data):
                if row["Name"] == customer_name:
                    # Get current paid installments
                    try:
                        paid_installments = eval(row.get("Paid_Installments", "[]"))
                        if not isinstance(paid_installments, list):
                            paid_installments = []
                    except:
                        paid_installments = []
                        
                    # Remove the installment date if it's paid
                    if installment_date in paid_installments:
                        paid_installments.remove(installment_date)
                        data[i]["Paid_Installments"] = str(paid_installments)
                        # Save updated data
                        return self.save_data(data)
                    else:
                        logging.info(f"Installment wasn't marked as paid: {installment_date}")
                        return True  # Not being in the list is not an error
            
            logging.warning(f"Customer not found: {customer_name}")
            return False
            
        except Exception as e:
            logging.error(f"Error unmarking installment as paid: {str(e)}")
            return False

# Initialize CSV manager
csv_filename = "customers.csv"
backup_folder = "backups"
csv_manager = CSVManager(csv_filename, backup_folder)

def read_csv_safely():
    """Read data from CSV file using CSVManager."""
    return csv_manager.read_data()

def save_to_csv_and_excel(data):
    """Save data using CSVManager."""
    return csv_manager.save_data(data)

def validate_and_save(name_entry, phone_entry, amount_entry, installments_entry, start_date_entry, file_list=None):
    name = name_entry.get().strip()
    phone = phone_entry.get().strip()
    amount = amount_entry.get().strip()
    installments = installments_entry.get().strip()
    start_date = start_date_entry.get().strip()

    # Validation patterns
    name_pattern = r"^[A-Za-z؀-ۿ\s]+$"
    phone_pattern = r"^\+?\d{10,15}$"
    amount_pattern = r"^\d+(\.\d{1,2})?$"
    installments_pattern = r"^\d+$"

    if not re.fullmatch(name_pattern, name):
        messagebox.showerror("خطأ", "الاسم يجب أن يحتوي فقط على أحرف ومسافات.")
        return

    if not re.fullmatch(phone_pattern, phone):
        messagebox.showerror("خطأ", "رقم الهاتف يجب أن يحتوي على أرقام فقط ويبدأ بـ +.")
        return

    if not re.fullmatch(amount_pattern, amount):
        messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقمًا صالحًا.")
        return

    if not re.fullmatch(installments_pattern, installments):
        messagebox.showerror("خطأ", "عدد الأقساط يجب أن يكون رقمًا صحيحًا.")
        return

    try:
        amount = float(amount)
        installments = int(installments)
        installment_value = round(amount / installments, 2)
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        
        installment_dates = [
            (start_date_obj + timedelta(days=30 * i)).strftime("%Y-%m-%d") 
            for i in range(installments)
        ]
        
        customer_data = {
            "Name": name,
            "Phone": phone,
            "Amount": amount,
            "Installments": installments,
            "Installment Value": installment_value,
            "Start Date": start_date,
            "Installment Dates": ";".join(installment_dates),
            "Notification Sent": False,
            "Paid_Installments": "[]"  # Initialize empty paid installments list
        }
        
        if csv_manager.append_customer(customer_data):
            # Handle file uploads if any
            if file_list and hasattr(file_list, 'files'):
                if file_manager.add_files(name, file_list.files):
                    logging.info(f"Files added for customer {name}")
                else:
                    messagebox.showwarning("تحذير", "تم حفظ بيانات العميل ولكن فشل في رفع بعض الملفات.")
            
            messagebox.showinfo("نجاح", "تم حفظ العميل بنجاح!")
            # Clear the input fields
            name_entry.delete(0, "end")
            phone_entry.delete(0, "end")
            amount_entry.delete(0, "end")
            installments_entry.delete(0, "end")
            start_date_entry.delete(0, "end")
            if file_list:
                file_list.configure(state="normal")
                file_list.delete("1.0", "end")
                file_list.configure(state="disabled")
                file_list.files = []
        else:
            messagebox.showerror("خطأ", "فشل في حفظ بيانات العميل.")
            
    except ValueError as e:
        messagebox.showerror("خطأ", f"خطأ في البيانات المدخلة: {str(e)}")
    except Exception as e:
        messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")

class DatePicker(CTkToplevel):
    """Popup calendar to select a date."""
    def __init__(self, parent, entry_widget):
        super().__init__(parent)
        self.entry_widget = entry_widget
        self.geometry("400x450")
        self.title("اختر التاريخ")
        
        # Create main frame
        main_frame = StyleManager.create_frame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add title
        StyleManager.create_label(
            main_frame,
            text="اختر تاريخ بدء الأقساط",
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
            text="تحديد",
            width=150,
            command=self.select_date
        ).grid(row=0, column=0, padx=5)
        
        # Cancel button
        StyleManager.create_button(
            buttons_frame,
            text="إلغاء",
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
    frame = frames["view"]
    selected_items = frame.tree.selection()
    
    if not selected_items:
        messagebox.showerror("خطأ", "يرجى تحديد عميل لعرض سجل الدفع.")
        return
        
    # Create payment history window
    history_window = CTkToplevel(app)
    history_window.geometry("800x600")
    history_window.title("سجل الدفع")
    
    # Add header
    StyleManager.create_label(
        history_window,
        text="سجل الدفع",
        font_style="heading"
    ).pack(pady=(20, 10))
    
    # Get selected customer data
    item = frame.tree.item(selected_items[0])
    values = item["values"]
    name = values[0]
    
    StyleManager.create_label(
        history_window,
        text=f"العميل: {name}",
        font_style="subheading"
    ).pack(pady=(0, 20))
    
    # Create table frame
    table_frame = StyleManager.create_frame(history_window)
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Create Treeview
    columns = ("Date", "Amount", "Status", "Actions")
    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        style="Custom.Treeview"
    )
    
    # Configure columns
    column_headers = {
        "Date": "التاريخ",
        "Amount": "المبلغ",
        "Status": "الحالة",
        "Actions": "الإجراءات"
    }
    
    column_widths = {
        "Date": 150, 
        "Amount": 150, 
        "Status": 150, 
        "Actions": 150
    }
    
    for col in columns:
        tree.column(col, width=column_widths[col], anchor="center")
        tree.heading(col, text=column_headers[col])
    
    # Get payment data from CSV
    data = csv_manager.read_data()
    customer_data = next((c for c in data if c["Name"] == name), None)
    
    if customer_data:
        installment_dates = customer_data["Installment Dates"].split(";")
        installment_value = customer_data["Installment Value"]
        paid_installments = eval(customer_data.get("Paid_Installments", "[]"))
        
        # Create a dictionary to store row IDs for each installment date
        date_to_row_map = {}
        today = datetime.now().strftime("%Y-%m-%d")
        
        for date in installment_dates:
            is_paid = date in paid_installments
            status = "مدفوع" if is_paid else "غير مدفوع"
            status_tags = ("paid",) if is_paid else ("unpaid",)
            
            # Determine if this installment date is in the future
            is_future = date > today
            
            # For unpaid installments, add a "Mark as Paid" button, unless it's in the future
            action = "" if is_paid else "تسجيل كمدفوع" if not is_future else "موعد مستقبلي"
            
            # Insert row and store the row ID
            row_id = tree.insert("", "end", values=(date, installment_value, status, action), tags=status_tags)
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
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        column = tree.identify_column(event.x)
        if column != "#4":  # Actions column
            return
            
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
            
        values = tree.item(item_id, "values")
        if not values or len(values) < 4 or values[3] != "تسجيل كمدفوع":
            return
            
        date = values[0]
        
        # Confirm payment with dialog
        if messagebox.askyesno("تأكيد الدفع", f"هل أنت متأكد من تسجيل هذا القسط ({date}) كمدفوع؟"):
            # Mark installment as paid
            if csv_manager.mark_installment_as_paid(name, date):
                # Update the treeview to show new status
                tree.item(item_id, values=(date, values[1], "مدفوع", ""), tags=("paid",))
                messagebox.showinfo("نجاح", "تم تسجيل القسط كمدفوع بنجاح.")
                # Refresh the main treeview to reflect changes
                refresh_treeview(frame.tree)
            else:
                messagebox.showerror("خطأ", "فشل في تسجيل القسط كمدفوع. يرجى المحاولة مرة أخرى.")
    
    # Bind click event for marking installments as paid
    tree.bind("<Button-1>", mark_as_paid)
    
    # Buttons container
    buttons_frame = StyleManager.create_frame(history_window)
    buttons_frame.pack(fill="x", padx=20, pady=20)
    
    # Calculate payment summary
    if customer_data:
        total_installments = len(installment_dates)
        paid_count = len(paid_installments)
        remaining_count = total_installments - paid_count
        paid_amount = float(installment_value) * paid_count
        total_amount = float(customer_data["Amount"])
        remaining_amount = total_amount - paid_amount
        
        # Create summary frame
        summary_frame = StyleManager.create_frame(history_window)
        summary_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Add summary information
        StyleManager.create_label(
            summary_frame,
            text=f"عدد الأقساط المدفوعة: {paid_count} من {total_installments}",
            font_style="body_bold"
        ).pack(pady=5)
        
        StyleManager.create_label(
            summary_frame,
            text=f"المبلغ المدفوع: {paid_amount} من {total_amount} ({round(paid_amount/total_amount*100, 1)}%)",
            font_style="body_bold"
        ).pack(pady=5)
        
        StyleManager.create_label(
            summary_frame,
            text=f"المبلغ المتبقي: {remaining_amount}",
            font_style="body_bold"
        ).pack(pady=5)
    
    # Close button
    StyleManager.create_button(
        buttons_frame,
        text="إغلاق",
        style="secondary",
        width=200,
        command=history_window.destroy
    ).pack(side="left", padx=10)

def export_to_excel():
    """Export customer data to Excel file with enhanced formatting."""
    try:
        data = csv_manager.read_data()
        if not data:
            messagebox.showerror("خطأ", "لا توجد بيانات للتصدير.")
            return
            
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"customers_export_{timestamp}.xlsx"
        
        # Convert data to DataFrame with Arabic column names
        arabic_columns = {
            "Name": "اسم العميل",
            "Phone": "رقم الهاتف",
            "Amount": "المبلغ الإجمالي",
            "Installments": "عدد الأقساط",
            "Installment Value": "قيمة القسط",
            "Start Date": "تاريخ البدء",
            "Installment Dates": "تواريخ الأقساط",
            "Notification Sent": "تم الإرسال"
        }
        
        # Clean and prepare data
        cleaned_data = []
        for row in data:
            cleaned_row = row.copy()
            # Convert boolean to Arabic text
            cleaned_row["Notification Sent"] = "نعم" if row["Notification Sent"] else "لا"
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
            df.to_excel(writer, sheet_name='بيانات العملاء', index=False)
            
            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['بيانات العملاء']
            
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
                "اسم العميل": 25,
                "رقم الهاتف": 20,
                "المبلغ الإجمالي": 20,
                "عدد الأقساط": 15,
                "قيمة القسط": 20,
                "تاريخ البدء": 20,
                "تواريخ الأقساط": 40,
                "تم الإرسال": 15
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
        messagebox.showinfo("نجاح", f"تم تصدير البيانات إلى ملف Excel: {excel_filename}")
        
        # Open the Excel file automatically
        os.startfile(os.path.abspath(excel_filename))
        
    except ImportError:
        messagebox.showerror("خطأ", "الرجاء التأكد من تثبيت حزمة xlsxwriter")
        logging.error("xlsxwriter package not installed")
    except Exception as e:
        logging.error(f"Error exporting to Excel: {str(e)}")
        messagebox.showerror("خطأ", "حدث خطأ أثناء تصدير البيانات.")

def setup_add_page():
    frame = frames["add"]
    frame.grid_columnconfigure(0, weight=1)
    
    # Create header
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)
    
    StyleManager.create_label(
        header_frame,
        text="إضافة عميل جديد",
        font_style="heading"
    ).grid(row=0, column=0, pady=(20, 10))
    
    StyleManager.create_label(
        header_frame,
        text="أدخل بيانات العميل وتفاصيل الأقساط",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, pady=(0, 20))
    
    # Create form container
    form_frame = StyleManager.create_frame(frame)
    form_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
    form_frame.grid_columnconfigure(0, weight=1)
    form_frame.grid_columnconfigure(1, weight=2)
    
    # Form fields
    fields = [
        {"label": "اسم العميل:", "type": "text"},
        {"label": "رقم الهاتف:", "type": "phone"},
        {"label": "المبلغ:", "type": "number"},
        {"label": "عدد الأقساط:", "type": "number"}
    ]
    
    entries = []
    row = 0
    
    for field in fields:
        # Create field container
        field_frame = StyleManager.create_frame(form_frame)
        field_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        field_frame.grid_columnconfigure(1, weight=1)
        
        # Add label
        StyleManager.create_label(
            field_frame,
            text=field["label"],
            font_style="body_bold"
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Add entry
        entry = StyleManager.create_entry(field_frame, width=300)
        entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        entries.append(entry)
        
        row += 1
    
    # Date Picker Section
    date_frame = StyleManager.create_frame(form_frame)
    date_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
    date_frame.grid_columnconfigure(1, weight=1)
    
    StyleManager.create_label(
        date_frame,
        text="تاريخ بدء الأقساط:",
        font_style="body_bold"
    ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
    
    start_date_entry = StyleManager.create_entry(date_frame, width=200)
    start_date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
    
    date_picker_btn = StyleManager.create_button(
        date_frame,
        text="📅 اختر التاريخ",
        style="secondary",
        command=lambda: DatePicker(app, start_date_entry)
    )
    date_picker_btn.grid(row=0, column=2, padx=10, pady=5)
    
    # Buttons container
    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)
    
    # Save Button
    save_btn = StyleManager.create_button(
        buttons_frame,
        text="حفظ العميل",
        width=200,
        command=lambda: validate_and_save(*entries, start_date_entry)
    )
    save_btn.grid(row=0, column=0, padx=10, pady=10)
    
    # Back Button
    back_btn = StyleManager.create_button(
        buttons_frame,
        text="رجوع",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    )
    back_btn.grid(row=0, column=1, padx=10, pady=10)

    # File upload section with modern design
    file_frame = StyleManager.create_frame(form_frame, fg_color="transparent")
    file_frame.grid(row=len(fields)*2+1, column=0, sticky="ew", pady=(20, 0))
    file_frame.grid_columnconfigure(1, weight=1)
    
    StyleManager.create_label(
        file_frame,
        text="📁 ملفات العميل",
        font_style="body_bold"
    ).grid(row=0, column=0, sticky="w", padx=(0, 10))
    
    # Create a frame for the file list and buttons
    file_list_frame = StyleManager.create_frame(file_frame, fg_color="transparent")
    file_list_frame.grid(row=0, column=1, sticky="ew", pady=(0, 10))
    file_list_frame.grid_columnconfigure(0, weight=1)
    
    # File list with scrollbar
    file_list = CTkTextbox(
        file_list_frame,
        width=400,
        height=100,
        font=StyleManager.FONTS["body"],
        fg_color=StyleManager.COLORS["background"],
        border_color=StyleManager.COLORS["border"],
        state="disabled"  # Make the text box read-only
    )
    file_list.grid(row=0, column=0, sticky="ew", padx=(0, 10))
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(file_list_frame, orient="vertical", command=file_list.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    file_list.configure(yscrollcommand=scrollbar.set)
    
    # Store selected files
    file_list.files = []
    
    # Buttons frame
    file_buttons_frame = StyleManager.create_frame(file_frame, fg_color="transparent")
    file_buttons_frame.grid(row=0, column=2, sticky="e")
    
    def add_files():
        files = filedialog.askopenfilenames(
            title="اختر ملفات العميل",
            filetypes=[
                ("All files", "*.*"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.png *.jpg *.jpeg"),
                ("Document files", "*.doc *.docx")
            ]
        )
        if files:
            file_list.files.extend(files)
            file_list.configure(state="normal")  # Temporarily enable for updating
            file_list.delete("1.0", "end")  # Clear existing content
            for file in files:
                file_list.insert("end", f"{os.path.basename(file)}\n")
            file_list.configure(state="disabled")  # Make read-only again
    
    def clear_files():
        if file_list.files:
            if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف جميع الملفات المحددة؟"):
                file_list.files = []
                file_list.configure(state="normal")
                file_list.delete("1.0", "end")
                file_list.configure(state="disabled")
    
    # Add file button
    StyleManager.create_button(
        file_buttons_frame,
        text="إضافة ملفات",
        width=120,
        command=add_files
    ).pack(side="left", padx=(0, 5))
    
    # Clear files button
    StyleManager.create_button(
        file_buttons_frame,
        text="مسح الملفات",
        style="secondary",
        width=120,
        command=clear_files
    ).pack(side="left")
    
    # Update save button to include file_list
    save_btn.configure(command=lambda: validate_and_save(*entries, start_date_entry, file_list))

def setup_view_page():
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
        text="عرض العملاء",
        font_style="heading"
    ).grid(row=0, column=0, pady=(5, 5), sticky="w")
    
    # Simplified search area with better spacing
    search_frame = StyleManager.create_frame(frame)
    search_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 15))
    search_frame.grid_columnconfigure(1, weight=1)
    
    # Simple search label
    StyleManager.create_label(
        search_frame,
        text="بحث:",
        font_style="body_bold"
    ).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
    
    # Clean search entry
    search_entry = StyleManager.create_entry(
        search_frame,
        width=400,
        font=("Arial", 14),
        height=35,
        placeholder_text="أدخل اسم العميل أو رقم الهاتف..."
    )
    search_entry.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ew")
    
    def perform_search():
        query = search_entry.get().strip()
        results = csv_manager.search_customers(query)
        refresh_treeview(frame.tree, results)
        
        # Update status message with search results
        result_count = len(results)
        status_label.configure(text=f"العملاء: {result_count}")
    
    # Add keyboard binding for Enter key
    search_entry.bind("<Return>", lambda event: perform_search())
    
    search_button = StyleManager.create_button(
        search_frame,
        text="بحث",
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
        "Name": "اسم العميل",
        "Phone": "رقم الهاتف",
        "Amount": "المبلغ",
        "Installments": "عدد الأقساط",
        "Installment Value": "قيمة القسط",
        "Start Date": "تاريخ البدء"
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
    data = csv_manager.read_data()
    status_label.configure(text=f"العملاء: {len(data)}")
    
    # Edit customer function - keeping functionality intact
    def edit_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد عميل للتعديل.")
            return
            
        # Get selected customer data
        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]
        
        # Get full customer data
        data = csv_manager.read_data()
        customer = next((c for c in data if c["Name"] == customer_name), None)
        
        if not customer:
            messagebox.showerror("خطأ", "لم يتم العثور على بيانات العميل.")
            return
        
        # Create edit window
        edit_window = CTkToplevel(app)
        edit_window.geometry("800x600")
        edit_window.title(f"تعديل بيانات العميل: {customer_name}")
        
        # Add header
        StyleManager.create_label(
            edit_window,
            text=f"تعديل بيانات العميل: {customer_name}",
            font_style="heading"
        ).pack(pady=(20, 10))
        
        # Create form container
        form_frame = StyleManager.create_frame(edit_window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Form fields with current values
        fields = [
            {"label": "اسم العميل:", "key": "Name", "type": "text"},
            {"label": "رقم الهاتف:", "key": "Phone", "type": "phone"},
            {"label": "المبلغ:", "key": "Amount", "type": "number"},
            {"label": "عدد الأقساط:", "key": "Installments", "type": "number"}
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
            text="تاريخ بدء الأقساط:",
            font_style="body_bold"
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        start_date_entry = StyleManager.create_entry(date_frame, width=200)
        start_date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        start_date_entry.insert(0, str(customer.get("Start Date", "")))
        entries["Start Date"] = start_date_entry
        
        date_picker_btn = StyleManager.create_button(
            date_frame,
            text="اختر التاريخ",
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
            name_pattern = r"^[A-Za-z؀-ۿ\s]+$"
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
                messagebox.showerror("خطأ", "الاسم يجب أن يحتوي فقط على أحرف ومسافات.")
                return
                
            if not re.fullmatch(phone_pattern, phone):
                messagebox.showerror("خطأ", "رقم الهاتف يجب أن يحتوي على أرقام فقط ويبدأ بـ +.")
                return
                
            if not re.fullmatch(amount_pattern, amount):
                messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقمًا صالحًا.")
                return
                
            if not re.fullmatch(installments_pattern, installments):
                messagebox.showerror("خطأ", "عدد الأقساط يجب أن يكون رقمًا صحيحًا.")
                return
            
            try:
                # Convert and calculate values
                amount_float = float(amount)
                installments_int = int(installments)
                installment_value = round(amount_float / installments_int, 2)
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                
                # Generate new installment dates
                installment_dates = [
                    (start_date_obj + timedelta(days=30 * i)).strftime("%Y-%m-%d") 
                    for i in range(installments_int)
                ]
                
                # Prepare updated data
                updated_data = {
                    "Name": name,
                    "Phone": phone,
                    "Amount": amount_float,
                    "Installments": installments_int,
                    "Installment Value": installment_value,
                    "Start Date": start_date,
                    "Installment Dates": ";".join(installment_dates)
                }
                
                # If name changed, delete old record and create new one
                if customer_name != name:
                    if csv_manager.delete_customer(customer_name) and csv_manager.append_customer({
                        **updated_data,
                        "Notification Sent": customer.get("Notification Sent", False),
                        "Paid_Installments": customer.get("Paid_Installments", "[]")
                    }):
                        messagebox.showinfo("نجاح", "تم تحديث بيانات العميل بنجاح!")
                        edit_window.destroy()
                        refresh_treeview(tree)
                    else:
                        messagebox.showerror("خطأ", "فشل في تحديث بيانات العميل.")
                else:
                    # Update existing record
                    if csv_manager.update_customer(customer_name, updated_data):
                        messagebox.showinfo("نجاح", "تم تحديث بيانات العميل بنجاح!")
                        edit_window.destroy()
                        refresh_treeview(tree)
                    else:
                        messagebox.showerror("خطأ", "فشل في تحديث بيانات العميل.")
                        
            except ValueError as e:
                messagebox.showerror("خطأ", f"خطأ في البيانات المدخلة: {str(e)}")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")
        
        # Save Button
        StyleManager.create_button(
            buttons_frame,
            text="حفظ التغييرات",
            width=200,
            command=save_changes
        ).grid(row=0, column=0, padx=10, pady=10)
        
        # Cancel Button
        StyleManager.create_button(
            buttons_frame,
            text="إلغاء",
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
            messagebox.showerror("خطأ", "يرجى تحديد عميل للحذف.")
            return
            
        # Get selected customer data
        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]
        
        # Confirm deletion
        if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف العميل {customer_name}؟\nلا يمكن التراجع عن هذه العملية."):
            if csv_manager.delete_customer(customer_name):
                messagebox.showinfo("نجاح", f"تم حذف العميل {customer_name} بنجاح.")
                refresh_treeview(tree)
            else:
                messagebox.showerror("خطأ", "فشل في حذف العميل.")
    
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
        text="تحديث",
        width=120,
        command=lambda: refresh_treeview(tree)
    )
    refresh_btn.pack(side="left", padx=(0, 10), pady=10)
    
    history_btn = StyleManager.create_button(
        left_buttons,
        text="سجل الدفع",
        width=120,
        command=show_payment_history
    )
    history_btn.pack(side="left", padx=(0, 10), pady=10)

    export_btn = StyleManager.create_button(
        left_buttons,
        text="تصدير Excel",
        width=120,
        command=export_to_excel
    )
    export_btn.pack(side="left", padx=(0, 10), pady=10)
    
    # Right side buttons - customer management
    back_btn = StyleManager.create_button(
        right_buttons,
        text="العودة",
        style="secondary",
        width=120,
        command=lambda: show_frame(frames["home"])
    )
    back_btn.pack(side="right", padx=(0, 0), pady=10)
    
    delete_btn = StyleManager.create_button(
        right_buttons,
        text="حذف العميل",
        style="danger",
        width=120,
        command=delete_customer
    )
    delete_btn.pack(side="right", padx=(0, 10), pady=10)
    
    edit_btn = StyleManager.create_button(
        right_buttons,
        text="تعديل العميل",
        width=120,
        command=edit_customer
    )
    edit_btn.pack(side="right", padx=(0, 10), pady=10)

def setup_manage_installments_page():
    frame = frames["manage_installments"]
    frame.grid_columnconfigure(0, weight=1)
    
    # Create header
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)
    
    StyleManager.create_label(
        header_frame,
        text="إدارة الأقساط",
        font_style="heading"
    ).grid(row=0, column=0, pady=(20, 10))
    
    StyleManager.create_label(
        header_frame,
        text="متابعة وإدارة الأقساط والمدفوعات",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, pady=(0, 20))
    
    # Create table container
    table_frame = StyleManager.create_frame(frame)
    table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)
    
    # Create a Treeview widget with modern styling
    columns = ("Name", "Phone", "Installment Date", "Installment Value", "Paid")
    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        style="Custom.Treeview"
    )
    
    # Set column widths and headings
    column_widths = {
        "Name": 150,
        "Phone": 120,
        "Installment Date": 120,
        "Installment Value": 120,
        "Paid": 100
    }
    
    column_headers = {
        "Name": "اسم العميل",
        "Phone": "رقم الهاتف",
        "Installment Date": "تاريخ القسط",
        "Installment Value": "قيمة القسط",
        "Paid": "مدفوع"
    }
    
    for col in columns:
        tree.column(col, width=column_widths[col], anchor="center")
        tree.heading(col, text=column_headers[col])
    
    tree.grid(row=0, column=0, sticky="nsew")
    
    # Add modern scrollbar
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)
    
    # Store the Treeview widget as an attribute of the frame
    frame.tree = tree
    
    # Load data into the Treeview
    def load_data():
        try:
            # Clear existing items
            for row in tree.get_children():
                tree.delete(row)
                
            data = csv_manager.read_data()
            today = datetime.now().date()
            
            # Sort data by date for better organization
            all_installments = []
            
            for customer in data:
                installment_dates = customer["Installment Dates"].split(";")
                paid_installments = eval(customer.get("Paid_Installments", "[]"))
                
                for date in installment_dates:
                    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                    is_paid = date in paid_installments
                    
                    all_installments.append({
                        "name": customer["Name"],
                        "phone": customer["Phone"],
                        "date": date_obj,
                        "date_str": date,
                        "value": customer["Installment Value"],
                        "is_paid": is_paid
                    })
            
            # Sort installments by date
            all_installments.sort(key=lambda x: x["date"])
            
            # Insert into tree
            for installment in all_installments:
                values = (
                    installment["name"],
                    installment["phone"],
                    installment["date_str"],
                    installment["value"],
                    "نعم" if installment["is_paid"] else "لا"
                )
                
                item = tree.insert("", "end", values=values)
                
                # Add tag for paid/unpaid status
                if installment["is_paid"]:
                    tree.item(item, tags=("paid",))
                else:
                    tree.item(item, tags=("unpaid",))
            
            # Configure payment status styles
            tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
            tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
            
        except Exception as e:
            logging.error(f"Error loading installments data: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء تحميل البيانات.")
    
    # Initial data load
    load_data()
    
    # Buttons Container
    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)
    buttons_frame.grid_columnconfigure(2, weight=1)
    
    # Refresh button
    def refresh_installments():
        load_data()
        messagebox.showinfo("نجاح", "تم تحديث البيانات بنجاح.")
    
    StyleManager.create_button(
        buttons_frame,
        text="تحديث البيانات",
        width=200,
        command=refresh_installments
    ).grid(row=0, column=0, padx=10, pady=10)
    
    # Mark as paid button
    def mark_as_paid():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد قسط لتمييزه كمُدفوع.")
            return
        
        try:
            for item in selected_items:
                values = tree.item(item)["values"]
                customer_name = values[0]
                installment_date = values[2]
                
                if csv_manager.mark_installment_as_paid(customer_name, installment_date):
                    tree.set(item, "Paid", "نعم")
                    tree.item(item, tags=("paid",))
                else:
                    messagebox.showerror("خطأ", f"فشل في تمييز القسط كمدفوع للعميل {customer_name}")
                    return
            
            messagebox.showinfo("نجاح", "تم تمييز الأقساط المحددة كمُدفوعة.")
            load_data()  # Refresh the view to ensure consistency
            
            # Refresh other relevant views if they exist
            if "view" in frames:
                refresh_treeview(frames["view"].tree)
                
        except Exception as e:
            logging.error(f"Error marking installments as paid: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء تمييز الأقساط كمدفوعة.")
    
    StyleManager.create_button(
        buttons_frame,
        text="تمييز كمُدفوع",
        width=200,
        command=mark_as_paid
    ).grid(row=0, column=1, padx=10, pady=10)
    
    # Edit installment button
    def edit_installment():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد قسط للتعديل.")
            return
        
        if len(selected_items) > 1:
            messagebox.showerror("خطأ", "يرجى تحديد قسط واحد فقط للتعديل.")
            return
            
        try:
            item = selected_items[0]
            values = tree.item(item)["values"]
            customer_name = values[0]
            customer_phone = values[1]
            installment_date = values[2]
            installment_value = values[3]
            is_paid = values[4] == "نعم"
            
            # Create edit installment window
            edit_window = CTkToplevel(app)
            edit_window.geometry("500x450")
            edit_window.title("تعديل القسط")
            
            # Make window modal
            edit_window.transient(app)
            edit_window.grab_set()
            
            # Create main frame
            main_frame = StyleManager.create_frame(edit_window)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Add title
            StyleManager.create_label(
                main_frame,
                text="تعديل بيانات القسط",
                font_style="subheading"
            ).pack(pady=(0, 20))
            
            # Customer info (non-editable)
            info_frame = StyleManager.create_frame(main_frame)
            info_frame.pack(fill="x", pady=10)
            
            StyleManager.create_label(
                info_frame,
                text=f"العميل: {customer_name}",
                font_style="body_bold"
            ).pack(anchor="w")
            
            StyleManager.create_label(
                info_frame,
                text=f"رقم الهاتف: {customer_phone}",
                font_style="body"
            ).pack(anchor="w")
            
            # Editable fields
            fields_frame = StyleManager.create_frame(main_frame)
            fields_frame.pack(fill="x", pady=20)
            
            # Date field
            date_frame = StyleManager.create_frame(fields_frame)
            date_frame.pack(fill="x", pady=10)
            
            StyleManager.create_label(
                date_frame,
                text="تاريخ القسط:",
                font_style="body"
            ).pack(side="left", padx=(0, 10))
            
            date_entry = StyleManager.create_entry(date_frame)
            date_entry.pack(side="left", fill="x", expand=True)
            date_entry.insert(0, installment_date)
            
            # Date picker button
            def open_date_picker():
                DatePicker(edit_window, date_entry)
                
            date_picker_btn = StyleManager.create_button(
                date_frame,
                text="📅",
                width=40,
                command=open_date_picker
            )
            date_picker_btn.pack(side="left", padx=(10, 0))
            
            # Amount field
            amount_frame = StyleManager.create_frame(fields_frame)
            amount_frame.pack(fill="x", pady=10)
            
            StyleManager.create_label(
                amount_frame,
                text="قيمة القسط:",
                font_style="body"
            ).pack(side="left", padx=(0, 10))
            
            amount_entry = StyleManager.create_entry(amount_frame)
            amount_entry.pack(side="left", fill="x", expand=True)
            amount_entry.insert(0, str(installment_value))
            
            # Paid status
            paid_frame = StyleManager.create_frame(fields_frame)
            paid_frame.pack(fill="x", pady=10)
            
            paid_status = tk.BooleanVar(value=is_paid)
            
            paid_checkbox = CTkCheckBox(
                paid_frame,
                text="مدفوع",
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
                        messagebox.showerror("خطأ", "تنسيق التاريخ غير صحيح. يجب أن يكون بهذا الشكل: YYYY-MM-DD")
                        return
                    
                    # Validate amount
                    if not re.match(r"^\d+(\.\d{1,2})?$", new_value_str):
                        messagebox.showerror("خطأ", "قيمة القسط يجب أن تكون رقمًا صالحًا.")
                        return
                        
                    new_value = float(new_value_str)
                    
                    # Update installment in database
                    if csv_manager.update_installment(customer_name, installment_date, new_date, new_value):
                        # Update paid status if needed
                        if is_paid != new_paid_status:
                            if new_paid_status:
                                csv_manager.mark_installment_as_paid(customer_name, new_date)
                            else:
                                csv_manager.unmark_installment_as_paid(customer_name, new_date)
                            
                        messagebox.showinfo("نجاح", "تم تحديث بيانات القسط بنجاح.")
                        edit_window.destroy()
                        load_data()  # Refresh the view
                    else:
                        messagebox.showerror("خطأ", "فشل في تحديث بيانات القسط.")
                        
                except Exception as e:
                    logging.error(f"Error saving installment changes: {str(e)}")
                    messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ التغييرات: {str(e)}")
            
            StyleManager.create_button(
                buttons_frame,
                text="حفظ التغييرات",
                width=200,
                command=save_changes
            ).grid(row=0, column=0, padx=5, pady=5)
            
            # Cancel button
            StyleManager.create_button(
                buttons_frame,
                text="إلغاء",
                width=200,
                style="secondary",
                command=edit_window.destroy
            ).grid(row=0, column=1, padx=5, pady=5)
            
        except Exception as e:
            logging.error(f"Error opening edit installment window: {str(e)}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء فتح نافذة التعديل: {str(e)}")
    
    StyleManager.create_button(
        buttons_frame,
        text="تعديل القسط",
        width=200,
        command=edit_installment
    ).grid(row=0, column=2, padx=10, pady=10)
    
    # Back button
    StyleManager.create_button(
        buttons_frame,
        text="العودة",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    ).grid(row=0, column=3, padx=10, pady=10)

def setup_backup_restore_page():
    frame = frames["backup_restore"]
    frame.grid_columnconfigure(0, weight=1)
    
    # Create header
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)
    
    StyleManager.create_label(
        header_frame,
        text="النسخ الاحتياطي واستعادة البيانات",
        font_style="heading"
    ).grid(row=0, column=0, pady=(20, 10))
    
    StyleManager.create_label(
        header_frame,
        text="إدارة النسخ الاحتياطية واستعادة البيانات",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, pady=(0, 20))
    
    # Create main content container
    content_frame = StyleManager.create_frame(frame)
    content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
    content_frame.grid_columnconfigure(0, weight=1)
    
    # Backup section
    backup_section = StyleManager.create_frame(content_frame)
    backup_section.grid(row=0, column=0, sticky="ew", pady=(0, 20))
    backup_section.grid_columnconfigure(1, weight=1)
    
    # Backup icon and title
    StyleManager.create_label(
        backup_section,
        text="💾",
        font=("Arial", 36)
    ).grid(row=0, column=0, padx=(20, 10), pady=20)
    
    backup_title_frame = CTkFrame(backup_section, fg_color="transparent")
    backup_title_frame.grid(row=0, column=1, sticky="nsew", pady=20)
    
    StyleManager.create_label(
        backup_title_frame,
        text="إنشاء نسخة احتياطية",
        font_style="subheading"
    ).grid(row=0, column=0, sticky="w")
    
    StyleManager.create_label(
        backup_title_frame,
        text="حفظ نسخة من البيانات الحالية",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, sticky="w")
    
    def create_backup():
        try:
            backup_file = csv_manager.create_backup()
            if backup_file:
                messagebox.showinfo("نجاح", f"تم إنشاء نسخة احتياطية في: {backup_file}")
            else:
                messagebox.showerror("خطأ", "فشل إنشاء النسخة الاحتياطية.")
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء إنشاء النسخة الاحتياطية.")
    
    StyleManager.create_button(
        backup_section,
        text="إنشاء نسخة احتياطية",
        width=200,
        command=create_backup
    ).grid(row=0, column=2, padx=20)
    
    # Restore section
    restore_section = StyleManager.create_frame(content_frame)
    restore_section.grid(row=1, column=0, sticky="ew")
    restore_section.grid_columnconfigure(1, weight=1)
    
    # Restore icon and title
    StyleManager.create_label(
        restore_section,
        text="🔄",
        font=("Arial", 36)
    ).grid(row=0, column=0, padx=(20, 10), pady=20)
    
    restore_title_frame = CTkFrame(restore_section, fg_color="transparent")
    restore_title_frame.grid(row=0, column=1, sticky="nsew", pady=20)
    
    StyleManager.create_label(
        restore_title_frame,
        text="استعادة نسخة احتياطية",
        font_style="subheading"
    ).grid(row=0, column=0, sticky="w")
    
    StyleManager.create_label(
        restore_title_frame,
        text="استعادة البيانات من نسخة احتياطية سابقة",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, sticky="w")
    
    def restore_backup():
        try:
            backup_files = csv_manager.get_backup_files()
            if not backup_files:
                messagebox.showerror("خطأ", "لا توجد نسخ احتياطية متاحة.")
                return
            
            # Create restore window
            restore_window = CTkToplevel(app)
            restore_window.geometry("600x400")
            restore_window.title("استعادة نسخة احتياطية")
            restore_window.transient(app)  # Make window modal
            restore_window.grab_set()  # Make window modal
            
            # Add header
            StyleManager.create_label(
                restore_window,
                text="اختر النسخة الاحتياطية للاستعادة",
                font_style="heading"
            ).pack(pady=(20, 10))
            
            StyleManager.create_label(
                restore_window,
                text="سيتم استبدال البيانات الحالية بالنسخة المحددة",
                font_style="body",
                text_color=StyleManager.COLORS["text_secondary"]
            ).pack(pady=(0, 20))
            
            # Create list of backups
            backup_frame = StyleManager.create_frame(restore_window)
            backup_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Create scrollable frame for backups
            backup_list = CTkScrollableFrame(backup_frame)
            backup_list.pack(fill="both", expand=True)
            
            selected_backup = StringVar()
            
            for backup in sorted(backup_files, reverse=True):  # Show newest first
                # Create a radio button for each backup
                backup_date = backup.replace("backup_", "").replace(".csv", "")
                try:
                    formatted_date = datetime.strptime(backup_date, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    formatted_date = backup_date  # Fallback if date parsing fails
                
                radio = CTkRadioButton(
                    backup_list,
                    text=f"نسخة {formatted_date}",
                    variable=selected_backup,
                    value=backup,
                    font=StyleManager.FONTS["body"]
                )
                radio.pack(pady=5, padx=10, anchor="w")
            
            # Set default selection to newest backup
            if backup_files:
                selected_backup.set(backup_files[0])
            
            # Buttons frame
            buttons_frame = StyleManager.create_frame(restore_window)
            buttons_frame.pack(fill="x", padx=20, pady=20)
            buttons_frame.grid_columnconfigure(0, weight=1)
            buttons_frame.grid_columnconfigure(1, weight=1)
            
            def confirm_restore():
                try:
                    selected = selected_backup.get()
                    if not selected:
                        messagebox.showerror("خطأ", "يرجى اختيار نسخة احتياطية.")
                        return
                        
                    if messagebox.askyesno("تأكيد", "هل أنت متأكد من استعادة هذه النسخة؟ سيتم استبدال البيانات الحالية."):
                        if csv_manager.restore_backup(selected):
                            messagebox.showinfo("نجاح", "تم استعادة النسخة الاحتياطية بنجاح.")
                            restore_window.destroy()
                        else:
                            messagebox.showerror("خطأ", "فشل استعادة النسخة الاحتياطية.")
                except Exception as e:
                    logging.error(f"Error restoring backup: {str(e)}")
                    messagebox.showerror("خطأ", "حدث خطأ أثناء استعادة النسخة الاحتياطية.")
            
            # Confirm button
            StyleManager.create_button(
                buttons_frame,
                text="استعادة",
                width=200,
                command=confirm_restore
            ).grid(row=0, column=0, padx=10)
            
            # Cancel button
            StyleManager.create_button(
                buttons_frame,
                text="إلغاء",
                style="secondary",
                width=200,
                command=restore_window.destroy
            ).grid(row=0, column=1, padx=10)
            
        except Exception as e:
            logging.error(f"Error in restore backup window: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء فتح نافذة الاستعادة.")
    
    StyleManager.create_button(
        restore_section,
        text="استعادة نسخة احتياطية",
        width=200,
        command=restore_backup
    ).grid(row=0, column=2, padx=20)
    
    # Back button container
    back_frame = StyleManager.create_frame(frame)
    back_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
    back_frame.grid_columnconfigure(0, weight=1)
    
    # Back button
    StyleManager.create_button(
        back_frame,
        text="العودة",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    ).grid(row=0, column=0)

def setup_send_notification_page():
    frame = frames["send_notification"]
    frame.grid_columnconfigure(0, weight=1)
    
    # Create header
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)
    
    StyleManager.create_label(
        header_frame,
        text="إرسال إشعارات الواتساب",
        font_style="heading"
    ).grid(row=0, column=0, pady=(20, 10))
    
    StyleManager.create_label(
        header_frame,
        text="إرسال تذكيرات الأقساط للعملاء عبر الواتساب",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, pady=(0, 20))
    
    # Create table container
    table_frame = StyleManager.create_frame(frame)
    table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)
    
    # Create a Treeview widget with modern styling
    columns = ("Name", "Phone", "Installment Date", "Installment Value", "Notification Sent")
    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        style="Custom.Treeview"
    )
    
    # Set column widths and headings
    column_widths = {
        "Name": 150,
        "Phone": 120,
        "Installment Date": 120,
        "Installment Value": 120,
        "Notification Sent": 120
    }
    
    column_headers = {
        "Name": "اسم العميل",
        "Phone": "رقم الهاتف",
        "Installment Date": "تاريخ القسط",
        "Installment Value": "قيمة القسط",
        "Notification Sent": "تم الإرسال"
    }
    
    for col in columns:
        tree.column(col, width=column_widths[col], anchor="center")
        tree.heading(col, text=column_headers[col])
    
    tree.grid(row=0, column=0, sticky="nsew")
    
    # Add modern scrollbar
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)
    
    # Store the Treeview widget as an attribute of the frame
    frame.tree = tree
    
    # Load data into the Treeview
    def load_data():
        for row in tree.get_children():
            tree.delete(row)
            
        data = csv_manager.read_data()
        today = datetime.now().date()
        
        for customer in data:
            installment_dates = customer["Installment Dates"].split(";")
            for date in installment_dates:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                # Only show upcoming installments
                if date_obj >= today:
                    notification_sent = "نعم" if customer["Notification Sent"] else "لا"
                    values = (
                        customer["Name"],
                        customer["Phone"],
                        date,
                        customer["Installment Value"],
                        notification_sent
                    )
                    item = tree.insert("", "end", values=values)
                    
                    # Add tag for sent notifications
                    if notification_sent == "نعم":
                        tree.item(item, tags=("sent",))
        
        # Configure sent notification style
        tree.tag_configure("sent", foreground=StyleManager.COLORS["success"])
    
    load_data()
    
    # Buttons Container
    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)
    buttons_frame.grid_columnconfigure(2, weight=1)
    
    # Send WhatsApp Notification Button
    def send_whatsapp_notification():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("خطأ", "يرجى تحديد عميل لإرسال الإشعار.")
            return
            
        item = tree.item(selected_item[0])  # Get the first selected item
        values = item["values"]
        name = values[0]
        phone = str(values[1])
        installment_date = values[2]
        installment_value = values[3]
        
        # Format phone number
        if not phone.startswith("+"):
            phone = "+" + phone
        
        # Show preview window
        preview_window = CTkToplevel(app)
        preview_window.geometry("500x550")
        preview_window.title("معاينة الرسالة")
        
        # Add header
        StyleManager.create_label(
            preview_window,
            text="معاينة رسالة الواتساب",
            font_style="heading"
        ).pack(pady=(20, 10))
        
        # Default message template
        default_message = (
            f"مرحبًا {name},\n"
            f"تذكير بدفع قسط بقيمة {installment_value} ريال في تاريخ {installment_date}.\n"
            f"شكرًا لتعاملك معنا!"
        )
        
        # Message customization section
        customization_frame = StyleManager.create_frame(preview_window)
        customization_frame.pack(fill="x", padx=20, pady=10)
        
        StyleManager.create_label(
            customization_frame,
            text="نص الرسالة:",
            font_style="body_bold"
        ).pack(anchor="w", pady=(5, 0))
        
        message_text = CTkTextbox(
            customization_frame,
            width=400,
            height=150,
            font=StyleManager.FONTS["body"]
        )
        message_text.pack(pady=10, padx=10, fill="both", expand=True)
        message_text.insert("end", default_message)
        
        # Template variables info
        template_info = StyleManager.create_frame(preview_window)
        template_info.pack(fill="x", padx=20, pady=5)
        
        StyleManager.create_label(
            template_info,
            text="يمكنك استخدام المتغيرات التالية في الرسالة:",
            font_style="small"
        ).pack(anchor="w")
        
        StyleManager.create_label(
            template_info,
            text="{name} - اسم العميل\n{date} - تاريخ القسط\n{value} - قيمة القسط",
            font_style="small",
            text_color=StyleManager.COLORS["text_secondary"]
        ).pack(anchor="w")
        
        # Message sending options frame
        options_frame = StyleManager.create_frame(preview_window)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        # Add a checkbox for retrying if failed
        retry_var = BooleanVar(value=True)
        retry_check = CTkCheckBox(
            options_frame, 
            text="محاولة الإرسال مرة أخرى في حالة الفشل",
            variable=retry_var
        )
        retry_check.pack(anchor="w", pady=5)
        
        # Max retry count
        retry_count_frame = StyleManager.create_frame(options_frame)
        retry_count_frame.pack(fill="x", pady=5)
        
        StyleManager.create_label(
            retry_count_frame,
            text="عدد المحاولات:",
            font_style="body"
        ).pack(side="left", padx=(0, 10))
        
        retry_count_var = StringVar(value="3")
        retry_count_entry = StyleManager.create_entry(
            retry_count_frame,
            width=50,
            textvariable=retry_count_var
        )
        retry_count_entry.pack(side="left")
        
        # Buttons frame
        buttons_frame = StyleManager.create_frame(preview_window)
        buttons_frame.pack(fill="x", padx=20, pady=20)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Status label for showing sending progress
        status_label = StyleManager.create_label(
            preview_window,
            text="",
            font_style="small",
            text_color=StyleManager.COLORS["text_secondary"]
        )
        status_label.pack(pady=(0, 10))
        
        def send_message():
            try:
                # Get customized message
                custom_message = message_text.get("1.0", "end-1c")
                
                # Apply template variables
                message = custom_message.replace("{name}", name).replace("{date}", installment_date).replace("{value}", str(installment_value))
                
                # Get retry settings
                should_retry = retry_var.get()
                max_retries = 1
                try:
                    max_retries = int(retry_count_var.get())
                    if max_retries < 1:
                        max_retries = 1
                except ValueError:
                    max_retries = 3
                
                # Disable buttons during sending
                for widget in buttons_frame.winfo_children():
                    widget.configure(state="disabled")
                
                success = False
                attempts = 0
                errors = []
                
                while attempts < max_retries and not success:
                    attempts += 1
                    try:
                        # Update status
                        status_label.configure(text=f"جاري إرسال الرسالة... المحاولة {attempts}/{max_retries}")
                        preview_window.update()
                        
                        # Send WhatsApp message with error handling
                        try:
                            kit.sendwhatmsg_instantly(
                                phone_no=phone,
                                message=message,
                                wait_time=20,
                                tab_close=True,
                                close_time=3
                            )
                        except Exception as e:
                            raise Exception(f"فشل في إرسال الرسالة: {str(e)}")
                        
                        # Update notification status
                        data = csv_manager.read_data()
                        updated = False
                        for customer in data:
                            if customer["Name"] == name:
                                customer["Notification Sent"] = True
                                updated = True
                                break
                        
                        if updated and csv_manager.save_data(data):
                            success = True
                            status_label.configure(text="تم الإرسال بنجاح!")
                            messagebox.showinfo("نجاح", f"تم إرسال الإشعار إلى {name} بنجاح.")
                            preview_window.destroy()
                            load_data()  # Refresh the view
                            logging.info(f"Manual notification sent to {name} at {phone}")
                        else:
                            errors.append("فشل في تحديث حالة الإشعار")
                    
                    except Exception as e:
                        error_msg = str(e)
                        errors.append(error_msg)
                        logging.error(f"Error sending WhatsApp message to {name} at {phone} (Attempt {attempts}): {error_msg}")
                        
                        if should_retry and attempts < max_retries:
                            status_label.configure(text=f"فشل المحاولة {attempts}. جاري المحاولة مرة أخرى...")
                            preview_window.update()
                            time.sleep(2)  # Wait before retrying
                        else:
                            status_label.configure(text="فشل الإرسال.")
                            messagebox.showerror("خطأ", f"فشل إرسال الإشعار بعد {attempts} محاولات.\nآخر خطأ: {error_msg}")
                            break
                
                # Re-enable buttons
                for widget in buttons_frame.winfo_children():
                    widget.configure(state="normal")
                    
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")
                logging.error(f"Unexpected error in send_message: {str(e)}")
                # Re-enable buttons
                for widget in buttons_frame.winfo_children():
                    widget.configure(state="normal")
        
        # Send button
        StyleManager.create_button(
            buttons_frame,
            text="إرسال",
            width=200,
            command=send_message
        ).grid(row=0, column=0, padx=10)
        
        # Cancel button
        StyleManager.create_button(
            buttons_frame,
            text="إلغاء",
            style="secondary",
            width=200,
            command=preview_window.destroy
        ).grid(row=0, column=1, padx=10)
    
    # Refresh button
    StyleManager.create_button(
        buttons_frame,
        text="تحديث البيانات",
        width=200,
        command=load_data
    ).grid(row=0, column=0, padx=10, pady=10)
    
    # Send notification button
    StyleManager.create_button(
        buttons_frame,
        text="إرسال إشعار",
        width=200,
        command=send_whatsapp_notification
    ).grid(row=0, column=1, padx=10, pady=10)
    
    # Back button
    StyleManager.create_button(
        buttons_frame,
        text="العودة",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    ).grid(row=0, column=2, padx=10, pady=10)

def check_due_installments():
    """Check for installments due in 3 days and send notifications."""
    while True:
        try:
            logging.info("Starting automatic installment check")
            
            # Read customer data
            data = csv_manager.read_data()
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
                    # Only process customers with notification not yet sent
                    if customer.get("Notification Sent", False):
                        skip_count += 1
                        continue
                        
                    # Get installment dates
                    dates_str = customer.get("Installment Dates", "")
                    if not dates_str:
                        logging.warning(f"Customer {customer['Name']} has no installment dates")
                        continue
                        
                    # Get paid installments to skip them
                    try:
                        paid_installments = eval(customer.get("Paid_Installments", "[]"))
                    except:
                        paid_installments = []
                        
                    installment_dates = dates_str.split(";")
                    
                    # Check each installment date
                    for date_str in installment_dates:
                        try:
                            # Skip if already paid
                            if date_str in paid_installments:
                                continue
                                
                            date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
                            days_until_due = (date - today).days
                            
                            # Send notification if due within notification window
                            if 0 <= days_until_due <= notification_window:
                                logging.info(f"Found upcoming payment for {customer['Name']} due in {days_until_due} days")
                                
                                message = (
                                    f"مرحبًا {customer['Name']},\n"
                                    f"تذكير بدفع قسط بقيمة {customer['Installment Value']} ريال "
                                    f"في تاريخ {date_str}.\n"
                                    f"شكرًا لتعاملك معنا!"
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
                                        
                                        # Send WhatsApp message
                                        kit.sendwhatmsg_instantly(
                                            phone_no=phone,
                                            message=message,
                                            wait_time=20,
                                            tab_close=True,
                                            close_time=3
                                        )
                                        
                                        # Update notification status
                                        customer["Notification Sent"] = True
                                        csv_manager.save_data(data)
                                        logging.info(f"Automatic notification sent to {customer['Name']} at {phone}")
                                        success = True
                                        success_count += 1
                                        
                                    except Exception as e:
                                        last_error = str(e)
                                        logging.error(f"Error sending WhatsApp message to {customer['Name']} at {phone} (Attempt {retry_count}): {last_error}")
                                        
                                        # Wait before retry
                                        if retry_count < max_retries:
                                            time.sleep(5)
                                
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

def setup_home_page():
    """Setup the home page with a modern dashboard layout"""
    frame = frames["home"]
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_rowconfigure(0, weight=0)  # Header row
    frame.grid_rowconfigure(1, weight=1)  # First row of cards
    frame.grid_rowconfigure(2, weight=1)  # Second row of cards
    frame.grid_rowconfigure(3, weight=1)  # Third row of cards
    
    # Create header frame with gradient effect
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)
    
    # Add title with larger font and bold
    StyleManager.create_label(
        header_frame,
        text="نظام إدارة الأقساط",
        font=("Arial", 42, "bold"),
        text_color="#ffffff"
    ).grid(row=0, column=0, pady=(20, 20))
    
    # Menu items configuration
    menu_items = [
        {
            "text": "إضافة عميل",
            "command": lambda: show_frame(frames["add"]),
            "icon": "👤",
            "color": "#4CAF50"
        },
        {
            "text": "عرض العملاء",
            "command": lambda: show_frame(frames["view"]),
            "icon": "📋",
            "color": "#2196F3"
        },
        {
            "text": "إدارة الأقساط",
            "command": lambda: show_frame(frames["manage_installments"]),
            "icon": "💰",
            "color": "#9C27B0"
        },
        {
            "text": "النسخ الاحتياطي",
            "command": lambda: show_frame(frames["backup_restore"]),
            "icon": "🔒",
            "color": "#FF9800"
        },
        {
            "text": "إرسال إشعارات",
            "command": lambda: show_frame(frames["send_notification"]),
            "icon": "📨",
            "color": "#E91E63"
        },
        {
            "text": "ملفات العملاء",
            "command": lambda: os.startfile("customer_files"),
            "icon": "📁",
            "color": "#607D8B"
        }
    ]
    
    # Create menu grid with improved spacing and responsiveness
    for i, item in enumerate(menu_items):
        row, col = divmod(i, 2)
        
        # Create a container frame for the button to handle hover effects
        button_container = CTkFrame(
            frame,
            fg_color="transparent"
        )
        button_container.grid(row=row+1, column=col, padx=30, pady=25, sticky="nsew")
        
        # Create button with icon and text
        button = CTkButton(
            button_container,
            text=f"{item['icon']}  {item['text']}",
            command=item["command"],
            width=500,
            height=80,
            corner_radius=15,
            fg_color=item["color"],
            hover_color=item["color"],  # Keep same color on hover
            text_color="#ffffff",
            font=("Arial", 24, "bold"),
            anchor="center"
        )
        button.pack(expand=True, fill="both")
        
        # Create hover effect
        def on_enter(e, button=button):
            # Add white border effect only
            button.configure(border_width=2, border_color="#ffffff")
            
        def on_leave(e, button=button):
            # Remove border effect
            button.configure(border_width=0)
        
        # Bind hover events
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

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
            messagebox.showwarning("تحذير", "فشل في تحميل النمط. سيتم استخدام النمط الافتراضي.")
        
        # Create main container with padding
        container = StyleManager.create_frame(app)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Configure container grid
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # Create frames
        page_names = ["home", "add", "delete", "edit", "view", "manage_installments", "backup_restore", "send_notification"]
        
        for name in page_names:
            try:
                frame = StyleManager.create_frame(container)
                frame.grid(row=0, column=0, sticky="nsew")
                frames[name] = frame
                frame.grid_columnconfigure(0, weight=1)
                frame.grid_rowconfigure(0, weight=1)
                logging.info(f"Created frame: {name}")
            except Exception as e:
                logging.error(f"Error creating frame {name}: {str(e)}")
                raise
        
        # Setup all pages with error handling
        setup_functions = [
            ("setup_home_page", setup_home_page),
            ("setup_add_page", setup_add_page),
            ("setup_view_page", setup_view_page),
            ("setup_manage_installments_page", setup_manage_installments_page),
            ("setup_backup_restore_page", setup_backup_restore_page),
            ("setup_send_notification_page", setup_send_notification_page)
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
        main()
    except Exception as e:
        logging.critical(f"Application failed to start: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("خطأ حرج", "فشل في بدء التطبيق. يرجى التأكد من تثبيت جميع المكتبات المطلوبة.")
        sys.exit(1)

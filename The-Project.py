import os
import sys
import traceback
import logging as stdlogging
from tkinter import messagebox

from customtkinter import CTk

from app.core.version import APP_NAME, VERSION_STRING, COPYRIGHT
from app.repositories.sqlite_repository import SQLiteRepository
from app.services.customer_service import CustomerService
from app.services.activity_service import ActivityService
from app.services.reminder_service import ReminderService
from app.services.analytics_service import AnalyticsService
from app.services.finance_service import FinanceService
from app.services.contract_service import ContractService
from app.services.customer_notes_service import CustomerNotesService, CustomerTagsService
from app.services.task_service import TaskService
from app.services.document_service import DocumentService
from app.database.database import DatabaseManager, DEFAULT_DB_PATH
from app.ui.styles.style import StyleManager
from app.core.file_manager import FileManager
from app.ui.widgets.date_picker import DatePicker
from app.ui.helpers.treeview_helpers import refresh_treeview
from app.ui.helpers.window_helpers import show_frame, setup_keyboard_shortcuts, nav_buttons
from app.ui.pages.home import setup_home_page
from app.ui.pages.add import setup_add_page
from app.ui.pages.view import setup_view_page
from app.ui.pages.manage import setup_manage_installments_page
from app.ui.pages.backup_restore import setup_backup_restore_page
from app.ui.pages.send_notification import setup_send_notification_page
from app.ui.pages.activity import setup_activity_page
from app.ui.pages.import_export import setup_import_export_page
from app.ui.pages.backup_manager import setup_backup_manager_page
from app.ui.pages.financial_dashboard import setup_financial_dashboard_page
from app.ui.pages.expenses import setup_expenses_page
from app.ui.pages.contracts import setup_contracts_page
from app.ui.pages.tasks_page import setup_tasks_page
from app.ui.pages.documents_page import setup_documents_page
from app.core.crash_recovery import install_global_exception_handler, load_session, clear_session
from app.core.recovery import run_startup_checks

install_global_exception_handler()

logging = stdlogging
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
)
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
logging.getLogger().addHandler(console)

frames = {}
file_manager = FileManager(os.path.join(os.path.dirname(os.path.abspath(__file__)), "customer_files"))


def initialize_app():
    try:
        app_window = CTk()
        app_window.geometry("1280x800")
        app_window.title(APP_NAME)
        app_window._set_appearance_mode("dark")
        try:
            sw = app_window.winfo_screenwidth()
            sh = app_window.winfo_screenheight()
            app_window.geometry(f"1280x800+{(sw-1280)//2}+{(sh-800)//2}")
        except Exception:
            pass
        return app_window
    except Exception as e:
        logging.critical(f"Failed to initialize: {e}\n{traceback.format_exc()}")
        messagebox.showerror(f"{APP_NAME} — Critical Error", "Failed to start the application.")
        sys.exit(1)


def create_app_shell(app):
    shell = StyleManager.create_frame(app, fg_color=StyleManager.COLORS["background"], border_width=0, corner_radius=0)
    shell.pack(fill="both", expand=True)
    shell.grid_columnconfigure(0, weight=0, minsize=220)
    shell.grid_columnconfigure(1, weight=1)
    shell.grid_rowconfigure(0, weight=1)

    sidebar = StyleManager.create_frame(shell, fg_color=StyleManager.COLORS["surface_low"], border_width=0, corner_radius=0)
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_rowconfigure(1, weight=1)

    brand = StyleManager.create_frame(sidebar, fg_color="transparent", border_width=0)
    brand.grid(row=0, column=0, sticky="ew", padx=16, pady=(24, 28))
    StyleManager.create_label(brand, text=APP_NAME, font_style="heading",
                              text_color=StyleManager.COLORS["primary"], anchor="w").pack(anchor="w")
    StyleManager.create_label(brand, text=VERSION_STRING, font_style="small",
                              text_color=StyleManager.COLORS["text_muted"], anchor="w").pack(anchor="w", pady=(2, 0))

    nav_frame = StyleManager.create_frame(sidebar, fg_color="transparent", border_width=0)
    nav_frame.grid(row=1, column=0, sticky="new", padx=8)
    nav_frame.grid_columnconfigure(0, weight=1)

    nav_items = [
        ("home", "Home"),
        ("add", "Add Customer"),
        ("view", "Customers"),
        ("manage", "Installments"),
        ("financial_dashboard", "Financial"),
        ("expenses", "Expenses"),
        ("notifications", "Notifications"),
        ("tasks", "Tasks"),
        ("contracts", "Contracts"),
        ("documents", "Documents"),
        ("backup_manager", "Backup Manager"),
        ("activity", "Activity Log"),
        ("import_export", "Import / Export"),
    ]

    for page_name, label in nav_items:
        from app.ui.helpers.window_helpers import create_nav_button
        btn = create_nav_button(nav_frame, label, lambda p=page_name: show_frame(frames[p]))
        btn.grid(row=len(nav_buttons), column=0, sticky="ew", pady=3)
        nav_buttons[page_name] = btn

    footer = StyleManager.create_frame(sidebar, fg_color="transparent", border_width=0)
    footer.grid(row=2, column=0, sticky="ew", padx=16, pady=20)
    StyleManager.create_label(footer, text=COPYRIGHT, font_style="small",
                              text_color=StyleManager.COLORS["text_secondary"], anchor="w").pack(anchor="w")

    content = StyleManager.create_frame(shell, fg_color=StyleManager.COLORS["background"], border_width=0, corner_radius=0)
    content.grid(row=0, column=1, sticky="nsew")
    content.grid_columnconfigure(0, weight=1)
    content.grid_rowconfigure(0, weight=1)
    return content


db = DatabaseManager(DEFAULT_DB_PATH)
db.initialize()
run_startup_checks(DEFAULT_DB_PATH, csv_path="customers.csv")
csv_repository = SQLiteRepository("customers.csv", "backups")
customer_service = CustomerService(csv_repository)
activity_service = ActivityService(db)
reminder_service = ReminderService(db)
analytics_service = AnalyticsService(db)
finance_service = FinanceService(db)
contract_service = ContractService(db)
notes_service = CustomerNotesService(db)
tags_service = CustomerTagsService(db)
task_service = TaskService(db)
document_service = DocumentService(db)

# ── Phase 8: Extensibility & Enterprise Platform ──────────────────────
from app.extensions.plugins.plugin_manager import PluginManager
from app.extensions.automation.rule_engine import RuleEngine
from app.extensions.automation.workflow_engine import WorkflowEngine
from app.extensions.events import dispatcher
from app.extensions.themes.theme_engine import ThemeEngine
from app.extensions.telemetry import telemetry
from app.extensions.integrations.integration_manager import IntegrationManager
from app.extensions.integrations.excel_integration import ExcelIntegration
from app.extensions.devtools.console import DeveloperConsole
from app.database.performance import PerformanceOptimizer

plugin_manager = PluginManager()
rule_engine = RuleEngine()
workflow_engine = WorkflowEngine()
theme_engine = ThemeEngine()
integration_manager = IntegrationManager()
perf_optimizer = PerformanceOptimizer(db)
dev_console = DeveloperConsole({"db": db, "services": {}, "events": dispatcher})

# Register built-in rule conditions/actions
for name, fn in rule_engine.builtin_conditions().items():
    rule_engine.register_condition(name, fn)
for name, fn in rule_engine.builtin_actions().items():
    rule_engine.register_action(name, fn)

# Register built-in workflow step handlers
for name, fn in workflow_engine.builtin_step_handlers().items():
    workflow_engine.register_step_handler(name, fn)

# Register built-in integrations
integration_manager.register(ExcelIntegration)

# Start telemetry
telemetry.record_startup()

# Apply performance optimizations
perf_optimizer.ensure_v5_indexes()

# Collect all services for API/scripting context
_services = {
    "db": db, "customer_service": customer_service, "finance_service": finance_service,
    "contract_service": contract_service, "task_service": task_service,
    "document_service": document_service, "activity_service": activity_service,
    "reminder_service": reminder_service, "analytics_service": analytics_service,
    "notes_service": notes_service, "tags_service": tags_service,
    "plugin_manager": plugin_manager, "rule_engine": rule_engine,
    "workflow_engine": workflow_engine, "theme_engine": theme_engine,
    "app_name": APP_NAME, "version": VERSION_STRING,
}
dev_console.set_context(services=_services)


def validate_and_save(name_entry, phone_entry, amount_entry, installments_entry, start_date_entry, file_list=None):
    from app.core.validation import ValidationService
    name = name_entry.get().strip()
    phone = phone_entry.get().strip()
    amount = amount_entry.get().strip()
    installments = installments_entry.get().strip()
    start_date = start_date_entry.get().strip()

    result = ValidationService.validate_customer(name, phone, amount, installments, start_date)
    if not result:
        messagebox.showerror("Error", result.errors[0])
        return False

    customer_data = customer_service.build_customer_record(name, phone, amount, installments, start_date)

    if customer_service.append_customer(customer_data):
        cid = csv_repository.get_customer_id_by_name(name)
        activity_service.log("Customer created", customer_id=cid, detail=f"{name} — {phone}")
        if file_list and hasattr(file_list, 'files') and file_list.files:
            file_manager.add_files(name, file_list.files)
        for w in (name_entry, phone_entry, amount_entry, installments_entry, start_date_entry):
            w.delete(0, "end")
        if file_list:
            file_list.files = []
            file_list.configure(state="normal")
            file_list.delete("1.0", "end")
            file_list.configure(state="disabled")
        messagebox.showinfo("Success", "Customer added successfully.")
        return True
    return False


def main(app_window):
    try:
        app_window.mainloop()
    except Exception as e:
        logging.critical(f"Critical error: {e}\n{traceback.format_exc()}")
        messagebox.showerror(f"{APP_NAME} — Critical Error", f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        app = initialize_app()

        from app.core.branding import show_splash_screen
        splash = show_splash_screen(app, StyleManager, duration_ms=2000)

        StyleManager.setup_theme()
        container = create_app_shell(app)

        page_names = [
            "home", "add", "view", "manage", "backup_restore", "notifications",
            "activity", "import_export", "backup_manager",
            "financial_dashboard", "expenses", "contracts",
            "tasks", "documents",
        ]
        for name in page_names:
            frame = StyleManager.create_frame(container)
            frame.grid(row=0, column=0, sticky="nsew")
            frame.page_name = name
            frames[name] = frame
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)

        from app.ui.pages.home import setup_home_page as _home
        from app.ui.pages.add import setup_add_page as _add
        from app.ui.pages.view import setup_view_page as _view
        from app.ui.pages.manage import setup_manage_installments_page as _manage
        from app.ui.pages.backup_restore import setup_backup_restore_page as _backup
        from app.ui.pages.send_notification import setup_send_notification_page as _notif
        from app.ui.pages.activity import setup_activity_page as _activity
        from app.ui.pages.import_export import setup_import_export_page as _import_export
        from app.ui.pages.backup_manager import setup_backup_manager_page as _backup_mgr
        from app.ui.pages.financial_dashboard import setup_financial_dashboard_page as _fin
        from app.ui.pages.expenses import setup_expenses_page as _expenses
        from app.ui.pages.contracts import setup_contracts_page as _contracts
        from app.ui.pages.tasks_page import setup_tasks_page as _tasks
        from app.ui.pages.documents_page import setup_documents_page as _docs
        from app.utils.export import export_to_excel
        from app.ui.widgets.payment_history import show_payment_history, refresh_payment_history_views

        _home(frames, StyleManager, show_frame, app, customer_service, csv_repository, activity_service, analytics_service)
        _add(frames, StyleManager, app, lambda *a: validate_and_save(*a) and show_frame(frames["manage"]), DatePicker, show_frame, csv_repository=csv_repository)
        _view(frames, StyleManager, customer_service, refresh_treeview, show_frame, app, DatePicker,
              lambda: refresh_payment_history_views(app),
              lambda: export_to_excel(csv_repository),
              lambda: show_payment_history(app, frames, csv_repository, customer_service),
              csv_repository=csv_repository, activity_service=activity_service)
        _manage(frames, StyleManager, customer_service, refresh_treeview, show_frame, app, DatePicker,
                lambda: refresh_payment_history_views(app),
                activity_service=activity_service, csv_repository=csv_repository)
        _backup(frames, StyleManager, csv_repository, show_frame, app, activity_service)
        _notif(frames, StyleManager, csv_repository, show_frame, app, reminder_service, activity_service)
        _activity(frames, StyleManager, activity_service, show_frame)
        _import_export(frames, StyleManager, csv_repository, customer_service, activity_service, show_frame, app)
        _backup_mgr(frames, StyleManager, csv_repository, show_frame, app, activity_service)
        _fin(frames, StyleManager, finance_service, show_frame)
        _expenses(frames, StyleManager, finance_service, show_frame)
        _contracts(frames, StyleManager, contract_service, show_frame)
        _tasks(frames, StyleManager, task_service, show_frame)
        _docs(frames, StyleManager, document_service, customer_service, show_frame)

        # ── Phase 8: Start optional API server ──────────────────────
        try:
            from app.extensions.api import start_api_server
            api_server = start_api_server(db, _services)
        except Exception as e:
            logging.warning("API server not started: %s", e)
            api_server = None

        # ── Phase 8: Wire events to activity service and telemetry ──
        dispatcher.on("*", lambda e: telemetry.record_event(e.name))
        dispatcher.on("customer.created", lambda e: activity_service.log("Customer created", e.data.get("customer_id")))
        dispatcher.on("customer.deleted", lambda e: activity_service.log("Customer deleted", e.data.get("customer_id")))
        dispatcher.on("installment.paid", lambda e: activity_service.log("Installment paid", e.data.get("customer_id")))
        dispatcher.on("app.startup", lambda e: telemetry.record_startup_complete())
        dispatcher.emit("app.startup", {})

        setup_keyboard_shortcuts(app, frames, show_frame)

        telemetry.record_startup_complete()
        last_page = load_session()
        if last_page and last_page in frames:
            show_frame(frames[last_page])
            clear_session()
        else:
            show_frame(frames["home"])

        if splash and splash.winfo_exists():
            try:
                splash.destroy()
            except Exception:
                pass

        main(app)
    except Exception as e:
        logging.critical(f"Application failed: {e}\n{traceback.format_exc()}")
        messagebox.showerror(f"{APP_NAME} — Critical Error", "Failed to start the application.")
        sys.exit(1)

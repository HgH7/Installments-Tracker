UI Pages Documentation
System Overview
This is a comprehensive installment management system built with CustomTkinter. The application helps manage customer installments with features for adding, viewing, managing, and tracking payments.

Navigation Structure
text
Home
├── Add Customer
├── View Customers
├── Manage Installments
├── Backup & Restore
└── Send Notifications
1. Home Page
Page Components
Component	Type	Description
App Title	Label	Main title "نظام إدارة الأقساط" (Installment Management System)
Subtitle	Label	"إدارة العملاء والأقساط بكل سهولة" (Manage customers and installments easily)
Action Buttons
Button	Type	Description
إضافة عميل جديد (Add Customer)	CTkButton	Navigates to the Add Customer page
عرض العملاء (View Customers)	CTkButton	Navigates to the View Customers page
إدارة الأقساط (Manage Installments)	CTkButton	Navigates to the Manage Installments page
النسخ الاحتياطي والاستعادة (Backup & Restore)	CTkButton	Navigates to the Backup & Restore page
إرسال إشعارات (Send Notifications)	CTkButton	Navigates to the Send Notifications page
2. Add Customer Page
Form Fields
Field	Type	Description	Validation
اسم العميل (Name)	CTkEntry	Customer's full name	Letters and spaces only
رقم الهاتف (Phone)	CTkEntry	Phone number with country code	10-15 digits, optional + prefix
المبلغ (Amount)	CTkEntry	Total installment amount	Positive number with 2 decimal places
عدد الأقساط (Installments)	CTkEntry	Number of installments	Positive integer
تاريخ البدء (Start Date)	CTkEntry + DatePicker	Start date for installments	YYYY-MM-DD format
File Upload
Component	Type	Description
رفع الملفات (Upload Files)	CTkTextbox	Drag-and-drop area for attaching customer files
File List Display	Text Widget	Shows uploaded files list
Action Buttons
Button	Type	Description
حفظ (Save)	CTkButton	Validates and saves customer data
اختر التاريخ (Pick Date)	CTkButton	Opens calendar popup for date selection
العودة (Back)	CTkButton	Returns to Home page
DatePicker (Popup)
Component	Type	Description
Calendar	tkcalendar.Calendar	Interactive calendar widget
تحديد (Select)	CTkButton	Confirms selected date
إلغاء (Cancel)	CTkButton	Closes calendar without selection
3. View Customers Page
Search Section
Component	Type	Description
بحث (Search)	Label	Search field label
Search Entry	CTkEntry	Search by customer name or phone
بحث (Search Button)	CTkButton	Executes search query
Status Label	CTkLabel	Shows current record count
Customer Table
Column	Description	Width
اسم العميل (Name)	Customer name	25%
رقم الهاتف (Phone)	Phone number	20%
المبلغ (Amount)	Total amount	15%
عدد الأقساط (Installments)	Number of installments	15%
قيمة القسط (Installment Value)	Per installment amount	15%
تاريخ البدء (Start Date)	Installment start date	10%
Action Buttons
Button	Type	Description
تحديث (Refresh)	CTkButton	Reloads customer data
سجل الدفع (Payment History)	CTkButton	Shows payment history for selected customer
تصدير Excel (Export)	CTkButton	Exports data to Excel file
تعديل العميل (Edit)	CTkButton	Opens edit dialog for selected customer
حذف العميل (Delete)	CTkButton	Deletes selected customer (with confirmation)
العودة (Back)	CTkButton	Returns to Home page
Edit Customer Dialog
Component	Type	Description
تعديل بيانات العميل (Title)	CTkLabel	Dialog title
اسم العميل (Name)	CTkEntry	Editable name field
رقم الهاتف (Phone)	CTkEntry	Editable phone field
المبلغ (Amount)	CTkEntry	Editable amount field
عدد الأقساط (Installments)	CTkEntry	Editable installments field
تاريخ البدء (Start Date)	CTkEntry + DatePicker	Editable start date
اختر التاريخ (Pick Date)	CTkButton	Opens calendar popup
حفظ التغييرات (Save)	CTkButton	Saves edited data
إلغاء (Cancel)	CTkButton	Closes dialog without saving
4. Manage Installments Page
Search Section
Component	Type	Description
بحث (Search)	Label	Search field label
Search Entry	CTkEntry	Search by customer name or phone
بحث (Search Button)	CTkButton	Executes search query
Installments Table
Column	Description	Width
اسم العميل (Name)	Customer name	20%
رقم الهاتف (Phone)	Phone number	15%
المبلغ (Amount)	Total amount	15%
عدد الأقساط (Installments)	Total number of installments	15%
المدفوع (Paid)	Paid/Total installments	20%
القادم (Next Due)	Next installment due date	15%
Color Coding
Green Text: All installments paid

Red Text: Pending installments

Installment Details Dialog
Component	Type	Description
تفاصيل أقساط العميل (Title)	CTkLabel	Dialog title with customer name
Installments Table	ttk.Treeview	Shows individual installment details
تاريخ القسط (Date)	Column	Installment date
المبلغ (Amount)	Column	Installment amount
الحالة (Status)	Column	Paid/Unpaid status
تسجيل كمدفوع (Mark Paid)	CTkButton	Marks selected installment as paid
إلغاء تسجيل الدفع (Unmark)	CTkButton	Unmarks selected installment as paid
إغلاق (Close)	CTkButton	Closes dialog
Action Buttons
Button	Type	Description
تحديث (Refresh)	CTkButton	Reloads installment data
العودة (Back)	CTkButton	Returns to Home page
5. Payment History Dialog
Dialog Components
Component	Type	Description
سجل المدفوعات (Title)	CTkLabel	Dialog title with customer name
Payment History Table	ttk.Treeview	Shows all installment payments
تاريخ القسط (Date)	Column	Installment date
قيمة القسط (Value)	Column	Installment amount
الحالة (Status)	Column	Paid/Unpaid status
إجراء (Action)	Column	Action button (if applicable)
Payment Summary
Component	Type	Description
Payment Progress	CTkLabel	Shows paid/total installments count
Amount Paid	CTkLabel	Shows total amount paid
Remaining Amount	CTkLabel	Shows remaining balance
Completion Percentage	CTkLabel	Shows payment progress percentage
Interactive Features
Feature	Description
Double-click	Marks installment as paid (if unpaid)
Right-click	Opens edit installment dialog
Edit Installment Dialog
Component	Type	Description
تعديل بيانات القسط (Title)	CTkLabel	Dialog title
العميل (Customer)	CTkLabel	Shows customer name (read-only)
تاريخ القسط (Date)	CTkEntry	Editable date field
📅 (Date Picker)	CTkButton	Opens calendar popup
قيمة القسط (Amount)	CTkEntry	Editable amount field
مدفوع (Paid)	CTkCheckBox	Toggle payment status
حفظ التغييرات (Save)	CTkButton	Saves changes
إلغاء (Cancel)	CTkButton	Closes dialog
6. Backup & Restore Page
Components
Component	Type	Description
النسخ الاحتياطي والاستعادة (Title)	CTkLabel	Page title
Info Frame	CTkFrame	Contains backup information
إدارة البيانات (Data Management)	CTkLabel	Section header
Backup Section
Component	Type	Description
عمل نسخة احتياطية (Backup)	CTkButton	Creates a backup of all customer data
التاريخ (Date)	CTkLabel	Shows last backup date (if available)
Restore Section
Component	Type	Description
استعادة من نسخة (Restore)	CTkButton	Opens file dialog to select backup file
اختر ملف (Choose File)	FileDialog	Opens system file picker
Action Buttons
Button	Type	Description
العودة (Back)	CTkButton	Returns to Home page
Features
Backup: Creates timestamped backup file

Restore: Replaces current data with selected backup

Automatic Backup: System creates backup before critical operations

7. Send Notification Page
Components
Component	Type	Description
إرسال إشعارات (Title)	CTkLabel	Page title
اختر العميل (Select Customer)	CTkLabel	Field label
Customer Selection
Component	Type	Description
Customer Selection	CTkComboBox	Dropdown with all customer names
Customer Details	CTkLabel	Shows selected customer's phone number
Message Section
Component	Type	Description
رسالة (Message)	CTkTextbox	Multi-line message input area
Character Count	CTkLabel	Shows remaining characters
Template Buttons
Button	Type	Description
رسالة قسط مستحق (Due Installment)	CTkButton	Pre-fills with due installment template
رسالة تأكيد دفع (Payment Confirmation)	CTkButton	Pre-fills with payment confirmation template
رسالة تذكير (Reminder)	CTkButton	Pre-fills with reminder template
Action Buttons
Button	Type	Description
إرسال عبر واتساب (Send WhatsApp)	CTkButton	Opens WhatsApp to send message
إرسال للجميع (Send All)	CTkButton	Sends message to all customers
العودة (Back)	CTkButton	Returns to Home page
Status Information
Component	Type	Description
Status Bar	CTkLabel	Shows current operation status
Progress Indicator	Optional	Shows notification sending progress
Global Components
Style Manager
Color Scheme: Dark mode with accent colors

Primary Color: #2B7DE9 (Blue)

Secondary Color: #E67E22 (Orange)

Success Color: #27AE60 (Green)

Danger Color: #E74C3C (Red)

Background: #1A1A2E (Dark)

Surface: #16213E (Dark Blue)

Text: #FFFFFF (White)

Common UI Elements
Element	Description
Frame	CTkFrame	Container for grouping elements
Label	CTkLabel	Text display with configurable styles
Entry	CTkEntry	Text input field
Button	CTkButton	Action trigger with various styles
Treeview	ttk.Treeview	Tabular data display
Scrollbar	ttk.Scrollbar	Navigation for overflowing content
Font Styles
Heading: Size 28, Bold

Subheading: Size 22, Bold

Body Bold: Size 16, Bold

Body: Size 14, Regular

Small: Size 12, Regular

Notification System
Thread: Background thread for automatic checks

Check Interval: Every hour

Notification Window: 3 days before due date

Retry Logic: 2 attempts with 10-second intervals

Data Management
CSV Repository: Main data storage

Backup System: Automatic and manual backups

File Manager: Handles customer file attachments

Keyboard Shortcuts
Shortcut	Action
Enter	Submit/Search
Double-click	Mark installment as paid
Right-click	Edit installment details
Error Handling
Common Error Messages
Message	Scenario
جميع الحقول مطلوبة (All fields required)	Form submission with empty fields
رقم الهاتف غير صالح (Invalid phone)	Phone number validation fails
المبلغ يجب أن يكون رقمًا صالحًا (Invalid amount)	Amount format is incorrect
عدد الأقساط يجب أن يكون رقمًا صحيحًا (Invalid installments)	Non-integer installment count
تنسيق التاريخ غير صحيح (Invalid date format)	Date not in YYYY-MM-DD format
لا توجد بيانات للتصدير (No data to export)	Empty dataset for export
Data Flow
text
Add Customer → CSV Storage → Display in Table
                    ↓
              Backup System
                    ↓
              Edit/Delete
                    ↓
             Installment Management
                    ↓
           Payment History Tracking
                    ↓
         Notification System (Auto & Manual)
Deployment Notes
Dependencies
python
customtkinter>=5.2.0
tkcalendar>=1.6.1
pandas>=1.5.0
openpyxl>=3.0.10
xlsxwriter>=3.0.2
pywhatkit>=5.4
Environment Variables
LOG_LEVEL: Set logging level (default: DEBUG)

BACKUP_INTERVAL: Hours between automatic backups

Directory Structure
text
app/
├── repositories/
│   └── csv_repository.py
├── services/
│   └── customer_service.py
├── ui/
│   ├── style.py
│   ├── file_manager.py
│   └── pages/
│       ├── home.py
│       ├── add.py
│       ├── view.py
│       ├── manage.py
│       ├── backup_restore.py
│       └── send_notification.py
└── utils/
    └── serialization.py

logs/
└── app.log

backups/
└── *.csv

customer_files/
└── [customer_name]/
    └── [uploaded_files]
Performance Optimizations
Feature	Optimization
Data Loading	Lazy loading, pagination ready
Search	Client-side filtering
Treeviews	Virtual scrolling
Notifications	Background threading
Backups	Incremental backup strategy
Security Features
Feature	Description
File Handling	Sanitized file paths
Data Validation	Input sanitization on all fields
Backup Integrity	Validation on restore operations
Error Logging	Comprehensive error tracking
This documentation covers all UI components and their functionality in the Installment Management System. For additional technical details, refer to the inline code comments and logging outputs.


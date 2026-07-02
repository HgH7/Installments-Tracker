# Installments Tracker — User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Home Dashboard](#home-dashboard)
3. [Adding Customers](#adding-customers)
4. [Viewing Customers](#viewing-customers)
5. [Managing Installments](#managing-installments)
6. [Payment History](#payment-history)
7. [Notifications & Reminders](#notifications--reminders)
8. [Backup Manager](#backup-manager)
9. [Activity Log](#activity-log)
10. [Import / Export](#import--export)
11. [File Attachments](#file-attachments)
12. [Settings](#settings)
13. [Keyboard Shortcuts](#keyboard-shortcuts)
14. [Crash Recovery](#crash-recovery)

---

## Getting Started

### Launching the Application

```bash
python The-Project.py
```

On first launch, the application will:
- Create a `data/` directory for the SQLite database
- Create a `logs/` directory for application logs
- Create a `backups/` directory for backup files
- Initialize the database schema with required tables

### System Requirements

- Python 3.9 or higher
- 512 MB RAM minimum
- 100 MB disk space

---

## Home Dashboard

The home page provides an overview of your business:

- **Total Customers** — count of all registered customers
- **Active Customers** — customers with pending installments
- **Total Revenue** — sum of all paid installments
- **Pending Amount** — outstanding balance across all customers
- **Overdue Installments** — count of past-due payments

### Recent Activity Feed

Shows the latest actions (additions, payments, edits) in chronological order.

### Quick Actions

- Click customer count to go to Customers page
- Click pending amount to go to Installments page

---

## Adding Customers

1. Click **Add Customer** in the sidebar
2. Fill in the required fields:
   - **Customer Name** — full name (minimum 3 characters)
   - **Phone Number** — valid phone number with country code
   - **Total Amount** — the total amount to be paid
   - **Installment Count** — number of installments
   - **Start Date** — first installment due date
3. Optionally attach files using the file picker
4. Click **Add Customer** to save

### Date Picker

Click the date entry field to open a date picker dialog. Navigate months with the arrow buttons and click a date to select it.

### File Attachments

Click "Browse Files" to attach one or more files to a customer. Supported file types include images, PDFs, and documents.

---

## Viewing Customers

The Customers page displays all customers in a searchable table:

### Searching

Use the search bar at the top to filter by name or phone number.

### Customer Details

Click a customer row to see:
- **Personal info** — name, phone, total amount
- **Installment schedule** — due dates, amounts, payment status
- **Payment history** — per-customer timeline
- **Attached files** — click to open/download

### Actions

- **Edit** — modify customer details
- **Delete** — remove customer and all associated data
- **View Payment History** — detailed payment timeline

---

## Managing Installments

Track and update installment payments:

1. Select a customer from the list
2. View the installment schedule with due dates and amounts
3. Mark installments as **Paid** or **Partially Paid**
4. Record partial payments with dates

### Payment Entry

- Enter the payment amount
- Select the payment date
- Add optional notes
- Click **Record Payment**

### Installment Status

- **Pending** — payment not yet due
- **Due** — payment is due but not paid
- **Partially Paid** — partial payment received
- **Paid** — fully paid
- **Overdue** — past the due date without payment

---

## Payment History

Access the payment history dialog from the Customers page:

- **Per-customer timeline** of all recorded payments
- **Date range filtering** — filter by start/end dates
- **Export to CSV** — download payment history as a CSV file
- **Summary bar** — total paid, remaining balance

---

## Notifications & Reminders

The Notifications page manages payment reminders:

### Viewing Reminders

- **Upcoming** — payments due in the next N days
- **Overdue** — payments past their due date
- **All** — complete list of all reminders

### Sending Notifications

- Click **Send Notification** for individual reminders
- Use **Force Check** to re-evaluate all reminder states

### Settings

Configure reminder behavior in Settings:
- Reminder days before due date
- Auto-dismiss notifications
- Enable/disable notification sounds

---

## Backup Manager

The Backup Manager supports automated and manual backups:

### Creating Backups

- **Manual Backup** — click "Create Backup" to save a snapshot
- **Automatic Backup** — enabled by default, runs every 7 days

### Restoring Backups

1. Select a backup from the list
2. Click **Restore** to replace current data
3. Confirm the restore operation

### Managing Backups

- **Delete** — remove individual backup files
- **Max Backups** — configure retention count in Settings
- **Backup Directory** — change the storage location in Settings

---

## Activity Log

The Activity Log records all operations for audit purposes:

### Viewing Logs

- **Search** by keyword across all log entries
- **Date filter** — select a date range
- **Export** — download visible entries as CSV

### Logged Events

- Customer created, updated, deleted
- Payment recorded
- Backup created, restored, deleted
- Import/export operations
- Settings changes

---

## Import / Export

### Export to Excel

1. Go to **Import / Export** page
2. Click **Export to Excel**
3. Choose a save location
4. The exported file includes formatted sheets

### Export to CSV

Same process as Excel export, but produces a comma-separated file.

### Import from CSV

1. Click **Import CSV**
2. Select the file to import
3. Map fields if needed
4. Preview data before importing

---

## File Attachments

Files are managed on a per-customer basis:

1. Go to **Customers** page
2. Click a customer name
3. View attached files in the details section
4. Click a file to open it with the default system application
5. Use **Delete** to remove attachments

---

## Settings

Access Settings from the gear icon or the sidebar:

### General

- Application name, language, update preferences

### Display

- Theme (dark, light, system)
- Accent color
- Items per page
- Date format
- Currency settings

### Notifications

- Enable/disable notifications
- Reminder period
- Auto-dismiss behavior

### Backup

- Automatic backup toggle
- Backup interval
- Maximum backup files
- Backup directory path

### Privacy

- Log anonymization
- Usage statistics collection
- Crash reporting

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New customer (focus Add Customer page) |
| `Ctrl+F` | Focus the search bar |
| `Ctrl+Q` | Quit the application |

---

## Crash Recovery

If the application crashes unexpectedly:

1. A crash log is saved to `logs/crash.log`
2. On next launch, the application attempts to restore the last session
3. If a crash is detected, you will be prompted to save a bug report

### Manual Recovery

If the application fails to start:

1. Check `logs/crash.log` for error details
2. Try restoring from a backup via the Backup Manager
3. If the database is corrupted, delete `data/database.sqlite` and restart (data will be lost unless you have a backup)

### Reporting Issues

Report issues at: https://github.com/otman-22-git/Installments-Tracker/issues

Include the crash log file (`logs/crash.log`) and a description of what happened.

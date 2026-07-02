# Database Schema

## Version: 2

## Tables

### customers
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| customer_name | TEXT NOT NULL | |
| phone_number | TEXT NOT NULL | |
| total_amount | REAL | Total contract amount |
| installment_count | INTEGER | Number of installments |
| start_date | TEXT | YYYY-MM-DD |
| notes | TEXT | |
| created_at | TEXT | Timestamp |
| updated_at | TEXT | Timestamp |

### installments
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| customer_id | INTEGER FK | References customers(id) ON DELETE CASCADE |
| installment_number | INTEGER | 1-based ordering |
| due_date | TEXT | YYYY-MM-DD |
| amount | REAL | Installment value |
| status | TEXT | 'pending' or 'paid' |
| notified | INTEGER | 0 or 1 |
| paid_date | TEXT | Null if unpaid |

### attachments
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| customer_id | INTEGER FK | References customers(id) ON DELETE CASCADE |
| file_name | TEXT | Display name |
| original_path | TEXT | Original file path |
| stored_path | TEXT | Stored file path |
| created_at | TEXT | Timestamp |

### backups
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| file_name | TEXT | Backup filename |
| file_size | INTEGER | Size in bytes |
| created_at | TEXT | Timestamp |

### _schema_version
| Column | Type |
|--------|------|
| version | INTEGER |
| applied_at | TEXT |

## Indexes

- customers: customer_name, phone_number
- installments: customer_id, due_date, status
- attachments: customer_id

## Migrations

- Version 1 (initial): customers, contracts, installments, payments, customer_files
- Version 2 (current): customers, installments, attachments, backups

Migration v1→v2 drops the old normalized tables and creates the flat storage schema.

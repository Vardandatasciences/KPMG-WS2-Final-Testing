# Update VARCHAR/CHAR Columns for Encryption Support

This script updates all VARCHAR and CHAR columns in the MySQL database that are 45 characters or less, or below 1000 characters, to support encryption.

## Why This Script?

When encrypting data using Fernet encryption (which uses base64 encoding), the encrypted data can be up to 50% larger than the original plain text. This script ensures all columns have sufficient space to store encrypted data.

## Features

- **Finds all small columns**: Scans the database for VARCHAR/CHAR columns with length <= 45 or < 1000
- **Accounts for encryption overhead**: Sets columns to minimum 1000 characters, or 1500 characters (recommended) to account for encryption overhead
- **Safe execution**: Shows a summary before making changes and asks for confirmation
- **Detailed logging**: Logs all changes and any errors encountered

## Prerequisites

1. Python 3.7+
2. MySQL database access credentials
3. `mysql-connector-python` package (already in requirements.txt)

## Usage

### Option 1: Using Environment Variables

```bash
export DB_NAME=grc2
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=3306

cd grc_backend
python update_varchar_columns.py
```

### Option 2: Using Django Settings

If Django is configured, the script will automatically use Django database settings:

```bash
cd grc_backend
python update_varchar_columns.py
```

### Option 3: Direct Database Connection

You can also modify the script to hardcode credentials (not recommended for production).

## What the Script Does

1. **Scans the database** (`grc2` by default) for all VARCHAR/CHAR columns
2. **Identifies columns** that need updating:
   - Columns with length <= 45 characters
   - Columns with length < 1000 characters
3. **Calculates new length**:
   - Small columns (<= 45): Set to 1500 characters (recommended for encryption)
   - Medium columns (< 1000): Set to 1500 characters
   - Accounts for ~50% encryption overhead
4. **Shows summary** of all columns that will be updated
5. **Asks for confirmation** before making changes
6. **Updates columns** one by one, logging success/failure
7. **Reports final summary** with success/error counts

## Example Output

```
2024-01-15 10:30:00 - INFO - Connected to database using Django settings: grc2
2024-01-15 10:30:00 - INFO - Scanning database 'grc2' for small VARCHAR/CHAR columns...
2024-01-15 10:30:01 - INFO - Found 25 columns that need updating:
2024-01-15 10:30:01 - INFO -   users: 3 columns
2024-01-15 10:30:01 - INFO -     - Email: varchar(255)
2024-01-15 10:30:01 - INFO -     - PhoneNumber: varchar(45)
2024-01-15 10:30:01 - INFO -     - Address: varchar(255)
...

================================================================================
Found 25 columns to update across 8 tables.
All columns will be updated to minimum 1000 characters.
Recommended length: 1500 characters (accounts for encryption overhead).
================================================================================

Do you want to proceed with the updates? (yes/no): yes

2024-01-15 10:30:05 - INFO - Starting column updates...
2024-01-15 10:30:05 - INFO - ✓ Successfully updated users.Email to VARCHAR(1500)
2024-01-15 10:30:05 - INFO - ✓ Successfully updated users.PhoneNumber to VARCHAR(1500)
...

================================================================================
UPDATE SUMMARY
================================================================================
Total columns found: 25
Successfully updated: 25
Errors: 0
================================================================================
```

## Column Length Recommendations

- **Minimum**: 1000 characters (for basic encryption support)
- **Recommended**: 1500 characters (accounts for encryption overhead)
- **Indexed Columns**: Maximum 767 characters (MySQL InnoDB utf8mb4 index limit)
- **Large Tables**: Columns in tables with >20 columns may be converted to TEXT to avoid row size limits
- **Encryption Overhead**: Fernet encryption with base64 encoding adds approximately 33-50% overhead

## Smart Handling

The script automatically handles:

1. **Indexed Columns**: Limited to 767 characters to respect MySQL's index key length limit (3072 bytes for utf8mb4)
2. **Row Size Limits**: Tables with many columns (>20) may have columns converted to TEXT instead of VARCHAR to avoid exceeding MySQL's 65535 byte row size limit
3. **TEXT Columns**: Automatically removes DEFAULT constraints (MySQL doesn't support DEFAULT for TEXT)
4. **Error Handling**: Continues processing other columns even if some fail

## Safety Features

1. **Read-only scan first**: The script scans and shows all changes before making any modifications
2. **User confirmation required**: You must type "yes" to proceed with updates
3. **Transaction safety**: Each column update is committed individually (can be modified for batch transactions)
4. **Error handling**: Errors are logged and the script continues with other columns
5. **Rollback on error**: Failed updates are rolled back automatically

## Troubleshooting

### Connection Errors

If you get connection errors, check:
- Database credentials are correct
- Database server is running
- Network connectivity to database host
- Firewall rules allow connections

### Permission Errors

Ensure the database user has `ALTER` permissions on all tables:
```sql
GRANT ALTER ON grc2.* TO 'your_user'@'%';
FLUSH PRIVILEGES;
```

### Column Update Errors

Some columns might fail to update due to:
- Data truncation (existing data longer than new limit - should not happen with this script)
- Foreign key constraints
- Index constraints
- Table locks

Check the error messages in the output for specific details.

## Backup Recommendation

**IMPORTANT**: Always backup your database before running this script:

```bash
mysqldump -u your_user -p grc2 > grc2_backup_$(date +%Y%m%d_%H%M%S).sql
```

## After Running the Script

1. Verify the changes:
   ```sql
   SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = 'grc2'
     AND DATA_TYPE IN ('varchar', 'char')
     AND CHARACTER_MAXIMUM_LENGTH < 1000;
   ```
   This should return no rows.

2. Update your Django models if needed (though the script updates the database directly)

3. Test your application to ensure everything works correctly

## Notes

- The script modifies the database schema directly
- Django models should be updated to reflect the new column sizes (optional, but recommended)
- The script preserves NULL/NOT NULL constraints and default values
- Indexes are automatically updated by MySQL when column sizes change


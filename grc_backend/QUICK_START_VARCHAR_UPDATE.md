# Quick Start: Update VARCHAR Columns for Encryption

## Quick Run

```bash
cd grc_backend

# Dry run (see what would change, no actual changes)
python update_varchar_columns.py --dry-run

# Actual update (will ask for confirmation)
python update_varchar_columns.py
```

## With Environment Variables

```bash
export DB_NAME=grc2
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=3306

python update_varchar_columns.py
```

## What It Does

1. Finds all VARCHAR/CHAR columns with length <= 45 or < 1000
2. Updates them to 1500 characters (accounts for encryption overhead)
3. Shows summary before and after

## Backup First!

```bash
mysqldump -u your_user -p grc2 > backup_$(date +%Y%m%d).sql
```

## Example Output

```
Found 25 columns to update across 8 tables.
All columns will be updated to minimum 1000 characters.
Recommended length: 1500 characters (accounts for encryption overhead).

Do you want to proceed with the updates? (yes/no): yes
```



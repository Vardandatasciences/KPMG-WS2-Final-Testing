# Encrypt All Database Data - Usage Guide

## Overview

This script encrypts all existing **plaintext** data in your database using the `GRC_ENCRYPTION_KEY` from your environment file.

## ⚠️ IMPORTANT WARNINGS

1. **BACKUP YOUR DATABASE FIRST!** This script modifies data in your database.
2. **Test in a development environment first** before running on production.
3. The script only encrypts data that is **NOT already encrypted**.
4. Once data is encrypted, you **MUST** use the same `GRC_ENCRYPTION_KEY` to decrypt it.

## Prerequisites

1. **Set `GRC_ENCRYPTION_KEY` in your environment:**
   ```bash
   # Windows PowerShell
   $env:GRC_ENCRYPTION_KEY = "your-encryption-key-here"
   
   # Or in .env file
   GRC_ENCRYPTION_KEY=your-encryption-key-here
   ```

2. **Verify your encryption key is loaded:**
   ```bash
   python check_encryption_key.py
   ```

## Usage

### Step 1: Dry Run (Preview what will be encrypted)

First, run in **dry-run mode** to see what will be encrypted **without modifying any data**:

```bash
cd grc_backend
python encrypt_all_data.py
```

This will show you:
- Which models will be processed
- Which fields will be encrypted
- How many records will be encrypted
- How many records are already encrypted (skipped)
- Any errors

### Step 2: Review the Output

Check the output carefully. Make sure:
- ✅ The encryption key is being used correctly
- ✅ The models and fields listed are correct
- ✅ The number of records to encrypt looks reasonable

### Step 3: Run Live (Actually Encrypt Data)

Once you're satisfied with the dry-run results, run in **live mode** to actually encrypt the data:

```bash
python encrypt_all_data.py --live
```

## What Gets Encrypted

The script encrypts all fields defined in `grc/utils/encryption_config.py`:

- **Users**: Email, PhoneNumber, Address, UserName, FirstName, LastName, etc.
- **Framework**: FrameworkName, FrameworkDescription, DocURL, Identifier
- **Risk**: RiskTitle, RiskDescription, PossibleDamage, BusinessImpact, RiskMitigation
- **RiskInstance**: RiskTitle, RiskDescription, PossibleDamage, BusinessImpact, RiskMitigation
- **Compliance**: ComplianceTitle, ComplianceItemDescription, Scope, Objective, etc.
- **Policy**: PolicyName, PolicyDescription, Applicability, Scope, Objective
- **Incident**: IncidentTitle, Description, Comments, etc.
- **Audit**: Title, Scope, Objective, Evidence, Comments
- And more...

## Example Output

```
================================================================================
DATABASE ENCRYPTION SCRIPT
================================================================================

🔍 DRY RUN MODE - No data will be modified

✅ Encryption key verified and working

📦 Processing model: Framework
  🔐 Encrypting field: FrameworkName
  Processing 50 records...
    ✅ Encrypted: 15 records
    ⏭️  Skipped (already encrypted/empty): 35 records
  🔐 Encrypting field: FrameworkDescription
  Processing 50 records...
    ✅ Encrypted: 20 records
    ⏭️  Skipped (already encrypted/empty): 30 records

📦 Processing model: Risk
  🔐 Encrypting field: RiskTitle
  Processing 100 records...
    ✅ Encrypted: 45 records
    ⏭️  Skipped (already encrypted/empty): 55 records

================================================================================
ENCRYPTION SUMMARY
================================================================================
Models processed: 10
Records encrypted: 150
Records skipped (already encrypted/empty): 350
Errors: 0

🔍 This was a DRY RUN - no data was modified
To actually encrypt the data, run:
  python encrypt_all_data.py --live
================================================================================
```

## Troubleshooting

### Error: "GRC_ENCRYPTION_KEY is not set!"

**Solution:** Make sure `GRC_ENCRYPTION_KEY` is set in your environment:
```bash
# Check if it's set
echo $env:GRC_ENCRYPTION_KEY  # Windows PowerShell
echo $GRC_ENCRYPTION_KEY       # Linux/Mac

# Set it if missing
$env:GRC_ENCRYPTION_KEY = "your-key-here"  # Windows PowerShell
export GRC_ENCRYPTION_KEY="your-key-here" # Linux/Mac
```

### Error: "Encryption service test failed!"

**Solution:** Your encryption key might be invalid. Generate a new one:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Use this as your GRC_ENCRYPTION_KEY
```

### Some records show errors

**Solution:** Check the error messages. Common issues:
- Field doesn't exist in model (script will skip it)
- Data type mismatch (script will log the error)
- Database connection issues

## After Running

1. **Verify encryption worked:**
   - Check a few records in your database
   - Encrypted fields should start with `gAAAAAB...`
   - Use the decryption endpoints to verify data can be decrypted

2. **Test your application:**
   - Make sure all pages load correctly
   - Verify data is displayed correctly (should be decrypted automatically)
   - Check that new data is being encrypted when created

3. **Monitor for issues:**
   - Check application logs for decryption errors
   - Verify all encrypted fields are being decrypted in the UI

## Notes

- **Passwords are NOT encrypted** - They should be hashed (bcrypt/argon2), not encrypted
- **Already encrypted data is skipped** - The script only encrypts plaintext data
- **Empty/None values are skipped** - No need to encrypt empty fields
- **The script is idempotent** - Running it multiple times is safe (it skips already encrypted data)

## Support

If you encounter issues:
1. Check the error messages in the script output
2. Verify your `GRC_ENCRYPTION_KEY` is correct
3. Make sure your database is accessible
4. Check Django logs for additional error details



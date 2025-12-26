# Quick Setup Guide: User Inactivity Auto-Deactivation

## Installation Steps

Follow these steps to enable automatic user deactivation based on inactivity:

### Step 1: Apply Database Migration

Add the `last_login` field to the Users table:

```bash
cd grc_backend
python manage.py migrate grc
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: grc
Running migrations:
  Applying grc.0002_add_last_login... OK
```

### Step 2: Verify the Installation

Run the test script to verify everything is set up correctly:

```bash
python test_user_inactivity.py
```

This will show you:
- Whether the `last_login` field was added successfully
- Statistics about user login activity
- Users who would be deactivated based on inactivity
- Recent login activity

### Step 3: Configure Inactivity Threshold (Optional)

Edit your `.env` file or set environment variables:

```env
# Number of days before deactivating inactive users (default: 90)
USER_INACTIVITY_DAYS=90

# Future feature: Email notifications
USER_INACTIVITY_EMAIL_ENABLED=false
USER_INACTIVITY_WARNING_DAYS=7
```

### Step 4: Test Deactivation (Dry Run)

See what users would be deactivated without actually deactivating them:

```bash
# Using default 90 days
python manage.py deactivate_inactive_users --dry-run

# Using custom threshold (e.g., 60 days)
python manage.py deactivate_inactive_users --days 60 --dry-run

# Exclude users who never logged in
python manage.py deactivate_inactive_users --exclude-never-logged-in --dry-run
```

### Step 5: Run Actual Deactivation

Once you're satisfied with the dry run results:

```bash
python manage.py deactivate_inactive_users
```

### Step 6: Schedule Automated Execution

#### Option A: Windows Task Scheduler

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Name: `Deactivate Inactive Users`
4. Trigger: **Daily**
5. Time: `02:00 AM` (or preferred time)
6. Action: **Start a program**
7. Program/script: Full path to Python executable
   ```
   C:\Python\python.exe
   ```
8. Add arguments:
   ```
   manage.py deactivate_inactive_users
   ```
9. Start in:
   ```
   C:\Users\louky\OneDrive - Vardaan Cyber Security Pvt Ltd\Desktop\GRC_TPRM\grc_backend
   ```

#### Option B: Create a Batch Script

Create `run_deactivation.bat`:

```batch
@echo off
cd /d "C:\Users\louky\OneDrive - Vardaan Cyber Security Pvt Ltd\Desktop\GRC_TPRM\grc_backend"
python manage.py deactivate_inactive_users >> logs\user_deactivation.log 2>&1
echo User deactivation completed at %date% %time% >> logs\user_deactivation.log
```

Then schedule this batch file in Task Scheduler.

#### Option C: Linux/Mac Cron

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * cd /path/to/grc_backend && python manage.py deactivate_inactive_users >> /var/log/user_deactivation.log 2>&1
```

## Verification

### Check Logs

After running the deactivation command, check the logs:

```python
python manage.py shell
```

```python
from grc.models import GRCLog

# View deactivation logs
logs = GRCLog.objects.filter(ActionType='USER_DEACTIVATED').order_by('-Timestamp')
for log in logs[:10]:
    print(f"{log.Timestamp}: {log.UserName} - {log.Description}")
```

### Check Deactivated Users

```python
from grc.models import Users

# Show recently deactivated users
inactive_users = Users.objects.filter(IsActive='N')
print(f"Total inactive users: {inactive_users.count()}")

for user in inactive_users[:10]:
    print(f"User: {user.UserName}, Last Login: {user.last_login}")
```

## Troubleshooting

### Issue: Migration fails

**Error:** `django.db.utils.OperationalError: (1054, "Unknown column 'last_login'")`

**Solution:**
```bash
# Check migrations status
python manage.py showmigrations grc

# If migration is not applied, run:
python manage.py migrate grc

# If migration is missing, create it:
python manage.py makemigrations grc
python manage.py migrate grc
```

### Issue: Command not found

**Error:** `Unknown command: 'deactivate_inactive_users'`

**Solution:**
- Verify the file exists: `grc/management/commands/deactivate_inactive_users.py`
- Ensure `__init__.py` files exist in all directories
- Try: `python manage.py help` to see available commands

### Issue: No users being deactivated

**Possible causes:**
1. All users have logged in recently
2. `last_login` field is NULL for all users (they need to log in first)
3. Inactivity threshold is too high

**Solution:**
```bash
# Check user statistics
python test_user_inactivity.py

# Try a shorter threshold (dry-run first)
python manage.py deactivate_inactive_users --days 30 --dry-run
```

### Issue: Last login not updating

**Solution:**
1. Verify users are logging in successfully
2. Check Django logs for errors
3. Verify the code changes were applied correctly
4. Restart the Django server

## Next Steps

After setup:

1. ✅ Monitor the first few deactivation runs
2. ✅ Review the audit logs regularly
3. ✅ Adjust the inactivity threshold based on your organization's needs
4. ✅ Consider implementing email notifications (future feature)
5. ✅ Document your organization's reactivation process

## Support

For detailed documentation, see:
- **Full Documentation:** `USER_INACTIVITY_IMPLEMENTATION.md`
- **Test Script:** `test_user_inactivity.py`
- **Migration File:** `grc/migrations/0002_add_last_login.py`
- **Management Command:** `grc/management/commands/deactivate_inactive_users.py`

---

**Quick Reference Commands:**

```bash
# Test the setup
python test_user_inactivity.py

# Dry run (no changes)
python manage.py deactivate_inactive_users --dry-run

# Deactivate users (90 days default)
python manage.py deactivate_inactive_users

# Custom threshold
python manage.py deactivate_inactive_users --days 60

# Exclude never-logged-in users
python manage.py deactivate_inactive_users --exclude-never-logged-in
```


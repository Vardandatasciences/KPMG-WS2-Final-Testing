# User Inactivity Auto-Deactivation Implementation

## Overview

This document describes the implementation of automatic user deactivation based on inactivity period. Users who haven't logged in for a specified number of days will automatically have their account status changed to inactive.

## Features Implemented

### 1. Last Login Tracking

- **Added `last_login` field** to the `Users` model to track when each user last successfully logged in
- **Automatically updated** on every successful login (both JWT and session-based authentication)
- Field type: `DateTimeField` (nullable, allows for users who have never logged in)

### 2. Login Functions Updated

Both login methods now track the last login time:

- **JWT Login** (`grc/authentication.py` - `jwt_login()`)
- **Session Login** (`grc/views.py` - `login_user()`)

The `last_login` field is updated immediately after successful authentication, license verification, and MFA verification (if enabled).

### 3. Management Command

A new Django management command has been created to automatically deactivate inactive users:

**Command:** `deactivate_inactive_users.py`

**Location:** `grc/management/commands/deactivate_inactive_users.py`

**Features:**
- Checks for users who haven't logged in for a specified number of days
- Marks inactive users by changing their `IsActive` status from 'Y' to 'N'
- Logs all deactivations to the `GRCLog` table for audit trail
- Supports dry-run mode for testing
- Can exclude users who have never logged in

### 4. Configuration Settings

New configuration settings added to `backend/settings.py`:

```python
# Number of days of inactivity before auto-deactivation (default: 90 days)
USER_INACTIVITY_DAYS = int(os.environ.get('USER_INACTIVITY_DAYS', '90'))

# Whether to send email notifications before deactivation (future feature)
USER_INACTIVITY_EMAIL_ENABLED = os.environ.get('USER_INACTIVITY_EMAIL_ENABLED', 'false').lower() == 'true'

# Days before deactivation to send warning email (future feature)
USER_INACTIVITY_WARNING_DAYS = int(os.environ.get('USER_INACTIVITY_WARNING_DAYS', '7'))
```

## Usage

### Running the Management Command

#### Basic Usage (uses default 90 days from settings)
```bash
python manage.py deactivate_inactive_users
```

#### Custom Inactivity Period
```bash
# Deactivate users inactive for 60 days
python manage.py deactivate_inactive_users --days 60

# Deactivate users inactive for 180 days (6 months)
python manage.py deactivate_inactive_users --days 180
```

#### Dry Run Mode (test without making changes)
```bash
python manage.py deactivate_inactive_users --days 90 --dry-run
```

#### Exclude Users Who Never Logged In
```bash
# Only deactivate users who logged in before but haven't logged in recently
python manage.py deactivate_inactive_users --exclude-never-logged-in
```

### Automated Scheduling

To automatically deactivate inactive users on a regular schedule, set up a scheduled task:

#### Windows Task Scheduler

1. Open Task Scheduler
2. Create a new task:
   - **Name:** Deactivate Inactive Users
   - **Trigger:** Daily at 2:00 AM (or preferred time)
   - **Action:** Start a program
     - **Program:** `python.exe` or path to your Python environment
     - **Arguments:** `manage.py deactivate_inactive_users`
     - **Start in:** Path to your `grc_backend` directory

Example command line:
```cmd
cd C:\Users\louky\OneDrive - Vardaan Cyber Security Pvt Ltd\Desktop\GRC_TPRM\grc_backend
python manage.py deactivate_inactive_users
```

#### Linux/Mac Cron Job

Add to crontab (`crontab -e`):

```bash
# Run daily at 2:00 AM
0 2 * * * cd /path/to/grc_backend && python manage.py deactivate_inactive_users >> /var/log/user_deactivation.log 2>&1
```

#### Django-Celery (for existing Celery setup)

If you have Celery configured, you can create a periodic task:

```python
# In your celery.py or tasks.py
from celery import shared_task
from django.core.management import call_command

@shared_task
def deactivate_inactive_users_task():
    call_command('deactivate_inactive_users')

# In celery beat schedule
from celery.schedules import crontab

app.conf.beat_schedule = {
    'deactivate-inactive-users': {
        'task': 'your_app.tasks.deactivate_inactive_users_task',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

## Database Migration

A migration file has been created to add the `last_login` field to the database:

**Location:** `grc/migrations/0002_add_last_login.py`

**To apply the migration:**

```bash
python manage.py migrate grc
```

**Note:** If you have a different migration naming scheme, you may need to rename the migration file or adjust the dependency in the migration file.

## Configuration via Environment Variables

You can configure the inactivity threshold using environment variables in your `.env` file:

```env
# Set inactivity period to 60 days instead of default 90
USER_INACTIVITY_DAYS=60

# Future feature: Enable warning emails
USER_INACTIVITY_EMAIL_ENABLED=true
USER_INACTIVITY_WARNING_DAYS=7
```

## Logging and Audit Trail

All user deactivations are logged to the `GRCLog` table with:

- **Module:** User Management
- **ActionType:** USER_DEACTIVATED
- **Description:** Details about the deactivation
- **Additional Info:**
  - Reason for deactivation
  - Inactivity days threshold
  - Last login date
  - User email
  - Deactivation type (automatic)

Example log entry:
```json
{
  "Module": "User Management",
  "ActionType": "USER_DEACTIVATED",
  "Description": "User john.doe (ID: 123) automatically deactivated due to inactivity",
  "UserId": "123",
  "UserName": "john.doe",
  "LogLevel": "INFO",
  "IPAddress": "system",
  "AdditionalInfo": {
    "reason": "Last login: 2024-09-01 (120 days ago)",
    "inactivity_days_threshold": 90,
    "deactivation_type": "automatic",
    "last_login": "2024-09-01T10:30:00",
    "email": "john.doe@example.com"
  }
}
```

## Impact on Users

### When a User is Deactivated

1. Their `IsActive` status changes from 'Y' to 'N'
2. They cannot log in until reactivated by an administrator
3. All login attempts will be rejected with "Account is inactive" message

### Reactivating a User

An administrator can reactivate a user by:

1. **Database Update:**
   ```sql
   UPDATE users SET IsActive='Y' WHERE UserId=123;
   ```

2. **Django Admin Panel** (if enabled)

3. **User Management Interface** (if available in your application)

**Note:** When a deactivated user logs in successfully after being reactivated, their `last_login` will be updated and they will remain active.

## Security Considerations

1. **Least Privilege:** Inactive accounts are potential security risks. Auto-deactivation reduces the attack surface.
2. **Audit Trail:** All deactivations are logged for compliance and security audits.
3. **Configurable:** Organizations can set their own inactivity thresholds based on security policies.
4. **Reversible:** Deactivation is non-destructive; users can be reactivated without data loss.

## Testing

### Test the Implementation

1. **Check existing users' last_login status:**
   ```bash
   python manage.py shell
   ```
   ```python
   from grc.models import Users
   from django.utils import timezone
   
   # Check users with no last_login
   users_no_login = Users.objects.filter(last_login__isnull=True)
   print(f"Users who never logged in: {users_no_login.count()}")
   
   # Check users with old logins
   cutoff = timezone.now() - timezone.timedelta(days=90)
   old_users = Users.objects.filter(last_login__lt=cutoff, IsActive='Y')
   print(f"Users inactive for 90+ days: {old_users.count()}")
   ```

2. **Run a dry-run to see what would be deactivated:**
   ```bash
   python manage.py deactivate_inactive_users --days 90 --dry-run
   ```

3. **Test with a short inactivity period on a test user:**
   ```bash
   # Deactivate users inactive for 1 day (for testing only)
   python manage.py deactivate_inactive_users --days 1 --dry-run
   ```

4. **Verify logging:**
   ```python
   from grc.models import GRCLog
   
   # Check deactivation logs
   logs = GRCLog.objects.filter(ActionType='USER_DEACTIVATED').order_by('-Timestamp')
   for log in logs[:10]:
       print(f"{log.Timestamp}: {log.UserName} - {log.Description}")
   ```

## Future Enhancements

Potential improvements for the system:

1. **Email Notifications:**
   - Send warning emails to users X days before deactivation
   - Send notification email when a user is deactivated
   - Include reactivation instructions

2. **Grace Period:**
   - Allow users to extend their activity period by clicking a link in the warning email

3. **Exemptions:**
   - Exclude certain roles (e.g., system administrators) from auto-deactivation
   - Whitelist specific users

4. **Dashboard:**
   - Admin dashboard showing inactivity statistics
   - List of users approaching inactivity threshold

5. **Reports:**
   - Generate monthly reports on deactivated users
   - Export deactivation audit logs

## Troubleshooting

### Users not being deactivated

1. Check that the migration has been applied: `python manage.py showmigrations grc`
2. Verify the configuration: Check `USER_INACTIVITY_DAYS` setting
3. Run with `--dry-run` to see what would be deactivated
4. Check the logs for any errors

### Last login not updating

1. Verify the `last_login` field exists in the database
2. Check that users are logging in successfully
3. Look for errors in the Django logs during login
4. Verify the field is being saved: `user.save(update_fields=['last_login'])`

### Logs not being created

1. Verify a Framework exists in the database (required for GRCLog)
2. Check database permissions
3. Look for errors in the Django logs

## Technical Details

### Model Changes

**File:** `grc/models.py`

```python
class Users(models.Model):
    # ... existing fields ...
    last_login = models.DateTimeField(null=True, blank=True)  # Track last successful login
    # ... rest of model ...
```

### Login Updates

Both login functions now include:

```python
from django.utils import timezone

# Update last login time
fields_to_update = ['last_login']
user.last_login = timezone.now()

# Activate user if needed
if user.IsActive != 'Y':
    user.IsActive = 'Y'
    fields_to_update.append('IsActive')

user.save(update_fields=fields_to_update)
```

## Support

For issues or questions about the user inactivity feature:

1. Check the logs in `GRCLog` table
2. Run the management command with `--dry-run` flag
3. Review the Django logs for error messages
4. Contact your system administrator

---

**Last Updated:** December 25, 2025  
**Version:** 1.0  
**Author:** GRC System Team


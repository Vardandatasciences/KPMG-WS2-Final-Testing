# Generated manually to rename auto_publish field to auto_approve
# This migration handles the case where the column may have been manually renamed

from django.db import migrations, models


def rename_column_if_needed(apps, schema_editor):
    """Rename the column if it exists, otherwise assume it's already renamed"""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Check if auto_publish column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'rfps' 
            AND COLUMN_NAME = 'auto_publish'
        """)
        auto_publish_exists = cursor.fetchone()[0] > 0
        
        # Check if auto_approve column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'rfps' 
            AND COLUMN_NAME = 'auto_approve'
        """)
        auto_approve_exists = cursor.fetchone()[0] > 0
        
        if auto_publish_exists and not auto_approve_exists:
            # Rename the column from auto_publish to auto_approve
            cursor.execute("ALTER TABLE rfps CHANGE COLUMN auto_publish auto_approve BOOLEAN DEFAULT FALSE")
        elif not auto_publish_exists and auto_approve_exists:
            # Column already renamed, do nothing
            pass
        elif auto_publish_exists and auto_approve_exists:
            # Both exist - drop auto_publish (shouldn't happen but handle it)
            cursor.execute("ALTER TABLE rfps DROP COLUMN auto_publish")


def reverse_rename(apps, schema_editor):
    """Reverse the rename operation"""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Check if auto_approve column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'rfps' 
            AND COLUMN_NAME = 'auto_approve'
        """)
        auto_approve_exists = cursor.fetchone()[0] > 0
        
        # Check if auto_publish column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'rfps' 
            AND COLUMN_NAME = 'auto_publish'
        """)
        auto_publish_exists = cursor.fetchone()[0] > 0
        
        if auto_approve_exists and not auto_publish_exists:
            # Rename back to auto_publish
            cursor.execute("ALTER TABLE rfps CHANGE COLUMN auto_approve auto_publish BOOLEAN DEFAULT FALSE")


class Migration(migrations.Migration):

    dependencies = [
        ('rfp', '0022_create_award_notification_model'),
    ]

    operations = [
        migrations.RunPython(
            rename_column_if_needed,
            reverse_rename,
        ),
        migrations.RenameField(
            model_name='rfp',
            old_name='auto_publish',
            new_name='auto_approve',
        ),
    ]


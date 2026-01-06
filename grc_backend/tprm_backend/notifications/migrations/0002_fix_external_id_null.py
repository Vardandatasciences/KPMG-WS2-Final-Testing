# Generated manually to fix external_id NULL constraint issue

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # MySQL syntax to alter the column to allow NULL
                "ALTER TABLE notifications MODIFY COLUMN external_id VARCHAR(255) NULL DEFAULT NULL;",
            ],
            reverse_sql=[
                # Reverse migration (though we won't use this)
                "ALTER TABLE notifications MODIFY COLUMN external_id VARCHAR(255) NOT NULL;",
            ],
        ),
    ]


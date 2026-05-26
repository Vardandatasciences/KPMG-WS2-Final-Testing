# Adds TenantId FK column to the entities table.
# The column was missing because the Entity model was created before
# Django's migration tracker was initialised, so 0007's AddField was
# recorded as applied but never actually executed against the DB.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0007_add_multitenancy_enhancement'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_column='TenantId',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='entities',
                to='grc.tenant',
            ),
        ),
    ]

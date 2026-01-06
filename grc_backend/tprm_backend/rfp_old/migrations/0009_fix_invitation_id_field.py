# Generated manually to fix invitation_id field only

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rfp', '0008_change_approval_workflow_id_to_char'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rfpunmatchedvendor',
            name='invitation_id',
            field=models.BigIntegerField(blank=True, null=True, default=None),
        ),
    ]

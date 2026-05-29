# Audit review escalation timestamp (manager queue)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0008_audit_recurrence_scope'),
    ]

    operations = [
        migrations.AddField(
            model_name='audit',
            name='ReviewEscalatedAt',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='When review backlog was escalated to Audit Manager',
            ),
        ),
    ]

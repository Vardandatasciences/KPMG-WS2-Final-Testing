# Generated for policy self-healing reminders

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0005_remove_audit_audits_tenant_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='policy',
            name='ReviewReminderFrequencyDays',
            field=models.IntegerField(default=30),
        ),
        migrations.CreateModel(
            name='PolicyReviewReminderSent',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('reminder_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'policy',
                    models.ForeignKey(
                        db_column='PolicyId',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='review_reminders_sent',
                        to='grc.policy',
                    ),
                ),
            ],
            options={
                'db_table': 'policy_review_reminder_sent',
                'unique_together': {('policy', 'reminder_date')},
            },
        ),
    ]

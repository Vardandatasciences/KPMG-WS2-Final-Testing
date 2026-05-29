"""
Generated manually: add PolicyReminderRule and PolicyReminderSchedule models.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('grc', '0009_audit_review_escalation'),
    ]

    operations = [
        migrations.CreateModel(
            name='PolicyReminderRule',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('start_value', models.PositiveIntegerField(default=1)),
                ('start_unit', models.CharField(choices=[('year', 'Year'), ('months', 'Months'), ('weeks', 'Weeks'), ('days', 'Days'), ('hours', 'Hours')], default='months', max_length=16)),
                ('frequency_unit', models.CharField(choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('half_yearly', 'Half-Yearly'), ('weekly', 'Weekly'), ('daily', 'Daily'), ('hourly', 'Hourly')], default='monthly', max_length=16)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('policy', models.ForeignKey(db_column='PolicyId', on_delete=django.db.models.deletion.CASCADE, related_name='reminder_rules', to='grc.policy')),
            ],
            options={
                'db_table': 'policy_reminder_rule',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='PolicyReminderSchedule',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('schedule_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('scheduled_at', models.DateTimeField()),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('sent', 'Sent'), ('cancelled', 'Cancelled')], default='scheduled', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('policy', models.ForeignKey(db_column='PolicyId', on_delete=django.db.models.deletion.CASCADE, related_name='reminder_schedules', to='grc.policy')),
                ('reminder_rule', models.ForeignKey(blank=True, db_column='rule_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='grc.policyreminderrule')),
            ],
            options={
                'db_table': 'policy_reminder_schedule',
                'indexes': [models.Index(fields=['policy', 'status'], name='policy_remi_policy_i_7c3e7e_idx'), models.Index(fields=['scheduled_at', 'status'], name='policy_remi_schedul_9c8b4e_idx')],
            },
        ),
    ]

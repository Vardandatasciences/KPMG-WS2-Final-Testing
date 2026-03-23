# Generated migration for ScreeningSchedule

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('vendor_core', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScreeningSchedule',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('tenant_id', models.CharField(blank=True, max_length=100, null=True)),
                ('frequency', models.CharField(
                    choices=[
                        ('does_not_repeat', 'One-time'),
                        ('daily', 'Daily'),
                        ('weekdays', 'Weekdays (Mon–Fri)'),
                        ('weekly', 'Weekly'),
                        ('monthly', 'Monthly'),
                        ('quarterly', 'Quarterly'),
                        ('yearly', 'Yearly'),
                    ],
                    default='daily',
                    max_length=32,
                )),
                ('cron_expression', models.CharField(blank=True, max_length=128, null=True)),
                ('scheduled_at', models.DateTimeField(
                    blank=True,
                    help_text='One-time run at this datetime',
                    null=True,
                )),
                ('next_run_at', models.DateTimeField(blank=True, null=True)),
                ('start_date', models.DateField(
                    blank=True,
                    help_text='Earliest date to start running',
                    null=True,
                )),
                ('is_active', models.BooleanField(default=True)),
                ('status', models.CharField(
                    choices=[
                        ('active', 'Active'),
                        ('paused', 'Paused'),
                        ('completed', 'Completed'),
                    ],
                    default='active',
                    max_length=16,
                )),
                ('last_run_at', models.DateTimeField(blank=True, null=True)),
                ('last_run_status', models.CharField(blank=True, max_length=32, null=True)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_by_id', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('temp_vendor', models.ForeignKey(
                    db_column='temp_vendor_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='screening_schedules',
                    to='vendor_core.tempvendor',
                )),
            ],
            options={
                'db_table': 'screening_schedules',
                'ordering': ['next_run_at'],
            },
        ),
    ]

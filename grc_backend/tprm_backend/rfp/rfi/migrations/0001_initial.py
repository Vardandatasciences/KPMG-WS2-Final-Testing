# Initial migration for RFI app.
#
# IMPORTANT:
# In many environments, the `rfis` / `rfi_evaluation_criteria` tables already exist.
# We still need the **migration state** to include the `RFI` model so later migrations
# (e.g. invitations/responses) can FK to it.
#
# This migration therefore adds **state-only** models (no DB operations).
#
# If your DB does NOT yet have `rfis`, you should create them via your existing
# migration strategy before applying invitation/response migrations.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='RFI',
                    fields=[
                        ('rfi_id', models.BigAutoField(primary_key=True, serialize=False)),
                    ],
                    options={
                        'db_table': 'rfis',
                    },
                ),
                migrations.CreateModel(
                    name='RFIEvaluationCriteria',
                    fields=[
                        ('criteria_id', models.BigAutoField(primary_key=True, serialize=False)),
                        ('rfi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_criteria', to='rfi.rfi', db_column='rfi_id')),
                    ],
                    options={
                        'db_table': 'rfi_evaluation_criteria',
                    },
                ),
            ],
        ),
    ]

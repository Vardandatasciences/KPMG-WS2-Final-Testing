# State-only models for existing RFI tables.
#
# These tables (`rfis`, `rfi_evaluation_criteria`) already exist in many environments,
# but earlier migrations did not include them in migration state. Later migrations
# (e.g. invitations/responses) need to FK to `RFI`, so we add state-only models here.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rfi', '0001_initial'),
    ]

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


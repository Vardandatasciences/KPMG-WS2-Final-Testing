# Policy self-heal escalation when creator left organization

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0006_policy_review_reminder_self_heal'),
    ]

    operations = [
        migrations.CreateModel(
            name='PolicySelfHealEscalation',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(
                    choices=[('pending_assignment', 'Pending assignment'), ('assigned', 'Assigned')],
                    default='pending_assignment',
                    max_length=32,
                )),
                ('original_created_by_name', models.CharField(blank=True, max_length=255, null=True)),
                ('assigned_user_id', models.IntegerField(blank=True, null=True)),
                ('assigned_by_user_id', models.IntegerField(blank=True, null=True)),
                ('assigned_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'policy',
                    models.ForeignKey(
                        db_column='PolicyId',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='self_heal_escalations',
                        to='grc.policy',
                    ),
                ),
            ],
            options={
                'db_table': 'policy_self_heal_escalation',
                'indexes': [models.Index(fields=['status', 'policy'], name='policy_self_heal_esc_status_idx')],
            },
        ),
    ]

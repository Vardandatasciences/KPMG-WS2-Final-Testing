# Generated manually for audit recurrence and assign scope

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0007_policy_self_heal_escalation'),
    ]

    operations = [
        migrations.AddField(
            model_name='audit',
            name='AssignScope',
            field=models.CharField(
                blank=True,
                choices=[('subpolicy', 'Sub-policy'), ('compliance', 'Compliance')],
                default='subpolicy',
                help_text='Whether assignment is at sub-policy or compliance level',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='audit',
            name='CompletionDays',
            field=models.IntegerField(
                blank=True,
                help_text='Days from period start to complete each audit round',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='audit',
            name='ParentAudit',
            field=models.ForeignKey(
                blank=True,
                db_column='ParentAuditId',
                help_text='Source audit for a recurring occurrence',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='recurrence_children',
                to='grc.audit',
            ),
        ),
        migrations.AddField(
            model_name='audit',
            name='OverdueEscalatedAt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='audit',
            name='IsRecurrenceRoot',
            field=models.BooleanField(
                default=False,
                help_text='True on the first audit in a recurring series',
            ),
        ),
    ]

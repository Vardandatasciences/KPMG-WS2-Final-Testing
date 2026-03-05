# Generated manually for QuestionnaireAssignmentSchedule

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vendor_questionnaire', '0002_questionnaireassignments_and_more'),
        ('vendor_core', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionnaireAssignmentSchedule',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, default='')),
                ('cron_expression', models.CharField(blank=True, max_length=128, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('scheduled_at', models.DateTimeField(blank=True, help_text='One-time run at this time', null=True)),
                ('next_run_at', models.DateTimeField(blank=True, help_text='Next run computed from cron or scheduled_at', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='vendor_core.users')),
                ('questionnaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignment_schedules', to='vendor_questionnaire.questionnaires')),
                ('temp_vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questionnaire_schedules', to='vendor_core.tempvendor')),
            ],
            options={
                'db_table': 'questionnaire_assignment_schedules',
                'ordering': ['next_run_at'],
            },
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0012_merge_leaves'),
    ]

    operations = [
        # Add threshold_limit column to Department (was in model but not in DB)
        migrations.AddField(
            model_name='department',
            name='threshold_limit',
            field=models.IntegerField(
                default=50,
                help_text='AI confidence threshold for risk identification (0-100)'
            ),
        ),
        # Make FrameworkId nullable on Department (was required, but save_department never passed it)
        migrations.AlterField(
            model_name='department',
            name='FrameworkId',
            field=models.ForeignKey(
                blank=True,
                db_column='FrameworkId',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='grc.framework',
            ),
        ),
    ]

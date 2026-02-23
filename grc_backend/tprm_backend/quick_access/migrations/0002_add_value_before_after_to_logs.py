# Generated migration for adding value_before and value_after fields to GRCLog model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quick_access', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='grclog',
            name='value_before',
            field=models.TextField(blank=True, help_text='Value before the change', null=True),
        ),
        migrations.AddField(
            model_name='grclog',
            name='value_after',
            field=models.TextField(blank=True, help_text='Value after the change', null=True),
        ),
    ]

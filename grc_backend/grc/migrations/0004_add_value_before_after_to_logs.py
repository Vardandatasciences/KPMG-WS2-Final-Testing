# Generated migration for adding ValueBefore and ValueAfter fields to GRCLog model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0003_add_multi_tenancy'),
    ]

    operations = [
        migrations.AddField(
            model_name='grclog',
            name='ValueBefore',
            field=models.TextField(blank=True, help_text='Value before the change', null=True),
        ),
        migrations.AddField(
            model_name='grclog',
            name='ValueAfter',
            field=models.TextField(blank=True, help_text='Value after the change', null=True),
        ),
    ]

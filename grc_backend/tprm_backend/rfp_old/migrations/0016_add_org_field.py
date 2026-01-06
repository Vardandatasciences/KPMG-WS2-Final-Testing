# Generated manually to fix missing org field in rfp_responses table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rfp', '0015_update_rfp_response_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='rfpresponse',
            name='org',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]

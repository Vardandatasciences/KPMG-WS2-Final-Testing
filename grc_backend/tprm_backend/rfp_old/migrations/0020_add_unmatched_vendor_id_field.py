# Generated manually for open submissions support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rfp', '0019_add_s3_files_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendorinvitation',
            name='unmatched_vendor_id',
            field=models.BigIntegerField(blank=True, null=True, help_text='For storing unmatched vendor IDs'),
        ),
    ]

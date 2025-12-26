# Generated migration for adding last_login field to Users model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0001_initial'),  # Replace with your actual last migration
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]


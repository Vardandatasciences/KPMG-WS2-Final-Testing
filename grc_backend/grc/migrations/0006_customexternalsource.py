from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0005_remove_audit_audits_tenant_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomExternalSource',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('url', models.URLField(max_length=2000)),
                ('feed_type', models.CharField(default='News', max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.IntegerField(blank=True, null=True)),
                ('tenant', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='custom_external_sources',
                    to='grc.tenant',
                )),
            ],
            options={
                'db_table': 'custom_external_sources',
                'ordering': ['-created_at'],
                'unique_together': {('tenant', 'url')},
            },
        ),
    ]

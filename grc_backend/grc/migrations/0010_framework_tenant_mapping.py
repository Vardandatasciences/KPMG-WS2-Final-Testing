from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0009_entity_add_tenant_fk'),
    ]

    operations = [
        migrations.CreateModel(
            name='FrameworkTenantMapping',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('framework', models.ForeignKey(
                    db_column='FrameworkId',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='framework_tenant_mappings',
                    to='grc.framework',
                )),
                ('tenant', models.ForeignKey(
                    db_column='TenantId',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='framework_tenant_mappings',
                    to='grc.tenant',
                )),
            ],
            options={
                'db_table': 'framework_tenant_mapping',
            },
        ),
        migrations.AlterUniqueTogether(
            name='frameworktenantmapping',
            unique_together={('framework', 'tenant')},
        ),
    ]

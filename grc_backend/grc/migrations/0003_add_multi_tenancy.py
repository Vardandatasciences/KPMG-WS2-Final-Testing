# Generated migration for Multi-Tenancy implementation

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0002_add_last_login'),
    ]

    operations = [
        # =========================================================================
        # STEP 1: Create Tenant table
        # =========================================================================
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('tenant_id', models.AutoField(db_column='TenantId', primary_key=True, serialize=False)),
                ('name', models.CharField(db_column='Name', help_text='Organization/Company Name', max_length=255)),
                ('subdomain', models.CharField(db_column='Subdomain', help_text="Unique subdomain for tenant (e.g., 'acmecorp' for acmecorp.grcplatform.com)", max_length=100, unique=True)),
                ('license_key', models.CharField(blank=True, db_column='LicenseKey', help_text='Unique license key for tenant', max_length=100, null=True, unique=True)),
                ('subscription_tier', models.CharField(choices=[('starter', 'Starter'), ('professional', 'Professional'), ('enterprise', 'Enterprise')], db_column='SubscriptionTier', default='starter', max_length=50)),
                ('status', models.CharField(choices=[('trial', 'Trial'), ('active', 'Active'), ('suspended', 'Suspended'), ('cancelled', 'Cancelled')], db_column='Status', default='trial', max_length=20)),
                ('max_users', models.IntegerField(db_column='MaxUsers', default=10, help_text='Maximum number of users allowed for this tenant')),
                ('storage_limit_gb', models.IntegerField(db_column='StorageLimitGB', default=10, help_text='Storage limit in GB')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='CreatedAt')),
                ('updated_at', models.DateTimeField(auto_now=True, db_column='UpdatedAt')),
                ('trial_ends_at', models.DateTimeField(blank=True, db_column='TrialEndsAt', null=True)),
                ('settings', models.JSONField(blank=True, db_column='Settings', default=dict, help_text='Tenant-specific configuration settings')),
                ('primary_contact_email', models.EmailField(blank=True, db_column='PrimaryContactEmail', max_length=254, null=True)),
                ('primary_contact_name', models.CharField(blank=True, db_column='PrimaryContactName', max_length=255, null=True)),
                ('primary_contact_phone', models.CharField(blank=True, db_column='PrimaryContactPhone', max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'Tenant',
                'verbose_name_plural': 'Tenants',
                'db_table': 'tenants',
            },
        ),
        
        # Add indexes for performance
        migrations.AddIndex(
            model_name='tenant',
            index=models.Index(fields=['subdomain'], name='tenants_subdomain_idx'),
        ),
        migrations.AddIndex(
            model_name='tenant',
            index=models.Index(fields=['license_key'], name='tenants_license_key_idx'),
        ),
        migrations.AddIndex(
            model_name='tenant',
            index=models.Index(fields=['status'], name='tenants_status_idx'),
        ),
        
        # =========================================================================
        # STEP 2: Add tenant_id to Users table
        # =========================================================================
        migrations.AddField(
            model_name='users',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this user belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='users',
                to='grc.tenant'
            ),
        ),
        
        # =========================================================================
        # STEP 3: Add tenant_id to all business models
        # =========================================================================
        
        # Frameworks and Policies
        migrations.AddField(
            model_name='framework',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this framework belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='frameworks',
                to='grc.tenant'
            ),
        ),
        migrations.AddField(
            model_name='policy',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this policy belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='policies',
                to='grc.tenant'
            ),
        ),
        migrations.AddField(
            model_name='subpolicy',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this subpolicy belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='subpolicies',
                to='grc.tenant'
            ),
        ),
        migrations.AddField(
            model_name='compliance',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this compliance belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='compliances',
                to='grc.tenant'
            ),
        ),
        
        # Audits
        migrations.AddField(
            model_name='audit',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this audit belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='audits',
                to='grc.tenant'
            ),
        ),
        migrations.AddField(
            model_name='auditfinding',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this audit finding belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='audit_findings',
                to='grc.tenant'
            ),
        ),
        
        # Incidents
        migrations.AddField(
            model_name='incident',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this incident belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='incidents',
                to='grc.tenant'
            ),
        ),
        
        # Risks
        migrations.AddField(
            model_name='risk',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this risk belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='risks',
                to='grc.tenant'
            ),
        ),
        migrations.AddField(
            model_name='riskinstance',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this risk instance belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='risk_instances',
                to='grc.tenant'
            ),
        ),
        
        # Notifications and Events
        migrations.AddField(
            model_name='notification',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this notification belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notifications',
                to='grc.tenant'
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this event belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='events',
                to='grc.tenant'
            ),
        ),
        
        # Departments
        migrations.AddField(
            model_name='department',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                db_column='TenantId',
                help_text='Tenant this department belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='departments',
                to='grc.tenant'
            ),
        ),
        
        # =========================================================================
        # STEP 4: Add indexes for tenant_id on frequently queried tables
        # =========================================================================
        migrations.AddIndex(
            model_name='users',
            index=models.Index(fields=['tenant'], name='users_tenant_idx'),
        ),
        migrations.AddIndex(
            model_name='framework',
            index=models.Index(fields=['tenant'], name='frameworks_tenant_idx'),
        ),
        migrations.AddIndex(
            model_name='policy',
            index=models.Index(fields=['tenant'], name='policies_tenant_idx'),
        ),
        migrations.AddIndex(
            model_name='compliance',
            index=models.Index(fields=['tenant'], name='compliances_tenant_idx'),
        ),
        migrations.AddIndex(
            model_name='audit',
            index=models.Index(fields=['tenant'], name='audits_tenant_idx'),
        ),
        migrations.AddIndex(
            model_name='incident',
            index=models.Index(fields=['tenant'], name='incidents_tenant_idx'),
        ),
        migrations.AddIndex(
            model_name='risk',
            index=models.Index(fields=['tenant'], name='risks_tenant_idx'),
        ),
    ]


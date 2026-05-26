# Phase 1 Multi-Tenancy Enhancement Migration
# Adds: Entity.tenant FK, RBAC.tenant FK, Tenant.status expansion,
# and 8 new models: TenantBusinessUnit, TenantUserMapping, UserEntityMapping,
# TenantModule, TenantSecuritySettings, TenantBranding, TenantAuditLog, SupportAccessRequest

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0006_customexternalsource'),
    ]

    operations = [

        # =========================================================================
        # 1.1a  Expand Tenant.status field (max_length 20 → 30, new choices)
        # =========================================================================
        migrations.AlterField(
            model_name='tenant',
            name='status',
            field=models.CharField(
                choices=[
                    ('trial', 'Trial'),
                    ('draft', 'Draft'),
                    ('onboarding', 'Onboarding'),
                    ('configuration_pending', 'Configuration Pending'),
                    ('security_setup_pending', 'Security Setup Pending'),
                    ('active', 'Active'),
                    ('suspended', 'Suspended'),
                    ('inactive', 'Inactive'),
                    ('archived', 'Archived'),
                    ('cancelled', 'Cancelled'),
                ],
                db_column='Status',
                default='trial',
                max_length=30,
            ),
        ),

        # =========================================================================
        # 1.1b  Add tenant FK to Entity (entities table)
        # =========================================================================
        migrations.AddField(
            model_name='entity',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_column='TenantId',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='entities',
                to='grc.tenant',
            ),
        ),

        # =========================================================================
        # 1.1c  Add tenant FK to RBAC
        # =========================================================================
        migrations.AddField(
            model_name='rbac',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_column='TenantId',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='rbac_records',
                to='grc.tenant',
            ),
        ),

        # =========================================================================
        # 1.2  New Model: TenantBusinessUnit
        # =========================================================================
        migrations.CreateModel(
            name='TenantBusinessUnit',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('status', models.CharField(default='active', max_length=20)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(
                    db_column='TenantId',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='grc.tenant',
                )),
                ('entity', models.ForeignKey(
                    db_column='EntityId',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='grc.entity',
                )),
                ('head', models.ForeignKey(
                    blank=True,
                    null=True,
                    db_column='HeadUserId',
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='grc.users',
                )),
                ('parent_bu', models.ForeignKey(
                    blank=True,
                    null=True,
                    db_column='ParentBUId',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='grc.tenantbusinessunit',
                )),
            ],
            options={
                'verbose_name': 'Business Unit (Tenant)',
                'verbose_name_plural': 'Business Units (Tenant)',
                'db_table': 'business_units',
            },
        ),

        # =========================================================================
        # 1.2  New Model: TenantUserMapping
        # =========================================================================
        migrations.CreateModel(
            name='TenantUserMapping',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('role', models.CharField(max_length=100)),
                ('is_primary', models.BooleanField(default=False)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default='active', max_length=20)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(
                    db_column='TenantId',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='grc.tenant',
                )),
                ('user', models.ForeignKey(
                    db_column='UserId',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='grc.users',
                )),
                ('assigned_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    db_column='AssignedById',
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='tenant_assignments',
                    to='grc.users',
                )),
            ],
            options={
                'verbose_name': 'Tenant User Mapping',
                'verbose_name_plural': 'Tenant User Mappings',
                'db_table': 'tenant_user_mapping',
                'unique_together': {('tenant', 'user')},
            },
        ),

        # =========================================================================
        # 1.2  New Model: UserEntityMapping
        # =========================================================================
        migrations.CreateModel(
            name='UserEntityMapping',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('role', models.CharField(max_length=100)),
                ('access_level', models.CharField(
                    choices=[('read', 'Read Only'), ('write', 'Read Write'), ('admin', 'Admin')],
                    default='read',
                    max_length=20,
                )),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default='active', max_length=20)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    db_column='UserId',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='grc.users',
                )),
                ('entity', models.ForeignKey(
                    db_column='EntityId',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='grc.entity',
                )),
                ('tenant', models.ForeignKey(
                    db_column='TenantId',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='grc.tenant',
                )),
                ('assigned_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    db_column='AssignedById',
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='entity_assignments',
                    to='grc.users',
                )),
            ],
            options={
                'verbose_name': 'User Entity Mapping',
                'verbose_name_plural': 'User Entity Mappings',
                'db_table': 'user_entity_mapping',
                'unique_together': {('user', 'entity')},
            },
        ),

        # =========================================================================
        # 1.2  New Model: TenantModule
        # =========================================================================
        migrations.CreateModel(
            name='TenantModule',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('module_code', models.CharField(
                    choices=[
                        ('framework', 'Framework'),
                        ('policy', 'Policy'),
                        ('compliance', 'Compliance'),
                        ('audit', 'Audit'),
                        ('risk', 'Risk'),
                        ('incident', 'Incident'),
                        ('event', 'Event'),
                    ],
                    max_length=50,
                )),
                ('is_enabled', models.BooleanField(default=True)),
                ('license_tier', models.CharField(default='basic', max_length=50)),
                ('effective_from', models.DateField(blank=True, null=True)),
                ('effective_to', models.DateField(blank=True, null=True)),
                ('user_limit', models.IntegerField(blank=True, null=True)),
                ('storage_limit_gb', models.IntegerField(blank=True, null=True)),
                ('api_limit', models.IntegerField(blank=True, null=True)),
                ('ai_limit', models.IntegerField(blank=True, null=True)),
                ('configured_at', models.DateTimeField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(
                    db_column='TenantId',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='grc.tenant',
                )),
                ('configured_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    db_column='ConfiguredById',
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='grc.users',
                )),
            ],
            options={
                'verbose_name': 'Tenant Module',
                'verbose_name_plural': 'Tenant Modules',
                'db_table': 'tenant_modules',
                'unique_together': {('tenant', 'module_code')},
            },
        ),

        # =========================================================================
        # 1.2  New Model: TenantSecuritySettings
        # =========================================================================
        migrations.CreateModel(
            name='TenantSecuritySettings',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('mfa_required', models.BooleanField(default=False)),
                ('mfa_methods', models.JSONField(default=list, help_text="['email', 'totp']")),
                ('sso_enabled', models.BooleanField(default=False)),
                ('sso_provider', models.CharField(blank=True, max_length=50, null=True)),
                ('sso_config', models.JSONField(default=dict)),
                ('allowed_email_domains', models.JSONField(
                    default=list,
                    help_text="['company.com', 'subsidiary.com']",
                )),
                ('ip_restriction_enabled', models.BooleanField(default=False)),
                ('allowed_ip_ranges', models.JSONField(
                    default=list,
                    help_text="['192.168.1.0/24', '10.0.0.0/8']",
                )),
                ('session_timeout_minutes', models.IntegerField(default=30)),
                ('password_expiry_days', models.IntegerField(default=90)),
                ('export_allowed', models.BooleanField(default=True)),
                ('export_requires_approval', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.OneToOneField(
                    db_column='TenantId',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='security_settings',
                    to='grc.tenant',
                )),
                ('updated_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    db_column='UpdatedById',
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='grc.users',
                )),
            ],
            options={
                'verbose_name': 'Tenant Security Settings',
                'verbose_name_plural': 'Tenant Security Settings',
                'db_table': 'tenant_security_settings',
            },
        ),

        # =========================================================================
        # 1.2  New Model: TenantBranding
        # =========================================================================
        migrations.CreateModel(
            name='TenantBranding',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('logo_url', models.CharField(blank=True, max_length=500, null=True)),
                ('favicon_url', models.CharField(blank=True, max_length=500, null=True)),
                ('primary_color', models.CharField(default='#1976D2', max_length=7)),
                ('secondary_color', models.CharField(default='#424242', max_length=7)),
                ('accent_color', models.CharField(default='#82B1FF', max_length=7)),
                ('custom_css', models.TextField(blank=True, null=True)),
                ('login_page_custom_html', models.TextField(blank=True, null=True)),
                ('email_template_logo', models.CharField(blank=True, max_length=500, null=True)),
                ('email_footer_text', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.OneToOneField(
                    db_column='TenantId',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='branding',
                    to='grc.tenant',
                )),
                ('updated_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    db_column='UpdatedById',
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='grc.users',
                )),
            ],
            options={
                'verbose_name': 'Tenant Branding',
                'verbose_name_plural': 'Tenant Branding',
                'db_table': 'tenant_branding',
            },
        ),

        # =========================================================================
        # 1.2  New Model: TenantAuditLog
        # =========================================================================
        migrations.CreateModel(
            name='TenantAuditLog',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('action_type', models.CharField(
                    choices=[
                        ('CREATE', 'Create'),
                        ('UPDATE', 'Update'),
                        ('DELETE', 'Delete'),
                        ('ACTIVATE', 'Activate'),
                        ('SUSPEND', 'Suspend'),
                        ('ARCHIVE', 'Archive'),
                        ('MAP_USER', 'Map User'),
                        ('UNMAP_USER', 'Unmap User'),
                        ('ENABLE_MODULE', 'Enable Module'),
                        ('DISABLE_MODULE', 'Disable Module'),
                    ],
                    max_length=50,
                )),
                ('entity_type', models.CharField(
                    choices=[
                        ('tenant', 'Tenant'),
                        ('entity', 'Entity'),
                        ('business_unit', 'Business Unit'),
                        ('department', 'Department'),
                        ('user', 'User'),
                        ('module', 'Module'),
                        ('security', 'Security Settings'),
                        ('branding', 'Branding'),
                        ('support_access', 'Support Access'),
                    ],
                    max_length=50,
                )),
                ('entity_id', models.IntegerField()),
                ('entity_name', models.CharField(max_length=255)),
                ('old_value', models.JSONField(blank=True, null=True)),
                ('new_value', models.JSONField(blank=True, null=True)),
                ('performed_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.CharField(blank=True, max_length=45, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('tenant', models.ForeignKey(
                    db_column='TenantId',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='grc.tenant',
                )),
                ('performed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    db_column='PerformedById',
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='grc.users',
                )),
            ],
            options={
                'verbose_name': 'Tenant Audit Log',
                'verbose_name_plural': 'Tenant Audit Logs',
                'db_table': 'tenant_audit_log',
                'ordering': ['-performed_at'],
            },
        ),

        # =========================================================================
        # 1.2  New Model: SupportAccessRequest
        # =========================================================================
        migrations.CreateModel(
            name='SupportAccessRequest',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('request_reason', models.TextField()),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('valid_from', models.DateTimeField(blank=True, null=True)),
                ('valid_to', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('approved', 'Approved'),
                        ('revoked', 'Revoked'),
                        ('expired', 'Expired'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('access_token', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(
                    db_column='TenantId',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='grc.tenant',
                )),
                ('support_user', models.ForeignKey(
                    db_column='SupportUserId',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='support_access_requests',
                    to='grc.users',
                )),
                ('approved_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    db_column='ApprovedById',
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approved_support_access',
                    to='grc.users',
                )),
            ],
            options={
                'verbose_name': 'Support Access Request',
                'verbose_name_plural': 'Support Access Requests',
                'db_table': 'support_access_request',
            },
        ),
    ]

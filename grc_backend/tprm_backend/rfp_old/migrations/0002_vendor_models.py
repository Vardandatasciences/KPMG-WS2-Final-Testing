from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('rfp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('vendor_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('vendor_code', models.CharField(blank=True, max_length=50, null=True)),
                ('company_name', models.CharField(max_length=255)),
                ('legal_name', models.CharField(blank=True, max_length=255, null=True)),
                ('business_type', models.CharField(blank=True, max_length=100, null=True)),
                ('incorporation_date', models.DateField(blank=True, null=True)),
                ('tax_id', models.CharField(blank=True, max_length=50, null=True)),
                ('duns_number', models.CharField(blank=True, max_length=20, null=True)),
                ('website', models.CharField(blank=True, max_length=255, null=True)),
                ('industry_sector', models.CharField(blank=True, max_length=100, null=True)),
                ('annual_revenue', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('employee_count', models.IntegerField(blank=True, null=True)),
                ('headquarters_country', models.CharField(blank=True, max_length=100, null=True)),
                ('headquarters_address', models.TextField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('vendor_category_id', models.BigIntegerField(blank=True, null=True)),
                ('risk_level', models.CharField(blank=True, choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')], max_length=10, null=True)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('SUBMITTED', 'Submitted'), ('IN_REVIEW', 'In Review'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('SUSPENDED', 'Suspended'), ('TERMINATED', 'Terminated')], default='DRAFT', max_length=20)),
                ('lifecycle_stage', models.CharField(blank=True, max_length=50, null=True)),
                ('onboarding_date', models.DateField(blank=True, null=True)),
                ('last_assessment_date', models.DateField(blank=True, null=True)),
                ('next_assessment_date', models.DateField(blank=True, null=True)),
                ('is_critical_vendor', models.BooleanField(default=False)),
                ('has_data_access', models.BooleanField(default=False)),
                ('has_system_access', models.BooleanField(default=False)),
                ('created_by', models.IntegerField(blank=True, null=True)),
                ('updated_by', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('match_score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('rating', models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('experience_years', models.IntegerField(blank=True, null=True)),
                ('email', models.EmailField(blank=True, max_length=255, null=True)),
                ('phone', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'db_table': 'vendors',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['vendor_code'], name='vendors_vendor__1e7ca5_idx'), models.Index(fields=['company_name'], name='vendors_company_2c4f5e_idx'), models.Index(fields=['status'], name='vendors_status_e9c337_idx')],
            },
        ),
        migrations.CreateModel(
            name='RFPUnmatchedVendor',
            fields=[
                ('unmatched_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('invitation_id', models.BigIntegerField(blank=True, null=True)),
                ('vendor_name', models.CharField(max_length=255)),
                ('vendor_email', models.CharField(max_length=255)),
                ('vendor_phone', models.CharField(blank=True, max_length=50, null=True)),
                ('company_name', models.CharField(max_length=255)),
                ('submission_data', models.JSONField(blank=True, null=True)),
                ('matched_vendor_id', models.BigIntegerField(blank=True, null=True)),
                ('matching_status', models.CharField(choices=[('unmatched', 'Unmatched'), ('pending_review', 'Pending Review'), ('matched', 'Matched'), ('rejected', 'Rejected')], default='unmatched', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('matched_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'rfp_unmatched_vendors',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['vendor_email'], name='rfp_unmatch_vendor__d9f20f_idx'), models.Index(fields=['matching_status'], name='rfp_unmatch_matchin_4c9a0e_idx')],
            },
        ),
        migrations.CreateModel(
            name='VendorCertification',
            fields=[
                ('certification_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('certification_name', models.CharField(max_length=100)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certifications', to='rfp.vendor')),
            ],
            options={
                'db_table': 'vendor_certifications',
                'unique_together': {('vendor', 'certification_name')},
            },
        ),
        migrations.CreateModel(
            name='VendorCapability',
            fields=[
                ('capability_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('capability_name', models.CharField(max_length=100)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='capabilities', to='rfp.vendor')),
            ],
            options={
                'db_table': 'vendor_capabilities',
                'unique_together': {('vendor', 'capability_name')},
            },
        ),
        migrations.CreateModel(
            name='RFPVendorSelection',
            fields=[
                ('selection_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('match_score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('selection_date', models.DateTimeField(auto_now_add=True)),
                ('selected_by', models.IntegerField()),
                ('invitation_sent', models.BooleanField(default=False)),
                ('invitation_url', models.CharField(blank=True, max_length=255, null=True)),
                ('invitation_sent_date', models.DateTimeField(blank=True, null=True)),
                ('rfp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='selected_vendors', to='rfp.rfp')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rfp_selections', to='rfp.vendor')),
            ],
            options={
                'db_table': 'rfp_vendor_selections',
                'unique_together': {('rfp', 'vendor')},
                'indexes': [models.Index(fields=['rfp'], name='rfp_vendor__rfp_id_c1c8f4_idx'), models.Index(fields=['vendor'], name='rfp_vendor__vendor__6a4a4e_idx')],
            },
        ),
    ]

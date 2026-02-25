# Generated manually for RFI vendor invitations and responses

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rfi', '0002_state_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='RFIVendorInvitation',
            fields=[
                ('invitation_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('vendor_id', models.BigIntegerField(blank=True, null=True)),
                ('vendor_email', models.CharField(blank=True, max_length=255, null=True)),
                ('vendor_name', models.CharField(blank=True, max_length=255, null=True)),
                ('vendor_phone', models.CharField(blank=True, max_length=50, null=True)),
                ('company_name', models.CharField(blank=True, max_length=255, null=True)),
                ('invited_date', models.DateTimeField(auto_now_add=True)),
                ('invitation_status', models.CharField(
                    choices=[
                        ('CREATED', 'Created'),
                        ('SENT', 'Sent'),
                        ('DELIVERED', 'Delivered'),
                        ('OPENED', 'Opened'),
                        ('CLICKED', 'Clicked'),
                        ('ACKNOWLEDGED', 'Acknowledged'),
                        ('DECLINED', 'Declined'),
                        ('SUBMITTED', 'Submitted'),
                        ('FAILED', 'Failed'),
                    ],
                    default='CREATED',
                    max_length=20
                )),
                ('acknowledged_date', models.DateTimeField(blank=True, null=True)),
                ('declined_reason', models.TextField(blank=True, null=True)),
                ('invitation_url', models.CharField(blank=True, max_length=500, null=True)),
                ('acknowledgment_url', models.CharField(blank=True, max_length=500, null=True)),
                ('submission_url', models.CharField(blank=True, max_length=500, null=True)),
                ('unique_token', models.CharField(blank=True, max_length=255, null=True)),
                ('is_matched_vendor', models.BooleanField(default=False)),
                ('submission_source', models.CharField(
                    choices=[('invited', 'Invited'), ('open', 'Open')],
                    default='invited',
                    max_length=10
                )),
                ('utm_parameters', models.JSONField(blank=True, null=True)),
                ('custom_message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rfi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='rfi.rfi', db_constraint=False)),
                ('tenant', models.ForeignKey(blank=True, db_column='TenantId', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rfi_vendor_invitations', to='core.tenant')),
            ],
            options={
                'db_table': 'rfi_vendor_invitations',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RFIResponse',
            fields=[
                ('response_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('vendor_id', models.BigIntegerField(blank=True, null=True)),
                ('invitation_id', models.BigIntegerField(blank=True, null=True)),
                ('submission_date', models.DateTimeField(blank=True, null=True)),
                ('response_documents', models.JSONField(blank=True, null=True)),
                ('document_urls', models.JSONField(blank=True, null=True)),
                ('proposed_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('technical_score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('commercial_score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('overall_score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('weighted_final_score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('evaluation_status', models.CharField(
                    choices=[
                        ('DRAFT', 'Draft'),
                        ('SUBMITTED', 'Submitted'),
                        ('UNDER_EVALUATION', 'Under Evaluation'),
                        ('SHORTLISTED', 'Shortlisted'),
                        ('REJECTED', 'Rejected'),
                        ('AWARDED', 'Awarded'),
                    ],
                    default='DRAFT',
                    max_length=20
                )),
                ('auto_rejected', models.BooleanField(default=False)),
                ('rejection_reason', models.TextField(blank=True, null=True)),
                ('submission_source', models.CharField(
                    choices=[('invited', 'Invited'), ('open', 'Open')],
                    default='invited',
                    max_length=10
                )),
                ('external_submission_data', models.JSONField(blank=True, null=True)),
                ('draft_data', models.JSONField(blank=True, null=True)),
                ('completion_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('last_saved_at', models.DateTimeField(blank=True, null=True)),
                ('submitted_by', models.CharField(blank=True, max_length=255, null=True)),
                ('evaluated_by', models.IntegerField(blank=True, null=True)),
                ('evaluation_date', models.DateTimeField(blank=True, null=True)),
                ('evaluation_comments', models.TextField(blank=True, null=True)),
                ('org', models.CharField(blank=True, max_length=255, null=True)),
                ('vendor_name', models.CharField(blank=True, max_length=255, null=True)),
                ('contact_email', models.CharField(blank=True, max_length=255, null=True)),
                ('contact_phone', models.CharField(blank=True, max_length=50, null=True)),
                ('proposal_data', models.JSONField(blank=True, null=True)),
                ('submission_status', models.CharField(default='DRAFT', max_length=20)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.CharField(blank=True, max_length=45, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rfi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='rfi.rfi', db_constraint=False)),
                ('tenant', models.ForeignKey(blank=True, db_column='TenantId', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rfi_responses', to='core.tenant')),
            ],
            options={
                'db_table': 'rfi_responses',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='rfivendorinvitation',
            index=models.Index(fields=['rfi'], name='rfi_vendor__rfi_id_3a7e3c_idx'),
        ),
        migrations.AddIndex(
            model_name='rfivendorinvitation',
            index=models.Index(fields=['unique_token'], name='rfi_vendor__unique__e0b26b_idx'),
        ),
        migrations.AddIndex(
            model_name='rfiresponse',
            index=models.Index(fields=['rfi'], name='rfi_respon_rfi_id_f3b802_idx'),
        ),
        migrations.AddIndex(
            model_name='rfiresponse',
            index=models.Index(fields=['invitation_id'], name='rfi_respon_invitat_8a2c4d_idx'),
        ),
    ]

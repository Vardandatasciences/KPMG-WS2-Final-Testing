# Generated manually for RFPAwardNotification model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rfp', '0021_create_committee_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='RFPAwardNotification',
            fields=[
                ('notification_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('response_id', models.BigIntegerField(db_index=True)),
                ('notification_type', models.CharField(choices=[('winner', 'Winner'), ('participant_thanks', 'Participant Thanks')], max_length=20)),
                ('recipient_email', models.CharField(max_length=255)),
                ('notification_status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('acknowledged', 'Acknowledged'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('sent_date', models.DateTimeField(blank=True, null=True)),
                ('acknowledged_date', models.DateTimeField(blank=True, null=True)),
                ('response_date', models.DateTimeField(blank=True, null=True)),
                ('accept_reject_token', models.CharField(blank=True, max_length=255, null=True)),
                ('award_message', models.TextField(blank=True, null=True)),
                ('next_steps', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'rfp_award_notifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='rfpawardnotification',
            index=models.Index(fields=['response_id'], name='rfp_award_n_response_4a1b2c_idx'),
        ),
        migrations.AddIndex(
            model_name='rfpawardnotification',
            index=models.Index(fields=['notification_type'], name='rfp_award_n_notifica_5d6e7f_idx'),
        ),
        migrations.AddIndex(
            model_name='rfpawardnotification',
            index=models.Index(fields=['notification_status'], name='rfp_award_n_notifica_8g9h0i_idx'),
        ),
        migrations.AddIndex(
            model_name='rfpawardnotification',
            index=models.Index(fields=['recipient_email'], name='rfp_award_n_recipie_j1k2l3_idx'),
        ),
        migrations.AddIndex(
            model_name='rfpawardnotification',
            index=models.Index(fields=['accept_reject_token'], name='rfp_award_n_accept__m4n5o6_idx'),
        ),
    ]

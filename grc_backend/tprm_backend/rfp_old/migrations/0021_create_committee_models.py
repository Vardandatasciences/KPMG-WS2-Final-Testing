# Generated migration for RFP Committee and Final Evaluation models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rfp', '0020_add_unmatched_vendor_id_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='RFPCommittee',
            fields=[
                ('committee_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('rfp_id', models.BigIntegerField(db_index=True)),
                ('response_id', models.JSONField(blank=True, null=True)),
                ('member_id', models.IntegerField(db_index=True)),
                ('member_role', models.CharField(default='Committee Member', max_length=100)),
                ('is_chair', models.BooleanField(default=False)),
                ('added_date', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.IntegerField()),
                ('rfp_committeecol', models.CharField(blank=True, max_length=45, null=True)),
                ('response_ids', models.JSONField(blank=True, null=True)),
            ],
            options={
                'db_table': 'rfp_committee',
                'ordering': ['-added_date'],
            },
        ),
        migrations.CreateModel(
            name='RFPFinalEvaluation',
            fields=[
                ('final_eval_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('rfp_id', models.BigIntegerField(db_index=True)),
                ('response_id', models.BigIntegerField(db_index=True)),
                ('evaluator_id', models.IntegerField(db_index=True)),
                ('ranking_position', models.IntegerField()),
                ('ranking_score', models.DecimalField(decimal_places=2, max_digits=5)),
                ('evaluation_comments', models.TextField(blank=True, null=True)),
                ('evaluation_date', models.DateTimeField(auto_now_add=True)),
                ('consensus_weight', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
            ],
            options={
                'db_table': 'rfp_final_evaluation',
                'ordering': ['-evaluation_date'],
            },
        ),
        migrations.AddIndex(
            model_name='rfpcommittee',
            index=models.Index(fields=['rfp_id'], name='rfp_committee_rfp_id_idx'),
        ),
        migrations.AddIndex(
            model_name='rfpcommittee',
            index=models.Index(fields=['member_id'], name='rfp_committee_member_id_idx'),
        ),
        migrations.AddIndex(
            model_name='rfpcommittee',
            index=models.Index(fields=['is_chair'], name='rfp_committee_is_chair_idx'),
        ),
        migrations.AddIndex(
            model_name='rfpfinalevaluation',
            index=models.Index(fields=['rfp_id'], name='rfp_final_eval_rfp_id_idx'),
        ),
        migrations.AddIndex(
            model_name='rfpfinalevaluation',
            index=models.Index(fields=['response_id'], name='rfp_final_eval_response_id_idx'),
        ),
        migrations.AddIndex(
            model_name='rfpfinalevaluation',
            index=models.Index(fields=['evaluator_id'], name='rfp_final_eval_evaluator_id_idx'),
        ),
        migrations.AddIndex(
            model_name='rfpfinalevaluation',
            index=models.Index(fields=['ranking_position'], name='rfp_final_eval_ranking_pos_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='rfpfinalevaluation',
            unique_together={('rfp_id', 'response_id', 'evaluator_id')},
        ),
    ]

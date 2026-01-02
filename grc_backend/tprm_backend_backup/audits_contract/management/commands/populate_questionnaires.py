from django.core.management.base import BaseCommand
from tprm_backend.audits_contract.models import ContractStaticQuestionnaire


class Command(BaseCommand):
    help = 'Populate contract static questionnaires with sample data'

    def handle(self, *args, **options):
        # Sample questionnaires for different terms
        sample_questionnaires = [
            # Term ID 1 - Service Level Agreement
            {
                'term_id': '1',
                'question_text': 'Is the service provider meeting the agreed response time?',
                'question_type': 'boolean',
                'is_required': True,
                'scoring_weightings': 15.00
            },
            {
                'term_id': '1',
                'question_text': 'What is the average response time in hours?',
                'question_type': 'number',
                'is_required': True,
                'scoring_weightings': 10.00
            },
            {
                'term_id': '1',
                'question_text': 'Describe the service quality observed',
                'question_type': 'text',
                'is_required': True,
                'scoring_weightings': 20.00
            },
            
            # Term ID 2 - Data Security
            {
                'term_id': '2',
                'question_text': 'Is data encryption implemented according to contract requirements?',
                'question_type': 'boolean',
                'is_required': True,
                'scoring_weightings': 25.00
            },
            {
                'term_id': '2',
                'question_text': 'What type of encryption is being used?',
                'question_type': 'multiple_choice',
                'is_required': False,
                'scoring_weightings': 10.00
            },
            {
                'term_id': '2',
                'question_text': 'Describe the data security measures in place',
                'question_type': 'text',
                'is_required': True,
                'scoring_weightings': 15.00
            },
            
            # Term ID 3 - Performance Metrics
            {
                'term_id': '3',
                'question_text': 'Is the system uptime meeting the agreed percentage?',
                'question_type': 'boolean',
                'is_required': True,
                'scoring_weightings': 20.00
            },
            {
                'term_id': '3',
                'question_text': 'What is the actual uptime percentage?',
                'question_type': 'number',
                'is_required': True,
                'scoring_weightings': 15.00
            },
            {
                'term_id': '3',
                'question_text': 'Describe any performance issues encountered',
                'question_type': 'text',
                'is_required': False,
                'scoring_weightings': 10.00
            },
            
            # Term ID 4 - Compliance
            {
                'term_id': '4',
                'question_text': 'Are all compliance requirements being met?',
                'question_type': 'boolean',
                'is_required': True,
                'scoring_weightings': 30.00
            },
            {
                'term_id': '4',
                'question_text': 'Which compliance standards are being followed?',
                'question_type': 'multiple_choice',
                'is_required': True,
                'scoring_weightings': 20.00
            },
            {
                'term_id': '4',
                'question_text': 'Describe any compliance gaps or issues',
                'question_type': 'text',
                'is_required': False,
                'scoring_weightings': 15.00
            },
        ]

        # Clear existing questionnaires
        ContractStaticQuestionnaire.objects.all().delete()
        
        # Create sample questionnaires
        created_count = 0
        for q_data in sample_questionnaires:
            questionnaire, created = ContractStaticQuestionnaire.objects.get_or_create(
                term_id=q_data['term_id'],
                question_text=q_data['question_text'],
                defaults={
                    'question_type': q_data['question_type'],
                    'is_required': q_data['is_required'],
                    'scoring_weightings': q_data['scoring_weightings']
                }
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} questionnaires'
            )
        )

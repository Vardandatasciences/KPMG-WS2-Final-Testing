from django.core.management.base import BaseCommand
from tprm_backend.audits_contract.models import ContractStaticQuestionnaire


class Command(BaseCommand):
    help = 'Add sample questionnaires to the database'

    def handle(self, *args, **options):
        self.stdout.write('Adding sample questionnaires...')
        
        # Clear existing questionnaires
        ContractStaticQuestionnaire.objects.all().delete()
        
        # Create sample questionnaires
        sample_questions = [
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
        ]
        
        created_count = 0
        for q_data in sample_questions:
            questionnaire = ContractStaticQuestionnaire.objects.create(**q_data)
            created_count += 1
            self.stdout.write(f'Created: {questionnaire.question_text[:50]}... (Term ID: {questionnaire.term_id})')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} questionnaires'
            )
        )
        
        # Show total count
        total_count = ContractStaticQuestionnaire.objects.count()
        self.stdout.write(f'Total questionnaires in database: {total_count}')

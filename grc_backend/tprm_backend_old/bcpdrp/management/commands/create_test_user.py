"""
Management command to create a test user for login testing
"""
from django.core.management.base import BaseCommand
from tprm_backend.bcpdrp.models import Users


class Command(BaseCommand):
    help = 'Create a test user for login testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the test user'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the test user'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Email for the test user'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Admin',
            help='First name for the test user'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='User',
            help='Last name for the test user'
        )
        parser.add_argument(
            '--role',
            type=str,
            default='ADMIN',
            help='Role for the test user'
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        first_name = options['first_name']
        last_name = options['last_name']
        role = options['role']

        # Check if user already exists
        if Users.objects.filter(user_name=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User with username "{username}" already exists')
            )
            return

        # Create user
        user = Users.objects.create(
            user_name=username,
            password=password,  # In production, this should be hashed
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active='Y',
            department_id=1,
            consent_accepted='Y'
        )


        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created test user:\n'
                f'  Username: {username}\n'
                f'  Password: {password}\n'
                f'  Email: {email}\n'
                f'  Name: {first_name} {last_name}\n'
                f'  Role: {role}\n'
                f'  User ID: {user.user_id}'
            )
        )

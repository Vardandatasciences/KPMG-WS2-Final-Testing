from django.core.management.base import BaseCommand
from grc.models import Users
from django.utils import timezone

class Command(BaseCommand):
    help = 'Creates test users in the database'

    def handle(self, *args, **kwargs):
        # Create system user (UserId=1) if it doesn't exist
        system_user, created = Users.objects.get_or_create(
            UserName='System',
            defaults={
                'Password': 'system123',
                'Email': 'system@example.com',
                'CreatedAt': timezone.now(),
                'UpdatedAt': timezone.now()
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created system user'))
        else:
            self.stdout.write(self.style.SUCCESS('System user already exists'))

        # Create test users
        test_users = [
            {
                'UserName': 'admin',
                'Password': 'admin123',
                'Email': 'admin@example.com'
            },
            {
                'UserName': 'auditor',
                'Password': 'audit123',
                'Email': 'auditor@example.com'
            },
            {
                'UserName': 'risk',
                'Password': 'risk123',
                'Email': 'risk@example.com'
            },
            {
                'UserName': 'compliance',
                'Password': 'comp123',
                'Email': 'compliance@example.com'
            }
        ]

        for user_data in test_users:
            user, created = Users.objects.get_or_create(
                UserName=user_data['UserName'],
                defaults={
                    'Password': user_data['Password'],
                    'Email': user_data['Email'],
                    'CreatedAt': timezone.now(),
                    'UpdatedAt': timezone.now()
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created user: {user.UserName}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'User already exists: {user.UserName}')
                ) 
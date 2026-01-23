from django.core.management.base import BaseCommand
from grc.models import RBAC

class Command(BaseCommand):
    help = 'Enable risk_performance_analytics permission for all users'

    def handle(self, *args, **options):
        # Enable risk_performance_analytics for all users
        updated_count = RBAC.objects.update(risk_performance_analytics=True)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully enabled risk_performance_analytics for {updated_count} users')
        )
        
        # Show current status
        users_with_analytics = RBAC.objects.filter(risk_performance_analytics=True)
        self.stdout.write(f'Users with risk_performance_analytics permission: {users_with_analytics.count()}')
        
        for user in users_with_analytics:
            self.stdout.write(f'- {user.username} (ID: {user.user_id})')

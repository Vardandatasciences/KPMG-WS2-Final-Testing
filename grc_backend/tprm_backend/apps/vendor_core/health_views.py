"""
Health check views for system monitoring
"""

import time
from django.core.cache import cache
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from tprm_backend.database.vendor_sqlalchemy_manager import vendor_db_manager
from tprm_backend.config.celery import app as celery_app


class VendorHealthCheckView(APIView):
    """
    Overall system health check
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get overall system health status"""
        health_data = {
            'vendor_system_status': 'healthy',
            'vendor_timestamp': int(time.time()),
            'vendor_checks': {}
        }
        
        overall_healthy = True
        
        # Check database health
        try:
            db_health = vendor_db_manager.vendor_health_check()
            health_data['vendor_checks']['vendor_database'] = db_health
            if not db_health.get('database_connected', False):
                overall_healthy = False
        except Exception as e:
            health_data['vendor_checks']['vendor_database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_healthy = False
        
        # Check cache health
        try:
            cache_start = time.time()
            cache.set('vendor_health_check', 'test', 10)
            cache_value = cache.get('vendor_health_check')
            cache_time = (time.time() - cache_start) * 1000
            
            health_data['vendor_checks']['vendor_cache'] = {
                'status': 'healthy' if cache_value == 'test' else 'unhealthy',
                'response_time_ms': round(cache_time, 2)
            }
            
            if cache_value != 'test':
                overall_healthy = False
                
        except Exception as e:
            health_data['vendor_checks']['vendor_cache'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_healthy = False
        
        # Check Celery health
        try:
            inspector = celery_app.control.inspect()
            stats = inspector.stats()
            
            health_data['vendor_checks']['vendor_celery'] = {
                'status': 'healthy' if stats else 'unhealthy',
                'workers': len(stats) if stats else 0
            }
            
            if not stats:
                overall_healthy = False
                
        except Exception as e:
            health_data['vendor_checks']['vendor_celery'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_healthy = False
        
        # Set overall status
        health_data['vendor_system_status'] = 'healthy' if overall_healthy else 'unhealthy'
        
        return Response(
            health_data,
            status=status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )


class VendorDatabaseHealthView(APIView):
    """
    Database-specific health check
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get database health details"""
        try:
            health_data = vendor_db_manager.vendor_health_check()
            health_data['vendor_timestamp'] = int(time.time())
            
            # Additional Django DB checks
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                health_data['vendor_django_db_connected'] = True
            
            return Response(health_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_data = {
                'vendor_system_status': 'unhealthy',
                'vendor_error': str(e),
                'vendor_timestamp': int(time.time())
            }
            return Response(error_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)

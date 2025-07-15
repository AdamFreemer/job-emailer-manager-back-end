from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
import redis
from django.conf import settings


class HealthCheckView(View):
    """Basic health check endpoint"""
    
    def get(self, request):
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'job-tracker-api'
        })


class DetailedHealthCheckView(View):
    """Detailed health check with component status"""
    
    def get(self, request):
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'job-tracker-api',
            'components': {}
        }
        
        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['components']['database'] = {
                'status': 'healthy',
                'type': 'postgresql'
            }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        # Check Redis
        try:
            redis_client = redis.from_url(settings.CELERY_BROKER_URL)
            redis_client.ping()
            health_status['components']['redis'] = {
                'status': 'healthy',
                'type': 'redis'
            }
        except Exception as e:
            health_status['components']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'degraded'
        
        # Return appropriate status code
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return JsonResponse(health_status, status=status_code)


class StatusView(View):
    """API status and version information"""
    
    def get(self, request):
        return JsonResponse({
            'api_version': '1.0.0',
            'django_version': '5.0.1',
            'environment': settings.DEBUG and 'development' or 'production',
            'features': {
                'google_oauth': bool(settings.GOOGLE_CLIENT_ID),
                'openai_integration': bool(settings.OPENAI_API_KEY),
                'email_enabled': bool(settings.EMAIL_HOST_USER),
            }
        })

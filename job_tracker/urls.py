"""
URL configuration for job_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# Root API view
def api_root(request):
    return JsonResponse({
        'message': 'Job Tracker API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health/',
            'health_detailed': '/api/health/detailed/',
            'status': '/api/status/',
            'admin': '/admin/',
            'auth': {
                'google_oauth_init': '/api/auth/oauth/google/',
                'google_oauth_callback': '/api/auth/oauth/google/callback/',
                'current_user': '/api/auth/user/',
                'logout': '/api/auth/logout/',
                'google_refresh': '/api/auth/google/refresh/',
                'google_disconnect': '/api/auth/google/disconnect/',
                'domains': '/api/auth/domains/',
                'domain_detail': '/api/auth/domains/{id}/',
            },
            'applications': {
                'list': '/api/apps/',
                'create': '/api/apps/',
                'detail': '/api/apps/{id}/',
                'update_status': '/api/apps/{id}/update_status/',
                'stats': '/api/apps/stats/',
                'bulk_update': '/api/apps/bulk_update_status/',
            },
            'gmail': {
                'fetch': '/api/gmail/fetch/',
                'list': '/api/gmail/',
                'detail': '/api/gmail/{id}/',
                'create_application': '/api/gmail/{id}/create-application/',
            }
        }
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/auth/', include('accounts.urls')),
    path('api/', include('applications.urls')),
    path('api/gmail/', include('gmail.urls')),
]

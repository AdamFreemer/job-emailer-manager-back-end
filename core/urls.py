from django.urls import path
from .views import HealthCheckView, DetailedHealthCheckView, StatusView

app_name = 'core'

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health'),
    path('health/detailed/', DetailedHealthCheckView.as_view(), name='health-detailed'),
    path('status/', StatusView.as_view(), name='status'),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApplicationViewSet

router = DefaultRouter()
router.register(r'apps', ApplicationViewSet, basename='application')

app_name = 'applications'

urlpatterns = [
    path('', include(router.urls)),
]
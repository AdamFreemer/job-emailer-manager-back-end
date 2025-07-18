"""
Gmail URL configuration
"""
from django.urls import path
from . import views

app_name = 'gmail'

urlpatterns = [
    # Email operations
    path('fetch/', views.fetch_emails, name='fetch_emails'),
    path('', views.list_emails, name='list_emails'),
    path('<int:email_id>/', views.email_detail, name='email_detail'),
    path('<int:email_id>/create-application/', views.create_application_from_email, name='create_application'),
]
from django.urls import path
from .views import (
    GoogleOAuthInitView,
    GoogleOAuthCallbackView,
    refresh_google_token,
    disconnect_google_account,
    current_user,
    logout_user,
)

app_name = 'accounts'

urlpatterns = [
    # OAuth endpoints
    path('oauth/google/', GoogleOAuthInitView.as_view(), name='google-oauth-init'),
    path('oauth/google/callback/', GoogleOAuthCallbackView.as_view(), name='google-oauth-callback'),
    
    # User management
    path('user/', current_user, name='current-user'),
    path('logout/', logout_user, name='logout'),
    
    # Google account management
    path('google/refresh/', refresh_google_token, name='google-refresh'),
    path('google/disconnect/', disconnect_google_account, name='google-disconnect'),
]
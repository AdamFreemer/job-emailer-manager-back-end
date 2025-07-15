"""
Google OAuth utilities for authentication and token management
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings
from django.utils import timezone


# Gmail API scopes required for the application
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]


def get_google_auth_flow(redirect_uri: Optional[str] = None) -> Flow:
    """
    Create and return a Google OAuth2 flow instance
    
    Args:
        redirect_uri: Optional custom redirect URI
        
    Returns:
        Configured Flow instance
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth credentials not configured")
    
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri or settings.GOOGLE_REDIRECT_URI],
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri or settings.GOOGLE_REDIRECT_URI
    )
    
    # Enable offline access to get refresh token
    flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return flow


def get_credentials_from_tokens(access_token: str, refresh_token: str, 
                               token_expiry: datetime) -> Credentials:
    """
    Create Credentials object from stored tokens
    
    Args:
        access_token: OAuth access token
        refresh_token: OAuth refresh token
        token_expiry: Token expiration datetime
        
    Returns:
        Google Credentials object
    """
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
        expiry=token_expiry
    )


def refresh_google_tokens(google_account) -> Dict[str, any]:
    """
    Refresh expired Google OAuth tokens
    
    Args:
        google_account: GoogleAccount model instance
        
    Returns:
        Dictionary with updated tokens and expiry
    """
    credentials = get_credentials_from_tokens(
        google_account.access_token,
        google_account.refresh_token,
        google_account.token_expiry
    )
    
    # Refresh the token
    credentials.refresh(Request())
    
    # Calculate new expiry (Google tokens typically expire in 1 hour)
    new_expiry = timezone.now() + timedelta(seconds=3600)
    
    # Update the model
    google_account.access_token = credentials.token
    google_account.token_expiry = new_expiry
    if credentials.refresh_token:  # Sometimes refresh token is not returned
        google_account.refresh_token = credentials.refresh_token
    google_account.save()
    
    return {
        'access_token': credentials.token,
        'refresh_token': google_account.refresh_token,
        'token_expiry': new_expiry
    }


def get_user_info(credentials: Credentials) -> Dict[str, str]:
    """
    Fetch user information from Google
    
    Args:
        credentials: Google OAuth credentials
        
    Returns:
        Dictionary with user email and name
    """
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    
    return {
        'email': user_info.get('email'),
        'name': user_info.get('name'),
        'picture': user_info.get('picture'),
        'google_id': user_info.get('id')
    }


def get_gmail_service(google_account):
    """
    Get an authenticated Gmail service instance
    
    Args:
        google_account: GoogleAccount model instance
        
    Returns:
        Gmail service instance
    """
    # Check if tokens need refresh
    if google_account.token_expiry <= timezone.now():
        refresh_google_tokens(google_account)
    
    credentials = get_credentials_from_tokens(
        google_account.access_token,
        google_account.refresh_token,
        google_account.token_expiry
    )
    
    return build('gmail', 'v1', credentials=credentials)
import secrets
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import GoogleAccount, DomainFilter
from .serializers import (
    UserSerializer, 
    OAuthCallbackSerializer, 
    OAuthInitSerializer,
    GoogleAccountSerializer,
    DomainFilterSerializer
)
from .utils import (
    get_google_auth_flow, 
    get_user_info, 
    get_credentials_from_tokens,
    refresh_google_tokens
)


class GoogleOAuthInitView(APIView):
    """Initialize Google OAuth flow"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Generate OAuth URL for user to authenticate with Google
        """
        try:
            # Generate a secure random state
            state = secrets.token_urlsafe(32)
            
            # Store state in session for verification
            request.session['oauth_state'] = state
            
            # Get OAuth flow
            flow = get_google_auth_flow()
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=state
            )
            
            serializer = OAuthInitSerializer(data={
                'auth_url': auth_url,
                'state': state
            })
            serializer.is_valid()
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to initialize OAuth: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleOAuthCallbackView(APIView):
    """Handle Google OAuth callback"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Exchange authorization code for tokens and create/update user
        """
        serializer = OAuthCallbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        code = serializer.validated_data['code']
        state = serializer.validated_data.get('state', '')
        
        # Verify state to prevent CSRF
        # Note: In a production environment with separate frontend/backend,
        # you'd want to store state in a database or cache instead of sessions
        session_state = request.session.get('oauth_state', '')
        if state and session_state and session_state != state:
            return Response(
                {'error': 'Invalid state parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # For development, we'll allow missing state if both are empty
        elif not state and not session_state:
            print("Warning: No state parameter provided or stored")
        
        try:
            # Exchange code for tokens
            print(f"Attempting to exchange code: {code[:10]}...")
            print(f"Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
            flow = get_google_auth_flow()
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Get user info from Google
            user_info = get_user_info(credentials)
            
            # Find or create user
            user, created = User.objects.get_or_create(
                email=user_info['email'],
                defaults={
                    'username': user_info['email'],
                    'first_name': user_info.get('name', '').split()[0] if user_info.get('name') else '',
                    'last_name': ' '.join(user_info.get('name', '').split()[1:]) if user_info.get('name') else '',
                }
            )
            
            # Create or update GoogleAccount
            google_account, _ = GoogleAccount.objects.update_or_create(
                user=user,
                defaults={
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_expiry': timezone.now() + timezone.timedelta(seconds=3600)
                }
            )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Clear session state
            request.session.pop('oauth_state', None)
            
            return Response({
                'user': UserSerializer(user).data,
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'google_account': GoogleAccountSerializer(google_account).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print(f"OAuth callback error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'OAuth callback failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_google_token(request):
    """Refresh Google OAuth tokens"""
    try:
        google_account = request.user.google_account
    except GoogleAccount.DoesNotExist:
        return Response(
            {'error': 'No Google account linked'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        tokens = refresh_google_tokens(google_account)
        return Response({
            'message': 'Tokens refreshed successfully',
            'token_expiry': tokens['token_expiry']
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'Failed to refresh tokens: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_google_account(request):
    """Disconnect Google account from user"""
    try:
        google_account = request.user.google_account
        google_account.delete()
        return Response(
            {'message': 'Google account disconnected successfully'},
            status=status.HTTP_200_OK
        )
    except GoogleAccount.DoesNotExist:
        return Response(
            {'error': 'No Google account linked'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current user information"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Logout user and invalidate tokens"""
    try:
        # Blacklist the refresh token if using JWT
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass  # Token might already be blacklisted or invalid
    
    logout(request)
    return Response(
        {'message': 'Logged out successfully'},
        status=status.HTTP_200_OK
    )


class DomainFilterListCreateView(APIView):
    """List and create domain filters"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's domain filters"""
        filters = DomainFilter.objects.filter(user=request.user)
        serializer = DomainFilterSerializer(filters, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new domain filter"""
        serializer = DomainFilterSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            # Check if domain already exists for user
            existing = DomainFilter.objects.filter(
                user=request.user,
                domain=serializer.validated_data['domain']
            ).first()
            
            if existing:
                return Response(
                    {'error': 'Domain filter already exists'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DomainFilterDetailView(APIView):
    """Update and delete domain filters"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return DomainFilter.objects.get(pk=pk, user=self.request.user)
        except DomainFilter.DoesNotExist:
            return None
    
    def delete(self, request, pk):
        """Delete a domain filter"""
        domain_filter = self.get_object(pk)
        if not domain_filter:
            return Response(
                {'error': 'Domain filter not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        domain_filter.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def patch(self, request, pk):
        """Toggle domain filter between allowed/blocked"""
        domain_filter = self.get_object(pk)
        if not domain_filter:
            return Response(
                {'error': 'Domain filter not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        domain_filter.is_allowed = not domain_filter.is_allowed
        domain_filter.save()
        
        serializer = DomainFilterSerializer(domain_filter)
        return Response(serializer.data)

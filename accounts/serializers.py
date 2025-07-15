from rest_framework import serializers
from django.contrib.auth.models import User
from .models import GoogleAccount, DomainFilter


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    has_google_account = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'date_joined', 'has_google_account']
        read_only_fields = ['id', 'date_joined']
    
    def get_has_google_account(self, obj):
        return hasattr(obj, 'google_account')


class GoogleAccountSerializer(serializers.ModelSerializer):
    """Serializer for GoogleAccount model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_token_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = GoogleAccount
        fields = ['id', 'user_email', 'token_expiry', 'created_at', 
                 'updated_at', 'is_token_valid']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_token_valid(self, obj):
        from django.utils import timezone
        return obj.token_expiry > timezone.now()


class DomainFilterSerializer(serializers.ModelSerializer):
    """Serializer for DomainFilter model"""
    
    class Meta:
        model = DomainFilter
        fields = ['id', 'domain', 'is_allowed', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_domain(self, value):
        # Remove protocol and path if provided
        value = value.lower().strip()
        value = value.replace('http://', '').replace('https://', '')
        value = value.split('/')[0]  # Remove path
        return value
    
    def create(self, validated_data):
        """Create domain filter with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OAuthCallbackSerializer(serializers.Serializer):
    """Serializer for OAuth callback data"""
    code = serializers.CharField(required=True)
    state = serializers.CharField(required=False, allow_blank=True)
    
    def validate_code(self, value):
        if not value:
            raise serializers.ValidationError("Authorization code is required")
        return value


class OAuthInitSerializer(serializers.Serializer):
    """Serializer for OAuth initialization response"""
    auth_url = serializers.URLField()
    state = serializers.CharField()
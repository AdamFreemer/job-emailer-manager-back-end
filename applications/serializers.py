from rest_framework import serializers
from .models import Application
from gmail.models import Email


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for Application model"""
    email_count = serializers.SerializerMethodField()
    latest_email_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = [
            'id', 'company', 'role', 'status', 'thread_id', 
            'source_url', 'created_at', 'updated_at',
            'email_count', 'latest_email_date'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def get_email_count(self, obj):
        """Get count of emails for this application"""
        return obj.emails.count()
    
    def get_latest_email_date(self, obj):
        """Get date of most recent email"""
        latest_email = obj.emails.order_by('-received_at').first()
        return latest_email.received_at if latest_email else None
    
    def create(self, validated_data):
        """Create application with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating applications manually"""
    
    class Meta:
        model = Application
        fields = ['company', 'role', 'status', 'source_url']
        
    def create(self, validated_data):
        """Create application with generated thread_id"""
        import uuid
        validated_data['user'] = self.context['request'].user
        validated_data['thread_id'] = f"manual_{uuid.uuid4().hex[:16]}"
        return super().create(validated_data)


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating application status"""
    status = serializers.ChoiceField(choices=Application.STATUS_CHOICES)
    
    def update(self, instance, validated_data):
        instance.status = validated_data['status']
        instance.save()
        return instance


class ApplicationStatsSerializer(serializers.Serializer):
    """Serializer for application statistics"""
    total = serializers.IntegerField()
    applied = serializers.IntegerField()
    interview = serializers.IntegerField()
    offer = serializers.IntegerField()
    rejected = serializers.IntegerField()
    archived = serializers.IntegerField()
    replied = serializers.IntegerField()
"""
Gmail serializers
"""
from rest_framework import serializers
from gmail.models import Email
from applications.serializers import ApplicationSerializer


class EmailSerializer(serializers.ModelSerializer):
    """Serializer for Email model"""
    application = ApplicationSerializer(read_only=True)
    has_application = serializers.SerializerMethodField()
    
    class Meta:
        model = Email
        fields = [
            'id',
            'gmail_id',
            'thread_id',
            'subject',
            'sender',
            'sender_email',
            'recipient',
            'date_received',
            'body_text',
            'body_html',
            'status',
            'is_job_related',
            'classification_confidence',
            'raw_data',
            'created_at',
            'updated_at',
            'application',
            'has_application',
        ]
        read_only_fields = [
            'gmail_id',
            'thread_id',
            'sender',
            'sender_email',
            'recipient',
            'date_received',
            'body_text',
            'body_html',
            'created_at',
            'updated_at',
        ]
    
    def get_has_application(self, obj):
        """Check if email has associated application"""
        return hasattr(obj, 'application')


class EmailListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for email lists"""
    has_application = serializers.SerializerMethodField()
    
    class Meta:
        model = Email
        fields = [
            'id',
            'subject',
            'sender',
            'sender_email',
            'date_received',
            'status',
            'is_job_related',
            'has_application',
        ]
    
    def get_has_application(self, obj):
        """Check if email has associated application"""
        return hasattr(obj, 'application')
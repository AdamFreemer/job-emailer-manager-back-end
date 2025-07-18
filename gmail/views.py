"""
Gmail API views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import models

from gmail.models import Email
from gmail.serializers import EmailSerializer, EmailListSerializer
from gmail.services import GmailService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetch_emails(request):
    """
    Fetch recent emails from Gmail
    
    Request body:
    {
        "days_back": 7,  // optional, default 7
        "max_results": 50  // optional, default 50
    }
    """
    # Check if user has Google account
    if not hasattr(request.user, 'google_account'):
        return Response(
            {'error': 'Google account not connected'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get parameters
    days_back = request.data.get('days_back', 7)
    max_results = request.data.get('max_results', 50)
    
    try:
        # Initialize Gmail service
        gmail_service = GmailService(request.user)
        
        # Fetch emails
        emails = gmail_service.fetch_recent_emails(
            days_back=days_back,
            max_results=max_results
        )
        
        # Save to database
        saved_count = gmail_service.save_emails_to_db(emails)
        
        return Response({
            'fetched': len(emails),
            'saved': saved_count,
            'message': f'Fetched {len(emails)} emails, saved {saved_count} new emails'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch emails: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_emails(request):
    """
    List emails for the authenticated user
    
    Query params:
    - status: Filter by processing status
    - is_job_related: Filter by job relation
    - search: Search in subject/sender
    - page: Page number
    """
    emails = Email.objects.filter(user=request.user)
    
    # Apply filters
    status_filter = request.query_params.get('status')
    if status_filter:
        emails = emails.filter(status=status_filter)
    
    is_job_related = request.query_params.get('is_job_related')
    if is_job_related is not None:
        emails = emails.filter(is_job_related=is_job_related.lower() == 'true')
    
    search = request.query_params.get('search')
    if search:
        emails = emails.filter(
            models.Q(subject__icontains=search) |
            models.Q(sender__icontains=search)
        )
    
    # Order by date
    emails = emails.order_by('-received_at')
    
    # Paginate
    from django.core.paginator import Paginator
    paginator = Paginator(emails, 20)
    page_number = request.query_params.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    serializer = EmailListSerializer(page_obj, many=True)
    
    return Response({
        'results': serializer.data,
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def email_detail(request, email_id):
    """Get or update a specific email"""
    email = get_object_or_404(Email, id=email_id, user=request.user)
    
    if request.method == 'GET':
        serializer = EmailSerializer(email)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = EmailSerializer(email, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # If marking as processed, mark as read in Gmail
            if request.data.get('category') == 'PROCESSED':
                try:
                    gmail_service = GmailService(request.user)
                    gmail_service.mark_as_read(email.gmail_id)
                except:
                    pass  # Don't fail if Gmail update fails
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_application_from_email(request, email_id):
    """
    Create a job application from an email
    
    Request body:
    {
        "company_name": "Company Inc",
        "position": "Software Engineer",
        "location": "San Francisco, CA",
        "salary_range": "$120k-150k"
    }
    """
    email = get_object_or_404(Email, id=email_id, user=request.user)
    
    # Check if application already exists
    if hasattr(email, 'application'):
        return Response(
            {'error': 'Application already exists for this email'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create application
    from applications.models import Application
    from applications.serializers import ApplicationSerializer
    
    # Merge email data with request data
    application_data = {
        'user': request.user.id,
        'email': email.id,
        'applied_date': email.date_received,
        **request.data
    }
    
    serializer = ApplicationSerializer(data=application_data)
    if serializer.is_valid():
        application = serializer.save()
        
        # Update email status
        email.status = 'PROCESSED'
        email.is_job_related = True
        email.save()
        
        # Add label in Gmail
        try:
            gmail_service = GmailService(request.user)
            gmail_service.add_label(email.gmail_id, 'Job Tracker/Processed')
        except:
            pass
        
        return Response(
            ApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
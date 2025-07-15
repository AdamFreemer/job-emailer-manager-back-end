from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Application
from .serializers import (
    ApplicationSerializer,
    ApplicationCreateSerializer,
    ApplicationStatusUpdateSerializer,
    ApplicationStatsSerializer
)


class ApplicationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing job applications
    """
    permission_classes = [IsAuthenticated]
    pagination_class = ApplicationPagination
    
    def get_queryset(self):
        """Filter applications by current user"""
        queryset = Application.objects.filter(user=self.request.user)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(company__icontains=search) | 
                Q(role__icontains=search)
            )
        
        # Order by
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return ApplicationCreateSerializer
        elif self.action == 'update_status':
            return ApplicationStatusUpdateSerializer
        return ApplicationSerializer
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update application status"""
        application = self.get_object()
        serializer = ApplicationStatusUpdateSerializer(
            application, 
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return updated application
        response_serializer = ApplicationSerializer(application)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get application statistics for current user"""
        applications = Application.objects.filter(user=request.user)
        
        stats_data = {
            'total': applications.count(),
            'applied': applications.filter(status='APPLIED').count(),
            'interview': applications.filter(status='INTERVIEW').count(),
            'offer': applications.filter(status='OFFER').count(),
            'rejected': applications.filter(status='REJECTED').count(),
            'archived': applications.filter(status='ARCHIVE').count(),
            'replied': applications.filter(status='REPLIED').count(),
        }
        
        serializer = ApplicationStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """Bulk update status for multiple applications"""
        ids = request.data.get('ids', [])
        new_status = request.data.get('status')
        
        if not ids or not new_status:
            return Response(
                {'error': 'ids and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status
        valid_statuses = [choice[0] for choice in Application.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {valid_statuses}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update applications
        updated = Application.objects.filter(
            user=request.user,
            id__in=ids
        ).update(status=new_status)
        
        return Response({
            'updated': updated,
            'status': new_status
        })

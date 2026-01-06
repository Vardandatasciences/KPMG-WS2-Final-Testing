"""
Views for the core app.
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    AuditLog, SystemConfiguration, NotificationTemplate,
    FileUpload, Dashboard, Widget, Report, ReportExecution, Integration
)
from .serializers import (
    AuditLogSerializer, SystemConfigurationSerializer,
    NotificationTemplateSerializer, FileUploadSerializer,
    DashboardSerializer, WidgetSerializer, ReportSerializer,
    ReportExecutionSerializer, IntegrationSerializer
)


# Dashboard Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_overview(request):
    """Get dashboard overview data."""
    # This would return dashboard overview data
    return Response({
        'message': 'Dashboard overview endpoint',
        'data': {}
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics."""
    # This would return dashboard statistics
    return Response({
        'message': 'Dashboard stats endpoint',
        'data': {}
    })


# File Upload Views
class FileUploadListView(generics.ListCreateAPIView):
    """List and create file uploads."""
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['processing_status', 'uploaded_by']
    search_fields = ['original_filename']
    ordering_fields = ['created_at', 'file_size']
    ordering = ['-created_at']


class FileUploadDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete file upload."""
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def file_upload(request):
    """Handle file upload."""
    # This would handle file upload logic
    return Response({'message': 'File upload endpoint'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def file_detail(request, pk):
    """Get file upload details."""
    file_upload = get_object_or_404(FileUpload, pk=pk)
    serializer = FileUploadSerializer(file_upload)
    return Response(serializer.data)


# System Configuration Views
class SystemConfigurationListView(generics.ListCreateAPIView):
    """List and create system configurations."""
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['key', 'description']
    ordering = ['key']


class SystemConfigurationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete system configuration."""
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def system_config(request):
    """Get system configuration."""
    configs = SystemConfiguration.objects.filter(is_active=True)
    serializer = SystemConfigurationSerializer(configs, many=True)
    return Response(serializer.data)


# Notification Templates Views
class NotificationTemplateListView(generics.ListCreateAPIView):
    """List and create notification templates."""
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'subject', 'body']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class NotificationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete notification template."""
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_templates(request):
    """Get notification templates."""
    templates = NotificationTemplate.objects.filter(is_active=True)
    serializer = NotificationTemplateSerializer(templates, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def template_detail(request, pk):
    """Get notification template details."""
    template = get_object_or_404(NotificationTemplate, pk=pk)
    serializer = NotificationTemplateSerializer(template)
    return Response(serializer.data)


# Reports Views
class ReportListView(generics.ListCreateAPIView):
    """List and create reports."""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete report."""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reports_list(request):
    """Get reports list."""
    reports = Report.objects.filter(is_active=True)
    serializer = ReportSerializer(reports, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def report_detail(request, pk):
    """Get report details."""
    report = get_object_or_404(Report, pk=pk)
    serializer = ReportSerializer(report)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def execute_report(request, pk):
    """Execute a report."""
    report = get_object_or_404(Report, pk=pk)
    # This would execute the report logic
    return Response({'message': f'Report {report.name} execution started'})


# Integrations Views
class IntegrationListView(generics.ListCreateAPIView):
    """List and create integrations."""
    queryset = Integration.objects.all()
    serializer_class = IntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['integration_type', 'is_active', 'sync_status']
    search_fields = ['name']
    ordering_fields = ['name', 'last_sync', 'created_at']
    ordering = ['name']


class IntegrationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete integration."""
    queryset = Integration.objects.all()
    serializer_class = IntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def integrations_list(request):
    """Get integrations list."""
    integrations = Integration.objects.filter(is_active=True)
    serializer = IntegrationSerializer(integrations, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def integration_detail(request, pk):
    """Get integration details."""
    integration = get_object_or_404(Integration, pk=pk)
    serializer = IntegrationSerializer(integration)
    return Response(serializer.data)


# Audit Logs Views
class AuditLogListView(generics.ListAPIView):
    """List audit logs."""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'entity_type', 'status', 'user']
    search_fields = ['entity_name', 'changes']
    ordering_fields = ['created_at', 'action', 'entity_type']
    ordering = ['-created_at']


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def audit_logs(request):
    """Get audit logs."""
    logs = AuditLog.objects.all()
    serializer = AuditLogSerializer(logs, many=True)
    return Response(serializer.data)


# Dashboard and Widget Views
class DashboardListView(generics.ListCreateAPIView):
    """List and create dashboards."""
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_default', 'is_public', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class DashboardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete dashboard."""
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    permission_classes = [permissions.IsAuthenticated]


class WidgetListView(generics.ListCreateAPIView):
    """List and create widgets."""
    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['widget_type', 'is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class WidgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete widget."""
    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer
    permission_classes = [permissions.IsAuthenticated]

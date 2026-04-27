"""
System Risk Schedule API - Stubs for missing functionality
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_sys_risk_schedule(request):
    return Response({'success': False, 'error': 'Not Implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_sys_risk_schedules(request):
    return Response({'success': True, 'schedules': []})

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def update_or_delete_sys_risk_schedule(request, schedule_id):
    return Response({'success': False, 'error': 'Not Implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_sys_risk_schedule_runs(request, schedule_id):
    return Response({'success': True, 'runs': []})

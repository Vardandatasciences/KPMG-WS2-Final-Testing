"""
Export Status Endpoints
Provides status checking for async export tasks
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_export_status(request, task_id):
    """
    Get status of an export task
    
    Args:
        task_id: ExportTask ID
    
    Returns:
        JSON with export status, file URL if completed, error if failed
    """
    try:
        from ...models import ExportTask
        
        export_task = ExportTask.objects.get(id=task_id)
        
        response_data = {
            'success': True,
            'task_id': task_id,
            'status': export_task.status,
            'file_type': export_task.file_type,
            'user_id': export_task.user_id,
            'created_at': export_task.created_at.isoformat() if export_task.created_at else None,
            'updated_at': export_task.updated_at.isoformat() if export_task.updated_at else None,
        }
        
        if export_task.status == 'completed':
            response_data['file_url'] = export_task.s3_url
            response_data['file_name'] = export_task.file_name
            response_data['completed_at'] = export_task.completed_at.isoformat() if export_task.completed_at else None
            response_data['metadata'] = export_task.metadata or {}
        elif export_task.status == 'failed':
            response_data['error'] = export_task.error
        elif export_task.status == 'processing':
            response_data['message'] = 'Export is being processed. Please check again in a few moments.'
        
        return JsonResponse(response_data)
        
    except ExportTask.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Export task {task_id} not found'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def list_user_exports(request, user_id):
    """
    List all exports for a user
    
    Args:
        user_id: User ID
    
    Returns:
        JSON list of export tasks
    """
    try:
        from ...models import ExportTask
        
        exports = ExportTask.objects.filter(user_id=str(user_id)).order_by('-created_at')[:50]
        
        export_list = []
        for export in exports:
            export_list.append({
                'task_id': export.id,
                'status': export.status,
                'file_type': export.file_type,
                'file_name': export.file_name,
                'file_url': export.s3_url,
                'created_at': export.created_at.isoformat() if export.created_at else None,
                'completed_at': export.completed_at.isoformat() if export.completed_at else None,
                'error': export.error
            })
        
        return JsonResponse({
            'success': True,
            'exports': export_list,
            'count': len(export_list)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)





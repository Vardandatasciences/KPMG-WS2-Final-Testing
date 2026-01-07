from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from grc.models import Domain, Framework
import json


@csrf_exempt
@require_http_methods(["GET"])
def get_domains_with_frameworks(request):
    """
    Get all domains with their associated frameworks.
    Also returns frameworks that are not linked to any domain.
    """
    try:
        # Get all active domains
        domains = Domain.objects.filter(IsActive='Y').order_by('domain_name')
        
        # Build domain data with frameworks
        domains_data = []
        for domain in domains:
            frameworks = Framework.objects.filter(domain=domain).order_by('FrameworkName')
            domains_data.append({
                'domain_id': domain.domain_id,
                'domain_name': domain.domain_name,
                'frameworks': [
                    {
                        'framework_id': fw.FrameworkId,
                        'framework_name': fw.FrameworkName,
                        'current_version': fw.CurrentVersion,
                        'status': fw.Status,
                        'active_inactive': fw.ActiveInactive
                    }
                    for fw in frameworks
                ]
            })
        
        # Get frameworks not linked to any domain
        unlinked_frameworks = Framework.objects.filter(domain__isnull=True).order_by('FrameworkName')
        unlinked_data = [
            {
                'framework_id': fw.FrameworkId,
                'framework_name': fw.FrameworkName,
                'current_version': fw.CurrentVersion,
                'status': fw.Status,
                'active_inactive': fw.ActiveInactive
            }
            for fw in unlinked_frameworks
        ]
        
        return JsonResponse({
            'status': 'success',
            'domains': domains_data,
            'unlinked_frameworks': unlinked_data
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_framework_domain(request):
    """
    Update the domain association for a framework.
    Request body: {
        "framework_id": int,
        "domain_id": int or null (null to unlink from domain)
    }
    """
    try:
        data = json.loads(request.body)
        framework_id = data.get('framework_id')
        domain_id = data.get('domain_id')  # Can be None to unlink
        
        if not framework_id:
            return JsonResponse({
                'status': 'error',
                'message': 'framework_id is required'
            }, status=400)
        
        # Get the framework
        try:
            framework = Framework.objects.get(FrameworkId=framework_id)
        except Framework.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': f'Framework with id {framework_id} not found'
            }, status=404)
        
        # Update domain association
        with transaction.atomic():
            if domain_id is None:
                # Unlink from domain
                framework.domain = None
            else:
                # Link to domain
                try:
                    domain = Domain.objects.get(domain_id=domain_id, IsActive='Y')
                    framework.domain = domain
                except Domain.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Domain with id {domain_id} not found or inactive'
                    }, status=404)
            
            framework.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Framework domain association updated successfully',
            'framework_id': framework_id,
            'domain_id': domain_id
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def bulk_update_framework_domains(request):
    """
    Bulk update domain associations for multiple frameworks.
    Request body: {
        "updates": [
            {"framework_id": int, "domain_id": int or null},
            ...
        ]
    }
    """
    try:
        data = json.loads(request.body)
        updates = data.get('updates', [])
        
        if not updates:
            return JsonResponse({
                'status': 'error',
                'message': 'No updates provided'
            }, status=400)
        
        results = []
        errors = []
        
        with transaction.atomic():
            for update in updates:
                framework_id = update.get('framework_id')
                domain_id = update.get('domain_id')
                
                if not framework_id:
                    errors.append({
                        'framework_id': framework_id,
                        'error': 'framework_id is required'
                    })
                    continue
                
                try:
                    framework = Framework.objects.get(FrameworkId=framework_id)
                    
                    if domain_id is None:
                        framework.domain = None
                    else:
                        domain = Domain.objects.get(domain_id=domain_id, IsActive='Y')
                        framework.domain = domain
                    
                    framework.save()
                    results.append({
                        'framework_id': framework_id,
                        'domain_id': domain_id,
                        'status': 'success'
                    })
                
                except Framework.DoesNotExist:
                    errors.append({
                        'framework_id': framework_id,
                        'error': f'Framework with id {framework_id} not found'
                    })
                except Domain.DoesNotExist:
                    errors.append({
                        'framework_id': framework_id,
                        'error': f'Domain with id {domain_id} not found or inactive'
                    })
                except Exception as e:
                    errors.append({
                        'framework_id': framework_id,
                        'error': str(e)
                    })
        
        return JsonResponse({
            'status': 'success',
            'updated': len(results),
            'errors': len(errors),
            'results': results,
            'errors_list': errors
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)









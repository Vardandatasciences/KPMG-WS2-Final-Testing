import logging
from celery import shared_task
from django.utils import timezone
from django.db import models
from .models import Risk
from .services import RiskAnalysisService

logger = logging.getLogger(__name__)


@shared_task
def analyze_module_data_task(module_data_id):
    """
    Celery task to analyze module data and predict risks
    
    Args:
        module_data_id: UUID of the ModuleData instance to analyze
    """
    try:
        # Get the module data
        module_data = ModuleData.objects.get(id=module_data_id)
        
        # Analyze the data
        service = RiskAnalysisService()
        created_risks = service.analyze_module_data(module_data)
        
        # Heatmap data is now generated dynamically, no need to update
        
        logger.info(f"Successfully processed module data {module_data_id} and created {len(created_risks)} risks")
        
        return {
            'status': 'success',
            'module_data_id': str(module_data_id),
            'risks_created': len(created_risks)
        }
        
    except ModuleData.DoesNotExist:
        logger.error(f"ModuleData with id {module_data_id} not found")
        return {
            'status': 'error',
            'error': 'ModuleData not found'
        }
    except Exception as e:
        logger.error(f"Error processing module data {module_data_id}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def update_heatmap_data_task(module_name=None):
    """
    Celery task to update heatmap data (now deprecated - heatmap data is generated dynamically)
    
    Args:
        module_name: Optional module name to update specific module heatmap
    """
    logger.info("Heatmap data is now generated dynamically from Risk table - no update needed")
    return {
        'status': 'success',
        'message': 'Heatmap data is generated dynamically',
        'module': module_name or 'all'
    }


@shared_task
def cleanup_old_data_task():
    """
    Celery task to cleanup old data (processed module data)
    """
    try:
        # Clean up processed module data older than 90 days
        ninety_days_ago = timezone.now() - timezone.timedelta(days=90)
        deleted_module_data = ModuleData.objects.filter(
            processed=True,
            created_at__lt=ninety_days_ago
        ).delete()
        
        logger.info(f"Cleaned up {deleted_module_data[0]} module data records")
        
        return {
            'status': 'success',
            'deleted_module_data': deleted_module_data[0]
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old data: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def generate_risk_report_task(module_name=None, date_from=None, date_to=None):
    """
    Celery task to generate risk reports
    
    Args:
        module_name: Optional module name to filter by
        date_from: Optional start date
        date_to: Optional end date
    """
    try:
        from django.db.models import Count, Avg
        from datetime import datetime
        
        # Build query
        risks = Risk.objects.all()
        
        if module_name:
            risks = risks.filter(module__name=module_name)
        
        if date_from:
            if isinstance(date_from, str):
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            risks = risks.filter(created_at__date__gte=date_from)
        
        if date_to:
            if isinstance(date_to, str):
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            risks = risks.filter(created_at__date__lte=date_to)
        
        # Generate statistics
        stats = risks.aggregate(
            total_risks=Count('id'),
            avg_score=Avg('score'),
            critical_risks=Count('id', filter=models.Q(priority='Critical')),
            high_risks=Count('id', filter=models.Q(priority='High')),
            medium_risks=Count('id', filter=models.Q(priority='Medium')),
            low_risks=Count('id', filter=models.Q(priority='Low'))
        )
        
        # Get risks by module
        module_stats = risks.values('module__name').annotate(
            count=Count('id'),
            avg_score=Avg('score')
        )
        
        # Get risks by priority
        priority_stats = risks.values('priority').annotate(
            count=Count('id'),
            avg_score=Avg('score')
        )
        
        report = {
            'generated_at': timezone.now().isoformat(),
            'filters': {
                'module': module_name,
                'date_from': date_from.isoformat() if date_from else None,
                'date_to': date_to.isoformat() if date_to else None
            },
            'summary': stats,
            'by_module': list(module_stats),
            'by_priority': list(priority_stats)
        }
        
        logger.info(f"Generated risk report for {stats['total_risks']} risks")
        
        return {
            'status': 'success',
            'report': report
        }
        
    except Exception as e:
        logger.error(f"Error generating risk report: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def process_bulk_module_data_task(module_data_ids):
    """
    Celery task to process multiple module data records
    
    Args:
        module_data_ids: List of ModuleData UUIDs to process
    """
    try:
        results = []
        service = RiskAnalysisService()
        
        for module_data_id in module_data_ids:
            try:
                module_data = ModuleData.objects.get(id=module_data_id)
                created_risks = service.analyze_module_data(module_data)
                
                results.append({
                    'module_data_id': str(module_data_id),
                    'status': 'success',
                    'risks_created': len(created_risks)
                })
                
            except ModuleData.DoesNotExist:
                results.append({
                    'module_data_id': str(module_data_id),
                    'status': 'error',
                    'error': 'ModuleData not found'
                })
            except Exception as e:
                results.append({
                    'module_data_id': str(module_data_id),
                    'status': 'error',
                    'error': str(e)
                })
        
        # Heatmap data is now generated dynamically, no need to update
        
        logger.info(f"Processed {len(module_data_ids)} module data records")
        
        return {
            'status': 'success',
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error processing bulk module data: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def generate_comprehensive_risks_task(plan_id, evaluation_id=None):
    """
    Background task to generate comprehensive risks for BCP/DRP plans
    
    Args:
        plan_id: Plan ID to analyze
        evaluation_id: Optional evaluation ID to include in analysis
        
    Returns:
        dict: Task result with risk generation status
    """
    try:
        logger.info(f"Starting background comprehensive risk generation for plan {plan_id} (evaluation: {evaluation_id})")
        
        # Import here to avoid circular imports
        from bcpdrp.views import get_comprehensive_plan_data
        from .comprehensive_llama_service import ComprehensiveLlamaService
        
        # Get comprehensive plan data
        comprehensive_data = get_comprehensive_plan_data(plan_id, evaluation_id)
        if not comprehensive_data:
            logger.error(f"Failed to gather comprehensive data for plan {plan_id}")
            return {
                'status': 'error',
                'error': 'Failed to gather comprehensive plan data'
            }
        
        # Generate risks using comprehensive LLaMA service
        comprehensive_llama_service = ComprehensiveLlamaService()
        created_risks = comprehensive_llama_service.create_risks_from_comprehensive_data(
            entity='bcp_drp_module',
            plan_info=comprehensive_data.get('plan_info', {}),
            extracted_details=comprehensive_data.get('extracted_details'),
            evaluation_data=comprehensive_data.get('evaluation_data')
        )
        
        logger.info(f"Background task successfully created {len(created_risks)} risks for plan {plan_id}")
        
        return {
            'status': 'success',
            'plan_id': plan_id,
            'evaluation_id': evaluation_id,
            'risks_created': len(created_risks),
            'risk_ids': [risk.id for risk in created_risks]
        }
        
    except Exception as e:
        logger.error(f"Error in background comprehensive risk generation for plan {plan_id}: {str(e)}")
        return {
            'status': 'error',
            'plan_id': plan_id,
            'evaluation_id': evaluation_id,
            'error': str(e)
        }


@shared_task
def generate_entity_risks_task(entity, table, row_id):
    """
    Background task to generate risks for entity data row
    
    Args:
        entity: Entity name (e.g., 'bcp_drp_module')
        table: Table name (e.g., 'bcp_drp_plans', 'bcp_drp_evaluations')
        row_id: Row ID to analyze
        
    Returns:
        dict: Task result with risk generation status
    """
    try:
        logger.info(f"Starting background risk generation for {entity} {table} row {row_id}")
        
        service = RiskAnalysisService()
        result = service.analyze_entity_data_row(
            entity=entity,
            table=table,
            row_id=row_id
        )
        
        risks_created = len(result.get('risks', []))
        logger.info(f"Background task successfully created {risks_created} risks for {entity} {table} row {row_id}")
        
        return {
            'status': 'success',
            'entity': entity,
            'table': table,
            'row_id': row_id,
            'risks_created': risks_created,
            'risk_ids': [risk['id'] for risk in result.get('risks', [])]
        }
        
    except Exception as e:
        logger.error(f"Error in background risk generation for {entity} {table} row {row_id}: {str(e)}")
        return {
            'status': 'error',
            'entity': entity,
            'table': table,
            'row_id': row_id,
            'error': str(e)
        }

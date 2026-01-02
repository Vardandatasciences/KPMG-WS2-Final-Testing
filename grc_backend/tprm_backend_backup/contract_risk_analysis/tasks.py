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
def generate_entity_risks_task(entity, table, row_id):
    """
    Background task to generate risks for entity data row
    
    Args:
        entity: Entity name (e.g., 'contract_module')
        table: Table name (e.g., 'vendor_contracts', 'contract_terms', 'contract_clauses')
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


@shared_task
def generate_comprehensive_contract_risks_task(contract_id):
    """
    Background task to generate comprehensive risks for contracts
    
    Args:
        contract_id: Contract ID to analyze
        
    Returns:
        dict: Task result with risk generation status
    """
    try:
        logger.info(f"Starting background comprehensive contract risk generation for contract {contract_id}")
        
        # Import contract risk service
        from .contract_risk_service import ContractRiskAnalysisService
        
        # Create service and run synchronous analysis
        contract_risk_service = ContractRiskAnalysisService()
        result = contract_risk_service._analyze_contract_synchronously(contract_id)
        
        if result.get('status') == 'completed':
            logger.info(f"Background task successfully created {len(result.get('risks', []))} risks for contract {contract_id}")
            return {
                'status': 'success',
                'contract_id': contract_id,
                'risks_created': len(result.get('risks', [])),
                'risk_ids': [risk.get('id') for risk in result.get('risks', [])]
            }
        else:
            logger.error(f"Background task failed for contract {contract_id}: {result.get('error', 'Unknown error')}")
            return {
                'status': 'error',
                'contract_id': contract_id,
                'error': result.get('error', 'Unknown error')
            }
        
    except Exception as e:
        logger.error(f"Error in background comprehensive contract risk generation for contract {contract_id}: {str(e)}")
        return {
            'status': 'error',
            'contract_id': contract_id,
            'error': str(e)
        }


@shared_task
def generate_contract_table_risks_task(table, contract_id):
    """
    Background task to generate risks for specific contract table
    
    Args:
        table: Table name ('vendor_contracts', 'contract_terms', 'contract_clauses')
        contract_id: Contract ID to analyze
        
    Returns:
        dict: Task result with risk generation status
    """
    try:
        logger.info(f"Starting background {table} risk generation for contract {contract_id}")
        
        # Import services
        from .services import RiskAnalysisService
        
        # Create service and analyze
        risk_service = RiskAnalysisService()
        result = risk_service.analyze_entity_data_row(
            entity='contract_module',
            table=table,
            row_id=str(contract_id)
        )
        
        risks_created = len(result.get('risks', []))
        logger.info(f"Background task successfully created {risks_created} risks for {table} contract {contract_id}")
        
        return {
            'status': 'success',
            'table': table,
            'contract_id': contract_id,
            'risks_created': risks_created,
            'risk_ids': [risk.get('id') for risk in result.get('risks', [])]
        }
        
    except Exception as e:
        logger.error(f"Error in background {table} risk generation for contract {contract_id}: {str(e)}")
        return {
            'status': 'error',
            'table': table,
            'contract_id': contract_id,
            'error': str(e)
        }


@shared_task
def analyze_contract_risk_task(contract_id):
    """
    Comprehensive contract risk analysis task using Llama
    
    This task analyzes a contract and its related terms and clauses to generate
    comprehensive risk assessments using the Llama AI service.
    
    Args:
        contract_id: The ID of the contract to analyze
        
    Returns:
        dict: Task result with risk generation status
    """
    try:
        print(f"=== RISK ANALYSIS TASK DEBUG: Starting comprehensive contract risk analysis for contract {contract_id} ===")
        logger.info(f"Starting comprehensive contract risk analysis for contract {contract_id}")
        
        # Import contract models
        from contracts.models import VendorContract, ContractTerm, ContractClause
        from .comprehensive_llama_service import ComprehensiveLlamaService
        
        print(f"=== RISK ANALYSIS TASK DEBUG: Imports successful ===")
        
        # Get the contract
        try:
            contract = VendorContract.objects.get(contract_id=contract_id)
            print(f"=== RISK ANALYSIS TASK DEBUG: Contract found: {contract.contract_title} ===")
        except VendorContract.DoesNotExist:
            print(f"=== RISK ANALYSIS TASK DEBUG: Contract {contract_id} not found ===")
            logger.error(f"Contract {contract_id} not found")
            return {
                'status': 'error',
                'contract_id': contract_id,
                'error': 'Contract not found'
            }
        
        # Get contract terms
        terms = ContractTerm.objects.filter(contract_id=contract_id)
        print(f"=== RISK ANALYSIS TASK DEBUG: Found {terms.count()} terms ===")
        
        # Get contract clauses
        clauses = ContractClause.objects.filter(contract_id=contract_id)
        print(f"=== RISK ANALYSIS TASK DEBUG: Found {clauses.count()} clauses ===")
        
        # Get vendor information
        vendor_name = 'Unknown Vendor'
        if contract.vendor_id:
            try:
                from contracts.models import Vendor
                vendor = Vendor.objects.get(vendor_id=contract.vendor_id)
                vendor_name = vendor.company_name or vendor.vendor_name or 'Unknown Vendor'
            except Exception as e:
                print(f"=== RISK ANALYSIS TASK DEBUG: Could not get vendor name: {e} ===")
        
        # Prepare comprehensive contract data
        contract_data = {
            'contract_id': contract.contract_id,
            'contract_title': contract.contract_title,
            'contract_type': contract.contract_type,
            'contract_value': contract.contract_value,
            'vendor_id': contract.vendor_id,
            'vendor_name': vendor_name,
            'start_date': contract.start_date,
            'end_date': contract.end_date,
            'priority': contract.priority,
            'compliance_status': contract.compliance_status,
            'dispute_resolution_method': contract.dispute_resolution_method,
            'governing_law': contract.governing_law,
            'termination_clause_type': contract.termination_clause_type,
            'contract_risk_score': contract.contract_risk_score,
            'terms': [
                {
                    'term_category': term.term_category,
                    'term_title': term.term_title,
                    'term_text': term.term_text,
                    'risk_level': term.risk_level,
                    'is_standard': term.is_standard
                } for term in terms
            ],
            'clauses': [
                {
                    'clause_name': clause.clause_name,
                    'clause_type': clause.clause_type,
                    'clause_text': clause.clause_text,
                    'risk_level': clause.risk_level,
                    'legal_category': clause.legal_category,
                    'is_standard': clause.is_standard,
                    'notice_period_days': clause.notice_period_days,
                    'auto_renew': clause.auto_renew,
                    'renewal_terms': clause.renewal_terms,
                    'termination_notice_period': clause.termination_notice_period,
                    'early_termination_fee': clause.early_termination_fee,
                    'termination_conditions': clause.termination_conditions
                } for clause in clauses
            ]
        }
        
        # Initialize Llama service
        print(f"=== RISK ANALYSIS TASK DEBUG: Initializing Llama service ===")
        llama_service = ComprehensiveLlamaService()
        print(f"=== RISK ANALYSIS TASK DEBUG: Llama service initialized ===")
        
        # Generate risks using Llama
        print(f"=== RISK ANALYSIS TASK DEBUG: Calling Llama service ===")
        risks = llama_service.create_risks_from_comprehensive_data(
            entity='contract_module',
            plan_info=contract_data,
            extracted_details=contract_data,
            evaluation_data=None
        )
        print(f"=== RISK ANALYSIS TASK DEBUG: Llama service completed ===")
        
        risks_created = len(risks)
        print(f"=== RISK ANALYSIS TASK DEBUG: Created {risks_created} risks ===")
        logger.info(f"Successfully created {risks_created} risks for contract {contract_id}")
        
        return {
            'status': 'success',
            'contract_id': contract_id,
            'risks_created': risks_created,
            'risk_ids': [risk.id for risk in risks]
        }
        
    except Exception as e:
        print(f"=== RISK ANALYSIS TASK DEBUG: Error occurred: {str(e)} ===")
        logger.error(f"Error in comprehensive contract risk analysis for contract {contract_id}: {str(e)}")
        return {
            'status': 'error',
            'contract_id': contract_id,
            'error': str(e)
        }
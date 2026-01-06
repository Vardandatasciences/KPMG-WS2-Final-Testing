"""
Contract Risk Analysis Service

This service provides specialized risk analysis functionality for contract management.
It integrates with the main risk analysis module to generate risks based on contract data.
"""

import logging
import threading
import time
from typing import Dict, List
from django.utils import timezone
from .services import RiskAnalysisService
from .entity_service import EntityDataService
from .tasks import generate_comprehensive_contract_risks_task, generate_contract_table_risks_task

logger = logging.getLogger(__name__)


class ContractRiskAnalysisService:
    """
    Specialized service for contract risk analysis
    
    This service handles:
    1. Individual contract risk analysis
    2. Comprehensive multi-table contract analysis
    3. Background risk generation for new contracts
    4. Contract-specific risk patterns and rules
    """
    
    def __init__(self):
        self.risk_service = RiskAnalysisService()
        self.entity_service = EntityDataService()
    
    def _run_background_thread(self, contract_id: str):
        """
        Run risk analysis in a background thread
        This ensures contract creation is never blocked
        """
        def background_task():
            try:
                print(f"=== RISK ANALYSIS THREAD DEBUG: Starting background thread risk analysis for contract {contract_id} ===")
                logger.info(f"=== RISK ANALYSIS THREAD DEBUG: Starting background thread risk analysis for contract {contract_id} ===")
                # Small delay to ensure contract creation and database transaction completes first
                print(f"=== RISK ANALYSIS THREAD DEBUG: Waiting 2 seconds for contract creation to complete ===")
                logger.info(f"=== RISK ANALYSIS THREAD DEBUG: Waiting 2 seconds for contract creation to complete ===")
                time.sleep(2)
                
                # Create new service instances in the thread to avoid any shared state issues
                print(f"=== RISK ANALYSIS THREAD DEBUG: Creating service instances ===")
                logger.info(f"=== RISK ANALYSIS THREAD DEBUG: Creating service instances ===")
                from .services import RiskAnalysisService
                from .entity_service import EntityDataService
                
                risk_service = RiskAnalysisService()
                entity_service = EntityDataService()
                print(f"=== RISK ANALYSIS THREAD DEBUG: Service instances created successfully ===")
                print(f"=== RISK ANALYSIS THREAD DEBUG: Risk service available: {risk_service.risk_service.is_available if hasattr(risk_service, 'risk_service') else 'Unknown'} ===")
                logger.info(f"=== RISK ANALYSIS THREAD DEBUG: Service instances created successfully ===")
                
                # Get comprehensive contract data
                print(f"=== RISK ANALYSIS THREAD DEBUG: Getting comprehensive contract data for {contract_id} ===")
                logger.info(f"=== RISK ANALYSIS THREAD DEBUG: Getting comprehensive contract data for {contract_id} ===")
                comprehensive_data = entity_service.get_comprehensive_contract_data(contract_id)
                
                if not comprehensive_data:
                    print(f"=== RISK ANALYSIS THREAD DEBUG: No data found for contract {contract_id} in background analysis ===")
                    logger.warning(f"=== RISK ANALYSIS THREAD DEBUG: No data found for contract {contract_id} in background analysis ===")
                    return
                
                print(f"=== RISK ANALYSIS THREAD DEBUG: Comprehensive data keys: {list(comprehensive_data.keys()) if comprehensive_data else 'None'} ===")
                
                print(f"=== RISK ANALYSIS THREAD DEBUG: Got comprehensive data, starting analysis ===")
                logger.info(f"=== RISK ANALYSIS THREAD DEBUG: Got comprehensive data, starting analysis ===")
                
                # Analyze comprehensive contract data
                print(f"=== RISK ANALYSIS THREAD DEBUG: Calling analyze_comprehensive_plan_data ===")
                logger.info(f"=== RISK ANALYSIS THREAD DEBUG: Calling analyze_comprehensive_plan_data ===")
                
                try:
                    result = risk_service.analyze_comprehensive_plan_data(
                        entity='contract_module',
                        comprehensive_data=comprehensive_data
                    )
                    print(f"=== RISK ANALYSIS THREAD DEBUG: Analysis completed successfully ===")
                    print(f"=== RISK ANALYSIS THREAD DEBUG: Background thread risk analysis completed for contract {contract_id}: {len(result.get('risks', []))} risks generated ===")
                    logger.info(f"=== RISK ANALYSIS THREAD DEBUG: Background thread risk analysis completed for contract {contract_id}: {len(result.get('risks', []))} risks generated ===")
                except Exception as analysis_error:
                    print(f"=== RISK ANALYSIS THREAD DEBUG: Analysis failed: {str(analysis_error)} ===")
                    logger.error(f"=== RISK ANALYSIS THREAD DEBUG: Analysis failed: {str(analysis_error)} ===")
                    import traceback
                    print(f"=== RISK ANALYSIS THREAD DEBUG: Analysis traceback: {traceback.format_exc()} ===")
                    logger.error(f"=== RISK ANALYSIS THREAD DEBUG: Analysis traceback: {traceback.format_exc()} ===")
                    raise
                
            except Exception as e:
                print(f"=== RISK ANALYSIS THREAD DEBUG: Background thread risk analysis failed for contract {contract_id}: {str(e)} ===")
                logger.error(f"=== RISK ANALYSIS THREAD DEBUG: Background thread risk analysis failed for contract {contract_id}: {str(e)} ===")
                import traceback
                print(f"=== RISK ANALYSIS THREAD DEBUG: Full traceback: {traceback.format_exc()} ===")
                logger.error(f"=== RISK ANALYSIS THREAD DEBUG: Full traceback: {traceback.format_exc()} ===")
        
        # Start the background thread with high priority for faster execution
        thread = threading.Thread(target=background_task, daemon=True, name=f"RiskAnalysis-{contract_id}")
        thread.start()
        print(f"=== RISK ANALYSIS THREAD DEBUG: Started background thread for contract {contract_id} risk analysis ===")
        logger.info(f"=== RISK ANALYSIS THREAD DEBUG: Started background thread for contract {contract_id} risk analysis ===")
    
    def analyze_contract_risks(self, contract_id: str, background: bool = True) -> Dict:
        """
        Analyze risks for a specific contract
        
        Args:
            contract_id: The contract ID to analyze
            background: If True, run analysis in background task
            
        Returns:
            Dict with risk analysis results or task info
        """
        try:
            logger.info(f"=== RISK ANALYSIS SERVICE DEBUG: Starting contract risk analysis for contract {contract_id} ===")
            
            if background:
                # Always use background thread for immediate non-blocking execution
                # This ensures contract creation is never delayed
                print(f"=== RISK ANALYSIS SERVICE DEBUG: Running in background mode ===")
                logger.info(f"=== RISK ANALYSIS SERVICE DEBUG: Running in background mode ===")
                self._run_background_thread(contract_id)
                result = {
                    'status': 'started',
                    'task_id': f'thread_{contract_id}_{int(time.time())}',
                    'message': f'Risk analysis started in background for contract {contract_id}',
                    'method': 'thread'
                }
                print(f"=== RISK ANALYSIS SERVICE DEBUG: Returning result: {result} ===")
                logger.info(f"=== RISK ANALYSIS SERVICE DEBUG: Returning result: {result} ===")
                return result
            else:
                # Run synchronously (only for manual testing)
                logger.info(f"=== RISK ANALYSIS SERVICE DEBUG: Running synchronously ===")
                return self._analyze_contract_synchronously(contract_id)
                
        except Exception as e:
            logger.error(f"=== RISK ANALYSIS SERVICE DEBUG: Error starting contract risk analysis for {contract_id}: {str(e)} ===")
            import traceback
            logger.error(f"=== RISK ANALYSIS SERVICE DEBUG: Full traceback: {traceback.format_exc()} ===")
            # Don't fail the entire process if risk analysis fails
            return {
                'status': 'warning',
                'error': str(e),
                'message': f'Risk analysis failed for contract {contract_id}, but contract creation succeeded'
            }
    
    def _analyze_contract_synchronously(self, contract_id: str) -> Dict:
        """
        Run contract risk analysis synchronously
        
        Args:
            contract_id: The contract ID to analyze
            
        Returns:
            Dict with comprehensive risk analysis results
        """
        try:
            # Get comprehensive contract data
            comprehensive_data = self.entity_service.get_comprehensive_contract_data(contract_id)
            
            if not comprehensive_data:
                return {
                    'status': 'error',
                    'error': 'Contract not found',
                    'message': f'Contract {contract_id} not found or has no data'
                }
            
            # Analyze comprehensive contract data
            result = self.risk_service.analyze_comprehensive_plan_data(
                entity='contract_module',
                comprehensive_data=comprehensive_data
            )
            
            # Add contract-specific metadata
            result.update({
                'status': 'completed',
                'contract_id': contract_id,
                'analysis_timestamp': timezone.now().isoformat(),
                'data_summary': comprehensive_data.get('summary', {}),
                'message': f'Risk analysis completed for contract {contract_id}'
            })
            
            logger.info(f"Completed synchronous risk analysis for contract {contract_id}: {len(result.get('risks', []))} risks generated")
            return result
            
        except Exception as e:
            logger.error(f"Error in synchronous contract risk analysis for {contract_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'message': f'Failed to analyze contract {contract_id}'
            }
    
    def analyze_contract_by_table(self, table: str, contract_id: str, background: bool = True) -> Dict:
        """
        Analyze risks for a specific contract table (vendor_contracts, contract_terms, contract_clauses)
        
        Args:
            table: The table name to analyze ('vendor_contracts', 'contract_terms', 'contract_clauses')
            contract_id: The contract ID to analyze
            background: If True, run analysis in background task
            
        Returns:
            Dict with risk analysis results
        """
        try:
            logger.info(f"Starting {table} risk analysis for contract {contract_id}")
            
            # Validate table name
            valid_tables = ['vendor_contracts', 'contract_terms', 'contract_clauses']
            if table not in valid_tables:
                return {
                    'status': 'error',
                    'error': 'Invalid table',
                    'message': f'Table {table} not supported. Valid tables: {valid_tables}'
                }
            
            if background:
                # Run in background task
                task = generate_contract_table_risks_task.delay(table, contract_id)
                return {
                    'status': 'started',
                    'task_id': task.id,
                    'message': f'Risk analysis started in background for {table} contract {contract_id}'
                }
            else:
                # Run synchronously using the entity-data-row approach
                result = self.risk_service.analyze_entity_data_row(
                    entity='contract_module',
                    table=table,
                    row_id=str(contract_id)
                )
                
                # Add metadata
                result.update({
                    'status': 'completed',
                    'table': table,
                    'contract_id': contract_id,
                    'analysis_timestamp': timezone.now().isoformat(),
                    'message': f'Risk analysis completed for {table} contract {contract_id}'
                })
                
                logger.info(f"Completed {table} risk analysis for contract {contract_id}: {len(result.get('risks', []))} risks generated")
                return result
                
        except Exception as e:
            logger.error(f"Error in {table} risk analysis for contract {contract_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'message': f'Failed to analyze {table} for contract {contract_id}'
            }
    
    def get_contract_risk_summary(self, contract_id: str) -> Dict:
        """
        Get risk summary for a contract
        
        Args:
            contract_id: The contract ID
            
        Returns:
            Dict with risk summary statistics
        """
        try:
            from .models import Risk
            
            # Get risks for this contract
            risks = Risk.objects.filter(
                entity='contract_module',
                row=str(contract_id)
            )
            
            total_risks = risks.count()
            if total_risks == 0:
                return {
                    'contract_id': contract_id,
                    'total_risks': 0,
                    'risk_breakdown': {},
                    'average_score': 0,
                    'message': 'No risks found for this contract'
                }
            
            # Calculate risk breakdown
            risk_breakdown = {
                'Critical': risks.filter(priority='Critical').count(),
                'High': risks.filter(priority='High').count(),
                'Medium': risks.filter(priority='Medium').count(),
                'Low': risks.filter(priority='Low').count()
            }
            
            # Calculate average score
            from django.db.models import Avg
            avg_score = risks.aggregate(avg=Avg('score'))['avg'] or 0
            
            return {
                'contract_id': contract_id,
                'total_risks': total_risks,
                'risk_breakdown': risk_breakdown,
                'average_score': round(avg_score, 2),
                'highest_risk': risks.order_by('-score').first().title if risks.exists() else None,
                'message': f'Found {total_risks} risks for contract {contract_id}'
            }
            
        except Exception as e:
            logger.error(f"Error getting risk summary for contract {contract_id}: {str(e)}")
            return {
                'contract_id': contract_id,
                'error': str(e),
                'message': f'Failed to get risk summary for contract {contract_id}'
            }


# Background task functions are implemented in tasks.py and imported above

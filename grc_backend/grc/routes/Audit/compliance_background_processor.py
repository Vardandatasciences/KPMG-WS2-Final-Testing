"""
Background Processor for Compliance Checks
Processes requirements in parallel batches to avoid timeouts
"""
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from django.db import connection
from django.utils import timezone
from datetime import datetime

from .compliance_job_tracker import ComplianceJobTracker
from .ai_audit_api import (
    _process_single_requirement_batch,
    _determine_status,
    extract_text_from_document,
    save_ai_compliance_to_checklist,
    _compute_basic_signals
)

logger = logging.getLogger(__name__)


def process_compliance_check_background(
    job_id: str,
    audit_id: int,
    document_id: int,
    requirements: List[Dict],
    document_text: str,
    inferred_schema: Dict,
    audit_context: Dict,
    framework_id: int,
    tenant_id: int,
    user_id: int,
    doc_path: str,
    document_name: str,
    file_size: int,
    external_source: str,
    external_id: str,
    policy_id: int,
    subpolicy_id: int
):
    """
    Process compliance check in background with parallel batch processing
    
    Args:
        job_id: Job ID for tracking
        audit_id: Audit ID
        document_id: Document ID
        requirements: List of requirements to process
        document_text: Extracted document text
        inferred_schema: Schema if Excel
        audit_context: Audit context dict
        framework_id: Framework ID
        tenant_id: Tenant ID
        user_id: User ID
        doc_path: Document path
        document_name: Document name
        file_size: File size
        external_source: External source
        external_id: External ID
        policy_id: Policy ID
        subpolicy_id: Subpolicy ID
    """
    try:
        logger.info(f"🚀 Starting background compliance check job {job_id} for {len(requirements)} requirements")
        
        total_requirements = len(requirements)
        ComplianceJobTracker.update_progress(job_id, 0, 0, 0)
        
        # Process requirements in parallel batches
        BATCH_SIZE = 5  # Process 5 requirements in parallel
        MAX_WORKERS = 5  # Maximum parallel workers
        
        all_results = []
        processed_count = 0
        completed_count = 0
        failed_count = 0
        
        # Split requirements into batches
        batches = []
        for i in range(0, len(requirements), BATCH_SIZE):
            batch = requirements[i:i+BATCH_SIZE]
            batch_start_idx = i + 1
            batches.append((batch, batch_start_idx))
        
        logger.info(f"📦 Split {len(requirements)} requirements into {len(batches)} batches of {BATCH_SIZE}")
        
        # Process batches with parallel execution
        # Use try-except to handle interpreter shutdown gracefully
        use_parallel = True
        processed_batch_indices = set()
        executor = None
        shutdown_error_occurred = False
        
        # Try to create executor first - if this fails, we know we can't use parallel processing
        try:
            executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        except RuntimeError as create_err:
            if 'interpreter shutdown' in str(create_err).lower() or 'cannot schedule new futures' in str(create_err).lower():
                logger.warning(f"⚠️ Cannot create ThreadPoolExecutor (interpreter shutting down), using sequential batch processing")
                use_parallel = False
                executor = None
                shutdown_error_occurred = True
            else:
                raise
        
        if executor and not shutdown_error_occurred:
                try:
                    with executor:
                        # Submit all batches
                        future_to_batch = {}
                        for batch, batch_start_idx in batches:
                            try:
                                future = executor.submit(
                                    _process_batch_parallel,
                                    document_text,
                                    batch,
                                    batch_start_idx,
                                    audit_id,
                                    document_id,
                                    audit_context
                                )
                                future_to_batch[future] = (batch, batch_start_idx)
                            except RuntimeError as shutdown_err:
                                if 'interpreter shutdown' in str(shutdown_err).lower() or 'cannot schedule new futures' in str(shutdown_err).lower():
                                    logger.warning(f"⚠️ Interpreter shutting down during submit, switching to sequential processing")
                                    use_parallel = False
                                    shutdown_error_occurred = True
                                    break  # Exit the loop to process remaining batches sequentially
                                else:
                                    raise  # Re-raise if it's a different RuntimeError
                        
                        # Collect results as they complete (only if parallel processing succeeded)
                        if use_parallel and future_to_batch and not shutdown_error_occurred:
                            for future in as_completed(future_to_batch):
                                batch, batch_start_idx = future_to_batch[future]
                                try:
                                    batch_results = future.result()
                                    all_results.extend(batch_results)
                                    completed_count += len(batch_results)
                                    processed_count += len(batch)
                                    processed_batch_indices.add(batch_start_idx)
                                    
                                    # Update progress
                                    ComplianceJobTracker.update_progress(
                                        job_id,
                                        processed_count,
                                        completed_count,
                                        failed_count
                                    )
                                    
                                    logger.info(f"✅ Batch {batch_start_idx}-{batch_start_idx+len(batch)-1} completed: {len(batch_results)} results")
                                except Exception as e:
                                    failed_count += len(batch)
                                    processed_count += len(batch)
                                    logger.error(f"❌ Batch {batch_start_idx}-{batch_start_idx+len(batch)-1} failed: {e}")
                                    ComplianceJobTracker.update_progress(
                                        job_id,
                                        processed_count,
                                        completed_count,
                                        failed_count
                                    )
                except RuntimeError as shutdown_err:
                    if 'interpreter shutdown' in str(shutdown_err).lower() or 'cannot schedule new futures' in str(shutdown_err).lower():
                        logger.warning(f"⚠️ ThreadPoolExecutor failed due to interpreter shutdown, falling back to sequential processing")
                        use_parallel = False
                        shutdown_error_occurred = True
                    else:
                        raise
                finally:
                    # Always shutdown executor if it was created
                    if executor:
                        try:
                            executor.shutdown(wait=False)
                        except:
                            pass
        
        # Process remaining batches sequentially if parallel processing failed or was interrupted
        # Always process sequentially if shutdown error occurred or if not all batches were processed
        if shutdown_error_occurred or not use_parallel or processed_count < total_requirements:
            logger.info(f"🔄 Processing remaining batches sequentially (processed: {processed_count}/{total_requirements})")
            for batch, batch_start_idx in batches:
                if batch_start_idx in processed_batch_indices:
                    continue  # Skip already processed batches
                    
                try:
                    batch_results = _process_batch_parallel(
                        document_text,
                        batch,
                        batch_start_idx,
                        audit_id,
                        document_id,
                        audit_context
                    )
                    all_results.extend(batch_results)
                    completed_count += len(batch_results)
                    processed_count += len(batch)
                    
                    ComplianceJobTracker.update_progress(
                        job_id,
                        processed_count,
                        completed_count,
                        failed_count
                    )
                    
                    logger.info(f"✅ Batch {batch_start_idx}-{batch_start_idx+len(batch)-1} completed sequentially: {len(batch_results)} results")
                except Exception as e:
                    failed_count += len(batch)
                    processed_count += len(batch)
                    logger.error(f"❌ Batch {batch_start_idx}-{batch_start_idx+len(batch)-1} failed: {e}")
                    ComplianceJobTracker.update_progress(
                        job_id,
                        processed_count,
                        completed_count,
                        failed_count
                    )
        
        logger.info(f"✅ Background job {job_id} completed: {completed_count}/{total_requirements} requirements processed")
        
        # Determine overall status
        status_label, confidence = _determine_status(requirements, all_results)
        
        # Save results to database
        try:
            import json
            with connection.cursor() as cursor:
                # Update ai_audit_data with results
                where_clause = "WHERE audit_id = %s AND document_path = %s"
                where_params = [int(audit_id), doc_path]
                
                update_sql = f"""
                    UPDATE ai_audit_data 
                    SET ai_processing_status = 'completed',
                        compliance_status = %s,
                        confidence_score = %s,
                        compliance_analyses = %s,
                        processing_completed_at = NOW(),
                        FrameworkId = %s
                    {where_clause}
                """
                
                cursor.execute(
                    update_sql,
                    [
                        status_label,
                        float(confidence),
                        json.dumps({
                            "compliance_status": status_label,
                            "confidence_score": float(confidence),
                            "compliance_analyses": all_results,
                            "processed_at": timezone.now().isoformat(),
                        }),
                        framework_id,
                        *where_params,
                    ],
                )
                rows_updated = cursor.rowcount
                logger.info(f"✅ Updated {rows_updated} record(s) in ai_audit_data table")
            
            # Save to checklist
            save_ai_compliance_to_checklist(
                audit_id=audit_id,
                document_id=document_id,
                analyses=all_results,
                user_id=user_id,
                framework_id=framework_id,
                policy_id=policy_id,
                subpolicy_id=subpolicy_id,
                tenant_id=tenant_id
            )
            
            # Mark job as completed
            ComplianceJobTracker.complete_job(job_id, {
                'success': True,
                'analyses': all_results,
                'status': status_label,
                'confidence': confidence,
                'total_processed': completed_count,
                'total_failed': failed_count
            }, success=True)
            
        except Exception as save_err:
            logger.error(f"❌ Error saving results for job {job_id}: {save_err}")
            ComplianceJobTracker.fail_job(job_id, f"Error saving results: {str(save_err)}")
            
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        # Don't fail the job if it's just a shutdown error - sequential processing should handle it
        error_str = str(e).lower()
        if 'interpreter shutdown' in error_str or 'cannot schedule new futures' in error_str:
            logger.warning(f"⚠️ Background job {job_id} encountered shutdown error, but sequential processing should continue")
            # Don't fail the job - let sequential processing handle it
            return
        logger.error(f"❌ Background job {job_id} failed: {e}\n{error_traceback}")
        ComplianceJobTracker.fail_job(job_id, str(e))


def _process_batch_parallel(
    document_text: str,
    batch: List[Dict],
    batch_start_idx: int,
    audit_id: int,
    document_id: int,
    audit_context: Dict
) -> List[Dict]:
    """
    Process a batch of requirements in parallel
    
    Args:
        document_text: Document text
        batch: List of requirements in this batch
        batch_start_idx: Starting index for this batch
        audit_id: Audit ID
        document_id: Document ID
        audit_context: Audit context
        
    Returns:
        List of analysis results
    """
    results = []
    for i, req in enumerate(batch):
        global_idx = batch_start_idx + i
        try:
            batch_result = _process_single_requirement_batch(
                document_text,
                [req],
                global_idx,
                audit_id,
                document_id,
                audit_context=audit_context
            )
            results.extend(batch_result)
            logger.info(f"✅ Completed requirement {global_idx}")
        except Exception as e:
            logger.error(f"❌ Requirement {global_idx} failed: {e}")
            # Add a failed result
            results.append({
                'index': global_idx,
                'compliance_id': req.get('compliance_id'),
                'compliance_status': 'FAILED',
                'compliance_score': 0.0,
                'relevance': 0.0,
                'error': str(e)
            })
    return results

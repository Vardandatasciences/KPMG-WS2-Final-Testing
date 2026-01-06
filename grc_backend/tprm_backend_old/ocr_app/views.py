from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
import json
import logging
import tempfile
import os
from datetime import datetime

from .models import Document, OcrResult, ExtractedData
from .serializers import (
    DocumentSerializer, OcrResultSerializer, ExtractedDataSerializer,
    DocumentUploadSerializer, DocumentProcessingSerializer, SLAExtractionPayloadSerializer,
    BcpDrpOcrRunSerializer, BcpDrpExtractionPayloadSerializer
)
from .services import document_service

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentUploadView(APIView):
    """API view for document upload and processing"""
    
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    authentication_classes = []  # Disable authentication for API
    permission_classes = []  # Disable permission checks for API
    
    def post(self, request):
        """Upload and process document"""
        try:
            # Log request details for debugging
            logger.info(f"[INFO] Upload request received")
            logger.info(f"[INFO] Request method: {request.method}")
            logger.info(f"[INFO] Content type: {request.content_type}")
            logger.info(f"[INFO] Files: {list(request.FILES.keys())}")
            logger.info(f"[INFO] Data keys: {list(request.data.keys())}")
            logger.info(f"[INFO] POST keys: {list(request.POST.keys())}")
            
            # Handle file upload
            if 'file' not in request.FILES:
                logger.error("[ERROR] No file provided in request")
                logger.error(f"[ERROR] Available files: {list(request.FILES.keys())}")
                logger.error(f"[ERROR] Available data: {list(request.data.keys())}")
                return Response({
                    'success': False,
                    'error': 'No file provided. Please select a file to upload.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES['file']
            
            # Log file details
            logger.info(f"[INFO] File details - Name: {uploaded_file.name}, Size: {uploaded_file.size} bytes, Type: {uploaded_file.content_type}")
            
            # Validate file
            if uploaded_file.size > 50 * 1024 * 1024:  # 50MB limit
                logger.error(f"[ERROR] File too large: {uploaded_file.size} bytes")
                return Response({
                    'success': False,
                    'error': 'File too large. Maximum size is 50MB.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate file name
            if not uploaded_file.name or uploaded_file.name.strip() == '':
                logger.error("[ERROR] Empty file name")
                return Response({
                    'success': False,
                    'error': 'File name cannot be empty.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            try:
                # Create document record
                document_data = {
                    'Title': request.data.get('title', uploaded_file.name),
                    'Description': request.data.get('description', ''),
                    'OriginalFilename': uploaded_file.name,
                    'Category': request.data.get('category', ''),
                    'Department': request.data.get('department', ''),
                    'DocType': request.data.get('doc_type', uploaded_file.name.split('.')[-1].upper()),
                    'ModuleId': int(request.data.get('module_id', 1)),
                    'CreatedBy': request.user.id if request.user.is_authenticated else 1
                }
                
                document = Document.objects.create(**document_data)
                logger.info(f"[INFO] Created document record: {document.DocumentId}")
                
                # Choose processing mode based on request (inside try)
                user_id = f"user_{document_data['CreatedBy']}"
                mode = (request.data.get('mode') or request.POST.get('mode') or '').strip().lower()
                if mode == 'contract_only':
                    processing_result = document_service.process_contract_only(tmp_file_path, user_id)
                else:
                    processing_result = document_service.process_document(tmp_file_path, user_id)
                
                if not processing_result['success']:
                    # Update document status to indicate failure
                    document.Status = 'QUARANTINED'
                    document.save()
                    
                    return Response({
                        'success': False,
                        'error': processing_result['error'],
                        'document_id': document.DocumentId
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Save OCR results
                ocr_result = OcrResult.objects.create(
                    DocumentId=document.DocumentId,  # Pass integer ID
                    OcrText=processing_result['ocr_result']['text'],
                    OcrLanguage='en',
                    OcrConfidence=processing_result['ocr_result']['confidence'],
                    OcrEngine=processing_result['ocr_result']['engine'],
                    ocr_data={
                        'page_count': processing_result['ocr_result'].get('page_count', 1),
                        'processing_method': 'AI_Enhanced'
                    }
                )
                logger.info(f"[INFO] Created OCR result: {ocr_result.OcrResultId}")
                
                # Save extracted data if available
                extracted_data = None
                if processing_result['extraction_result']['success']:
                    extraction_data = processing_result['extraction_result']['data']
                    # Guard: Ensure extracted data is a dict (AI may return a list)
                    if isinstance(extraction_data, list):
                        try:
                            extraction_data = extraction_data[0] if extraction_data and isinstance(extraction_data[0], dict) else {}
                        except Exception:
                            extraction_data = {}
                    
                    # Convert string dates to date objects
                    effective_date = None
                    expiry_date = None
                    
                    try:
                        if extraction_data.get('effective_date'):
                            effective_date = datetime.strptime(extraction_data['effective_date'], '%Y-%m-%d').date()
                    except:
                        pass
                    
                    try:
                        if extraction_data.get('expiry_date'):
                            expiry_date = datetime.strptime(extraction_data['expiry_date'], '%Y-%m-%d').date()
                    except:
                        pass
                    
                    # Convert numeric fields
                    penalty_threshold = None
                    credit_threshold = None
                    compliance_score = None
                    
                    try:
                        if extraction_data.get('penalty_threshold'):
                            penalty_threshold = float(extraction_data['penalty_threshold'])
                    except:
                        pass
                    
                    try:
                        if extraction_data.get('credit_threshold'):
                            credit_threshold = float(extraction_data['credit_threshold'])
                    except:
                        pass
                    
                    try:
                        if extraction_data.get('compliance_score'):
                            compliance_score = float(extraction_data['compliance_score'])
                    except:
                        pass
                    
                    # Ensure reporting_frequency is not empty or None
                    reporting_freq = extraction_data.get('reporting_frequency', '') or 'monthly'
                    if not reporting_freq or reporting_freq.strip() == '':
                        reporting_freq = 'monthly'
                    
                    extracted_data = ExtractedData.objects.create(
                        DocumentId_id=document.DocumentId,  # Pass integer ID
                        OcrResultId_id=ocr_result.OcrResultId,  # Pass integer ID
                        sla_name=extraction_data.get('sla_name', ''),
                        vendor_id=extraction_data.get('vendor_id', ''),
                        contract_id=extraction_data.get('contract_id', ''),
                        sla_type=extraction_data.get('sla_type', ''),
                        effective_date=effective_date,
                        expiry_date=expiry_date,
                        status=extraction_data.get('status', 'PENDING'),
                        business_service_impacted=extraction_data.get('business_service_impacted', ''),
                        reporting_frequency=reporting_freq,
                        baseline_period=extraction_data.get('baseline_period', ''),
                        improvement_targets=extraction_data.get('improvement_targets', {}),
                        penalty_threshold=penalty_threshold,
                        credit_threshold=credit_threshold,
                        measurement_methodology=extraction_data.get('measurement_methodology', ''),
                        exclusions=extraction_data.get('exclusions', ''),
                        force_majeure_clauses=extraction_data.get('force_majeure_clauses', ''),
                        compliance_framework=extraction_data.get('compliance_framework', ''),
                        audit_requirements=extraction_data.get('audit_requirements', ''),
                        document_versioning=extraction_data.get('document_versioning', ''),
                        compliance_score=compliance_score,
                        priority=extraction_data.get('priority', ''),
                        approval_status=extraction_data.get('approval_status', 'PENDING'),
                        metrics=extraction_data.get('metrics', []),
                        raw_extracted_data=extraction_data,
                        extraction_confidence=processing_result['extraction_result'].get('confidence', 0.0),
                        extraction_method='AI_LLAMA'
                    )
                    logger.info(f"[INFO] Created extracted data: {extracted_data.ExtractedDataId}")
                
                # Update document with S3 URL
                if processing_result.get('upload_info'):
                    document.DocumentLink = processing_result['upload_info'].get('url', '')
                    document.save()
                
                # Prepare response
                response_data = {
                    'success': True,
                    'message': 'Document uploaded and processed successfully',
                    'document': DocumentSerializer(document).data,
                    'ocr_result': OcrResultSerializer(ocr_result).data,
                    'upload_info': processing_result.get('upload_info'),
                    'processing_info': {
                        'ocr_success': True,
                        'extraction_success': processing_result['extraction_result']['success'],
                        'extraction_confidence': processing_result['extraction_result'].get('confidence', 0.0)
                    }
                }
                
                # Include contract extraction payload for frontend auto-fill
                if isinstance(processing_result.get('data'), dict):
                    response_data['data'] = processing_result.get('data')
                else:
                    # Ensure field exists for frontend even when empty/failed
                    response_data['data'] = {}
                
                # Add full contract_extraction block for debugging/visibility
                if processing_result.get('contract_extraction') is not None:
                    response_data['contract_extraction'] = processing_result.get('contract_extraction')
                
                if extracted_data:
                    response_data['extracted_data'] = ExtractedDataSerializer(extracted_data).data
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
                
        except Exception as e:
            logger.error(f"[ERROR] Document upload error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentListView(APIView):
    """API view for listing documents"""
    
    authentication_classes = []  # Disable authentication for API
    permission_classes = []  # Disable permission checks for API
    
    def get(self, request):
        """Get list of documents"""
        try:
            documents = Document.objects.filter(Status='ACTIVE').order_by('-CreatedAt')
            serializer = DocumentSerializer(documents, many=True)
            
            return Response({
                'success': True,
                'documents': serializer.data,
                'count': documents.count()
            })
            
        except Exception as e:
            logger.error(f"[ERROR] Document list error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentDetailView(APIView):
    """API view for document details"""
    
    authentication_classes = []  # Disable authentication for API
    permission_classes = []  # Disable permission checks for API
    
    def get(self, request, document_id):
        """Get document details with OCR and extracted data"""
        try:
            try:
                document = Document.objects.get(DocumentId=document_id, Status='ACTIVE')
            except Document.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Document not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get OCR results
            ocr_results = OcrResult.objects.filter(DocumentId=document_id).order_by('-CreatedAt')
            ocr_serializer = OcrResultSerializer(ocr_results, many=True)
            
            # Get extracted data
            extracted_data = ExtractedData.objects.filter(DocumentId_id=document_id).order_by('-CreatedAt')
            extracted_serializer = ExtractedDataSerializer(extracted_data, many=True)
            
            response_data = {
                'success': True,
                'document': DocumentSerializer(document).data,
                'ocr_results': ocr_serializer.data,
                'extracted_data': extracted_serializer.data
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"[ERROR] Document detail error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class SLAExtractionView(APIView):
    """API view for SLA data extraction with payload headers"""
    
    authentication_classes = []  # Disable authentication for API
    permission_classes = []  # Disable permission checks for API
    
    def post(self, request):
        """Extract SLA data using provided payload headers and OCR text"""
        try:
            # Get document ID and payload headers
            document_id = request.data.get('document_id')
            payload_headers = request.data.get('payload_headers', {})
            
            if not document_id:
                return Response({
                    'success': False,
                    'error': 'Document ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not payload_headers:
                return Response({
                    'success': False,
                    'error': 'Payload headers are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the document and its OCR text
            try:
                document = Document.objects.get(DocumentId=document_id, Status='ACTIVE')
                ocr_result = OcrResult.objects.filter(DocumentId=document_id).first()
                
                if not ocr_result:
                    return Response({
                        'success': False,
                        'error': 'No OCR result found for this document'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                ocr_text = ocr_result.OcrText
                
            except Document.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Document not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Use AI service to extract SLA data with payload headers
            extraction_result = document_service.extract_sla_data_with_payload(ocr_text, payload_headers)
            
            if extraction_result['success']:
                # For now, just return the extracted data without saving to database
                # This avoids any database issues and focuses on the extraction
                logger.info(f"[INFO] SLA extraction successful for document {document_id}")
                
                return Response({
                    'success': True,
                    'extracted_data': extraction_result['data'],
                    'confidence': extraction_result.get('confidence', 0.0),
                    'message': 'SLA data extracted successfully using payload headers'
                })
            else:
                return Response({
                    'success': False,
                    'error': extraction_result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"[ERROR] SLA extraction error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(APIView):
    """Health check endpoint"""
    
    authentication_classes = []  # Disable authentication for API
    permission_classes = []  # Disable permission checks for API
    
    def get(self, request):
        """Check service health"""
        try:
            # Test S3 connection
            s3_status = "unknown"
            if document_service.s3_client:
                test_result = document_service.s3_client.test_connection()
                s3_status = "connected" if test_result.get('overall_success') else "failed"
            
            return Response({
                'status': 'healthy',
                'service': 'OCR Microservice',
                'version': '1.0.0',
                'components': {
                    'database': 'connected',
                    's3_service': s3_status,
                    'ai_service': 'available'
                },
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def index_view(request):
    """Main page view"""
    return render(request, 'index.html')


def upload_view(request):
    """Upload page view"""
    return render(request, 'upload.html')


def documents_view(request):
    """Documents listing page view"""
    return render(request, 'documents.html')


def document_detail_view(request, document_id):
    """Document detail page view"""
    return render(request, 'document_detail.html', {'document_id': document_id})


@csrf_exempt
def get_csrf_token(request):
    """Get CSRF token for debugging"""
    return JsonResponse({'csrfToken': get_token(request)})


@method_decorator(csrf_exempt, name='dispatch')
class BcpDrpOcrRunView(APIView):
    """API view for running OCR on BCP/DRP plans"""
    
    parser_classes = (JSONParser,)
    authentication_classes = []  # Disable authentication for API
    permission_classes = []  # Disable permission checks for API
    
    def post(self, request, plan_id):
        """Run OCR on a BCP/DRP plan document"""
        try:
            # Ensure plan_id is an integer
            try:
                plan_id = int(plan_id)
            except (ValueError, TypeError):
                logger.error(f"[ERROR] Invalid plan_id type: {plan_id}")
                return Response({
                    'success': False,
                    'error': f'Invalid plan_id: {plan_id}. Must be an integer.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"[INFO] BCP/DRP OCR run request for plan_id: {plan_id} (type: {type(plan_id).__name__})")
            
            # Get plan document from BCP/DRP database first
            try:
                # Import here to avoid circular imports - use full module path
                from tprm_backend.bcpdrp.models import Plan
                plan = Plan.objects.get(plan_id=plan_id)
                plan_type = plan.plan_type
                file_uri = plan.file_uri
                
                logger.info(f"[INFO] Found plan: {plan_id}, type: {plan_type}, file_uri: {file_uri}")
                
                if not file_uri or (isinstance(file_uri, str) and file_uri.strip() == ''):
                    logger.error(f"[ERROR] No file_uri found for plan {plan_id}")
                    return Response({
                        'success': False,
                        'error': f'No document file found for plan {plan_id}. Please ensure the plan has a file uploaded.'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                logger.info(f"[INFO] Processing {plan_type} plan {plan_id} with file: {file_uri}")
                
            except ImportError as e:
                logger.error(f"[ERROR] Failed to import Plan model: {e}", exc_info=True)
                return Response({
                    'success': False,
                    'error': f'Failed to import Plan model: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Plan.DoesNotExist:
                logger.error(f"[ERROR] Plan {plan_id} not found in database")
                return Response({
                    'success': False,
                    'error': f'Plan {plan_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"[ERROR] Error retrieving plan {plan_id}: {e}", exc_info=True)
                return Response({
                    'success': False,
                    'error': f'Error retrieving plan: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Validate request data (optional validation)
            try:
                serializer = BcpDrpOcrRunSerializer(data={
                    'plan_id': plan_id,
                    'plan_type': plan_type,
                    'file_uri': file_uri
                })
                
                if not serializer.is_valid():
                    logger.error(f"[ERROR] Invalid request data: {serializer.errors}")
                    return Response({
                        'success': False,
                        'error': 'Invalid request data',
                        'details': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"[ERROR] Serializer validation error: {e}", exc_info=True)
                return Response({
                    'success': False,
                    'error': f'Validation error: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process document with OCR and AI extraction
            try:
                logger.info(f"[INFO] Starting OCR processing for plan {plan_id}")
                # Run OCR and AI extraction
                result = document_service.process_bcp_drp_document(
                    plan_id=plan_id,
                    plan_type=plan_type,
                    file_uri=file_uri
                )
                
                logger.info(f"[INFO] OCR processing result: success={result.get('success')}")
                
                if result.get('success'):
                    logger.info(f"[SUCCESS] OCR processing completed for plan {plan_id}")
                    response_data = {
                        'success': True,
                        'data': {
                            'message': f'OCR processing completed for {plan_type} plan {plan_id}',
                            'extracted_data': result.get('extracted_data', {}),
                            'ocr_text': result.get('ocr_text', ''),
                            'confidence': result.get('confidence', 0.0)
                        },
                        'extracted_data': result.get('extracted_data', {})  # Also include at top level for frontend compatibility
                    }
                    logger.info(f"[DEBUG] Returning response data with extracted_data keys: {list(result.get('extracted_data', {}).keys())}")
                    return Response(response_data, content_type='application/json')
                else:
                    error_msg = result.get('error', 'OCR processing failed')
                    logger.error(f"[ERROR] OCR processing failed: {error_msg}")
                    return Response({
                        'success': False,
                        'error': error_msg
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as e:
                logger.error(f"[ERROR] OCR processing exception: {e}", exc_info=True)
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"[ERROR] Full traceback: {error_trace}")
                return Response({
                    'success': False,
                    'error': f'OCR processing failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"[ERROR] BCP/DRP OCR run exception: {e}", exc_info=True)
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"[ERROR] Full traceback: {error_trace}")
            return Response({
                'success': False,
                'error': f'Server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class BcpDrpExtractDataView(APIView):
    """API view for extracting data from BCP/DRP plans"""
    
    parser_classes = (JSONParser,)
    authentication_classes = []  # Disable authentication for API
    permission_classes = []  # Disable permission checks for API
    
    def post(self, request, plan_id):
        """Extract structured data from BCP/DRP plan"""
        try:
            logger.info(f"[INFO] BCP/DRP data extraction request for plan_id: {plan_id}")
            
            # Get extracted data from request
            extracted_data = request.data.get('extracted_data', {})
            
            if not extracted_data:
                return Response({
                    'success': False,
                    'error': 'No extracted data provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get plan type from BCP/DRP database
            try:
                from tprm_backend.bcpdrp.models import Plan
                plan = Plan.objects.get(plan_id=plan_id)
                plan_type = plan.plan_type
            except ImportError as e:
                logger.error(f"[ERROR] Failed to import Plan model: {e}", exc_info=True)
                return Response({
                    'success': False,
                    'error': f'Failed to import Plan model: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Plan.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Plan {plan_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Save extracted data to appropriate table
            try:
                if plan_type == 'BCP':
                    # Save to BCP extracted details table
                    from tprm_backend.bcpdrp.models import BcpDetails
                    bcp_data, created = BcpDetails.objects.update_or_create(
                        plan_id=plan_id,
                        defaults={
                            'purpose_scope': extracted_data.get('purpose_scope', ''),
                            'regulatory_references': extracted_data.get('regulatory_references', []),
                            'critical_services': extracted_data.get('critical_services', []),
                            'dependencies_internal': extracted_data.get('dependencies_internal', []),
                            'dependencies_external': extracted_data.get('dependencies_external', []),
                            'risk_assessment_summary': extracted_data.get('risk_assessment_summary', ''),
                            'bia_summary': extracted_data.get('bia_summary', ''),
                            'rto_targets': extracted_data.get('rto_targets', {}),
                            'rpo_targets': extracted_data.get('rpo_targets', {}),
                            'incident_types': extracted_data.get('incident_types', []),
                            'alternate_work_locations': extracted_data.get('alternate_work_locations', []),
                            'communication_plan_internal': extracted_data.get('communication_plan_internal', ''),
                            'communication_plan_bank': extracted_data.get('communication_plan_bank', ''),
                            'roles_responsibilities': extracted_data.get('roles_responsibilities', []),
                            'training_testing_schedule': extracted_data.get('training_testing_schedule', ''),
                            'maintenance_review_cycle': extracted_data.get('maintenance_review_cycle', ''),
                            'extractor_version': 'AI_LLAMA'
                        }
                    )
                    
                    # Update plan status
                    plan.ocr_extracted = True
                    plan.ocr_extracted_at = datetime.now()
                    plan.save()
                    
                    logger.info(f"[SUCCESS] BCP data saved for plan {plan_id}")
                    
                elif plan_type == 'DRP':
                    # Save to DRP extracted details table
                    from tprm_backend.bcpdrp.models import DrpDetails
                    drp_data, created = DrpDetails.objects.update_or_create(
                        plan_id=plan_id,
                        defaults={
                            'purpose_scope': extracted_data.get('purpose_scope', ''),
                            'regulatory_references': extracted_data.get('regulatory_references', []),
                            'critical_systems': extracted_data.get('critical_systems', []),
                            'critical_applications': extracted_data.get('critical_applications', []),
                            'databases_list': extracted_data.get('databases_list', []),
                            'supporting_infrastructure': extracted_data.get('supporting_infrastructure', []),
                            'third_party_services': extracted_data.get('third_party_services', []),
                            'rto_targets': extracted_data.get('rto_targets', {}),
                            'rpo_targets': extracted_data.get('rpo_targets', {}),
                            'disaster_scenarios': extracted_data.get('disaster_scenarios', []),
                            'disaster_declaration_process': extracted_data.get('disaster_declaration_process', ''),
                            'data_backup_strategy': extracted_data.get('data_backup_strategy', ''),
                            'recovery_site_details': extracted_data.get('recovery_site_details', ''),
                            'failover_procedures': extracted_data.get('failover_procedures', ''),
                            'failback_procedures': extracted_data.get('failback_procedures', ''),
                            'network_recovery_steps': extracted_data.get('network_recovery_steps', ''),
                            'application_restoration_order': extracted_data.get('application_restoration_order', []),
                            'testing_validation_schedule': extracted_data.get('testing_validation_schedule', ''),
                            'maintenance_review_cycle': extracted_data.get('maintenance_review_cycle', ''),
                            'extractor_version': 'AI_LLAMA'
                        }
                    )
                    
                    # Update plan status
                    plan.ocr_extracted = True
                    plan.ocr_extracted_at = datetime.now()
                    plan.save()
                    
                    logger.info(f"[SUCCESS] DRP data saved for plan {plan_id}")
                
                return Response({
                    'success': True,
                    'message': f'Extracted data saved successfully for {plan_type} plan {plan_id}',
                    'plan_type': plan_type,
                    'created': created
                })
                
            except Exception as e:
                logger.error(f"[ERROR] Failed to save extracted data: {e}")
                return Response({
                    'success': False,
                    'error': f'Failed to save extracted data: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"[ERROR] BCP/DRP data extraction error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class BcpDrpExtractedDataView(APIView):
    """API view for retrieving extracted BCP/DRP data"""
    
    authentication_classes = []  # Disable authentication for API
    permission_classes = []  # Disable permission checks for API
    
    def get(self, request, plan_id):
        """Get extracted data for a BCP/DRP plan"""
        try:
            logger.info(f"[INFO] Retrieving extracted data for plan_id: {plan_id}")
            
            # Get plan type from BCP/DRP database
            try:
                from tprm_backend.bcpdrp.models import Plan
                plan = Plan.objects.get(plan_id=plan_id)
                plan_type = plan.plan_type
            except ImportError as e:
                logger.error(f"[ERROR] Failed to import Plan model: {e}", exc_info=True)
                return Response({
                    'success': False,
                    'error': f'Failed to import Plan model: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Plan.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Plan {plan_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get extracted data from appropriate table
            try:
                if plan_type == 'BCP':
                    try:
                        from tprm_backend.bcpdrp.models import BcpDetails
                        bcp_data = BcpDetails.objects.get(plan_id=plan_id)
                        # Convert model instance to dictionary
                        extracted_data = {
                            'purpose_scope': bcp_data.purpose_scope,
                            'regulatory_references': bcp_data.regulatory_references,
                            'critical_services': bcp_data.critical_services,
                            'dependencies_internal': bcp_data.dependencies_internal,
                            'dependencies_external': bcp_data.dependencies_external,
                            'risk_assessment_summary': bcp_data.risk_assessment_summary,
                            'bia_summary': bcp_data.bia_summary,
                            'rto_targets': bcp_data.rto_targets,
                            'rpo_targets': bcp_data.rpo_targets,
                            'incident_types': bcp_data.incident_types,
                            'alternate_work_locations': bcp_data.alternate_work_locations,
                            'communication_plan_internal': bcp_data.communication_plan_internal,
                            'communication_plan_bank': bcp_data.communication_plan_bank,
                            'roles_responsibilities': bcp_data.roles_responsibilities,
                            'training_testing_schedule': bcp_data.training_testing_schedule,
                            'maintenance_review_cycle': bcp_data.maintenance_review_cycle,
                            'extracted_at': bcp_data.extracted_at,
                            'extractor_version': bcp_data.extractor_version
                        }
                        return Response({
                            'success': True,
                            'plan_type': plan_type,
                            'extracted_data': extracted_data
                        })
                    except BcpDetails.DoesNotExist:
                        return Response({
                            'success': False,
                            'error': f'No extracted data found for BCP plan {plan_id}'
                        }, status=status.HTTP_404_NOT_FOUND)
                        
                elif plan_type == 'DRP':
                    try:
                        from tprm_backend.bcpdrp.models import DrpDetails
                        drp_data = DrpDetails.objects.get(plan_id=plan_id)
                        # Convert model instance to dictionary
                        extracted_data = {
                            'purpose_scope': drp_data.purpose_scope,
                            'regulatory_references': drp_data.regulatory_references,
                            'critical_systems': drp_data.critical_systems,
                            'critical_applications': drp_data.critical_applications,
                            'databases_list': drp_data.databases_list,
                            'supporting_infrastructure': drp_data.supporting_infrastructure,
                            'third_party_services': drp_data.third_party_services,
                            'rto_targets': drp_data.rto_targets,
                            'rpo_targets': drp_data.rpo_targets,
                            'disaster_scenarios': drp_data.disaster_scenarios,
                            'disaster_declaration_process': drp_data.disaster_declaration_process,
                            'data_backup_strategy': drp_data.data_backup_strategy,
                            'recovery_site_details': drp_data.recovery_site_details,
                            'failover_procedures': drp_data.failover_procedures,
                            'failback_procedures': drp_data.failback_procedures,
                            'network_recovery_steps': drp_data.network_recovery_steps,
                            'application_restoration_order': drp_data.application_restoration_order,
                            'testing_validation_schedule': drp_data.testing_validation_schedule,
                            'maintenance_review_cycle': drp_data.maintenance_review_cycle,
                            'extracted_at': drp_data.extracted_at,
                            'extractor_version': drp_data.extractor_version
                        }
                        return Response({
                            'success': True,
                            'plan_type': plan_type,
                            'extracted_data': extracted_data
                        })
                    except DrpDetails.DoesNotExist:
                        return Response({
                            'success': False,
                            'error': f'No extracted data found for DRP plan {plan_id}'
                        }, status=status.HTTP_404_NOT_FOUND)
                
                else:
                    return Response({
                        'success': False,
                        'error': f'Invalid plan type: {plan_type}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                logger.error(f"[ERROR] Failed to retrieve extracted data: {e}")
                return Response({
                    'success': False,
                    'error': f'Failed to retrieve extracted data: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"[ERROR] BCP/DRP extracted data retrieval error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



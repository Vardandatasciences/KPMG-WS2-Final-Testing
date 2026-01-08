from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.middleware.csrf import get_token
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
import json
import logging
import tempfile
import os
import traceback
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
                        reporting_frequency=extraction_data.get('reporting_frequency', 'monthly'),
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
                'timestamp': (timezone.now() if settings.USE_TZ else datetime.now()).isoformat()
            })
            
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': (timezone.now() if settings.USE_TZ else datetime.now()).isoformat()
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
            logger.info(f"[INFO] BCP/DRP OCR run request for plan_id: {plan_id}")
            
            # MULTI-TENANCY: Get tenant_id from request
            try:
                from tprm_backend.core.tenant_utils import get_tenant_id_from_request
                tenant_id = get_tenant_id_from_request(request)
                if tenant_id:
                    logger.info(f"[INFO] Using tenant_id: {tenant_id} for plan {plan_id}")
            except Exception as tenant_error:
                logger.warning(f"[WARNING] Could not get tenant_id: {tenant_error}")
                tenant_id = None
            
            # Get plan document from BCP/DRP database first
            try:
                # Import here to avoid circular imports
                from tprm_backend.bcpdrp.models import Plan
                
                # MULTI-TENANCY: Filter by tenant if available
                # Try with tenant_id first, then fallback to without tenant_id
                plan = None
                try:
                    if tenant_id:
                        try:
                            plan = Plan.objects.get(plan_id=plan_id, tenant_id=tenant_id)
                            logger.info(f"[INFO] Found plan {plan_id} with tenant_id {tenant_id}")
                        except (Plan.DoesNotExist, Exception) as tenant_error:
                            # If tenant_id field doesn't exist or plan not found, try without tenant
                            logger.warning(f"[WARNING] Could not get plan with tenant_id: {tenant_error}, trying without tenant filter")
                            plan = Plan.objects.get(plan_id=plan_id)
                            logger.info(f"[INFO] Found plan {plan_id} without tenant filter (fallback)")
                    else:
                        plan = Plan.objects.get(plan_id=plan_id)
                        logger.info(f"[INFO] Found plan {plan_id} without tenant filter")
                except Plan.DoesNotExist:
                    raise
                
                plan_type = plan.plan_type
                # ENCRYPTION: file_uri is encrypted, use _plain property to get decrypted value
                # The TPRMEncryptedFieldsMixin automatically provides _plain properties via __getattribute__
                try:
                    # Access decrypted file_uri using _plain property
                    file_uri = plan.file_uri_plain
                    logger.info(f"[INFO] Retrieved decrypted file_uri for plan {plan_id}")
                except Exception as decrypt_error:
                    logger.warning(f"[WARNING] Error accessing file_uri_plain: {decrypt_error}")
                    # Fallback: try _get_decrypted_value method
                    try:
                        file_uri = plan._get_decrypted_value('file_uri')
                        logger.info(f"[INFO] Retrieved decrypted file_uri using _get_decrypted_value method")
                    except Exception as decrypt_error2:
                        logger.error(f"[ERROR] Could not decrypt file_uri: {decrypt_error2}")
                        # Last resort: use direct access (might work if field is not actually encrypted)
                        file_uri = plan.file_uri
                        logger.warning(f"[WARNING] Using encrypted file_uri value (may cause issues)")
                
                logger.info(f"[INFO] File URI for plan {plan_id}: {file_uri[:100] if file_uri else 'None'}...")
                
                if not file_uri:
                    logger.error(f"[ERROR] Plan {plan_id} has no file_uri")
                    return Response({
                        'success': False,
                        'error': f'No document file found for plan {plan_id}'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                logger.info(f"[INFO] Processing {plan_type} plan {plan_id} with file: {file_uri}")
                
            except Plan.DoesNotExist:
                logger.error(f"[ERROR] Plan {plan_id} not found")
                return Response({
                    'success': False,
                    'error': f'Plan {plan_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as import_error:
                logger.error(f"[ERROR] Error accessing Plan model: {import_error}")
                logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
                return Response({
                    'success': False,
                    'error': f'Error accessing plan data: {str(import_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Validate request data (optional validation)
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
            
            # Process document with OCR and AI extraction
            try:
                # Run OCR and AI extraction
                result = document_service.process_bcp_drp_document(
                    plan_id=plan_id,
                    plan_type=plan_type,
                    file_uri=file_uri
                )
                
                if result['success']:
                    logger.info(f"[SUCCESS] OCR processing completed for plan {plan_id}")
                    response_data = {
                        'success': True,
                        'data': {
                            'message': f'OCR processing completed for {plan_type} plan {plan_id}',
                            'extracted_data': result.get('extracted_data', {}),
                            'ocr_text': result.get('ocr_text', ''),
                            'confidence': result.get('confidence', 0.0)
                        }
                    }
                    logger.info(f"[DEBUG] Returning response data: {response_data}")
                    return Response(response_data, content_type='application/json')
                else:
                    logger.error(f"[ERROR] OCR processing failed: {result.get('error')}")
                    return Response({
                        'success': False,
                        'error': result.get('error', 'OCR processing failed')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as e:
                logger.error(f"[ERROR] OCR processing error: {e}")
                logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
                return Response({
                    'success': False,
                    'error': f'OCR processing failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"[ERROR] BCP/DRP OCR run error: {e}")
            logger.error(f"[ERROR] Traceback: {error_traceback}")
            # Include error details in response for debugging (only in DEBUG mode)
            error_message = str(e)
            try:
                from django.conf import settings as django_settings
                if django_settings.DEBUG:
                    error_message = f"{error_message}\n\nTraceback:\n{error_traceback}"
            except:
                pass
            return Response({
                'success': False,
                'error': error_message
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
            except Plan.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Plan {plan_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Save extracted data to ocr_extracted_data field (unified for all plan types)
            try:
                # Helper function to check if a value is empty/null
                def is_empty_value(val):
                    if val is None:
                        return True
                    if isinstance(val, str) and val.strip() == '':
                        return True
                    if isinstance(val, list) and len(val) == 0:
                        return True
                    if isinstance(val, dict) and len(val) == 0:
                        return True
                    return False
                
                # Prepare unified data structure - include all fields from extracted_data (including custom fields)
                # Only include fields that have non-empty values
                unified_data = {'plan_id': plan_id}
                
                # Process all fields from extracted_data (including custom fields)
                for key, value in extracted_data.items():
                    # Skip plan_id as it's already set
                    if key == 'plan_id':
                        continue
                    
                    # Only add non-empty values
                    if not is_empty_value(value):
                        unified_data[key] = value
                
                logger.info(f"[INFO] Saving {len(unified_data) - 1} non-empty fields for plan {plan_id} (including custom fields)")
                
                # Check if data already exists
                created = plan.ocr_extracted_data is None or not plan.ocr_extracted_data
                
                # Save to ocr_extracted_data field
                plan.ocr_extracted_data = unified_data
                plan.ocr_extracted = True
                if not plan.ocr_extracted_at:
                    # Get current datetime based on USE_TZ setting
                    if settings.USE_TZ:
                        plan.ocr_extracted_at = timezone.now()
                    else:
                        plan.ocr_extracted_at = datetime.now()
                plan.save()
                
                logger.info(f"[SUCCESS] Unified extracted data saved for {plan_type} plan {plan_id}")
                
                # Generate risks after OCR data is saved (background task)
                task_info = None
                try:
                    logger.info(f"[INFO] Triggering background comprehensive risk generation for OCR completed plan {plan_id}")
                    
                    # Import the background task
                    from risk_analysis.tasks import generate_comprehensive_risks_task
                    
                    # Start background task - analyze plan with extracted OCR data (no evaluation yet)
                    task = generate_comprehensive_risks_task.delay(
                        plan_id=plan_id,
                        evaluation_id=None  # No evaluation at OCR stage, only plan + extracted details
                    )
                    
                    task_info = {
                        'task_id': task.id,
                        'status': 'started',
                        'message': 'Comprehensive risk generation started in background'
                    }
                    
                    logger.info(f"[SUCCESS] Started background risk generation task {task.id} for OCR completed plan {plan_id}")
                    
                except Exception as task_error:
                    logger.warning(f"[WARNING] Background task system not available, will generate risks after response: {task_error}")
                    
                    # Instead of blocking, we'll generate risks after sending the response
                    task_info = {
                        'task_id': 'deferred',
                        'status': 'deferred',
                        'message': 'Risk generation will start after OCR save completes'
                    }
                
                response_data = {
                    'success': True,
                    'message': f'Extracted data saved successfully for {plan_type} plan {plan_id}',
                    'plan_type': plan_type,
                    'created': created
                }
                
                # Include background task info in response
                if task_info:
                    response_data['risk_generation'] = task_info
                    if task_info['status'] == 'deferred':
                        response_data['risk_message'] = "OCR data saved! Comprehensive risk generation will start shortly - check Risk Analytics in a few minutes"
                    else:
                        response_data['risk_message'] = "Comprehensive risk generation started in background - risks will appear in Risk Analytics shortly"
                
                # Create response
                response = Response(response_data)
                
                # Start deferred risk generation after response (if needed)
                if task_info and task_info['status'] == 'deferred':
                    import threading
                    
                    def deferred_ocr_risk_generation():
                        try:
                            logger.info(f"[INFO] Starting deferred risk generation for OCR completed plan {plan_id}")
                            from bcpdrp.views import generate_risks_for_plan_evaluation
                            sync_result = generate_risks_for_plan_evaluation(
                                plan_id=plan_id,
                                evaluation_id=None  # No evaluation at OCR stage
                            )
                            if sync_result:
                                logger.info(f"[SUCCESS] Deferred OCR risk generation completed: {len(sync_result.get('risks', []))} risks created")
                            else:
                                logger.error("[ERROR] Deferred OCR risk generation failed")
                        except Exception as e:
                            logger.error(f"[ERROR] Error in deferred OCR risk generation: {str(e)}")
                    
                    # Start the risk generation in a separate thread
                    thread = threading.Thread(target=deferred_ocr_risk_generation)
                    thread.daemon = True  # Thread will die when main process dies
                    thread.start()
                    logger.info(f"[INFO] Started deferred OCR risk generation thread for plan {plan_id}")
                
                return response
                
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
            except Plan.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Plan {plan_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get extracted data from ocr_extracted_data field (unified for all plan types)
            try:
                if plan.ocr_extracted_data:
                    extracted_data = plan.ocr_extracted_data.copy()
                    # Add metadata
                    extracted_data['extracted_at'] = plan.ocr_extracted_at.isoformat() if plan.ocr_extracted_at else None
                    extracted_data['extractor_version'] = 'AI_LLAMA'
                    
                    return Response({
                        'success': True,
                        'plan_type': plan_type,
                        'extracted_data': extracted_data
                    })
                else:
                    return Response({
                        'success': False,
                        'error': f'No extracted data found for plan {plan_id}'
                    }, status=status.HTTP_404_NOT_FOUND)
                    
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



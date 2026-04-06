from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect as csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import os
import shutil
import time
import threading
from pathlib import Path

# Phase 3 Optimizations - Rate limiting and queuing
from ...utils.request_queue import (
    rate_limit_decorator,
    process_with_queue,
    get_queue_status
)
from ...utils.model_router import (
    track_system_load,
    get_current_system_load
)

# Import the processing modules
# COMMENTED OUT OLD IMPORT - Using new AI upload API
# from ..uploadNist.all_integrated_upload import upload_pdf_and_extract_complete
from ..uploadNist import ai_upload
from ..uploadNist import pdf_index_extractor
from ..uploadNist import index_content_extractor
from ..uploadNist import policy_extractor_enhanced
from ..Policy import policy_ai_service as centralized_policy_ai
from ...utils.file_compression import decompress_if_needed
from ...routes.Global.s3_fucntions import create_direct_mysql_client
from datetime import datetime
from ...debug_utils import debug_print
from ...utils.safe_paths import (
    safe_join,
    require_safe_user_key,
    require_safe_rel_segment,
    safe_upload_filename,
    UnsafePathError,
)

# Global progress tracking
processing_status = {}

def update_progress(task_id, progress, message):
    """Update processing progress (keeps existing keys like result)."""
    existing = processing_status.get(task_id, {})
    processing_status[task_id] = {
        **existing,
        'progress': progress,
        'message': message,
        'timestamp': time.time()
    }

def create_user_folder(userid):
    """
    Creates a folder with the name 'upload_userid' where userid is the provided user ID.
    If folder exists, tries to delete it and creates a new one.
    Handles OneDrive sync issues with retry logic.
    
    Args:
        userid (str): The user ID to create the folder for
        
    Returns:
        str: The path of the created folder
        
    Raises:
        OSError: If there's an error creating the folder after retries
    """
    key = require_safe_user_key(userid)
    folder_name = f"upload_{key}"
    folder_path = safe_join(settings.MEDIA_ROOT, folder_name)
    
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            # Delete folder if it exists (with retry logic for OneDrive sync issues)
            if os.path.exists(folder_path):
                try:
                    shutil.rmtree(folder_path)
                    debug_print(f"Deleted existing folder: {folder_path}")
                    # Small delay after deletion to let OneDrive sync
                    time.sleep(0.5)
                except (OSError, PermissionError) as delete_error:
                    if attempt < max_retries - 1:
                        debug_print(f"Warning: Could not delete folder (attempt {attempt + 1}/{max_retries}): {delete_error}")
                        debug_print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        # If we can't delete, try to use existing folder or clear contents
                        debug_print(f"Warning: Could not delete folder after {max_retries} attempts. Trying to clear contents instead...")
                        try:
                            # Clear folder contents instead of deleting
                            for item in os.listdir(folder_path):
                                item_path = safe_join(folder_path, item)
                                if os.path.isdir(item_path):
                                    shutil.rmtree(item_path, ignore_errors=True)
                                else:
                                    try:
                                        os.remove(item_path)
                                    except (OSError, PermissionError):
                                        pass
                            debug_print(f"Cleared contents of existing folder: {folder_path}")
                        except Exception as clear_error:
                            debug_print(f"Warning: Could not clear folder contents: {clear_error}")
                            # Continue anyway - will try to create/use existing folder
            
            # Create the new folder (or ensure it exists)
            os.makedirs(folder_path, exist_ok=True)
            debug_print(f"Created/verified folder: {folder_path}")
            
            return folder_path
            
        except (OSError, PermissionError) as e:
            if attempt < max_retries - 1:
                debug_print(f"Error creating folder '{folder_name}' (attempt {attempt + 1}/{max_retries}): {e}")
                debug_print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                debug_print(f"Error creating folder '{folder_name}' after {max_retries} attempts: {e}")
                raise OSError(f"Failed to create folder '{folder_name}' after {max_retries} attempts. "
                            f"This may be due to OneDrive sync locking the folder. "
                            f"Original error: {e}")
    
    # Should not reach here, but just in case
    raise OSError(f"Failed to create folder '{folder_name}'")

def save_uploaded_file(uploaded_file, user_folder):
    """
    Save the uploaded file to the user's folder.
    
    Args:
        uploaded_file: The uploaded file object
        user_folder (str): Path to the user's folder
        
    Returns:
        str: Path to the saved file
    """
    try:
        file_path = safe_join(user_folder, safe_upload_filename(uploaded_file.name))
        
        # Save the file
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        debug_print(f"File saved successfully to: {file_path}")
        return file_path
        
    except Exception as e:
        debug_print(f"Error saving file: {e}")
        raise

def process_document_background(userid, file_path, task_id):
    """
    Background processing function using NEW AI upload pipeline (Phase 1, 2, 3 optimized).
    
    Args:
        userid (str): The user ID
        file_path (str): Path to the uploaded file
        task_id (str): Task ID for progress tracking
    """
    start_time = time.time()
    
    def _do_processing():
        try:
            update_progress(task_id, 10, "Starting document processing...")
            
            media_root = ai_upload.get_media_root()
            user_key = require_safe_user_key(userid)
            user_folder = Path(safe_join(str(media_root), f"upload_{user_key}"))
            pdf_path = Path(file_path)
            pdf_name = pdf_path.stem
            
            # Step 1: Extract Index
            update_progress(task_id, 30, "Extracting PDF index...")
            debug_print(f"[STEP 1] Extracting index from {file_path}...")
            
            index_json_path = user_folder / f"{pdf_name}_index.json"
            try:
                index_data = pdf_index_extractor.extract_and_save_index(
                    pdf_path=str(file_path),
                    output_path=str(index_json_path),
                    prefer_toc=True
                )
                index_items_count = len(index_data.get('items', []))
                debug_print(f"[SUCCESS] Extracted {index_items_count} index items")
                update_progress(task_id, 40, f"Index extracted: {index_items_count} items")
            except Exception as e:
                update_progress(task_id, 100, f"Index extraction failed: {str(e)}")
                return False
            
            # Step 2: Extract Sections (index-based or no-index path)
            update_progress(task_id, 45, "Extracting sections and creating PDFs...")
            debug_print(f"[STEP 2] Extracting sections...")
            
            sections_dir = user_folder / f"sections_{pdf_name}"
            try:
                if index_items_count == 0 or index_data.get('extraction_method') == 'none_found':
                    # Document has no index/TOC (e.g. 1-2 pages of content only): treat whole PDF as one section
                    debug_print(f"[INFO] No index found – processing document as single section (no-index path)")
                    update_progress(task_id, 50, "No index: processing full document as one section...")
                    manifest = index_content_extractor.process_pdf_as_single_section(
                        pdf_path=str(file_path),
                        output_dir=str(sections_dir),
                        section_title=pdf_name or "Document content",
                        verbose=True
                    )
                else:
                    manifest = index_content_extractor.process_pdf_sections(
                        pdf_path=str(file_path),
                        index_json_path=str(index_json_path),
                        output_dir=str(sections_dir),
                        verbose=True
                    )
                sections_count = len(manifest.get('sections_written', []))
                debug_print(f"[SUCCESS] Extracted {sections_count} sections")
                update_progress(task_id, 60, f"Sections extracted: {sections_count} sections")
            except Exception as e:
                err_msg = f"Section extraction failed: {str(e)}"
                debug_print(f"[ERROR] {err_msg}")
                processing_status[task_id]["result"] = {"status": "failed", "error": err_msg}
                update_progress(task_id, 100, err_msg)
                return False
            
            # Step 3: Extract Policies (Phase 1, 2, 3 optimized)
            update_progress(task_id, 65, "Extracting policies using AI (Phase 1, 2, 3 optimized)...")
            debug_print(f"[STEP 3] Extracting policies with Phase 1, 2, 3 optimizations...")
            
            policies_dir = user_folder / f"policies_{pdf_name}"
            try:
                policy_results = policy_extractor_enhanced.extract_policies(
                    sections_dir=str(sections_dir),
                    output_dir=str(policies_dir),
                    verbose=True
                )
                
                if not policy_results.get('success'):
                    raise Exception(policy_results.get('error', 'Policy extraction failed'))
                
                total_policies = policy_results['summary']['extraction_summary']['total_policies']
                total_subpolicies = policy_results['summary']['extraction_summary']['total_subpolicies']
                
                debug_print(f"[SUCCESS] Extracted {total_policies} policies, {total_subpolicies} subpolicies")
                # Even if 0 policies were extracted, mark as successful so UI can advance
                update_progress(task_id, 95, f"Policies extracted: {total_policies} policies")
                
                # Phase 3: Track system load
                processing_time = time.time() - start_time
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                track_system_load(processing_time, file_size)
                
                # Create framework_data.json so get_sections_by_user has data when frontend loads step 3
                try:
                    from .consolidate_data import create_consolidated_json
                    create_consolidated_json(str(userid))
                except Exception as cons_err:
                    debug_print(f"[WARNING] Could not create consolidated JSON: {cons_err}")
                
                # Store final result
                processing_status[task_id]["result"] = {
                    "status": "success",
                    "data": {
                        'user_folder': f"upload_{userid}",
                        'index_items': index_items_count,
                        'sections': sections_count,
                        'policies': total_policies,
                        'subpolicies': total_subpolicies,
                        'phase3_metadata': {
                            'processing_time': processing_time,
                            'system_load': get_current_system_load(),
                            'model_routing': 'enabled'
                        }
                    }
                }
                
                update_progress(task_id, 100, "Document processing completed successfully!")
                return True
                
            except Exception as e:
                err_msg = f"Policy extraction failed: {str(e)}"
                debug_print(f"[ERROR] {err_msg}")
                processing_status[task_id]["result"] = {"status": "failed", "error": err_msg}
                update_progress(task_id, 100, err_msg)
                return False
                
        except Exception as e:
            err_msg = f"Error during processing: {str(e)}"
            debug_print(f"[ERROR] {err_msg}")
            processing_status[task_id]["result"] = {"status": "failed", "error": err_msg}
            update_progress(task_id, 100, err_msg)
            return False
    
    # Phase 3: Use queuing for large files
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    if file_size > 10 * 1024 * 1024:  # 10MB threshold
        debug_print(f"📋 Large file detected ({file_size / 1024 / 1024:.2f}MB), using Phase 3 queuing...")
        return process_with_queue(task_id, _do_processing)
    else:
        return _do_processing()

@csrf_exempt
@require_http_methods(["POST"])
@rate_limit_decorator(requests_per_minute=5, requests_per_hour=50)  # Phase 3: Rate limiting
def upload_framework_file(request):
    """
    Main upload endpoint that handles file upload and starts processing.
    
    Expected request:
    - file: The uploaded file
    - userid: The user ID (optional, defaults to 'default')
    """
    try:
        # Check if file is provided
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Get user ID from request, default to 'default' if not provided
        userid = request.POST.get('userid', 'default')
        
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.xls']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # Generate task ID for progress tracking
        task_id = f"upload_{int(time.time())}_{uploaded_file.name}"
        
        # Step 1: Create user folder (delete if exists, create new)
        try:
            user_folder = create_user_folder(userid)
        except UnsafePathError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Failed to create user folder: {str(e)}'}, status=500)
        
        try:
            file_path = save_uploaded_file(uploaded_file, user_folder)
        except UnsafePathError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Failed to save uploaded file: {str(e)}'}, status=500)
        
        # Step 2.5: Decompress if needed (client-side compression)
        compression_metadata = None
        try:
            file_path, was_compressed, compression_stats = decompress_if_needed(file_path)
            if was_compressed:
                compression_metadata = compression_stats
                file_extension = os.path.splitext(file_path)[1].lower()
                debug_print(f"📦 Decompressed file: {compression_stats['ratio']}% reduction, saved {compression_stats['bandwidth_saved_kb']} KB")
        except Exception as e:
            debug_print(f"⚠️ Decompression error (continuing): {str(e)}")
        
        # Step 2.6: Upload to S3 for backup and cloud storage
        s3_url = None
        s3_key = None
        try:
            debug_print(f"☁️ Uploading file to S3...")
            s3_client = create_direct_mysql_client()
            connection_test = s3_client.test_connection()
            if connection_test.get('overall_success', False):
                # Generate unique filename for S3
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                s3_filename = f"framework_{timestamp}_{os.path.basename(file_path)}"
                upload_result = s3_client.upload(
                    file_path=file_path,
                    user_id=userid,
                    custom_file_name=s3_filename,
                    module='Framework'
                )
                if upload_result.get('success'):
                    s3_url = upload_result['file_info']['url']
                    s3_key = upload_result['file_info'].get('s3Key', '')
                    debug_print(f"✅ File uploaded to S3: {s3_url}")
                else:
                    debug_print(f"⚠️ S3 upload failed: {upload_result.get('error', 'Unknown error')}")
            else:
                debug_print(f"⚠️ S3 service unavailable, continuing with local file")
        except Exception as s3_error:
            debug_print(f"⚠️ S3 upload error (continuing with local file): {str(s3_error)}")
        
        # Step 3: Start background processing
        update_progress(task_id, 5, "File uploaded successfully. Starting processing...")
        
        # Start processing in background thread
        thread = threading.Thread(
            target=process_document_background,
            args=(userid, file_path, task_id)
        )
        thread.daemon = True
        thread.start()
        
        response_data = {
            'message': 'File uploaded successfully. Processing started.',
            'filename': uploaded_file.name,
            'file_path': file_path,
            'file_size': uploaded_file.size,
            'task_id': task_id,
            'processing': True,
            'file_type': file_extension,
            'user_folder': user_folder
        }
        
        # Include compression metadata if file was compressed
        if compression_metadata:
            response_data['compression_metadata'] = compression_metadata
        
        # Include S3 info if uploaded successfully
        if s3_url:
            response_data['s3_url'] = s3_url
            response_data['s3_key'] = s3_key
        
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_processing_status(request, task_id):
    """
    Get processing status for a task.
    
    Args:
        request: Django request object
        task_id (str): Task ID to get status for
    """
    try:
        if task_id in processing_status:
            status_data = processing_status[task_id]
            return JsonResponse({
                'task_id': task_id,
                'progress': status_data.get('progress', 0),
                'message': status_data.get('message', ''),
                'timestamp': status_data.get('timestamp', 0),
                'result': status_data.get('result', None)
            })
        else:
            return JsonResponse({
                'error': 'Task not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_sections(request, task_id):
    """
    Get extracted sections for a task.
    
    Args:
        request: Django request object
        task_id (str): Task ID to get sections for
    """
    try:
        if task_id not in processing_status:
            return JsonResponse({'error': 'Task not found'}, status=404)
        
        status_data = processing_status[task_id]
        result = status_data.get('result')
        
        if not result or result.get('status') != 'success':
            return JsonResponse({'error': 'Processing not completed or failed'}, status=400)
        
        # Extract sections from the result
        sections = []
        
        # If we have extracted sections directory
        if 'extracted_sections_dir' in result:
            sections_dir = result['extracted_sections_dir']
            if os.path.exists(sections_dir):
                # Read sections from the directory structure
                sections = read_sections_from_directory(sections_dir)
        
        return JsonResponse({
            'task_id': task_id,
            'sections': sections
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_sections_by_user(request, userid):
    """
    Get extracted sections with policies and subpolicies for a specific user.
    NOW READS FROM: upload_1/framework_data.json (consolidated JSON file)
    
    Args:
        request: Django request object
        userid (str): User ID to get sections for
    """
    try:
        debug_print(f"[INFO] Getting sections for user: {userid}")
        try:
            require_safe_user_key(userid)
        except UnsafePathError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

        # Import the consolidate_data module
        from .consolidate_data import load_consolidated_json

        # Load consolidated JSON (will create if doesn't exist)
        data = load_consolidated_json(userid)
        
        # If we have data but no policy/subpolicy has ai_analysis, regenerate from all_policies.json to pick up AI fields
        if data:
            sections_list = data.get('sections', [])
            has_any_ai = False
            for sec in sections_list:
                for pol in sec.get('policies', []):
                    if pol.get('ai_analysis'):
                        has_any_ai = True
                        break
                    for sp in pol.get('subpolicies', []):
                        if sp.get('ai_analysis'):
                            has_any_ai = True
                            break
            if sections_list and not has_any_ai:
                try:
                    from .consolidate_data import create_consolidated_json
                    data = create_consolidated_json(userid)
                    debug_print(f"[INFO] Regenerated consolidated data to include ai_analysis")
                except Exception as e:
                    debug_print(f"[WARNING] Could not regenerate consolidated JSON: {e}")
        
        if not data:
            # Fallback: Check if we have basic files and return minimal data
            debug_print(f"[WARNING] No consolidated data found, checking for basic files...")
            user_folder = safe_join(settings.MEDIA_ROOT, f"upload_{require_safe_user_key(userid)}")
            
            if os.path.exists(user_folder):
                # Check if we have at least the PDF and index file
                pdf_files = [f for f in os.listdir(user_folder) if f.endswith('.pdf')]
                json_files = [f for f in os.listdir(user_folder) if f.endswith('.json')]
                
                if pdf_files and json_files:
                    debug_print(f"[INFO] Found basic files, returning minimal response")
                    return JsonResponse({
                        'success': True,
                        'task_id': f"upload_{userid}",
                        'framework_name': 'Uploaded Framework',
                        'framework_info': {'framework_name': 'Uploaded Framework'},
                        'sections': [],
                        'total_sections': 0,
                        'total_policies': 0,
                        'total_subpolicies': 0,
                        'source': f'Basic files in upload_{userid}',
                        'message': 'Upload completed but policy extraction may be in progress'
                    })
            
            return JsonResponse({
                'success': False,
                'error': f'Could not load data for user {userid}'
            }, status=404)
        
        # Extract data from consolidated structure
        sections = data.get('sections', [])
        framework_info = data.get('framework_info', {}) or {}
        summary = data.get('summary', {})
        
        # If consolidated has no sections (e.g. all_policies.json was empty due to AI format), try sections from index
        if not sections:
            try:
                from ..uploadNist.uploaded_data_loader import build_complete_structure
                fallback_sections = build_complete_structure(str(userid))
                if fallback_sections:
                    # Convert to same shape as consolidated: section with title, folder_path, policies
                    sections = []
                    for s in fallback_sections:
                        sections.append({
                            'section_id': s.get('section_id', f"section_{len(sections)}"),
                            'title': s.get('title', 'Untitled'),
                            'level': s.get('level', 1),
                            'folder_path': s.get('folder', s.get('folder_path', '')),
                            'policies': s.get('policies', [])
                        })
                    total_p = sum(len(sec.get('policies', [])) for sec in sections)
                    total_sp = sum(len(p.get('subpolicies', [])) for sec in sections for p in sec.get('policies', []))
                    summary = {'total_sections': len(sections), 'total_policies': total_p, 'total_subpolicies': total_sp}
                    debug_print(f"[FALLBACK] Built {len(sections)} sections from sections_index (policies: {total_p}, subpolicies: {total_sp})")
            except Exception as e:
                debug_print(f"[WARNING] Fallback build_complete_structure failed: {e}")
        
        # Get framework name (handle None case)
        if framework_info and isinstance(framework_info, dict):
            framework_name = framework_info.get('framework_name', 'Uploaded Framework')
        else:
            framework_name = 'Uploaded Framework'
        
        debug_print(f"[SUCCESS] Loaded from framework_data.json: {summary}")
        
        return JsonResponse({
            'success': True,
            'task_id': f"upload_{userid}",
            'framework_name': framework_name,
            'framework_info': framework_info,
            'sections': sections,
            'total_sections': summary.get('total_sections', len(sections)),
            'total_policies': summary.get('total_policies', 0),
            'total_subpolicies': summary.get('total_subpolicies', 0),
            'source': f'framework_data.json in upload_{userid}'
        })
        
    except Exception as e:
        debug_print(f"[ERROR] Error in get_sections_by_user: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e), 'success': False}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def save_checked_sections_json(request):
    return centralized_policy_ai.save_checked_sections_json(request)

@csrf_exempt
@require_http_methods(["POST"])
def generate_compliances_for_checked_sections(request):
    return centralized_policy_ai.generate_compliances_for_checked_sections(request)

@csrf_exempt
@require_http_methods(["GET"])
def get_checked_sections_with_compliance(request):
    return centralized_policy_ai.get_checked_sections_with_compliance(request)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def test_endpoint(request):
    """Test endpoint to verify URL mapping is working"""
    return JsonResponse({
        'message': 'Test endpoint is working',
        'method': request.method,
        'status': 'success'
    })

@csrf_exempt
@require_http_methods(["POST"])
def generate_consolidated_json(request):
    """
    Manually generate consolidated framework_data.json file for a user
    This creates a clean, simple JSON file in upload_1/ folder
    """
    try:
        data = json.loads(request.body)
        userid = data.get('userid', '1')
        try:
            require_safe_user_key(userid)
        except UnsafePathError as e:
            return JsonResponse({'error': str(e), 'success': False}, status=400)

        debug_print(f"[INFO] Generating consolidated JSON for user: {userid}")
        
        # Import the consolidate_data module
        from .consolidate_data import create_consolidated_json
        
        # Create the consolidated JSON
        consolidated_data = create_consolidated_json(userid)
        
        return JsonResponse({
            'success': True,
            'message': f'Consolidated JSON created successfully for user {userid}',
            'file_path': f'MEDIA_ROOT/upload_{userid}/framework_data.json',
            'summary': consolidated_data.get('summary', {}),
            'framework_name': consolidated_data.get('framework_info', {}).get('framework_name', 'Unknown')
        })
        
    except Exception as e:
        debug_print(f"[ERROR] Error generating consolidated JSON: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e), 'success': False}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def list_user_folders(request):
    """
    List all available user folders.
    
    Args:
        request: Django request object
    """
    try:
        user_folders = find_user_folders()
        
        return JsonResponse({
            'user_folders': user_folders,
            'total_users': len(user_folders)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def read_sections_from_directory(sections_dir):
    """
    Read sections from the extracted sections directory.
    
    Args:
        sections_dir (str): Path to the sections directory
        
    Returns:
        list: List of sections with their subsections
    """
    sections = []
    
    try:
        index_file = safe_join(sections_dir, 'sections_index.json')
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                
            # Extract sections from the index
            for section_info in index_data.get('sections_written', []):
                section = {
                    'id': len(sections),
                    'title': section_info.get('title', ''),
                    'selected': False,
                    'expanded': False,
                    'subsections': []
                }
                
                raw_folder = (section_info.get('folder') or '').strip()
                if not raw_folder:
                    sections.append(section)
                    continue
                try:
                    folder_seg = require_safe_rel_segment(raw_folder)
                except UnsafePathError:
                    sections.append(section)
                    continue
                section_folder = safe_join(sections_dir, 'sections', folder_seg)
                if os.path.exists(section_folder):
                    content_file = safe_join(section_folder, 'content.json')
                    if os.path.exists(content_file):
                        with open(content_file, 'r', encoding='utf-8') as f:
                            content_data = json.load(f)
                            section['content'] = content_data.get('content', '')
                sections.append(section)
        
        return sections
        
    except Exception as e:
        debug_print(f"Error reading sections from directory: {e}")
        return []

def get_sections_from_user_folder(userid):
    """
    Get sections from a user's folder by searching for the sections_index.json file.
    DEPRECATED: This function is now replaced by the uploaded_data_loader.
    Use get_sections_by_user endpoint instead for complete hierarchical data.
    
    Args:
        userid (str): The user ID to search for
        
    Returns:
        list: List of sections with their titles and metadata
    """
    try:
        key = require_safe_user_key(userid)
        user_folder = safe_join(settings.MEDIA_ROOT, f"upload_{key}")

        if not os.path.exists(user_folder):
            debug_print(f"User folder not found: {user_folder}")
            return []
        
        # Look for sections_index.json - try multiple possible locations
        sections_index_path = None
        possible_paths = [
            safe_join(user_folder, 'extracted_sections', 'sections_index.json'),
            safe_join(user_folder, 'sections_PCI_DSS_1', 'sections_index.json'),
            safe_join(user_folder, 'sections_PCI_DSS', 'sections_index.json'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                sections_index_path = path
                debug_print(f"Found sections index at: {sections_index_path}")
                break
        
        if not sections_index_path:
            debug_print(f"Sections index file not found in any of the expected locations")
            return []
        
        # Read the sections index file
        with open(sections_index_path, 'r', encoding='utf-8') as f:
            sections_data = json.load(f)
        
        # Extract sections from the sections_written array
        sections = []
        for section_info in sections_data.get('sections_written', []):
            section = {
                'id': len(sections),
                'title': section_info.get('title', ''),
                'folder': section_info.get('folder', ''),
                'level': section_info.get('level', 1),
                'selected': False,
                'expanded': False,
                'subsections': []
            }
            
            raw_folder = (section_info.get('folder') or '').strip()
            if not raw_folder:
                section['content'] = ''
                sections.append(section)
                continue
            try:
                folder_seg = require_safe_rel_segment(raw_folder)
            except UnsafePathError:
                section['content'] = ''
                sections.append(section)
                continue
            section_folder = safe_join(user_folder, 'extracted_sections', 'sections', folder_seg)
            content_file = safe_join(section_folder, 'content.json')
            
            if os.path.exists(content_file):
                try:
                    with open(content_file, 'r', encoding='utf-8') as f:
                        content_data = json.load(f)
                        section['content'] = content_data.get('content', '')
                except Exception as e:
                    debug_print(f"Error reading content file {content_file}: {e}")
                    section['content'] = ''
            else:
                section['content'] = ''
            
            extracted_controls_folder = safe_join(section_folder, 'extracted_controls')
            if os.path.exists(extracted_controls_folder):
                try:
                    control_headings_file = safe_join(extracted_controls_folder, 'control_headings.json')
                    if os.path.exists(control_headings_file):
                        with open(control_headings_file, 'r', encoding='utf-8') as f:
                            control_data = json.load(f)
                            
                        controls = control_data.get('controls', [])
                        for control in controls:
                            control_name = control.get('name', '')
                            if control_name:
                                subsection = {
                                    'id': len(section['subsections']),
                                    'title': control_name,
                                    'selected': False,
                                    'content': control.get('description', ''),
                                    'control_id': control.get('id', ''),
                                    'type': 'control'
                                }
                                section['subsections'].append(subsection)
                    
                    for item in os.listdir(extracted_controls_folder):
                        item_path = safe_join(extracted_controls_folder, item)
                        if os.path.isdir(item_path):
                            subsection = {
                                'id': len(section['subsections']),
                                'title': item.replace('_', ' '),
                                'selected': False,
                                'content': f'Control folder: {item}',
                                'control_id': item,
                                'type': 'control_folder'
                            }
                            section['subsections'].append(subsection)
                            
                except Exception as e:
                    debug_print(f"Error reading extracted controls from {extracted_controls_folder}: {e}")
            
            sections.append(section)
        
        debug_print(f"Found {len(sections)} sections in user folder: {user_folder}")
        return sections
        
    except Exception as e:
        debug_print(f"Error getting sections from user folder: {e}")
        return []

def find_user_folders():
    """
    Find all user folders in MEDIA_ROOT.
    
    Returns:
        list: List of user IDs that have folders
    """
    try:
        user_folders = []
        media_root = settings.MEDIA_ROOT
        
        if not os.path.exists(media_root):
            return user_folders
        
        # Look for folders that start with 'upload_'
        for item in os.listdir(media_root):
            try:
                item_path = safe_join(media_root, item)
            except UnsafePathError:
                continue
            if os.path.isdir(item_path) and item.startswith('upload_'):
                userid = item.replace('upload_', '')
                user_folders.append(userid)
        
        return user_folders
        
    except Exception as e:
        debug_print(f"Error finding user folders: {e}")
        return []

@csrf_exempt
@require_http_methods(["POST"])
def load_default_data(request):
    """
    Load default framework data from main_default folder.
    
    Args:
        request: Django request object
    """
    try:
        main_default_folder = safe_join(settings.MEDIA_ROOT, 'main_default')
        
        if not os.path.exists(main_default_folder):
            return JsonResponse({'error': 'Default data folder not found'}, status=404)
        
        extracted_sections_folder = safe_join(main_default_folder, 'extracted_sections')
        if not os.path.exists(extracted_sections_folder):
            return JsonResponse({'error': 'Default extracted sections not found'}, status=404)
        
        # Read sections from the main_default folder
        sections = get_sections_from_main_default()
        
        if not sections:
            return JsonResponse({'error': 'No sections found in default data'}, status=404)
        
        # Generate a default task ID
        default_task_id = f"default_{int(time.time())}"
        
        return JsonResponse({
            'message': 'Default framework data loaded successfully',
            'task_id': default_task_id,
            'processing': False,
            'sections': sections,
            'total_sections': len(sections),
            'source': 'main_default'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_sections_from_main_default():
    """
    Get sections from the main_default folder.
    
    Returns:
        list: List of sections with their titles and metadata
    """
    try:
        main_default_folder = safe_join(settings.MEDIA_ROOT, 'main_default')
        
        if not os.path.exists(main_default_folder):
            debug_print(f"Main default folder not found: {main_default_folder}")
            return []
        
        sections_index_path = safe_join(main_default_folder, 'extracted_sections', 'sections_index.json')
        
        if not os.path.exists(sections_index_path):
            debug_print(f"Sections index file not found: {sections_index_path}")
            return []
        
        with open(sections_index_path, 'r', encoding='utf-8') as f:
            sections_data = json.load(f)
        
        sections = []
        for section_info in sections_data.get('sections_written', []):
            section = {
                'id': len(sections),
                'title': section_info.get('title', ''),
                'folder': section_info.get('folder', ''),
                'level': section_info.get('level', 1),
                'selected': False,
                'expanded': False,
                'subsections': []
            }
            
            raw_folder = (section_info.get('folder') or '').strip()
            if not raw_folder:
                section['content'] = ''
                sections.append(section)
                continue
            try:
                folder_seg = require_safe_rel_segment(raw_folder)
            except UnsafePathError:
                section['content'] = ''
                sections.append(section)
                continue
            section_folder = safe_join(main_default_folder, 'extracted_sections', 'sections', folder_seg)
            content_file = safe_join(section_folder, 'content.json')
            
            if os.path.exists(content_file):
                try:
                    with open(content_file, 'r', encoding='utf-8') as f:
                        content_data = json.load(f)
                        section['content'] = content_data.get('content', '')
                except Exception as e:
                    debug_print(f"Error reading content file {content_file}: {e}")
                    section['content'] = ''
            else:
                section['content'] = ''
            
            extracted_controls_folder = safe_join(section_folder, 'extracted_controls')
            if os.path.exists(extracted_controls_folder):
                try:
                    control_headings_file = safe_join(extracted_controls_folder, 'control_headings.json')
                    if os.path.exists(control_headings_file):
                        with open(control_headings_file, 'r', encoding='utf-8') as f:
                            control_data = json.load(f)
                            
                        controls = control_data.get('controls', [])
                        for control in controls:
                            control_name = control.get('name', '')
                            if control_name:
                                subsection = {
                                    'id': len(section['subsections']),
                                    'title': control_name,
                                    'selected': False,
                                    'content': control.get('description', ''),
                                    'control_id': control.get('id', ''),
                                    'type': 'control'
                                }
                                section['subsections'].append(subsection)
                    
                    for item in os.listdir(extracted_controls_folder):
                        item_path = safe_join(extracted_controls_folder, item)
                        if os.path.isdir(item_path):
                            subsection = {
                                'id': len(section['subsections']),
                                'title': item.replace('_', ' '),
                                'selected': False,
                                'content': f'Control folder: {item}',
                                'control_id': item,
                                'type': 'control_folder'
                            }
                            section['subsections'].append(subsection)
                            
                except Exception as e:
                    debug_print(f"Error reading extracted controls from {extracted_controls_folder}: {e}")
            
            sections.append(section)
        
        debug_print(f"Found {len(sections)} sections in main_default folder: {main_default_folder}")
        return sections
        
    except Exception as e:
        debug_print(f"Error getting sections from main_default folder: {e}")
        return []
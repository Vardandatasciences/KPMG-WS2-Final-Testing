import os
import json
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect as csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from pathlib import Path

logger = logging.getLogger(__name__)

def get_temp_media_root():
    """Get the TEMP_MEDIA_ROOT path - defaults to backend/TEMP_MEDIA_ROOT"""
    temp_media_root = getattr(settings, 'TEMP_MEDIA_ROOT', None)
    if not temp_media_root:
        # Default to backend/TEMP_MEDIA_ROOT (same level as manage.py)
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up from routes/uploadNist to backend
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir)))
        temp_media_root = os.path.join(backend_dir, 'TEMP_MEDIA_ROOT')
    else:
        # Convert Path object to string if needed
        if isinstance(temp_media_root, Path):
            temp_media_root = str(temp_media_root)
        else:
            temp_media_root = str(temp_media_root)
    
    # Normalize the path (resolve any relative paths, symlinks, etc.)
    temp_media_root = os.path.abspath(os.path.expanduser(temp_media_root))
    logger.info(f"TEMP_MEDIA_ROOT resolved to: {temp_media_root}")
    
    return temp_media_root

def get_available_frameworks():
    """
    Scan TEMP_MEDIA_ROOT to find available frameworks
    Returns list of framework info dictionaries
    """
    frameworks = []
    try:
        temp_media_root = get_temp_media_root()
        if not os.path.exists(temp_media_root):
            return frameworks
        
        # Look for directories matching the pattern: sections_* or policies_*
        for item in os.listdir(temp_media_root):
            item_path = os.path.join(temp_media_root, item)
            if not os.path.isdir(item_path):
                continue
            
            # Check if it's a sections directory
            if item.startswith('sections_'):
                framework_key = item.replace('sections_', '')
                # Check if corresponding policies directory exists
                policies_dir_name = f'policies_{framework_key}'
                policies_path = os.path.join(temp_media_root, policies_dir_name)
                
                if os.path.exists(policies_path):
                    # Format framework name for display
                    framework_name = framework_key.replace('_', ' ').title()
                    # Special handling for known frameworks
                    if framework_key == 'PCI_DSS_2':
                        framework_name = 'PCI DSS 2'
                    elif framework_key == 'basel_3_framework':
                        framework_name = 'Basel 3 Framework'
                    
                    frameworks.append({
                        'key': framework_key,
                        'name': framework_name,
                        'sections_dir': item,
                        'policies_dir': policies_dir_name
                    })
        
        # Sort frameworks by name
        frameworks.sort(key=lambda x: x['name'])
        return frameworks
    except Exception as e:
        logger.exception(f"Error getting available frameworks: {str(e)}")
        return frameworks

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def list_available_frameworks(request):
    """API endpoint to list all available frameworks in TEMP_MEDIA_ROOT"""
    try:
        frameworks = get_available_frameworks()
        return JsonResponse({
            "success": True,
            "frameworks": frameworks,
            "total": len(frameworks)
        })
    except Exception as e:
        logger.exception(f"Error listing frameworks: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def load_default_data(request):
    """
    Load default data from TEMP_MEDIA_ROOT directory
    Returns complete hierarchical structure: sections → policies → subpolicies
    
    Accepts framework parameter in request body (POST) or query params (GET)
    Defaults to 'PCI_DSS_2' if not specified
    """
    try:
        temp_media_root = get_temp_media_root()
        logger.info(f"Loading default data from {temp_media_root}")
        
        # Get framework from request (POST body or GET query params)
        if request.method == 'POST':
            framework_key = request.data.get('framework', 'PCI_DSS_2')
        else:
            framework_key = request.GET.get('framework', 'PCI_DSS_2')
        
        # Normalize framework key
        framework_key = framework_key.strip()
        
        # Special handling for frameworks with nested structure
        if framework_key == 'dgca_framework':
            # DGCA has a nested structure inside dgca_framework folder
            dgca_base = os.path.join(temp_media_root, 'dgca_framework')
            if not os.path.exists(dgca_base):
                return JsonResponse({"success": False, "error": f"DGCA framework directory not found: {dgca_base}"}, status=404)
            
            # Find the sections and policies folders inside dgca_framework
            # They are named like "sections_CAR Sec 7 Seriess J Pt 3" and "policies_CAR Sec 7 Seriess J Pt 3"
            sections_dir = None
            policies_dir = None
            
            for item in os.listdir(dgca_base):
                item_path = os.path.join(dgca_base, item)
                if os.path.isdir(item_path):
                    if item.startswith('sections_'):
                        sections_dir = item_path
                    elif item.startswith('policies_'):
                        policies_dir = item_path
            
            if not sections_dir:
                return JsonResponse({"success": False, "error": f"DGCA sections directory not found in {dgca_base}"}, status=404)
            
            if not policies_dir:
                return JsonResponse({"success": False, "error": f"DGCA policies directory not found in {dgca_base}"}, status=404)
        elif framework_key == 'rbi_framework':
            # RBI framework is in "master_rbac" folder
            # Try exact match first
            rbi_base = os.path.join(temp_media_root, 'master_rbac')
            logger.info(f"Looking for RBI framework at: {rbi_base}")
            logger.info(f"TEMP_MEDIA_ROOT exists: {os.path.exists(temp_media_root)}")
            
            if not os.path.exists(temp_media_root):
                # List what's actually in the parent directory
                parent_dir = os.path.dirname(temp_media_root)
                if os.path.exists(parent_dir):
                    try:
                        items = [item for item in os.listdir(parent_dir) if 'TEMP' in item.upper() or 'MEDIA' in item.upper()]
                        logger.info(f"Found TEMP/MEDIA related items in {parent_dir}: {items}")
                    except:
                        pass
                return JsonResponse({
                    "success": False, 
                    "error": f"TEMP_MEDIA_ROOT directory not found: {temp_media_root}",
                    "debug_info": {
                        "temp_media_root": temp_media_root,
                        "parent_dir": parent_dir if 'parent_dir' in locals() else None
                    }
                }, status=404)
            
            # If exact match doesn't exist, try to find it by fuzzy matching
            if not os.path.exists(rbi_base):
                try:
                    items_in_temp = os.listdir(temp_media_root)
                    logger.info(f"Items in TEMP_MEDIA_ROOT: {items_in_temp}")
                    
                    # Look for any directory that might be the RBI folder (case-insensitive, partial match)
                    rbi_candidates = []
                    for item in items_in_temp:
                        item_lower = item.lower()
                        # Look for master_rbac or any folder with master/rbac/rbi keywords
                        if any(keyword in item_lower for keyword in ['master_rbac', 'master', 'rbac', 'rbi', 'direction', 'reserve', 'bank', 'india']):
                            item_path = os.path.join(temp_media_root, item)
                            if os.path.isdir(item_path):
                                rbi_candidates.append(item)
                    
                    if rbi_candidates:
                        logger.info(f"Found potential RBI framework folders: {rbi_candidates}")
                        # Use the first candidate that looks like it has sections and policies
                        for candidate in rbi_candidates:
                            candidate_path = os.path.join(temp_media_root, candidate)
                            try:
                                candidate_items = os.listdir(candidate_path)
                                has_sections = any(item.startswith('sections_') for item in candidate_items)
                                has_policies = any(item.startswith('policies_') for item in candidate_items)
                                if has_sections and has_policies:
                                    rbi_base = candidate_path
                                    logger.info(f"Using RBI framework folder: {rbi_base}")
                                    break
                            except:
                                continue
                    
                    # If still not found, return error with helpful info
                    if not os.path.exists(rbi_base):
                        return JsonResponse({
                            "success": False, 
                            "error": f"RBI framework directory not found. Expected: 'master_rbac'",
                            "debug_info": {
                                "temp_media_root": temp_media_root,
                                "rbi_base_attempted": rbi_base,
                                "temp_media_root_exists": os.path.exists(temp_media_root),
                                "items_in_temp": items_in_temp,
                                "rbi_candidates": rbi_candidates if rbi_candidates else "None found"
                            }
                        }, status=404)
                except Exception as e:
                    logger.error(f"Error searching for RBI folder: {e}")
                    return JsonResponse({
                        "success": False, 
                        "error": f"Error accessing TEMP_MEDIA_ROOT: {str(e)}"
                    }, status=500)
            
            # Find the sections and policies folders inside RBI folder
            # They are named like "sections_RBI-MASTER-DIRECTION-NBFC-19-10-2023" and "policies_RBI-MASTER-DIRECTION-NBFC-19-10-2023"
            sections_dir = None
            policies_dir = None
            
            try:
                items_in_rbi = os.listdir(rbi_base)
                logger.info(f"Items in RBI folder: {items_in_rbi}")
                
                for item in items_in_rbi:
                    item_path = os.path.join(rbi_base, item)
                    if os.path.isdir(item_path):
                        if item.startswith('sections_'):
                            sections_dir = item_path
                            logger.info(f"Found sections directory: {sections_dir}")
                        elif item.startswith('policies_'):
                            policies_dir = item_path
                            logger.info(f"Found policies directory: {policies_dir}")
            except Exception as e:
                logger.error(f"Error listing RBI folder contents: {e}")
                return JsonResponse({
                    "success": False, 
                    "error": f"Error accessing RBI framework folder: {str(e)}"
                }, status=500)
            
            if not sections_dir:
                return JsonResponse({"success": False, "error": f"RBI sections directory not found in {rbi_base}"}, status=404)
            
            if not policies_dir:
                return JsonResponse({"success": False, "error": f"RBI policies directory not found in {rbi_base}"}, status=404)
        else:
            # Standard structure for other frameworks (Basel, PCI DSS, etc.)
            sections_dir = os.path.join(temp_media_root, f'sections_{framework_key}')
            policies_dir = os.path.join(temp_media_root, f'policies_{framework_key}')
            
            # Check if required directories exist
            if not os.path.exists(sections_dir):
                return JsonResponse({"success": False, "error": f"Sections directory not found: {sections_dir}"}, status=404)
            
            if not os.path.exists(policies_dir):
                return JsonResponse({"success": False, "error": f"Policies directory not found: {policies_dir}"}, status=404)
        
        # Load policies data first
        # Try all_policies.json first, then all_policies_temp.json (for RBI framework)
        policies_file = os.path.join(policies_dir, 'all_policies.json')
        if not os.path.exists(policies_file):
            policies_file = os.path.join(policies_dir, 'all_policies_temp.json')
            if not os.path.exists(policies_file):
                return JsonResponse({"success": False, "error": f"Policies file not found in {policies_dir}. Tried: all_policies.json, all_policies_temp.json"}, status=404)
            
        with open(policies_file, 'r', encoding='utf-8') as f:
            policies_data = json.load(f)
        
        # Load compliances data if available (for DGCA framework)
        compliances_data = None
        if framework_key == 'dgca_framework':
            checked_section_file = os.path.join(temp_media_root, 'dgca_framework', 'checked_section.json')
        elif framework_key == 'rbi_framework':
            # RBI framework doesn't have checked_section.json yet, skip for now
            checked_section_file = None
        else:
            checked_section_file = os.path.join(temp_media_root, 'checked_section.json')
        
        if checked_section_file and os.path.exists(checked_section_file):
            try:
                with open(checked_section_file, 'r', encoding='utf-8') as f:
                    compliances_data = json.load(f)
                logger.info(f"Loaded compliances data from {checked_section_file}")
            except Exception as e:
                logger.warning(f"Could not load compliances from {checked_section_file}: {str(e)}")
                compliances_data = None
        
        # Build complete hierarchical structure with sections, policies, subpolicies, and compliances
        sections_data = build_complete_structure(sections_dir, policies_data, compliances_data)
        
        # Format framework name for display
        framework_name = framework_key.replace('_', ' ').title()
        if framework_key == 'PCI_DSS_2':
            framework_name = 'PCI DSS 2'
        elif framework_key == 'basel_3_framework':
            framework_name = 'Basel 3 Framework'
        elif framework_key == 'dgca_framework':
            framework_name = 'DGCA Framework'
        elif framework_key == 'rbi_framework':
            framework_name = 'RBI Master Direction - NBFC Framework'
        
        # Generate task ID for this default data session
        user_id = request.user.id if hasattr(request, 'user') and hasattr(request.user, 'id') else '1'
        task_id = f"default_{framework_key}_{user_id}"
        
        # Count total policies, subpolicies, and compliances
        total_policies = 0
        total_subpolicies = 0
        total_compliances = 0
        for section in sections_data:
            total_policies += len(section.get('policies', []))
            for policy in section.get('policies', []):
                total_subpolicies += len(policy.get('subpolicies', []))
                for subpolicy in policy.get('subpolicies', []):
                    total_compliances += len(subpolicy.get('compliances', []))
        
        # Return the combined data
        response_data = {
            "success": True,
            "task_id": task_id,
            "framework_key": framework_key,
            "framework_name": framework_name,
            "sections": sections_data,
            "total_sections": len(sections_data),
            "total_policies": total_policies,
            "total_subpolicies": total_subpolicies,
            "total_compliances": total_compliances,
            "source": "TEMP_MEDIA_ROOT"
        }
        
        logger.info(f"Successfully loaded default data for {framework_name}: {len(sections_data)} sections, {total_policies} policies, {total_subpolicies} subpolicies, {total_compliances} compliances")
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.exception(f"Error loading default data: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

def build_complete_structure(sections_dir, policies_data, compliances_data=None):
    """
    Build complete hierarchical structure: sections → policies → subpolicies → compliances
    All in proper order with checkboxes at every level
    """
    sections = []
    sections_folder = os.path.join(sections_dir, 'sections')
    
    if not os.path.exists(sections_folder):
        logger.error(f"Sections folder not found: {sections_folder}")
        return sections
    
    try:
        # Get all section folders and sort them by numeric prefix (001, 002, 003, etc.)
        all_folders = [f for f in os.listdir(sections_folder) if os.path.isdir(os.path.join(sections_folder, f))]
        
        # Sort by extracting the numeric prefix from folder names
        def get_sort_key(folder_name):
            if '-' in folder_name:
                prefix = folder_name.split('-')[0]
                try:
                    return int(prefix)  # Convert to integer for proper numeric sorting
                except ValueError:
                    return 999  # Put non-numeric folders at the end
            return 999
        
        section_folders = sorted(all_folders, key=get_sort_key)
        logger.info(f"Section folders in order: {section_folders}")
        
        logger.info(f"Found {len(section_folders)} section folders")
        
        for idx, section_folder in enumerate(section_folders):
            section_path = os.path.join(sections_folder, section_folder)
            
            # Read content.json for section title and content
            content_file = os.path.join(section_path, 'content.json')
            section_title = section_folder.split('-', 1)[-1].replace('_', ' ') if '-' in section_folder else section_folder.replace('_', ' ')
            section_content = ''
            
            if os.path.exists(content_file):
                try:
                    with open(content_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content_data = json.load(f)
                        section_title = content_data.get('name', section_title)
                        section_content = content_data.get('content', '')
                except Exception as e:
                    logger.warning(f"Error reading content.json for {section_folder}: {str(e)}")
            
            # Get all policies for this section from all_policies.json
            section_policies = _get_policies_for_section_internal(policies_data, section_folder, compliances_data)
            
            # Build the section object with complete hierarchy
            section_obj = {
                'id': idx,
                'section_id': f"section_{idx}",
                'title': section_title,
                'folder': section_folder,
                'content': section_content,
                'selected': False,
                'expanded': False,
                'policies': section_policies,
                'total_policies': len(section_policies),
                'total_subpolicies': sum(len(p.get('subpolicies', [])) for p in section_policies)
            }
            
            sections.append(section_obj)
            
        logger.info(f"Built {len(sections)} sections with complete hierarchy")
        
    except Exception as e:
        logger.exception(f"Error building complete structure: {str(e)}")
    
    return sections

def _get_compliances_for_subpolicy(compliances_data, subpolicy_id):
    """
    Extract compliances for a specific subpolicy from checked_section.json data
    """
    compliances = []
    
    if not compliances_data or not subpolicy_id:
        return compliances
    
    try:
        # Check if compliances_data has the expected structure
        sections = compliances_data.get('sections', [])
        
        for section in sections:
            policies = section.get('policies', [])
            for policy in policies:
                subpolicies = policy.get('subpolicies', [])
                for subpolicy in subpolicies:
                    # Match by subpolicy_id
                    if subpolicy.get('subpolicy_id') == subpolicy_id:
                        subpolicy_compliances = subpolicy.get('compliances', [])
                        for comp in subpolicy_compliances:
                            # Format compliance for frontend
                            formatted_compliance = {
                                'compliance_id': comp.get('ComplianceId') or comp.get('compliance_id') or comp.get('id'),
                                'compliance_title': comp.get('ComplianceTitle') or comp.get('compliance_title') or comp.get('title'),
                                'compliance_description': comp.get('ComplianceItemDescription') or comp.get('compliance_description') or comp.get('Description') or comp.get('description'),
                                'Criticality': comp.get('Criticality') or comp.get('criticality'),
                                'ComplianceType': comp.get('ComplianceType') or comp.get('compliance_type'),
                                'MandatoryOptional': comp.get('MandatoryOptional') or comp.get('mandatory_optional')
                            }
                            # Only add if we have at least an ID or title
                            if formatted_compliance['compliance_id'] or formatted_compliance['compliance_title']:
                                compliances.append(formatted_compliance)
                        # Found the subpolicy, return its compliances
                        return compliances
    except Exception as e:
        logger.warning(f"Error extracting compliances for subpolicy {subpolicy_id}: {str(e)}")
    
    return compliances

def _get_policies_for_section_internal(policies_data, section_folder, compliances_data=None):
    """
    Internal helper: Get all policies for a specific section from all_policies.json
    Returns policies with their subpolicies in proper structure
    
    Args:
        policies_data: List of policy entries from all_policies.json
        section_folder: Folder name of the section to get policies for
        compliances_data: Optional compliances data from checked_section.json
    """
    section_policies = []
    
    try:
        # Ensure policies_data is a list
        if not isinstance(policies_data, list):
            logger.warning(f"policies_data is not a list, got {type(policies_data)}")
            return section_policies
        
        matched_count = 0
        logger.debug(f"Processing {len(policies_data)} policy entries for section {section_folder}")
        
        for policy_entry in policies_data:
            section_info = policy_entry.get('section_info', {})
            folder_path = section_info.get('folder_path', '')
            
            # Normalize paths for comparison - handle both full paths and just folder names
            folder_path_normalized = folder_path.replace('\\', '/').strip('/').lower()
            section_folder_normalized = section_folder.replace('\\', '/').strip('/').lower()
            
            # Extract just the folder name from folder_path if it contains path separators
            if '/' in folder_path_normalized:
                folder_path_normalized = folder_path_normalized.split('/')[-1]
            if '/' in section_folder_normalized:
                section_folder_normalized = section_folder_normalized.split('/')[-1]
            
            # Remove any leading/trailing whitespace and compare
            folder_path_normalized = folder_path_normalized.strip()
            section_folder_normalized = section_folder_normalized.strip()
            
            # Check if this policy belongs to the current section or its subsections
            # Match by exact folder name (case-insensitive) or if one starts with the other
            is_match = (
                folder_path_normalized == section_folder_normalized or 
                folder_path_normalized.startswith(section_folder_normalized) or
                section_folder_normalized.startswith(folder_path_normalized)
            )
            
            if is_match:
                analysis = policy_entry.get('analysis', {})
                policies = analysis.get('policies', [])
                matched_count += len(policies)
                
                for policy_idx, policy in enumerate(policies):
                    # Format policy with all details
                    formatted_policy = {
                        'policy_id': policy.get('policy_id'),
                        'policy_title': policy.get('policy_title'),
                        'policy_description': policy.get('policy_description'),
                        'policy_text': policy.get('policy_text'),
                        'scope': policy.get('scope'),
                        'objective': policy.get('objective'),
                        'policy_type': policy.get('policy_type'),
                        'policy_category': policy.get('policy_category'),
                        'policy_subcategory': policy.get('policy_subcategory'),
                        'selected': False,
                        'expanded': False,
                        'subpolicies': []
                    }
                    
                    # Add all subpolicies with compliances
                    subpolicies = policy.get('subpolicies', [])
                    for subpolicy_idx, subpolicy in enumerate(subpolicies):
                        formatted_subpolicy = {
                            'subpolicy_id': subpolicy.get('subpolicy_id'),
                            'subpolicy_title': subpolicy.get('subpolicy_title'),
                            'subpolicy_description': subpolicy.get('subpolicy_description'),
                            'subpolicy_text': subpolicy.get('subpolicy_text'),
                            'control': subpolicy.get('control'),
                            'selected': False,
                            'compliances': []
                        }
                        
                        # Add compliances for this subpolicy if compliances_data is available
                        if compliances_data:
                            subpolicy_id = subpolicy.get('subpolicy_id')
                            subpolicy_compliances = _get_compliances_for_subpolicy(compliances_data, subpolicy_id)
                            formatted_subpolicy['compliances'] = subpolicy_compliances
                        
                        formatted_policy['subpolicies'].append(formatted_subpolicy)
                    
                    section_policies.append(formatted_policy)
        
        if matched_count > 0:
            logger.debug(f"Matched {matched_count} policies for section {section_folder}")
                    
    except Exception as e:
        logger.exception(f"Error getting policies for section {section_folder}: {str(e)}")
    
    return section_policies

def build_sections_from_index(sections_dir, sections_index):
    """Build section data from sections_index.json"""
    sections = []
    
    try:
        # Handle both list and string formats
        if isinstance(sections_index, str):
            # If it's a string, try to parse it as JSON
            try:
                sections_index = json.loads(sections_index)
            except:
                logger.warning("Could not parse sections_index as JSON, treating as folder list")
                return build_sections_from_folders(sections_dir)
        
        if not isinstance(sections_index, list):
            logger.warning("sections_index is not a list, using folder structure")
            return build_sections_from_folders(sections_dir)
        
        for idx, section in enumerate(sections_index):
            # Skip if section doesn't have required fields or is not a dict
            if not isinstance(section, dict) or not section.get('title') or not section.get('folder'):
                continue
                
            section_folder = section.get('folder')
            section_path = os.path.join(sections_dir, 'sections', section_folder)
            
            # Check if section folder exists
            if not os.path.exists(section_path):
                continue
                
            # Read content.json for section title and content
            content_file = os.path.join(section_path, 'content.json')
            section_title = section.get('title')
            section_content = section.get('content', '')
            
            if os.path.exists(content_file):
                try:
                    with open(content_file, 'r') as f:
                        content_data = json.load(f)
                        section_title = content_data.get('name', section_title)
                        section_content = content_data.get('content', section_content)
                except Exception as e:
                    logger.warning(f"Error reading content.json for {section_folder}: {str(e)}")
            
            # Get subsections based on PDFs in the section folder
            subsections = []
            try:
                for pdf_file in os.listdir(section_path):
                    if pdf_file.endswith('.pdf'):
                        control_id = pdf_file.replace('.pdf', '')
                        subsection_title = control_id.replace('_', ' ')
                        
                        subsections.append({
                            'title': subsection_title,
                            'control_id': control_id,
                            'selected': False,
                            'showPDF': False,
                            'path': os.path.join(section_path, pdf_file),
                            'relative_path': f"sections/{section_folder}/{pdf_file}"
                        })
            except Exception as e:
                logger.warning(f"Error processing subsections for {section_folder}: {str(e)}")
            
            # Add section with subsections
            sections.append({
                'id': idx,
                'title': section_title,
                'folder': section_folder,
                'selected': False,
                'expanded': False,  # Start collapsed
                'subsections': subsections,
                'content': section_content
            })
            
    except Exception as e:
        logger.exception(f"Error building sections from index: {str(e)}")
        
    return sections

def build_sections_from_folders(sections_dir):
    """Build section data from folder structure as fallback"""
    sections = []
    sections_folder = os.path.join(sections_dir, 'sections')
    
    if not os.path.exists(sections_folder):
        return sections
        
    try:
        for idx, section_folder in enumerate(os.listdir(sections_folder)):
            section_path = os.path.join(sections_folder, section_folder)
            
            if not os.path.isdir(section_path):
                continue
            
            # Read content.json for section title and content
            content_file = os.path.join(section_path, 'content.json')
            section_title = section_folder.split('-', 1)[-1].replace('_', ' ')
            section_content = ''
            
            if os.path.exists(content_file):
                try:
                    with open(content_file, 'r') as f:
                        content_data = json.load(f)
                        section_title = content_data.get('name', section_title)
                        section_content = content_data.get('content', '')
                except Exception as e:
                    logger.warning(f"Error reading content.json for {section_folder}: {str(e)}")
            
            if not section_title:
                section_title = f"Section {idx+1}"
                
            # Get subsections based on PDFs in the section folder
            subsections = []
            try:
                for pdf_file in os.listdir(section_path):
                    if pdf_file.endswith('.pdf'):
                        control_id = pdf_file.replace('.pdf', '')
                        subsection_title = control_id.replace('_', ' ')
                        
                        subsections.append({
                            'title': subsection_title,
                            'control_id': control_id,
                            'selected': False,
                            'showPDF': False,
                            'path': os.path.join(section_path, pdf_file),
                            'relative_path': f"sections/{section_folder}/{pdf_file}"
                        })
            except Exception as e:
                logger.warning(f"Error processing subsections for {section_folder}: {str(e)}")
            
            # Add section with subsections
            sections.append({
                'id': idx,
                'title': section_title,
                'folder': section_folder,
                'selected': False,
                'expanded': False,  # Start collapsed
                'subsections': subsections,
                'content': section_content
            })
            
    except Exception as e:
        logger.exception(f"Error building sections from folders: {str(e)}")
        
    return sections

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_default_data_sections(request, user_id=None):
    """API endpoint to get sections from default data for a specific user"""
    try:
        # Load default data
        response = load_default_data(request)
        if response.status_code != 200:
            return response
            
        # Parse JSON content
        data = json.loads(response.content)
        
        # Return just the sections part
        return JsonResponse({
            "success": True,
            "sections": data.get("sections", []),
            "task_id": data.get("task_id", "default_task"),
            "framework_name": data.get("framework_name", "PCI DSS 2"),
            "total_sections": data.get("total_sections", 0)
        })
        
    except Exception as e:
        logger.exception(f"Error getting default data sections: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_policies_for_section(request, section_folder):
    """API endpoint to get policies for a specific section"""
    try:
        temp_media_root = get_temp_media_root()
        policies_file = os.path.join(temp_media_root, 'policies_PCI_DSS_2', 'all_policies.json')
        
        if not os.path.exists(policies_file):
            return JsonResponse({"success": False, "error": "Policies file not found"}, status=404)
        
        with open(policies_file, 'r') as f:
            all_policies = json.load(f)
        
        # Filter policies for the specific section
        section_policies = []
        for policy_data in all_policies:
            section_info = policy_data.get('section_info', {})
            if section_info.get('folder_path') == section_folder:
                # Extract policy details without subpolicies initially
                analysis = policy_data.get('analysis', {})
                policies = analysis.get('policies', [])
                
                for policy in policies:
                    policy_details = {
                        'policy_id': policy.get('policy_id'),
                        'policy_title': policy.get('policy_title'),
                        'policy_description': policy.get('policy_description'),
                        'policy_text': policy.get('policy_text'),
                        'scope': policy.get('scope'),
                        'objective': policy.get('objective'),
                        'policy_type': policy.get('policy_type'),
                        'policy_category': policy.get('policy_category'),
                        'policy_subcategory': policy.get('policy_subcategory'),
                        'subpolicies_count': len(policy.get('subpolicies', [])),
                        'subpolicies': []  # Initially empty, will be loaded on demand
                    }
                    section_policies.append(policy_details)
        
        return JsonResponse({
            "success": True,
            "section_folder": section_folder,
            "policies": section_policies,
            "total_policies": len(section_policies)
        })
        
    except Exception as e:
        logger.exception(f"Error getting policies for section {section_folder}: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_subpolicies_for_policy(request, section_folder, policy_id):
    """API endpoint to get subpolicies for a specific policy"""
    try:
        temp_media_root = get_temp_media_root()
        policies_file = os.path.join(temp_media_root, 'policies_PCI_DSS_2', 'all_policies.json')
        
        if not os.path.exists(policies_file):
            return JsonResponse({"success": False, "error": "Policies file not found"}, status=404)
        
        with open(policies_file, 'r') as f:
            all_policies = json.load(f)
        
        # Find the specific policy and return its subpolicies
        for policy_data in all_policies:
            section_info = policy_data.get('section_info', {})
            if section_info.get('folder_path') == section_folder:
                analysis = policy_data.get('analysis', {})
                policies = analysis.get('policies', [])
                
                for policy in policies:
                    if policy.get('policy_id') == policy_id:
                        subpolicies = policy.get('subpolicies', [])
                        
                        # Format subpolicies for display
                        formatted_subpolicies = []
                        for subpolicy in subpolicies:
                            formatted_subpolicies.append({
                                'subpolicy_id': subpolicy.get('subpolicy_id'),
                                'subpolicy_title': subpolicy.get('subpolicy_title'),
                                'subpolicy_description': subpolicy.get('subpolicy_description'),
                                'subpolicy_text': subpolicy.get('subpolicy_text'),
                                'control': subpolicy.get('control')
                            })
                        
                        return JsonResponse({
                            "success": True,
                            "section_folder": section_folder,
                            "policy_id": policy_id,
                            "subpolicies": formatted_subpolicies,
                            "total_subpolicies": len(formatted_subpolicies)
                        })
        
        return JsonResponse({"success": False, "error": "Policy not found"}, status=404)
        
    except Exception as e:
        logger.exception(f"Error getting subpolicies for policy {policy_id}: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_default_pdf_content(request, section_folder, control_id):
    """
    API endpoint to get PDF content for a specific section and control
    Accepts framework parameter in query params, defaults to 'PCI_DSS_2'
    """
    try:
        from django.http import FileResponse
        
        temp_media_root = get_temp_media_root()
        
        # Get framework from query params, default to PCI_DSS_2
        framework_key = request.GET.get('framework', 'PCI_DSS_2')
        framework_key = framework_key.strip()
        
        # Special handling for dgca_framework which has nested structure
        if framework_key == 'dgca_framework':
            # DGCA has a nested structure inside dgca_framework folder
            dgca_base = os.path.join(temp_media_root, 'dgca_framework')
            
            # Find the sections folder inside dgca_framework
            sections_dir = None
            for item in os.listdir(dgca_base):
                item_path = os.path.join(dgca_base, item)
                if os.path.isdir(item_path) and item.startswith('sections_'):
                    sections_dir = item_path
                    break
            
            if not sections_dir:
                return JsonResponse({"success": False, "error": f"DGCA sections directory not found in {dgca_base}"}, status=404)
            
            pdf_path = os.path.join(sections_dir, 'sections', section_folder, f"{control_id}.pdf")
        else:
            # Standard structure for other frameworks (Basel, PCI DSS, etc.)
            pdf_path = os.path.join(temp_media_root, f'sections_{framework_key}', 'sections', section_folder, f"{control_id}.pdf")
        
        logger.info(f"Attempting to serve PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return JsonResponse({"success": False, "error": f"PDF file not found: {pdf_path}"}, status=404)
        
        # Serve the PDF file
        try:
            pdf_file = open(pdf_path, 'rb')
            response = FileResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{control_id}.pdf"'
            logger.info(f"Successfully serving PDF: {pdf_path}")
            return response
        except Exception as e:
            logger.exception(f"Error opening PDF file: {str(e)}")
            return JsonResponse({"success": False, "error": f"Error opening PDF file: {str(e)}"}, status=500)
        
    except Exception as e:
        logger.exception(f"Error getting default PDF content: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

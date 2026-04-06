"""
No-Index PDF Policy Extraction

Fallback approach for PDFs without usable index/TOC.
Extracts text page by page and uses centralized AI to generate policies and subpolicies directly.
Used when pdf_index_extractor fails or returns empty index.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from django.conf import settings
from ...ai.service import get_ai_service
from ...ai.types import AIRequestOptions
from ...debug_utils import debug_print
from ...utils.document_preprocessor import preprocess_document, calculate_document_hash

# PDF parsing imports (same as other modules)
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def extract_pdf_text_by_pages(pdf_path: str, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract text from PDF page by page without requiring index/TOC.
    
    Args:
        pdf_path: Path to the PDF file
        max_pages: Maximum number of pages to process (None for all pages)
        
    Returns:
        List of dicts with page number and text content
    """
    pages_data = []
    
    try:
        # Try pdfplumber first (best text extraction)
        if pdfplumber:
            debug_print(f"📄 Using pdfplumber to extract text from: {os.path.basename(pdf_path)}")
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                process_pages = min(total_pages, max_pages) if max_pages else total_pages
                debug_print(f"📄 Processing {process_pages} of {total_pages} pages")
                
                for page_num in range(process_pages):
                    try:
                        page = pdf.pages[page_num]
                        text = page.extract_text() or ""
                        
                        # Basic cleanup
                        text = text.strip()
                        if len(text) > 50:  # Only include pages with meaningful content
                            pages_data.append({
                                "page_number": page_num + 1,
                                "text": text,
                                "char_count": len(text)
                            })
                            debug_print(f"📄 Page {page_num + 1}: {len(text)} characters extracted")
                        else:
                            debug_print(f"📄 Page {page_num + 1}: Skipped (insufficient content)")
                    except Exception as e:
                        debug_print(f"⚠️ Error extracting page {page_num + 1}: {e}")
                        continue
                        
        # Fallback to PyPDF2 if pdfplumber failed or unavailable
        elif PyPDF2:
            debug_print(f"📄 Using PyPDF2 to extract text from: {os.path.basename(pdf_path)}")
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                process_pages = min(total_pages, max_pages) if max_pages else total_pages
                debug_print(f"📄 Processing {process_pages} of {total_pages} pages")
                
                for page_num in range(process_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text() or ""
                        
                        text = text.strip()
                        if len(text) > 50:
                            pages_data.append({
                                "page_number": page_num + 1,
                                "text": text,
                                "char_count": len(text)
                            })
                            debug_print(f"📄 Page {page_num + 1}: {len(text)} characters extracted")
                        else:
                            debug_print(f"📄 Page {page_num + 1}: Skipped (insufficient content)")
                    except Exception as e:
                        debug_print(f"⚠️ Error extracting page {page_num + 1}: {e}")
                        continue
                        
        # Fallback to PyMuPDF if available
        elif fitz:
            debug_print(f"📄 Using PyMuPDF to extract text from: {os.path.basename(pdf_path)}")
            with fitz.open(pdf_path) as pdf_doc:
                total_pages = len(pdf_doc)
                process_pages = min(total_pages, max_pages) if max_pages else total_pages
                debug_print(f"📄 Processing {process_pages} of {total_pages} pages")
                
                for page_num in range(process_pages):
                    try:
                        page = pdf_doc[page_num]
                        text = page.get_text() or ""
                        
                        text = text.strip()
                        if len(text) > 50:
                            pages_data.append({
                                "page_number": page_num + 1,
                                "text": text,
                                "char_count": len(text)
                            })
                            debug_print(f"📄 Page {page_num + 1}: {len(text)} characters extracted")
                        else:
                            debug_print(f"📄 Page {page_num + 1}: Skipped (insufficient content)")
                    except Exception as e:
                        debug_print(f"⚠️ Error extracting page {page_num + 1}: {e}")
                        continue
            
        else:
            raise Exception("No PDF parsing library available (pdfplumber, PyPDF2, or PyMuPDF required)")
            
    except Exception as e:
        debug_print(f"❌ PDF text extraction failed: {e}")
        raise
    
    debug_print(f"✅ Extracted text from {len(pages_data)} pages")
    return pages_data


def extract_framework_info_from_text(combined_text: str) -> Dict[str, Any]:
    """
    Extract basic framework information using centralized AI.
    
    Args:
        combined_text: Combined text from PDF pages
        
    Returns:
        Dict with framework name, description, category, etc.
    """
    print("[NO-INDEX] extract_framework_info_from_text: starting AI extraction")
    debug_print(f"🤖 Extracting framework info from {len(combined_text)} characters of text")
    
    try:
        ai_service = get_ai_service()
        
        # Use centralized AI task for framework structure extraction
        framework_info = ai_service.run_task(
            "policy.extract_framework_structure",
            payload={"document_text": combined_text[:8000]},  # Limit to first 8K chars for framework info
            options=AIRequestOptions(
                task_name="policy.extract_framework_structure",
                use_cache=True
            )
        )
        
        print(f"[NO-INDEX] extract_framework_structure DONE: sections={len(framework_info.get('sections', []))}")
        debug_print(f"✅ Framework info extracted: {framework_info.get('framework_name', 'N/A')}")
        return framework_info
        
    except Exception as e:
        debug_print(f"❌ Framework info extraction failed: {e}")
        # Return fallback framework info
        return {
            "framework_name": "Extracted Framework",
            "framework_description": "Framework extracted using no-index approach",
            "category": "Regulatory",
            "identifier_prefix": "NOIDX",
            "sections": []
        }


def extract_policies_from_text_chunks(text_chunks: List[str], chunk_labels: List[str]) -> List[Dict[str, Any]]:
    """
    Extract policies and subpolicies from text chunks using centralized AI.
    
    Args:
        text_chunks: List of text chunks to process
        chunk_labels: List of labels for each chunk (e.g., "Pages 1-5")
        
    Returns:
        List of sections with policies and subpolicies
    """
    print(f"[NO-INDEX] extract_policies_from_text_chunks: processing {len(text_chunks)} chunks")
    debug_print(f"🤖 Processing {len(text_chunks)} text chunks for policy extraction")
    
    ai_service = get_ai_service()
    extracted_sections = []
    
    for idx, (text_chunk, chunk_label) in enumerate(zip(text_chunks, chunk_labels)):
        try:
            print(f"[NO-INDEX] processing chunk {idx+1}/{len(text_chunks)}: {chunk_label}")
            debug_print(f"🔍 Processing chunk {idx+1}/{len(text_chunks)}: {chunk_label} ({len(text_chunk)} chars)")
            
            # Use centralized AI task for policy hierarchy extraction
            section_result = ai_service.run_task(
                "policy.extract_policy_hierarchy",
                payload={
                    "section_title": chunk_label,
                    "section_text": text_chunk
                },
                options=AIRequestOptions(
                    task_name="policy.extract_policy_hierarchy",
                    use_cache=True
                )
            )
            
            if isinstance(section_result, dict) and section_result.get("policies"):
                policies_count = len(section_result.get("policies", []))
                subpolicies_count = sum(len(p.get("subpolicies", [])) for p in section_result.get("policies", []))
                
                print(f"[NO-INDEX] chunk {idx+1} DONE: policies={policies_count}, subpolicies={subpolicies_count}")
                debug_print(f"✅ Chunk {idx+1}: {policies_count} policies, {subpolicies_count} subpolicies")
                
                # Enrich the section with metadata
                enriched_section = {
                    "section_title": chunk_label,
                    "section_name": f"section_{idx+1}",
                    "source_info": {
                        "extraction_method": "no_index_ai",
                        "chunk_index": idx,
                        "text_length": len(text_chunk)
                    },
                    "policies": section_result.get("policies", [])
                }
                extracted_sections.append(enriched_section)
            else:
                debug_print(f"⚠️ Chunk {idx+1}: No policies extracted")
                
        except Exception as e:
            debug_print(f"❌ Error processing chunk {idx+1} ({chunk_label}): {e}")
            continue
    
    total_policies = sum(len(section.get("policies", [])) for section in extracted_sections)
    total_subpolicies = sum(
        len(policy.get("subpolicies", []))
        for section in extracted_sections
        for policy in section.get("policies", [])
    )
    
    print(f"[NO-INDEX] extract_policies_from_text_chunks DONE: sections={len(extracted_sections)}, policies={total_policies}, subpolicies={total_subpolicies}")
    debug_print(f"✅ Total extracted: {len(extracted_sections)} sections, {total_policies} policies, {total_subpolicies} subpolicies")
    
    return extracted_sections


def create_text_chunks(pages_data: List[Dict[str, Any]], max_chunk_size: int = 4000) -> tuple[List[str], List[str]]:
    """
    Group pages into manageable chunks for AI processing.
    
    Args:
        pages_data: List of page data from extract_pdf_text_by_pages
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        Tuple of (text_chunks, chunk_labels)
    """
    text_chunks = []
    chunk_labels = []
    current_chunk = ""
    start_page = None
    end_page = None
    
    for page_data in pages_data:
        page_num = page_data["page_number"]
        page_text = page_data["text"]
        
        # If adding this page would exceed limit, save current chunk
        if current_chunk and len(current_chunk) + len(page_text) > max_chunk_size:
            text_chunks.append(current_chunk.strip())
            if start_page == end_page:
                chunk_labels.append(f"Page {start_page}")
            else:
                chunk_labels.append(f"Pages {start_page}-{end_page}")
            
            # Start new chunk
            current_chunk = page_text
            start_page = page_num
            end_page = page_num
        else:
            # Add to current chunk
            if not current_chunk:
                start_page = page_num
            current_chunk += "\n\n" + page_text if current_chunk else page_text
            end_page = page_num
    
    # Add final chunk
    if current_chunk.strip():
        text_chunks.append(current_chunk.strip())
        if start_page == end_page:
            chunk_labels.append(f"Page {start_page}")
        else:
            chunk_labels.append(f"Pages {start_page}-{end_page}")
    
    debug_print(f"📑 Created {len(text_chunks)} text chunks from {len(pages_data)} pages")
    return text_chunks, chunk_labels


def process_no_index_pdf(
    pdf_path: str,
    output_dir: str,
    user_id: str,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Main function to process PDF without index using centralized AI.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for results
        user_id: User ID for tracking
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dict with extraction results
    """
    def update_progress(progress: int, message: str):
        if progress_callback:
            progress_callback(progress, f"[No-Index] {message}")
        debug_print(f"📊 Progress {progress}%: {message}")
    
    try:
        print(f"[NO-INDEX] process_no_index_pdf: starting for user_id={user_id}")
        update_progress(5, "Starting no-index PDF processing...")
        
        # Step 1: Extract text page by page
        update_progress(15, "Extracting text from PDF pages...")
        pages_data = extract_pdf_text_by_pages(pdf_path, max_pages=100)  # Limit to first 100 pages
        
        if not pages_data:
            raise Exception("No text could be extracted from PDF")
        
        total_chars = sum(p["char_count"] for p in pages_data)
        update_progress(25, f"Extracted text from {len(pages_data)} pages ({total_chars:,} characters)")
        
        # Step 2: Create text chunks for processing
        update_progress(35, "Creating text chunks for AI processing...")
        text_chunks, chunk_labels = create_text_chunks(pages_data, max_chunk_size=4000)
        
        # Step 3: Extract framework information from first chunk
        update_progress(45, "Extracting framework information...")
        combined_text = "\n\n".join(chunk[:2000] for chunk in text_chunks[:3])  # First 3 chunks, 2K chars each
        framework_info = extract_framework_info_from_text(combined_text)
        
        # Step 4: Extract policies from all chunks
        update_progress(60, "Extracting policies and subpolicies using AI...")
        extracted_sections = extract_policies_from_text_chunks(text_chunks, chunk_labels)
        
        # Step 5: Prepare results
        update_progress(85, "Preparing extraction results...")
        
        # Create output directory structure
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save framework info
        framework_file = Path(output_dir) / "framework_info.json"
        with open(framework_file, 'w', encoding='utf-8') as f:
            json.dump(framework_info, f, indent=2, ensure_ascii=False)
        
        # Save sections data (for debugging)
        sections_file = Path(output_dir) / "extracted_sections.json"
        sections_data = {
            "metadata": {
                "extraction_method": "no_index_ai",
                "user_id": user_id,
                "pdf_path": pdf_path,
                "total_pages": len(pages_data),
                "total_chunks": len(text_chunks),
                "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_characters": total_chars
            },
            "sections": extracted_sections
        }
        
        with open(sections_file, 'w', encoding='utf-8') as f:
            json.dump(sections_data, f, indent=2, ensure_ascii=False)
        
        # Create compatible data files for existing APIs
        user_folder_path = Path(output_dir).parent  # Go up one level to get upload_{user_id}
        
        # 1. Create all_policies.json (expected by build_complete_structure)
        all_policies_file = user_folder_path / "all_policies.json"
        all_policies_data = create_all_policies_format(extracted_sections, framework_info)
        with open(all_policies_file, 'w', encoding='utf-8') as f:
            json.dump(all_policies_data, f, indent=2, ensure_ascii=False)
        
        # 2. Create framework_data.json (expected by load_consolidated_json)
        framework_data_file = user_folder_path / "framework_data.json"
        framework_data = create_framework_data_format(extracted_sections, framework_info, user_id)
        with open(framework_data_file, 'w', encoding='utf-8') as f:
            json.dump(framework_data, f, indent=2, ensure_ascii=False)
        
        print(f"[NO-INDEX] Created compatible data files: all_policies.json, framework_data.json")
        
        # Calculate summary statistics
        total_policies = sum(len(section.get("policies", [])) for section in extracted_sections)
        total_subpolicies = sum(
            len(policy.get("subpolicies", []))
            for section in extracted_sections
            for policy in section.get("policies", [])
        )
        
        result = {
            "status": "success",
            "method": "no_index_ai",
            "data": {
                "user_folder": f"upload_{user_id}",
                "framework_info": framework_info,
                "sections": len(extracted_sections),
                "policies": total_policies,
                "subpolicies": total_subpolicies,
                "pages_processed": len(pages_data),
                "chunks_processed": len(text_chunks),
                "total_characters": total_chars
            },
            "files": {
                "framework_info": str(framework_file),
                "sections_data": str(sections_file)
            }
        }
        
        update_progress(100, f"No-index processing completed: {total_policies} policies, {total_subpolicies} subpolicies")
        print(f"[NO-INDEX] process_no_index_pdf DONE: {result['data']}")
        
        return result
        
    except Exception as e:
        error_msg = f"No-index processing failed: {str(e)}"
        update_progress(100, error_msg)
        print(f"[NO-INDEX] ERROR: {error_msg}")
        debug_print(f"❌ {error_msg}")
        return {
            "status": "error",
            "method": "no_index_ai",
            "error": str(e),
            "data": {
                "user_folder": f"upload_{user_id}",
                "sections": 0,
                "policies": 0,
                "subpolicies": 0
            }
        }


def create_all_policies_format(sections: List[Dict[str, Any]], framework_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create all_policies.json format expected by build_complete_structure.
    
    Args:
        sections: Extracted sections with policies and subpolicies
        framework_info: Framework metadata
        
    Returns:
        Dict in all_policies.json format
    """
    all_policies: List[Dict[str, Any]] = []
    policy_id_counter = 1

    for section in sections:
        section_title = section.get("section_title", "Untitled Section")
        section_name = section.get("section_name", f"section_{policy_id_counter}")

        for policy in section.get("policies", []):
            # Prefer AI policy title; if missing, derive a meaningful fallback
            raw_title = (policy.get("policy_title") or "").strip()
            if not raw_title:
                base = (framework_info.get("framework_name") or "").strip() or "Framework Policy"
                first_sub = (policy.get("subpolicies") or [{}])[0]
                sub_title = (first_sub.get("subpolicy_title") or "").strip()
                if section_title and sub_title:
                    raw_title = f"{base} - {sub_title}"
                elif section_title:
                    raw_title = f"{base} - {section_title}"
                elif sub_title:
                    raw_title = f"{base} - {sub_title}"
                else:
                    raw_title = base

            policy_data = {
                "policy_id": f"POL_{policy_id_counter:03d}",
                "policy_title": raw_title,
                "policy_description": policy.get("policy_description", ""),
                "section_title": section_title,
                "section_name": section_name,
                "scope": policy.get("scope", ""),
                "objective": policy.get("objective", ""),
                "policy_type": policy.get("policy_type", "Regulatory"),
                "policy_category": policy.get("policy_category", "Compliance"),
                "policy_subcategory": policy.get("policy_subcategory", "General"),
                "ai_analysis": policy.get("ai_analysis", {}),
                "subpolicies": []
            }
            
            # Add subpolicies
            subpolicy_id_counter = 1
            for subpolicy in policy.get("subpolicies", []):
                subpolicy_data = {
                    "subpolicy_id": f"SP_{policy_id_counter:03d}_{subpolicy_id_counter:02d}",
                    "subpolicy_title": subpolicy.get("subpolicy_title", "Untitled Subpolicy"),
                    "subpolicy_description": subpolicy.get("subpolicy_description", ""),
                    "control": subpolicy.get("control", ""),
                    "ai_analysis": subpolicy.get("ai_analysis", {}),
                    "policy_id": policy_data["policy_id"]
                }
                policy_data["subpolicies"].append(subpolicy_data)
                subpolicy_id_counter += 1
            
            all_policies.append(policy_data)
            policy_id_counter += 1
    
    return {
        "metadata": {
            "extraction_method": "no_index_ai",
            "framework_name": framework_info.get("framework_name", "No-Index Framework"),
            "total_policies": len(all_policies),
            "total_subpolicies": sum(len(p["subpolicies"]) for p in all_policies),
            "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "policies": all_policies
    }


def create_framework_data_format(sections: List[Dict[str, Any]], framework_info: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Create framework_data.json format expected by load_consolidated_json.
    
    Args:
        sections: Extracted sections with policies and subpolicies
        framework_info: Framework metadata
        user_id: User ID
        
    Returns:
        Dict in framework_data.json format
    """
    # Convert sections to the expected format
    formatted_sections = []
    
    for idx, section in enumerate(sections):
        section_id = f"sect_{idx+1:03d}"
        formatted_section = {
            "section_id": section_id,
            "title": section.get("section_title", f"Section {idx+1}"),
            "level": 1,
            "folder_path": f"no_index_section_{idx+1}",
            "source_info": section.get("source_info", {}),
            "policies": []
        }
        
        # Convert policies
        for policy_idx, policy in enumerate(section.get("policies", [])):
            policy_id = f"pol_{idx+1:03d}_{policy_idx+1:02d}"
            # Prefer AI title; if empty, derive a better one
            raw_title = (policy.get("policy_title") or "").strip()
            if not raw_title:
                base = (framework_info.get("framework_name") or "").strip() or "Framework Policy"
                first_sub = (policy.get("subpolicies") or [{}])[0]
                sub_title = (first_sub.get("subpolicy_title") or "").strip()
                section_title = section.get("section_title", "").strip()
                if section_title and sub_title:
                    raw_title = f"{base} - {sub_title}"
                elif sub_title:
                    raw_title = f"{base} - {sub_title}"
                elif section_title:
                    raw_title = f"{base} - {section_title}"
                else:
                    raw_title = base

            formatted_policy = {
                "policy_id": policy_id,
                "policy_title": raw_title,
                "policy_description": policy.get("policy_description", ""),
                "scope": policy.get("scope", ""),
                "objective": policy.get("objective", ""),
                "policy_type": policy.get("policy_type", "Regulatory"),
                "policy_category": policy.get("policy_category", "Compliance"),
                "policy_subcategory": policy.get("policy_subcategory", "General"),
                "ai_analysis": policy.get("ai_analysis", {}),
                "subpolicies": []
            }
            
            # Convert subpolicies
            for subpolicy_idx, subpolicy in enumerate(policy.get("subpolicies", [])):
                subpolicy_id = f"sp_{idx+1:03d}_{policy_idx+1:02d}_{subpolicy_idx+1:02d}"
                formatted_subpolicy = {
                    "subpolicy_id": subpolicy_id,
                    "subpolicy_title": subpolicy.get("subpolicy_title", "Untitled Subpolicy"),
                    "subpolicy_description": subpolicy.get("subpolicy_description", ""),
                    "subpolicy_text": subpolicy.get("control", ""),  # Map control to subpolicy_text
                    "control": subpolicy.get("control", ""),
                    "ai_analysis": subpolicy.get("ai_analysis", {}),
                    "policy_id": formatted_policy["policy_id"]
                }
                formatted_policy["subpolicies"].append(formatted_subpolicy)
            
            formatted_section["policies"].append(formatted_policy)
        
        formatted_sections.append(formatted_section)
    
    # Calculate totals
    total_policies = sum(len(section["policies"]) for section in formatted_sections)
    total_subpolicies = sum(
        len(policy["subpolicies"]) 
        for section in formatted_sections 
        for policy in section["policies"]
    )
    
    return {
        "framework_info": {
            "framework_name": framework_info.get("framework_name", "No-Index Framework"),
            "framework_description": framework_info.get("framework_description", "Framework extracted using no-index approach"),
            "category": framework_info.get("category", "Regulatory"),
            "identifier_prefix": framework_info.get("identifier_prefix", "NOIDX"),
            "extraction_method": "no_index_ai"
        },
        "sections": formatted_sections,
        "summary": {
            "total_sections": len(formatted_sections),
            "total_policies": total_policies,
            "total_subpolicies": total_subpolicies
        },
        "metadata": {
            "user_id": user_id,
            "extraction_method": "no_index_ai",
            "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "no_index_pdf_processing"
        }
    }


def is_no_index_approach_needed(index_data: Optional[Dict[str, Any]]) -> bool:
    """
    Determine if no-index approach should be used based on index extraction results.
    
    Args:
        index_data: Result from pdf_index_extractor, or None if extraction failed
        
    Returns:
        True if no-index approach should be used
    """
    if index_data is None:
        return True
    
    items = index_data.get('items', [])
    if not items or len(items) == 0:
        return True
    
    # Check if index has meaningful content
    meaningful_items = [
        item for item in items
        if item.get('title') and len(item.get('title', '').strip()) > 3
    ]
    
    if len(meaningful_items) < 2:  # Need at least 2 meaningful index items
        return True
    
    return False
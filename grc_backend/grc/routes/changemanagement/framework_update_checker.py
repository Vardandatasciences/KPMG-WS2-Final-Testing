import json
import logging
import os
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)


def create_system_prompt(framework_name: str, last_updated_date: str) -> str:
    """Create system prompt for Perplexity API."""
    return f"""You are a GRC (Governance, Risk, and Compliance) framework update tracker.

Your task is to check if the {framework_name} framework has been updated after {last_updated_date} and find the DIRECT PDF download link for the LATEST AMENDMENT document (NOT the full framework document).

CRITICAL: The has_update field should ONLY be true if the latest official update date is AFTER {last_updated_date}.
If the latest update is on or before {last_updated_date}, set has_update to false.

IMPORTANT: You are looking for AMENDMENT documents, NOT the full framework document.
- Amendments are typically smaller PDFs (usually 10-100 pages) that describe changes/updates
- Full framework documents are large (hundreds of pages) - DO NOT download these
- Search for terms like: "amendment", "update", "change document", "revision", "supplement"
- Look for documents titled: "Amendment to...", "Update to...", "Changes to...", "Revision..."

Instructions:
1. Search for the latest official AMENDMENT/UPDATE document of {framework_name} (NOT the full framework)
2. Find the exact release/publication date of the latest amendment
3. Compare the latest update date with {last_updated_date}
4. Set has_update to true ONLY if latest_update_date > {last_updated_date}
5. MOST IMPORTANT: Find the DIRECT PDF download link for the LATEST AMENDMENT document only
6. Respond ONLY in the following JSON format (no additional text):

{{
    "framework_name": "{framework_name}",
    "has_update": true or false,
    "latest_update_date": "YYYY-MM-DD",
    "document_url": "DIRECT PDF download URL for AMENDMENT" or null,
    "version": "version number if available",
    "notes": "brief description of changes if updated"
}}

CRITICAL REQUIREMENTS FOR document_url:
- document_url MUST be a DIRECT download link to an AMENDMENT PDF file (must end with .pdf)
- document_url MUST be for the AMENDMENT document, NOT the full framework document
- Amendment documents are typically smaller PDFs (10-100 pages)
- DO NOT download full framework documents (which are large, 200+ pages)
- Search specifically for: "amendment PDF", "update PDF", "change document PDF", "revision PDF"
- Look for URLs containing words like: amendment, update, changes, revision, supplement
- document_url MUST be the actual PDF file URL, NOT a webpage or HTML page
- Look for URLs like: https://example.com/amendment-2025.pdf or https://example.com/updates/changes.pdf
- DO NOT provide page URLs like https://example.com/pages/document (these are HTML pages)
- DO NOT provide URLs that redirect to pages - find the actual PDF file URL
- If you cannot find a direct AMENDMENT PDF download link, set document_url to null
- Use only official sources (nist.gov, iso.org, hhs.gov, etc.)
- Focus on finding the PDF for the LATEST AMENDMENT ONLY (small document, not full framework)

Other Requirements:
- has_update must be true ONLY if latest_update_date is AFTER {last_updated_date}
- If latest_update_date is same as or before {last_updated_date}, set has_update to false
- If no update found or dates are equal/before, set has_update to false and document_url to null
- If update found but no AMENDMENT PDF download link available, set document_url to null

Example date comparison:
- If last_updated_date is 2025-09-13 and latest is 2025-08-27: has_update = false
- If last_updated_date is 2025-08-27 and latest is 2025-09-13: has_update = true

Example of GOOD document_url (AMENDMENT documents):
- https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/upd1/final/sp800-53r5-upd1.pdf (amendment)
- https://example.com/downloads/framework-amendment-2025.pdf (amendment)
- https://example.com/updates/changes-to-framework.pdf (amendment)

Example of BAD document_url (DO NOT USE):
- https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final/sp800-53r5.pdf (full framework, too large)
- https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final (this is a webpage, not a PDF)
- https://example.com/pages/document (this is an HTML page)
- Any URL to the complete/full framework document (these are too large)"""


def _clean_response_content(content: str) -> str:
    """Remove markdown fences and return raw JSON string."""
    if "```json" in content:
        return content.split("```json", 1)[1].split("```", 1)[0].strip()
    if "```" in content:
        return content.split("```", 1)[1].split("```", 1)[0].strip()
    return content.strip()


def query_perplexity_api(framework_name: str, last_updated_date: str, api_key: str) -> dict:
    """Call Perplexity API and return parsed JSON response."""
    if not api_key:
        raise ValueError("Perplexity API key is required")

    system_prompt = create_system_prompt(framework_name, last_updated_date)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "user",
                "content": (
                    f"{system_prompt}\n\n"
                    f"Check if {framework_name} has been updated after {last_updated_date}. "
                    f"Find the DIRECT PDF download link for the LATEST AMENDMENT document (NOT the full framework). "
                    f"Amendment documents are typically small PDFs (10-100 pages) that describe changes. "
                    f"DO NOT download the full framework document (which is large, 200+ pages). "
                    f"Search specifically for: 'amendment PDF', 'update PDF', 'change document PDF'. "
                    f"The document_url MUST be a direct PDF file URL (ending in .pdf), NOT a webpage. "
                    f"Look for URLs containing words like: amendment, update, changes, revision."
                ),
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1000,
    }

    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error_msg = f"Perplexity API error: {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg += " - Unauthorized. Please check that your PERPLEXITY_API_KEY is valid and correctly set in the environment variables."
            logger.error(f"{error_msg} API key length: {len(api_key)}, starts with: {api_key[:10] if api_key else 'None'}...")
        else:
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {e.response.text[:200]}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except requests.exceptions.RequestException as e:
        error_msg = f"Perplexity API request failed: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    # Log raw response for debugging
    logger.info(f"Perplexity API raw response for {framework_name}: {content[:500]}...")
    
    parsed = json.loads(_clean_response_content(content))
    logger.info(f"Parsed update info: has_update={parsed.get('has_update')}, latest_update_date={parsed.get('latest_update_date')}, document_url={parsed.get('document_url')}")

    # Validate date ordering per business rules
    if parsed.get("has_update") and parsed.get("latest_update_date"):
        try:
            latest_date = datetime.strptime(parsed["latest_update_date"], "%Y-%m-%d").date()
            last_known = datetime.strptime(last_updated_date, "%Y-%m-%d").date()
            if latest_date <= last_known:
                parsed["has_update"] = False
        except ValueError:
            parsed["has_update"] = False
    
    # Validate document_url - must be a PDF URL
    doc_url = parsed.get("document_url")
    if doc_url:
        # Check if it's a valid PDF URL
        if not doc_url.lower().endswith('.pdf'):
            logger.warning(f"document_url from Perplexity is not a PDF URL: {doc_url}. Will attempt to find PDF link.")
            # Keep the URL so we can try to find the PDF from it
        else:
            logger.info(f"document_url appears to be a valid PDF URL: {doc_url}")

    return parsed


def find_actual_pdf_url(page_url: str, framework_name: str, api_key: str) -> Optional[str]:
    """Use Perplexity to find the actual PDF download link from a page for the latest amendment"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "user",
                "content": f"""Find the DIRECT PDF download link for the LATEST AMENDMENT of {framework_name} from this page: {page_url}

CRITICAL REQUIREMENTS:
1. Find the ACTUAL downloadable AMENDMENT PDF file link (MUST end with .pdf)
2. You are looking for AMENDMENT documents (small PDFs, 10-100 pages), NOT the full framework document
3. Amendment documents are typically titled: "Amendment to...", "Update to...", "Changes to...", "Revision..."
4. The URL must be a direct link to a PDF file, NOT a webpage or HTML page
5. Look specifically for the LATEST AMENDMENT PDF download link (small document, not full framework)
6. Search for links containing words like: "amendment", "update", "changes", "revision", "supplement"
7. Search for links like "Download Amendment PDF", "View Update PDF", "PDF Download", or direct .pdf file URLs
8. The URL should look like: https://example.com/amendment.pdf or https://example.com/downloads/update-2025.pdf
9. Do NOT return page URLs like https://example.com/pages/document (these are HTML pages)
10. Do NOT return URLs to full framework documents (these are too large, 200+ pages)
11. If multiple PDFs exist, return the PDF for the LATEST AMENDMENT only (smallest/shortest document)
12. Return ONLY the direct PDF URL, nothing else

Examples of GOOD AMENDMENT PDF URLs:
- https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/upd1/final/sp800-53r5-upd1.pdf (amendment)
- https://example.com/downloads/framework-amendment-2025.pdf (amendment)
- https://example.com/updates/changes-to-framework.pdf (amendment)

Examples of BAD URLs (DO NOT USE):
- https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final/sp800-53r5.pdf (full framework, too large)
- https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final (this is a webpage)
- https://example.com/pages/document (this is an HTML page)
- Any URL to the complete/full framework document (these are too large)

Respond with ONLY the PDF URL or "NOT_FOUND" if no direct AMENDMENT PDF download link exists."""
            }
        ],
        "temperature": 0.1,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        pdf_url = result['choices'][0]['message']['content'].strip()
        
        # Clean up the response
        if pdf_url and pdf_url != "NOT_FOUND" and ".pdf" in pdf_url.lower():
            # Remove any markdown or extra text
            if "http" in pdf_url:
                # Extract just the URL
                urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+\.pdf', pdf_url)
                if urls:
                    return urls[0]
        
        return None
        
    except Exception as e:
        return None


def download_document(
    framework_name: str,
    document_url: str,
    download_dir: str,
    api_key: Optional[str] = None,
    store_in_media: bool = True,
) -> Optional[str]:
    """Download framework document - uses robust logic from framework_testing.py"""
    
    if not document_url:
        logger.warning("No document_url provided for download")
        return None
    
    # If store_in_media is True, use MEDIA_ROOT/change_management/
    if store_in_media:
        from django.conf import settings
        download_dir = os.path.join(settings.MEDIA_ROOT, 'change_management')
        logger.info(f"Storing document in MEDIA_ROOT/change_management/: {download_dir}")
    
    # Create download directory
    os.makedirs(download_dir, exist_ok=True)
    logger.info(f"Download directory: {download_dir}")
    
    def _attempt_download(url: str):
        logger.info(f"Downloading from: {url}")
        resp = requests.get(url, stream=True, timeout=60, allow_redirects=True)
        resp.raise_for_status()
        return resp
    
    try:
        url_to_fetch = document_url
        logger.info(f"Attempting to download from URL: {document_url}")
        
        # Validate URL - must be a direct PDF link
        if not document_url.lower().endswith('.pdf'):
            logger.info("URL does not end with .pdf, attempting to discover a direct PDF link for latest amendment...")
            
            # 1) Try plain HTML scraping for PDF links on the page
            try:
                page_resp = requests.get(document_url, timeout=30)
                page_resp.raise_for_status()
                html = page_resp.text or ""
                logger.info(f"Fetched HTML page for PDF discovery, length={len(html)}")

                # Find all .pdf hrefs
                raw_links = re.findall(r'href=["\\\'](.*?\\.pdf)["\\\']', html, flags=re.IGNORECASE)
                pdf_links = []
                seen_links = set()
                for href in raw_links:
                    absolute = urljoin(document_url, href)
                    if absolute not in seen_links:
                        seen_links.add(absolute)
                        pdf_links.append(absolute)

                if pdf_links:
                    # Prefer links that look like amendments/updates
                    def _score(link: str) -> int:
                        s = link.lower()
                        score = 0
                        if 'amend' in s:
                            score += 3
                        if 'update' in s or 'upd' in s:
                            score += 2
                        if 'rev' in s or 'revision' in s:
                            score += 1
                        if framework_name and any(part.lower() in s for part in framework_name.split()):
                            score += 1
                        return score

                    pdf_links.sort(key=_score, reverse=True)
                    url_to_fetch = pdf_links[0]
                    logger.info(f"Discovered PDF link via HTML scraping: {url_to_fetch}")
                elif api_key:
                    # 2) Fall back to Perplexity-based discovery if scraping fails
                    logger.info("No PDF links found via HTML scraping, falling back to Perplexity PDF discovery...")
                    direct_pdf_url = find_actual_pdf_url(document_url, framework_name, api_key)
                    if direct_pdf_url and direct_pdf_url.lower().endswith('.pdf') and direct_pdf_url != "NOT_FOUND":
                        logger.info(f"Found direct PDF URL via Perplexity: {direct_pdf_url}")
                        url_to_fetch = direct_pdf_url
                    else:
                        logger.warning("Could not find direct PDF download link for the latest amendment. PDF document is not available.")
                        return None
                else:
                    logger.warning("No PDF links found via HTML scraping and no API key provided for Perplexity discovery. PDF document is not available.")
                    return None
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to fetch HTML page for PDF discovery: {str(e)}")
                # If we have an API key, still try Perplexity as a fallback
                if api_key:
                    direct_pdf_url = find_actual_pdf_url(document_url, framework_name, api_key)
                    if direct_pdf_url and direct_pdf_url.lower().endswith('.pdf') and direct_pdf_url != "NOT_FOUND":
                        logger.info(f"Found direct PDF URL via Perplexity after HTML fetch failure: {direct_pdf_url}")
                        url_to_fetch = direct_pdf_url
                    else:
                        logger.warning("Could not find direct PDF download link for the latest amendment after HTML fetch failure. PDF document is not available.")
                        return None
                else:
                    return None
        else:
            # URL ends with .pdf, but verify it's actually a PDF URL (not a redirect)
            logger.info("URL appears to be a PDF link, proceeding with download...")
        
        # Try to download the file, with fallback if the direct link fails
        response = None
        try:
            response = _attempt_download(url_to_fetch)
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error downloading {url_to_fetch}: {http_err}")
            # If the direct link failed but we have an API key, ask Perplexity for another PDF URL
            if api_key:
                logger.info("Attempting to locate alternate PDF URL via Perplexity...")
                alternate_url = find_actual_pdf_url(document_url, framework_name, api_key)
                if alternate_url and alternate_url.lower().endswith('.pdf') and alternate_url != url_to_fetch:
                    logger.info(f"Alternate PDF URL found: {alternate_url}")
                    url_to_fetch = alternate_url
                    response = _attempt_download(url_to_fetch)
            if response is None:
                raise
        except Exception:
            raise
        
        # Check if we actually got a PDF
        content_type = response.headers.get('content-type', '').lower()
        logger.info(f"Response content-type: {content_type}")
        
        # Create temporary filename for download
        safe_name = framework_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filepath = os.path.join(download_dir, f"{safe_name}_{timestamp}.tmp")
        
        # Download file first to check if it's actually a PDF
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        logger.info(f"Downloading {total_size} bytes to temporary file: {temp_filepath}")
        
        with open(temp_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        
        logger.info(f"Downloaded {downloaded} bytes to temporary file")
        
        # Verify it's actually a PDF by checking magic number
        try:
            with open(temp_filepath, 'rb') as f:
                first_bytes = f.read(4)
                if first_bytes != b'%PDF':
                    # Not a PDF file, delete it and return None
                    os.remove(temp_filepath)
                    logger.warning(f"Downloaded file is not a PDF (magic number: {first_bytes}). PDF document is not available.")
                    return None
        except Exception as e:
            # If we can't read the file, delete it and return None
            try:
                os.remove(temp_filepath)
            except:
                pass
            logger.warning(f"Could not verify PDF file: {str(e)}. PDF document is not available.")
            return None
        
        # Check file size - amendments are typically smaller (1-15 MB), full frameworks are large (20+ MB)
        file_size_mb = downloaded / (1024 * 1024)
        MAX_AMENDMENT_SIZE_MB = 15  # Amendments are typically 1-15 MB
        
        if file_size_mb > MAX_AMENDMENT_SIZE_MB:
            # File is too large, likely the full framework document, not an amendment
            os.remove(temp_filepath)
            logger.warning(f"Downloaded PDF is too large ({file_size_mb:.2f} MB). This appears to be the full framework document, not an amendment. Amendments are typically 1-15 MB. PDF document is not available.")
            return None
        
        logger.info(f"PDF file size: {file_size_mb:.2f} MB (acceptable for amendment document)")
        
        # It's a valid PDF and size is appropriate for an amendment, rename to .pdf extension
        filename = f"{safe_name}_{timestamp}.pdf"
        filepath = os.path.join(download_dir, filename)
        os.rename(temp_filepath, filepath)
        
        logger.info(f"Successfully downloaded amendment PDF: {filepath} ({downloaded} bytes, {file_size_mb:.2f} MB)")
        
        # Upload to S3 after successful download
        try:
            from grc.routes.Global.s3_fucntions import create_direct_mysql_client
            from django.conf import settings
            
            logger.info("Uploading document to S3...")
            s3_client = create_direct_mysql_client()
            
            # Get user_id from settings or use default
            user_id = getattr(settings, 'DEFAULT_USER_ID', 'system')
            
            # Upload to S3 with changemanagement module
            upload_result = s3_client.upload(
                file_path=filepath,
                user_id=user_id,
                custom_file_name=filename,
                module='changemanagement'
            )
            
            if upload_result.get('success'):
                s3_url = upload_result['file_info']['url']
                logger.info(f"Successfully uploaded to S3: {s3_url}")
                # Return both local path and S3 URL as a dict
                return {
                    'local_path': filepath,
                    's3_url': s3_url,
                    's3_key': upload_result['file_info'].get('s3Key', ''),
                    'stored_name': upload_result['file_info'].get('storedName', filename)
                }
            else:
                logger.warning(f"Failed to upload to S3: {upload_result.get('error')}")
                # Return just local path if S3 upload fails
                return filepath
                
        except Exception as s3_error:
            logger.error(f"Error uploading to S3: {str(s3_error)}")
            import traceback
            logger.error(traceback.format_exc())
            # Return local path even if S3 upload fails
            return filepath
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error downloading document: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading document: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def run_framework_update_check(
    framework_name: str,
    last_updated_date: str,
    api_key: str,
    download_dir: Optional[str] = None,
    framework_id: Optional[int] = None,
    process_amendment: bool = False,
    store_in_media: bool = True,
) -> dict:
    """
    Run the Perplexity check for a framework.

    Args:
        framework_name: Name of the framework
        last_updated_date: Last known update date (YYYY-MM-DD)
        api_key: Perplexity API key
        download_dir: Directory to save downloaded documents (ignored if store_in_media=True)
        framework_id: Framework ID for processing (optional)
        process_amendment: Whether to process the downloaded amendment (default: False)
        store_in_media: Whether to store in MEDIA_ROOT/change_management/ (default: True)

    Returns:
        dict with keys: has_update, latest_update_date, document_url, version,
        notes, downloaded_path (optional), processing_result (optional)
    """
    download_folder = download_dir or "downloads"
    update_info = query_perplexity_api(framework_name, last_updated_date, api_key)

    downloaded_path = None
    downloaded_info = None  # Will contain S3 info if available
    processing_result = None
    
    # Log the update check results
    logger.info(f"Update check results for {framework_name}: has_update={update_info.get('has_update')}, document_url={update_info.get('document_url')}")
    
    if update_info.get("has_update") and update_info.get("document_url"):
        logger.info(f"Attempting to download document from: {update_info['document_url']}")
        try:
            download_result = download_document(
                framework_name,
                update_info["document_url"],
                download_folder,
                api_key=api_key,
                store_in_media=store_in_media,
            )
            
            if download_result:
                # Handle both dict (with S3 info) and string (local path only) returns
                if isinstance(download_result, dict):
                    downloaded_path = download_result.get('local_path')
                    downloaded_info = download_result
                    logger.info(f"Successfully downloaded and uploaded to S3: {downloaded_info.get('s3_url')}")
                else:
                    downloaded_path = download_result
                    logger.info(f"Successfully downloaded amendment document for {framework_name} to {downloaded_path}")
                
                # Only process the downloaded amendment if explicitly requested
                # Note: By default, we now wait for manual trigger via "Start Analysis" button
                if process_amendment and framework_id and downloaded_path and downloaded_path.lower().endswith('.pdf'):
                    try:
                        from .amendment_processor import process_downloaded_amendment
                        
                        logger.info(f"Starting amendment processing for {framework_name}")
                        
                        # Use the download directory as the output directory for processing
                        output_dir = download_dir if download_dir else os.path.dirname(downloaded_path)
                        
                        processing_result = process_downloaded_amendment(
                            pdf_path=downloaded_path,
                            framework_name=framework_name,
                            framework_id=framework_id,
                            amendment_date=update_info.get('latest_update_date', last_updated_date),
                            output_dir=output_dir
                        )
                        
                        if processing_result.get('success'):
                            logger.info(f"Successfully processed amendment: {processing_result.get('output_file')}")
                        else:
                            logger.error(f"Amendment processing failed: {processing_result.get('error')}")
                            
                    except Exception as e:
                        logger.error(f"Error processing amendment: {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())
                        processing_result = {
                            'success': False,
                            'error': str(e)
                        }
            else:
                logger.warning(f"Download failed or returned None for {framework_name}. document_url was: {update_info.get('document_url')}")
                        
        except Exception as e:
            logger.error(f"Error downloading document for {framework_name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            downloaded_path = None
    else:
        if not update_info.get("has_update"):
            logger.info(f"No update found for {framework_name} (has_update=False)")
        elif not update_info.get("document_url"):
            logger.warning(f"Update found for {framework_name} but no document_url provided")

    result = {
        **update_info,
        "downloaded_path": downloaded_path,
    }
    
    # Add S3 information if available
    if downloaded_info and isinstance(downloaded_info, dict):
        result["s3_url"] = downloaded_info.get('s3_url')
        result["s3_key"] = downloaded_info.get('s3_key')
        result["s3_stored_name"] = downloaded_info.get('stored_name')
    
    if processing_result:
        result["processing_result"] = processing_result
    
    return result


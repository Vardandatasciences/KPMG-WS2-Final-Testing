import json
import re
try:
    from ...debug_utils import debug_print
except ImportError:
    def debug_debug_print(*args, **kwargs): pass
from pathlib import Path
from collections import Counter

# ---------- Normalization helpers ----------
DASHES = r"[\u2010\u2011\u2012\u2013\u2014\u2212]"

def norm_dashes(s: str) -> str:
    return re.sub(DASHES, "-", s)

def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def slug(s: str, maxlen: int = 40) -> str:
    """Create a filesystem-safe slug from a string, with shorter max length to avoid path issues."""
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)
    s = re.sub(r"_+", "_", s).strip("_")
    if len(s) > maxlen:
        s = s[:maxlen].rstrip("_")
    return s or "section"

# ---------- PDF helpers ----------
def load_doc(pdf_path: str):
    import fitz  # PyMuPDF
    return fitz.open(pdf_path)

# ---------- Detect printed page number offset ----------
def detect_page_offset(items, doc):
    page_texts = [norm_ws(norm_dashes(doc[i].get_text("text"))).lower() for i in range(len(doc))]
    offsets = []
    
    for it in items:
        pn = it.get("page_number")
        if not isinstance(pn, int) or pn < 1:
            continue
        printed_idx = pn - 1
        title_norm = norm_ws(norm_dashes(it["title"])).lower()

        # Look for the title as a heading (not in TOC), prioritize pages with less TOC-like content
        for idx in range(max(0, printed_idx - 3), min(len(doc), printed_idx + 8)):
            page_text = page_texts[idx]
            
            # Skip if this looks like a TOC page (has many dot leaders or multiple numbered items)
            if (page_text.count('....') > 3 or 
                page_text.count('table of contents') > 0 or
                len(re.findall(r'\d+\..*?\d+$', page_text, re.MULTILINE)) > 5):
                continue
                
            # Look for title as a heading (usually at start of line or after page header)
            if title_norm in page_text:
                # Check if it appears as a heading (not just mentioned)
                title_pos = page_text.find(title_norm)
                # Look for context that suggests this is the actual section start
                context_before = page_text[max(0, title_pos-100):title_pos].lower()
                context_after = page_text[title_pos:title_pos+200].lower()
                
                # Strong indicators this is the actual section, not TOC
                if (any(phrase in context_after for phrase in ['this document', 'this section', 'the following']) or
                    any(phrase in context_before for phrase in [f'{pn} ', f'page {pn}', f'{pn}\n']) or
                    (title_pos < 200 and 'overview' in title_norm)):  # Likely at start of page
                    offsets.append(idx - printed_idx)
                    break

    if offsets:
        most_common_offset = Counter(offsets).most_common(1)[0][0]
        debug_print(f"[INFO] Detected printed→PDF page offset: {most_common_offset}")
        return most_common_offset
    else:
        debug_print("[WARN] No offset detected, assuming printed page N = PDF index N-1 (offset 0)")
        # Default: printed page 1 = PDF index 0, printed 4 = PDF index 3 (common for PCI DSS, etc.)
        return 0

# ---------- Assign start pages (with offset) ----------
def assign_start_pages(items, doc):
    offset = detect_page_offset(items, doc)
    doc_len = len(doc)
    starts = {}
    out_of_range = {}
    for it in items:
        pn = it.get("page_number")
        if isinstance(pn, int) and pn >= 1:
            raw_idx = (pn - 1) + offset
            # If computed start is beyond the document (e.g. cropped PDF), mark as out of range
            if raw_idx >= doc_len:
                starts[it["title"]] = doc_len - 1  # clamp for ordering; content will be left empty
                out_of_range[it["title"]] = True
            else:
                idx = max(0, min(raw_idx, doc_len - 1))
                starts[it["title"]] = idx
                out_of_range[it["title"]] = False
        else:
            starts[it["title"]] = None
            out_of_range[it["title"]] = False
    return [
        {
            "title": it["title"],
            "start": starts.get(it["title"]),
            "printed_page": it.get("page_number"),
            "source_page": it.get("source_page"),
            "level": it.get("level", 1),
            "out_of_range": out_of_range.get(it["title"], False),
        }
        for it in items
    ]

# ---------- Hierarchy ----------
def build_hierarchy(items):
    hierarchy = []
    stack = []
    for item in items:
        level = item.get("level", 1)
        while stack and stack[-1]["level"] >= level:
            stack.pop()
        node = {
            "title": item["title"],
            "level": level,
            "page_number": item.get("page_number"),
            "page_label": item.get("page_label"),
            "source_page": item.get("source_page"),
            "children": []
        }
        if stack:
            stack[-1]["children"].append(node)
        else:
            hierarchy.append(node)
        stack.append(node)
    return hierarchy

def flatten_hierarchy_with_paths(hierarchy, parent_path="", parent_counter=1):
    flat_list = []
    for idx, item in enumerate(hierarchy, start=parent_counter):
        folder = f"{idx:03d}-{slug(item['title'])}"
        current_path = f"{parent_path}/{folder}" if parent_path else folder
        flat_item = {
            "title": item["title"],
            "level": item["level"],
            "page_number": item.get("page_number"),
            "page_label": item.get("page_label"),
            "source_page": item.get("source_page"),
            "folder_path": current_path,
            "children": item["children"]
        }
        flat_list.append(flat_item)
        if item["children"]:
            flat_list.extend(flatten_hierarchy_with_paths(item["children"], current_path, 1))
    return flat_list

# ---------- Compute ranges ----------
def compute_ranges_hierarchical(flat_items, doc_page_count):
    """
    Assign start/end so each section gets all PDF pages from its start until
    (but not including) the next section's start. No pages skipped between sections.
    If the next section is out_of_range (clamped), this section extends to end of document.
    """
    items = [it for it in flat_items if it.get("start") is not None]
    # Sort by start, then by printed_page so order is stable and matches index
    items.sort(key=lambda x: (x["start"], x.get("printed_page") or 0))
    for i, itm in enumerate(items):
        if i + 1 < len(items):
            nxt = items[i + 1]
            # If next section is out_of_range (clamped), it doesn't really start in the PDF;
            # this section gets all pages until end of document (no gap).
            if nxt.get("out_of_range"):
                end_page = doc_page_count - 1
            else:
                end_page = nxt["start"] - 1
        else:
            end_page = doc_page_count - 1
        if end_page < itm["start"]:
            end_page = itm["start"]
        itm["end"] = end_page
    return items

# ---------- Extract section text with intra-page cropping ----------
def extract_section_text(doc, start_page, end_page, heading_title, next_heading_title=None):
    start_norm = norm_ws(norm_dashes(heading_title)).lower()
    end_norm = norm_ws(norm_dashes(next_heading_title)).lower() if next_heading_title else None
    parts = []
    for pno in range(start_page, end_page + 1):
        txt = doc[pno].get_text("text")
        txt_norm = norm_ws(norm_dashes(txt))
        # Trim start page
        if pno == start_page:
            idx = txt_norm.lower().find(start_norm)
            if idx != -1:
                txt_norm = txt_norm[idx:]
        # Trim end page
        if pno == end_page and end_norm:
            idx_end = txt_norm.lower().find(end_norm)
            if idx_end != -1:
                txt_norm = txt_norm[:idx_end]
        parts.append(txt_norm)
    return "\n\n".join(parts).strip()

# ---------- Extract PDF pages ----------
def extract_pdf_pages(doc, start_page, end_page, output_path):
    """
    Extract specific pages from a PDF and save as a new PDF file.
    """
    try:
        import fitz  # PyMuPDF
        # Create a new PDF document
        new_doc = fitz.open()
        
        # Copy pages from the original document
        for page_num in range(start_page, end_page + 1):
            if page_num < len(doc):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        # Save the new PDF
        new_doc.save(str(output_path))
        new_doc.close()
        
        debug_print(f"[INFO] Saved PDF section: {output_path}")
        return True
    except Exception as e:
        debug_print(f"[ERROR] Failed to extract PDF pages {start_page}-{end_page}: {e}")
        return False

# ---------- Save sections ----------
def save_sections_hierarchical(doc, sections_with_paths, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    doc_len = len(doc)
    manifest = []
    for i, sec in enumerate(sections_with_paths):
        if sec.get("start") is None:
            continue
        # Section is beyond document (e.g. cropped PDF): leave content empty, no PDF
        out_of_range = sec.get("out_of_range", False) or sec["start"] >= doc_len or sec["end"] >= doc_len or sec["start"] > sec["end"]
        if out_of_range:
            content = ""
            pdf_filename = None
        else:
            next_title = sections_with_paths[i+1]["title"] if i+1 < len(sections_with_paths) else None
            extracted = extract_section_text(doc, sec["start"], sec["end"], sec["title"], next_title)
            content = f"**{sec['title']}**\n\n" + extracted
            pdf_filename = f"{slug(sec['title'])}.pdf"

        folder_path = out_dir / sec["folder_path"]
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            debug_print(f"[ERROR] Could not create directory {folder_path}: {e}")
            debug_print(f"[ERROR] Path length: {len(str(folder_path))}")
            short_folder = f"{i+1:03d}-section_{i+1}"
            folder_path = out_dir / short_folder
            folder_path.mkdir(parents=True, exist_ok=True)
            debug_print(f"[INFO] Using shorter path: {folder_path}")
            sec["folder_path"] = short_folder

        rec = {
            "name": sec["title"],
            "level": sec.get("level", 1),
            "start_page": int(sec["start"]),
            "end_page": int(sec["end"]),
            "printed_page": sec.get("printed_page"),
            "content": content,
            "out_of_range": out_of_range,
        }
        with open(folder_path / "content.json", "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)

        if not out_of_range and pdf_filename:
            pdf_path = folder_path / pdf_filename
            extract_pdf_pages(doc, sec["start"], sec["end"], pdf_path)

        manifest.append({
            "folder": sec["folder_path"],
            "title": sec["title"],
            "level": sec.get("level", 1),
            "start_page": rec["start_page"],
            "end_page": rec["end_page"],
            "printed_page": rec.get("printed_page"),
            "has_children": bool(sec.get("children")),
            "pdf_file": pdf_filename or "(empty - page range beyond document)",
            "out_of_range": out_of_range,
        })
    return manifest

# ---------- No-index path: whole document as one section ----------
def process_pdf_as_single_section(pdf_path, output_dir, section_title=None, verbose=True):
    """
    Process a PDF that has no index/TOC: treat the entire document as one section.
    Use this when the document is 1-2 pages of content only or has no table of contents.
    
    Creates the same folder structure as process_pdf_sections so policy extraction
    and the rest of the pipeline work unchanged: sections/001-<title>/content.json
    and sections_index.json.
    
    Args:
        pdf_path (str): Path to the source PDF file
        output_dir (str): Directory where extracted section will be saved (e.g. sections_<pdf_name>)
        section_title (str, optional): Title for the single section. Default: "Document content" or PDF name
        verbose (bool): Whether to print progress messages (default: True)
    
    Returns:
        dict: Manifest in same shape as process_pdf_sections: source_pdf, structure_type "single_section", sections_written
    """
    pdf_path = str(Path(pdf_path).expanduser())
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sections_dir = out_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    
    title = section_title or Path(pdf_path).stem or "Document content"
    title = norm_ws(norm_dashes(title))
    if not title:
        title = "Document content"
    
    folder_name = f"001-{slug(title)}"
    folder_path = sections_dir / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)
    
    doc = load_doc(pdf_path)
    doc_len = len(doc)
    parts = []
    for pno in range(doc_len):
        try:
            txt = doc[pno].get_text("text")
            parts.append(norm_ws(txt))
        except Exception:
            parts.append("")
    full_text = "\n\n".join(parts).strip()
    content = f"**{title}**\n\n" + full_text if full_text else f"**{title}**\n\n(No text extracted)"
    doc.close()
    
    rec = {
        "name": title,
        "level": 1,
        "start_page": 0,
        "end_page": max(0, doc_len - 1),
        "printed_page": 1,
        "content": content,
        "out_of_range": False,
    }
    with open(folder_path / "content.json", "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    
    # Optional: save full PDF as single section PDF (same as other sections)
    try:
        doc = load_doc(pdf_path)
        pdf_filename = f"{slug(title)}.pdf"
        extract_pdf_pages(doc, 0, doc_len - 1, folder_path / pdf_filename)
        doc.close()
    except Exception as e:
        debug_print(f"[WARN] Could not save full-doc PDF: {e}")
        pdf_filename = None
    
    manifest = [{
        "folder": folder_name,
        "title": title,
        "level": 1,
        "start_page": 0,
        "end_page": max(0, doc_len - 1),
        "printed_page": 1,
        "has_children": False,
        "pdf_file": pdf_filename or "(full document)",
        "out_of_range": False,
    }]
    manifest_obj = {
        "source_pdf": str(Path(pdf_path).resolve()),
        "structure_type": "single_section",
        "sections_written": manifest,
        "unresolved_titles": [],
    }
    with open(out_dir / "sections_index.json", "w", encoding="utf-8") as f:
        json.dump(manifest_obj, f, ensure_ascii=False, indent=2)
    
    if verbose:
        debug_print(f"[INFO] No-index path: treated entire document ({doc_len} pages) as one section: {title}")
        debug_print(f"[INFO] Output: {sections_dir.resolve()}")
    return manifest_obj


# ---------- Main Processing Function ----------
def process_pdf_sections(pdf_path, index_json_path, output_dir, verbose=True):
    """
    Extract sections from a PDF based on an index JSON file.
    
    Args:
        pdf_path (str): Path to the source PDF file
        index_json_path (str): Path to the index JSON file containing section metadata
        output_dir (str): Directory where extracted sections will be saved
        verbose (bool): Whether to print progress messages (default: True)
    
    Returns:
        dict: A manifest object containing:
            - source_pdf: Resolved path to source PDF
            - index_json: Resolved path to index JSON
            - structure_type: Type of structure (hierarchical)
            - sections_written: List of extracted sections with metadata
            - unresolved_titles: List of section titles that could not be resolved
    """
    debug_print(f"[DEBUG] index_content_extractor.process_pdf_sections called")
    debug_print(f"[DEBUG] PDF path: {pdf_path}")
    debug_print(f"[DEBUG] Index JSON path: {index_json_path}")
    debug_print(f"[DEBUG] Output directory: {output_dir}")
    debug_print(f"[DEBUG] Verbose mode: {verbose}")
    
    if verbose:
        debug_print("=== PDF Section Extractor (page_number based, offset, bold headings) ===")
    
    try:
        pdf_path = str(Path(pdf_path).expanduser())
        idx_path = str(Path(index_json_path).expanduser())
        out_dir = Path(output_dir)
        debug_print(f"[DEBUG] Expanded paths - PDF: {pdf_path}, Index: {idx_path}, Output: {out_dir}")
        
        # Create output directory if it doesn't exist
        if not out_dir.exists():
            debug_print(f"[DEBUG] Creating output directory: {out_dir}")
            out_dir.mkdir(parents=True, exist_ok=True)
            debug_print(f"[DEBUG] Output directory created")
        
        # Load index JSON
        debug_print(f"[DEBUG] Loading index JSON from: {idx_path}")
        with open(idx_path, "r", encoding="utf-8") as f:
            index_obj = json.load(f)
        
        items = index_obj.get("items", [])
        debug_print(f"[DEBUG] Found {len(items)} items in index JSON")
        
        if not items:
            debug_print(f"[ERROR] No items found in the index JSON")
            raise ValueError("No items in the index JSON.")
    except Exception as e:
        debug_print(f"[ERROR] Error in process_pdf_sections initialization: {str(e)}")
        import traceback
        debug_print(f"[DEBUG] Exception traceback: {traceback.format_exc()}")
        raise

    # Normalize items
    norm_items = []
    for it in items:
        title = norm_ws(norm_dashes(it.get("title", "")))
        if not title:
            continue
        norm_items.append({
            "title": title,
            "level": it.get("level", 1),
            "page_number": it.get("page_number"),
            "page_label": it.get("page_label"),
            "source_page": it.get("source_page"),
        })

    # Build hierarchy and flatten with paths
    hierarchy = build_hierarchy(norm_items)
    flat_with_paths = flatten_hierarchy_with_paths(hierarchy)
    
    # Load PDF document
    doc = load_doc(pdf_path)

    # Assign start pages (and detect out-of-range when PDF has fewer pages than index)
    starts = assign_start_pages(norm_items, doc)
    title_to_start = {s["title"]: s["start"] for s in starts}
    title_to_out_of_range = {s["title"]: s["out_of_range"] for s in starts}

    # Build sections with paths
    sections_with_paths = []
    for item in flat_with_paths:
        start_page = title_to_start.get(item["title"])
        if start_page is not None:
            item["start"] = start_page
            item["printed_page"] = next((it.get("page_number") for it in norm_items if it["title"] == item["title"]), None)
            item["out_of_range"] = title_to_out_of_range.get(item["title"], False)
            sections_with_paths.append(item)

    # Compute ranges and identify unresolved sections
    resolved_sections = compute_ranges_hierarchical(sections_with_paths, len(doc))
    unresolved_sections = [s for s in flat_with_paths if s.get("start") is None]

    # Save sections
    sections_dir = out_dir / "sections"
    manifest = save_sections_hierarchical(doc, resolved_sections, sections_dir)

    # Create manifest object
    manifest_obj = {
        "source_pdf": str(Path(pdf_path).resolve()),
        "index_json": str(Path(idx_path).resolve()),
        "structure_type": "hierarchical",
        "sections_written": manifest,
        "unresolved_titles": [u["title"] for u in unresolved_sections]
    }
    
    # Save manifest
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "sections_index.json", "w", encoding="utf-8") as f:
        json.dump(manifest_obj, f, ensure_ascii=False, indent=2)

    if verbose:
        debug_print(f"\nDone. Sections written: {len(manifest)}")
        if unresolved_sections:
            debug_print("Unresolved titles:")
            for u in unresolved_sections:
                debug_print(f" - {u['title']}")
        debug_print(f"Output folder: {out_dir.resolve()}")
    
    # Close the PDF document
    doc.close()
    
    return manifest_obj


# ---------- Main for standalone execution ----------
def main():
    """Main function for standalone script execution with default paths."""
    PDF_PATH = "PCI_DSS.pdf"            # Path to your PDF
    INDEX_JSON_PATH = "PCI_DSS_index.json"  # Path to your index JSON
    OUTPUT_DIR = "sections_out_PCI_DSS_UPDATED"      # Output base directory
    
    try:
        result = process_pdf_sections(PDF_PATH, INDEX_JSON_PATH, OUTPUT_DIR, verbose=True)
        return result
    except Exception as e:
        debug_print(f"[ERROR] Failed to process PDF sections: {e}")
        raise


if __name__ == "__main__":
    main()

# Upload Framework – Detailed Step-by-Step Flow

This document describes **exactly** what happens when you upload a framework PDF in the Policy **Upload Framework** flow: frontend steps, backend processing, file layout, and every place AI is used.

---

## Table of Contents

1. [Overview: The 6 Steps](#overview-the-6-steps)
2. [Step 1: Upload Document](#step-1-upload-document)
3. [Step 2: Processing](#step-2-processing)
4. **[Step 1 & 2 Backend Deep Dive: Index and Section Processing](#step-1--2-backend-deep-dive-index-and-section-processing)** ← Index extraction, page filtering, section splitting; **no-index path**: document treated as one section
5. [Step 3: Content Selection](#step-3-content-selection)
6. [Step 4: Generate Compliances](#step-4-generate-compliances)
7. [Step 5: Overview](#step-5-overview)
8. [Step 6: Edit Policy Details](#step-6-edit-policy-details)
9. [Backend Document Processing (PDF Pipeline)](#backend-document-processing-pdf-pipeline)
10. [AI Tasks Used](#ai-tasks-used)
11. [File and Folder Layout](#file-and-folder-layout)
12. [APIs Reference](#apis-reference)

---

## Overview: The 6 Steps

| Step | Name                 | What happens |
|------|----------------------|--------------|
| 1    | **Upload Document**  | Select PDF (or load default RBI data), optional compression, POST to backend; backend saves file and starts background processing. |
| 2    | **Processing**       | Frontend polls status; backend runs PDF index → sections → AI policy extraction. |
| 3    | **Content Selection**| Load sections/policies/subpolicies tree; user selects what to keep; save to `checked_section.json`. |
| 4    | **Generate Compliances** | For each selected subpolicy, AI generates compliance records; results cached. |
| 5    | **Overview**         | Summary of sections, policies, subpolicies, compliances. |
| 6    | **Edit Policy Details** | Load full draft, edit fields, save to database. |

---

## Step 1: Upload Document

### What you see

- **Upload Framework** page with:
  - Drag-and-drop or click to select file.
  - Supported formats: **PDF, DOC, DOCX, TXT, XLS, XLSX**.
  - Optional: **Load Default RBI Framework Data** (skips upload, uses pre-loaded data).
  - **Clear cache** button (broom icon): clears frontend policy cache, module AI cache, and calls backend `POST /api/ai-cache/clear/` to clear backend AI cache.

### What the frontend does

1. **File selection**  
   - User selects a file (or drops it).  
   - `selectedFile` is set; optional **client-side compression** (e.g. PDF → `.gz`) if the app decides it’s beneficial.

2. **Upload**  
   - Builds `FormData`: `file`, `userid` (from `localStorage`), optional `compression_metadata`.  
   - Calls **`policyFrameworkCacheService.uploadDocument(formData, file)`**:
     - If the same file (name/size/lastModified) is in cache, returns cached `{ data, timestamp, taskId }` and **no** new HTTP request.
     - Otherwise: **`POST /api/upload-framework/`** with JWT.

3. **Response handling**  
   - Backend returns `task_id`, `processing: true`, `filename`, etc.  
   - Frontend sets `taskId`, `uploadedFileName`, moves to **Step 2**, starts **progress polling**, and saves processing state to `sessionStorage`.

### What the backend does (POST /api/upload-framework/)

1. Validates `file` and `userid` (default `'default'`).
2. Validates extension (`.pdf`, `.doc`, `.docx`, `.txt`, `.xlsx`, `.xls`); allows `.gz` (compressed).
3. Generates **task_id**: `upload_{timestamp}_{filename}` (e.g. `upload_1773547316_PCI_DSS_1.pdf.gz`).
4. **Creates user folder**: `MEDIA_ROOT/upload_{userid}/` (recreates if exists).
5. **Saves file** under that folder (e.g. `upload_1/PCI_DSS_1.pdf` or `.gz`).
6. If file is `.gz`, **decompresses** and uses the decompressed path for processing.
7. **Starts a background thread** that runs the PDF pipeline (see [Backend Document Processing](#backend-document-processing-pdf-pipeline)).
8. **Returns immediately** with:
   - `task_id`, `filename`, `processing: true`, `file_type`, `user_folder`, etc.

So **Step 1** only uploads and kicks off processing; the heavy work is in the background and in **Step 2** (polling).

---

## Step 2: Processing

### What you see

- **Processing** step with:
  - Animated “Processing Framework Document” UI.
  - Progress percentage and message (e.g. “Extracting PDF index…”, “Extracting sections…”, “Extracting policies using AI…”).
  - Stages: Document Analysis → Text Extraction → Structure Processing → Content Organization → Policy Identification → Final Processing.

### What the frontend does

1. **Progress polling**  
   - Every **1.5 seconds**: **`GET /api/processing-status/{task_id}/`**  
   - Backend returns `{ progress, message, ... }` from Django cache.

2. **When `progress >= 100`**  
   - Stops polling.  
   - Calls **`fetchExtractedContent()`** (loads sections for Step 3).  
   - Moves to **Step 3** and shows the section tree.

3. **If status returns 404**  
   - “Task not found or expired”: frontend clears that task from cache, shows error, resets to **Step 1**.

### What the backend does (background thread, for PDF)

Progress is updated in Django cache under `processing_{task_id}`. Main stages:

| Progress % | Stage              | What runs |
|------------|--------------------|-----------|
| 5          | Starting           | `update_progress(task_id, 5, "Starting PDF processing...")` |
| 10         | Integrated system  | “Processing PDF with integrated system...” |
| 30         | Index              | **PDF index extraction** (TOC/structure). |
| 40         | Index done         | “Index extracted: N items” |
| 45         | Sections           | **Section extraction** (split PDF by index). |
| 60         | Sections done      | “Sections extracted: N sections” |
| 65         | Policies (AI)      | **AI policy extraction** (see below). |
| 95         | Policies done      | “Policies extracted: N policies” |
| 100        | Complete           | “PDF processing completed successfully!” |

Details of index, sections, and AI policy extraction are in [Backend Document Processing](#backend-document-processing-pdf-pipeline).

---

## Step 1 & 2 Backend Deep Dive: Index and Section Processing

This section explains **exactly** what the backend does with your PDF in the background: how the index (table of contents) is extracted, how pages are filtered, and how the document is split into sections. Code lives in `grc_backend/grc/routes/uploadNist/` (**pdf_index_extractor.py**, **index_content_extractor.py**).

---

### Part A: Index Extraction (Table of Contents)

**Entry point:** `pdf_index_extractor.extract_and_save_index(pdf_path, output_path, prefer_toc=True)`  
**Output:** `{pdf_name}_index.json` in the user folder (e.g. `upload_1/PCI_DSS_1_index.json`).

#### 1. Load every page as text + position

- **PyMuPDF (fitz)** is used first.
- For **each page** in the PDF:
  - `page.get_text("dict")` returns a structure of **blocks → lines → spans**.
  - For each span, the code takes **text** and **bbox** (bounding box); the left coordinate **x0** is kept.
  - Result: `pages[page_index]` = list of `(text_line, x0_left)` for that page.
- So we have **all pages** as lists of lines with their **horizontal position** (indentation). That is used later to infer **TOC hierarchy** (level 1, 2, 3 from indentation).
- If PyMuPDF fails, fallback is **pdfminer**: one text blob per page (no positions), so hierarchy is less accurate.

#### 2. Find where the TOC starts (page filtering)

- **TOC title patterns** (regex) look for:
  - “table of contents”, “contents”, “index” (case-insensitive).
- The code scans **only the first 30 pages** (`max_scan = min(len(pages), 30)`).
- **Candidate TOC start pages** = pages where any of these patterns appears in the page text.
- For **GRI-style** PDFs: if a page has 3+ lines like `GRI 1:`, `GRI 2:`, etc., that page can also be treated as a TOC candidate.
- If multiple candidates exist, the one with the **most GRI-style lines** is chosen as `start_pno`; otherwise the first candidate (or page 0) is used.

So: **only the first 30 pages** are considered, and among them only pages that “look like” a TOC page are used as the **start** of TOC parsing.

#### 3. Parse TOC lines page by page (with filtering)

- Parsing starts at `start_pno` and goes **forward** for at most **15 pages** (`MAX_PAGES = start_pno + 15`) or until **stop conditions** below.
- For **each page** in that range:

  **Stop conditions (filtering out non-TOC pages):**

  - **Too much body text:** If the page has more than 3 lines longer than 100 characters **and** we’re already 2+ pages past the TOC start → treat as start of real content, **stop** TOC parsing.
  - **Body-content phrases:** If the page text contains any of:
    - `requirement`, `guidance`, `disclosure`, `reporting`, `organization should`, `this standard`, `the organization is required`
    - **and** we’re 2+ pages past the TOC start → **stop** (we’ve left the TOC).

  **Line-level parsing:**

  - Each **line** on the page is matched against **TOC line patterns** (`TOC_LINE_RES`):
    - **GRI format:** e.g. `GRI 1: Foundation 2021` with page number on next line (right-aligned). Checks: page number 3–2000, title x0 roughly 50–100, page number x0 > 400.
    - **Dots format:** `Title ......... 123` or `Title ......... iv` (roman).
    - **Spaces format:** `Title      123` (5+ spaces or 3+ spaces before page number).
    - **Loose:** `Title 123` (minimal space).
  - **Filtering:** Title must be at least 3 chars and contain a letter; page number must parse (integer or roman) and be ≤ 2000.
  - Each matched line becomes one TOC **item**: `(title, page_label, x0, source_page)`.

  **Miss logic:**

  - If **no** line on the current page matches any TOC pattern → **misses += 1**.
  - If **at least one** line matches → **misses = 0**.
  - If **misses ≥ 3** and we already have **more than 5** TOC items → **stop** (we’ve left the TOC).

So: **pages are filtered** by (1) “does this page look like TOC or body?”, and (2) “do we see 3 consecutive pages with no TOC lines?”. Only lines that match **title + page number** patterns are kept.

#### 4. Assign hierarchy levels (1, 2, 3, …)

- Levels are **not** taken from the PDF; they are **inferred from indentation**.
- For each TOC item we have **x0** (left position). The code:
  - Groups similar x0 values into “buckets” (within 4 pt tolerance).
  - Assigns **level = 1, 2, 3, …** by bucket order (leftmost = 1, then 2, etc.).
- If most items share the same x0 (e.g. 70%+), every item gets **level 1**.

So: **level** = section depth in the outline, derived from **horizontal position** of the title text on the TOC page(s).

#### 5. Build index items and save

- Each parsed entry becomes:
  - `level`, `title`, `page_label` (string, e.g. `"5"` or `"iv"`), `page_number` (integer if numeric), `source_page` (PDF page index + 1 where this TOC line was found).
- **Fallback:** If **no** TOC was found from printed text, the code tries **PDF outline/bookmarks** (`doc.get_toc(simple=True)` in PyMuPDF): list of `[level, title, page]`. Those become index items with `page_number` from the bookmark.
- Result is saved to **`{pdf_name}_index.json`** with keys: `source_pdf`, `extraction_method`, `items` (array of the above).

**Summary (index):** The backend loads every page’s text (and positions), finds TOC start in the first 30 pages, parses only lines that look like “title + page number” on a limited number of pages, stops when it hits body-like content or 3 empty TOC pages, infers levels from indentation, and writes the list to `*_index.json`.

---

### Part B: Section Extraction (Splitting the PDF by Index)

**Entry point:** `index_content_extractor.process_pdf_sections(pdf_path, index_json_path, output_dir)`  
**Input:** The `*_index.json` from Part A.  
**Output:** Folder `sections_{pdf_name}/sections/` with one subfolder per section; each has **content.json** (text) and a **PDF** of that section’s pages.

#### 1. Load index and normalize items

- Read **index JSON**; take `items` array.
- Normalize: trim/dash-normalize each `title`, keep `level`, `page_number`, `page_label`, `source_page`. Skip items with empty title.

#### 2. Map “printed” page numbers to real PDF page indices (offset)

- Many PDFs have **printed page numbers** (1, 2, 3…) that don’t match the **PDF’s internal page index** (0, 1, 2…) because of cover, TOC, etc.
- **detect_page_offset(items, doc):**
  - For each index item that has a numeric **page_number** (printed), we know “this section title should appear on printed page X”.
  - The code builds **page_texts** = full text of every PDF page (normalized).
  - For each item, it searches a **window** of PDF pages: from `printed_page - 3` to `printed_page + 8`.
  - **Filtering:** It **skips** PDF pages that look like TOC:
    - More than 3 occurrences of `....`
    - “table of contents” in the page text
    - Many lines matching “number.number…number” (TOC-style lines)
  - When the **section title** is found in the page text, it checks **context** (before/after) for phrases like “this document”, “this section”, “the following”, or “page N”, to decide this is the **real** section start, not the TOC line.
  - When found, it records **offset = (PDF page index) − (printed page − 1)**.
  - **Final offset** = most common offset among all items (so one mapping for the whole document).
- If **no** offset could be detected, default **4** is used (e.g. NIST CSF: printed page 1 = PDF page 5).

So: **pages are filtered** again here: TOC-like pages are skipped when matching section titles; only “body” pages are used to detect where each section really starts in the PDF.

#### 3. Assign start page (PDF index) to each index item

- **assign_start_pages(items, doc):**
  - For each item: **start = (printed_page - 1) + offset**, clamped to `[0, len(doc)-1]`.
  - So each TOC entry gets a **start** = the **0-based PDF page index** where that section begins.

#### 4. Build hierarchy and flatten with folder paths

- **build_hierarchy(items):** Converts the flat list into a tree using **level** (parent = last item with smaller level).
- **flatten_hierarchy_with_paths:** Walks the tree and assigns **folder_path** like `001-Introduction`, `002-Overview/001-Subsection`, etc. (with slugs, max 40 chars). So we get a flat list again but with paths and parent/child preserved.

#### 5. Compute end page for each section

- **compute_ranges_hierarchical(flat_items, doc_page_count):**
  - Items are sorted by **start** page.
  - For each section, **end** = start of the **next** section at the **same or higher level** (sibling or parent). If none, end = last page of the PDF.
  - So each section has **start** and **end** (0-based PDF page indices). That’s the **page range** for that section.

#### 6. Extract text and PDF per section

- **save_sections_hierarchical(doc, sections_with_paths, out_dir):**
  - For each section with a valid **start** (and thus **end**):
    - **extract_section_text(doc, start, end, heading_title, next_heading_title):**
      - For each page in `[start, end]`:
        - Get full page text.
        - On the **first page**: find the **heading_title** in the text and **trim everything before it** (so we don’t include previous section’s tail).
        - On the **last page**: if we have **next_heading_title**, find it and **trim everything after it** (so we don’t include next section’s start).
      - Concatenate trimmed page texts with `\n\n`.
    - Content is saved as **`content.json`** in the section folder: `name`, `level`, `start_page`, `end_page`, `printed_page`, `content` (with a bold markdown title at the top).
    - **extract_pdf_pages(doc, start, end, output_path):** Uses PyMuPDF to copy **only** pages `start`…`end` into a new PDF file (e.g. `Introduction.pdf`) in the same folder.

So: **page filtering** in section extraction is (1) **offset detection** (skip TOC-like pages when matching titles), and (2) **trimming** so each section’s text starts at its heading and ends before the next.

#### 7. Unresolved sections

- Any index item whose **start** could not be resolved (e.g. title never found in the PDF) is **not** written; it’s listed in **unresolved_titles** in the manifest. Only sections with a valid page range get a folder and files.

#### 8. Manifest

- **sections_index.json** is written in the sections output dir with: `source_pdf`, `index_json`, `structure_type`, `sections_written` (list of folder, title, level, start/end page, pdf_file), `unresolved_titles`.

**Summary (sections):** The backend maps printed page numbers to PDF indices (using TOC-page filtering), assigns each TOC entry a start/end PDF page, trims text per section so it starts at the section heading and stops at the next, and writes one folder per section with **content.json** (text) and a **section PDF**. Only index entries that could be mapped to a page range are written; the rest are “unresolved”.

---

### How this feeds into Step 2 (policy extraction)

- **Index** → `*_index.json` (list of sections with level, title, page).
- **Sections** → `sections_{pdf_name}/sections/` (one folder per section with text + PDF).
- The **policy extractor** (Step 2, 65–95%) reads each section’s **content.json**, sends that text (plus section title) to the AI task **policy.extract_policy_hierarchy**, and writes **policies_{pdf_name}/all_policies.json**.

So: **Step 1** = upload + start this pipeline. **Step 2** = frontend polls while this pipeline runs; the “processing” you see is index → sections → AI policies, with all the page loading, TOC detection, line and page filtering, offset detection, and range computation described above.

---

## Step 3: Content Selection

### What you see

- Hierarchical tree: **Sections → Policies → Subpolicies** (with titles, descriptions, controls).
- Expand/collapse; checkboxes to **select** which sections/policies/subpolicies to keep.
- **Save Selected Sections** (or similar) to confirm and move on.

### What the frontend does

1. **Load sections**  
   - **`policyFrameworkCacheService.getSections(userId, taskId)`** → **`GET /api/get-sections-by-user/{userid}/`**  
   - Backend returns `{ success, sections, framework_name, framework_info, total_sections, total_policies, total_subpolicies }`.  
   - Sections are mapped to the tree (policies → subsections, subpolicies → items with control text).

2. **User selection**  
   - User expands nodes and checks the items to keep.  
   - State is local (e.g. `sections[].subsections[].selected`, subpolicy selection).

3. **Save selected**  
   - Builds **selected_items** (hierarchical: sections → policies → subpolicies).  
   - **`POST /api/save-checked-sections-json/`** with `task_id`, `user_id`, `selected_items`.  
   - Backend writes **`checked_section.json`** under the user’s upload folder (e.g. `upload_1/checked_sections/checked_section.json` or similar path).  
   - Frontend then **automatically** calls **Step 4** (generate compliances).

### What the backend does

- **GET get-sections-by-user/{userid}/**  
  - Uses **`load_consolidated_json(userid)`**:
    - If **`upload_{userid}/framework_data.json`** exists → load and return it.
    - If not, **`create_consolidated_json(userid)`**:
      - Finds **`upload_{userid}/policies_*/all_policies.json`** (written by the PDF pipeline).
      - Builds a single structure (sections → policies → subpolicies) and saves **`framework_data.json`**.
  - Returns that structure as the **sections** payload.

- **POST save-checked-sections-json**  
  - Receives `task_id`, `user_id`, `selected_items`.  
  - Writes the selected hierarchy to **checked_section.json** (path depends on implementation; often under user folder or `checked_sections`).

So **Step 3** only selects content and persists it; no AI here.

---

## Step 4: Generate Compliances

### What you see

- Messages like “Checking cache…”, “Generating compliances with AI…”, “Finalizing compliance records…”.
- Progress 10 → 25 → 75 → 100.
- Then automatic transition to **Step 5 (Overview)**.

### What the frontend does

1. **Cache check**  
   - **`policyFrameworkCacheService.getCachedCompliances(taskId)`**  
   - If cache hit: use cached counts and payload, go to Step 5.

2. **Generate**  
   - **`policyFrameworkCacheService.generateCompliances(taskId, userId)`**  
   - → **`POST /api/generate-compliances-for-checked-sections/`** with `task_id`, `user_id`.  
   - Response: full structure with **compliances** per subpolicy; frontend caches it and updates stats.

3. **Navigate**  
   - Move to **Step 5** and save state.

### What the backend does (generate compliances)

1. Resolve **user_id** from request.
2. Load **checked_section.json** for that user (path from `_checked_section_path(user_id)`).
3. For **each section → policy → subpolicy** in that file:
   - Build payload: `subpolicy_id`, `subpolicy_title`, `subpolicy_description`, `control`.
   - Call **AI task** **`policy.generate_subpolicy_compliances`** with that payload.
   - AI returns a list of compliance objects (e.g. ComplianceTitle, ComplianceItemDescription, Criticality, Scope, etc.).
   - If AI returns nothing, a single fallback compliance is created.
4. Attach **compliances** to each subpolicy and build the full nested structure.
5. Return the full data + counts (total_sections, total_policies, total_subpolicies, total_compliances).

So **Step 4** is where **AI generates compliance records** for every selected subpolicy.

---

## Step 5: Overview

### What you see

- Summary of what was generated:
  - Total sections, policies, subpolicies, compliances.
- Button like **“Edit Policy Details”** to go to **Step 6**.

### What the frontend does

- Displays **overviewStats** (from Step 4 result or cache).  
- **Edit Policy Details** → **goToStep(6)**.

No new API or AI here; it’s read-only from Step 4 data.

---

## Step 6: Edit Policy Details

### What you see

- Full form/view of the draft: sections, policies, subpolicies, compliances.
- Editable fields (titles, descriptions, control text, compliance fields, etc.).
- Option to **save to database** (e.g. “Save to database” / “Save Framework”).

### What the frontend does

1. **Load draft**  
   - **`GET /api/get-checked-sections-with-compliance/?user_id=...`**  
   - Backend returns the full **checked_section** data with compliances (from **checked_section.json** or from the last generate response stored server-side).

2. **Edit**  
   - User edits policy/subpolicy/compliance fields in the UI.

3. **Save to database**  
   - **`POST /api/save-edited-framework-to-database/`** (or similar) with the full draft.  
   - Backend persists framework/policies/subpolicies/compliances into the DB (tenant-aware if applicable).

No AI in Step 6; it’s load → edit → save.

---

## Backend Document Processing (PDF Pipeline)

This runs in the **background thread** started in Step 1 (for **PDF** uploads). Entry: **`process_pdf_framework_new(userid, pdf_path, task_id)`**.

### 1. Extract PDF index (TOC)

- **Module**: `pdf_index_extractor` (e.g. `extract_and_save_index()`).
- **Input**: `pdf_path`.
- **Output**: **`{pdf_name}_index.json`** in the user folder (e.g. `upload_1/PCI_DSS_1_index.json`).
- **Content**: List of TOC items (title, page number, level), or **empty** when the document has no table of contents (`extraction_method: "none_found"`, `items: []`).
- **Progress**: 30 → 40.

### 2. Extract sections (two paths)

- **Path A – Document has index (TOC):**
  - **Module**: `index_content_extractor.process_pdf_sections()`.
  - **Input**: `pdf_path`, index JSON path, output dir.
  - **Output**: **`sections_{pdf_name}/`** with one folder per TOC entry; each section has `content.json` and optional per-section PDFs.
  - Sections are split by the index (page ranges, hierarchy).
- **Path B – Document has no index (e.g. 1–2 pages of content only):**
  - **Module**: `index_content_extractor.process_pdf_as_single_section()`.
  - **Trigger**: `index_items_count == 0` or `extraction_method == "none_found"`.
  - **Input**: `pdf_path`, output dir, optional section title (default: PDF name or "Document content").
  - **Output**: **`sections_{pdf_name}/sections/001-<title>/`** with a single **`content.json`** containing the **full document text** (all pages). Optional full-document PDF in that folder.
  - **`sections_index.json`** has `structure_type: "single_section"` and one entry in `sections_written`.
- **Progress**: 45 → 60.

Downstream (policy extraction, Content Selection, etc.) is the same: they read `sections_index.json` and section `content.json` files, so one section or many sections both work.

### 3. Extract policies (AI)

- **Module**: **`policy_extractor_enhanced`** (e.g. `extract_policies()` → `extract_policies_from_sections_enhanced()`).
- **Input**: `sections_{pdf_name}/` directory.
- **Output**: **`policies_{pdf_name}/all_policies.json`** (and possibly per-section files).
- **Logic**:
  - Detects framework type (e.g. PCI DSS, NIST) from folder name.
  - For **each section** (or chunk of section text):
    - Builds a prompt with **section title** and **section text**.
    - Calls **AI task** **`policy.extract_policy_hierarchy`** (via centralized `get_ai_service().generate_json(...)`).
    - AI returns JSON: `has_policies`, `policies[]` (each with `policy_title`, `policy_description`, `scope`, `objective`, `policy_type`, … and **subpolicies[]** with `subpolicy_title`, `subpolicy_description`, `control`).
    - Response is validated, normalized, and enhanced (IDs, scope/objective generation if missing).
  - Writes **all_policies.json**: array of `{ section_info, analysis: { has_policies, policies, framework_info } }`.
- **Progress**: 65 → 95 → 100.

So the **document** is: **PDF → index → sections (text) → AI policy/subpolicy extraction → all_policies.json**.

---

## AI Tasks Used

| AI Task name                         | When it runs | Input | Output |
|-------------------------------------|--------------|-------|--------|
| **policy.extract_policy_hierarchy**  | Step 2 (backend, per section) | Section title + section text | JSON: `has_policies`, `policies[]` (with `subpolicies[]` and controls). |
| **policy.generate_subpolicy_compliances** | Step 4 (backend, per selected subpolicy) | Subpolicy title, description, control text | JSON: `compliances[]` (ComplianceTitle, ComplianceItemDescription, Criticality, Scope, etc.). |

- **Provider/model**: From app config (e.g. OpenAI or Ollama); model can be chosen by a router (e.g. by task name, document size).
- **Caching**: Backend can cache AI responses (e.g. by prompt hash) so repeated runs use cache when possible. **Clear cache** (Step 1) calls **`POST /api/ai-cache/clear/`** to clear backend AI cache.

---

## File and Folder Layout

After a successful PDF upload and processing for **userid = 1** and file **PCI_DSS_1.pdf**:

```
MEDIA_ROOT/
  upload_1/
    PCI_DSS_1.pdf                    # (or .gz before decompression)
    PCI_DSS_1_index.json            # TOC/index
    sections_PCI_DSS_1/             # Extracted sections (one dir per section)
      <section_folders>/
        content.json, .txt, .pdf...
    policies_PCI_DSS_1/
      all_policies.json             # AI-extracted policies/subpolicies per section
    framework_data.json             # Created on first get-sections-by-user (from all_policies.json)
    checked_sections/               # (or similar)
      checked_section.json          # User’s selected sections/policies/subpolicies (Step 3)
```

- **all_policies.json**: Full hierarchy from AI (section_info + analysis with policies/subpolicies).
- **framework_data.json**: Flattened structure for the UI (sections → policies → subpolicies).
- **checked_section.json**: Selected subset + later filled with compliances in Step 4.

---

## APIs Reference

| Purpose | Method | Endpoint | When |
|--------|--------|----------|------|
| Upload file | POST | `/api/upload-framework/` | Step 1 |
| Processing status | GET | `/api/processing-status/{task_id}/` | Step 2 (polling) |
| Get sections | GET | `/api/get-sections-by-user/{userid}/` | Step 3 |
| Save selected sections | POST | `/api/save-checked-sections-json/` | Step 3 |
| Generate compliances | POST | `/api/generate-compliances-for-checked-sections/` | Step 4 |
| Get checked sections + compliances | GET | `/api/get-checked-sections-with-compliance/?user_id=...` | Step 6 |
| Save to database | POST | `/api/save-edited-framework-to-database/` | Step 6 |
| Clear backend AI cache | POST | `/api/ai-cache/clear/` | Step 1 (Clear cache button) |

---

## Summary: What Happens to Your PDF

1. **Upload**: File is stored under **`upload_{userid}/`** and a **task_id** is created; background processing starts.
2. **Index**: PDF table of contents is extracted → **`*_index.json`**.
3. **Sections**: PDF is split into sections by that index → **`sections_*/`**.
4. **Policies (AI)**: For each section, **AI** extracts **policies** and **subpolicies** (with controls) → **`policies_*/all_policies.json`**.
5. **Consolidation**: First time you open Step 3, **`framework_data.json`** is built from **all_policies.json** and served as the section tree.
6. **Selection**: You choose what to keep → **`checked_section.json`**.
7. **Compliances (AI)**: For each selected subpolicy, **AI** generates **compliance** records; they are attached and returned.
8. **Overview**: You see counts; then in Step 6 you edit and **save to database**.

All “intelligence” is in two places: **policy.extract_policy_hierarchy** (document → structure) and **policy.generate_subpolicy_compliances** (control text → compliance records).

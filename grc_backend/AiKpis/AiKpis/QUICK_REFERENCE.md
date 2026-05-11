# Quick Reference Guide for Students

## 🎯 Understanding the Code Structure

### What Does Each File Do?

Think of this system like a **factory assembly line** for generating KPIs:

```
1. config.py          → Settings & Configuration (like the factory blueprint)
2. database.py        → Gets data from MySQL (raw materials)
3. s3_handler.py      → Gets documents from S3 (additional materials)
4. evidence.py        → Organizes evidence (quality control)
5. module_summaries.py → Creates summaries (preprocessing)
6. ollama_client.py   → Talks to AI (the smart robot)
7. kpi_validation.py  → Checks KPIs are valid (quality check)
8. formula_evaluator.py → Calculates KPI values (calculator)
9. synthetic_data.py  → Creates fake data when needed (backup generator)
10. kpi_generator.py  → Runs the whole process (factory manager)
11. generateFrameworkKpi.py    → Start button (factory entrance)
```

## 🔄 Complete Workflow (Step by Step)

### Phase 1: Setup & Data Collection
```
START
  ↓
[1] Read config.py → Get settings
  ↓
[2] database.py → Connect to MySQL
  ↓
[3] database.py → Get framework info (What framework are we working with?)
  ↓
[4] s3_handler.py → Download documents from S3
  ↓
[5] database.py → Get all framework data (policies, risks, etc.)
  ↓
[6] database.py → Get database schema (what tables/columns exist?)
```

### Phase 2: Organization
```
[7] module_summaries.py → Create JSON files for each module
    - Groups related tables together
    - Creates: module_summary_336_policies_20240101.json
    - Creates: module_summary_336_audit_20240101.json
    - etc.
  ↓
[8] evidence.py → Attach relevant S3 documents to each module
    - Uses AI to find relevant documents
    - Scores documents by relevance
    - Adds top documents to module summaries
```

### Phase 3: KPI Generation (The Magic!)
```
[9] For each module:
    ↓
    [9a] module_summaries.py → Check if data is too big
         - If too big → Split into chunks
         - If small → Keep as is
    ↓
    [9b] ollama_client.py → Send data to Ollama AI
         - AI reads the data
         - AI generates 12 KPIs per module
         - Returns JSON with KPIs
    ↓
    [9c] kpi_validation.py → Check if KPIs are valid
         - Do formulas reference real columns?
         - Are there duplicates?
         - Is everything formatted correctly?
```

### Phase 4: Data & Values
```
[10] For each KPI:
     ↓
     [10a] Check: Does this KPI have data?
           ↓
           YES → formula_evaluator.py → Calculate value
           ↓
           NO → synthetic_data.py → Create fake data
                ↓
                - AI generates realistic dataset
                - Uploads to S3
                - Creates PDF evidence
                ↓
                formula_evaluator.py → Calculate value
```

### Phase 5: Save Results
```
[11] kpi_validation.py → Remove duplicates
  ↓
[12] database.py → Save all KPIs to MySQL
  ↓
END (Success!)
```

## 📝 Key Functions Explained

### database.py
```python
connect_to_database()          # Opens connection to MySQL
get_framework_info()           # Gets framework details (name, ID, etc.)
get_database_schema()          # Gets all tables and columns
get_framework_data()           # Gets policies, risks, incidents, etc.
write_kpis_to_database()       # Saves KPIs to database
```

### s3_handler.py
```python
get_s3_documents()             # Downloads documents from S3
extract_text_from_pdf()        # Reads text from PDF files
extract_text_from_excel()      # Reads data from Excel files
load_s3_cache()                # Loads cached documents (faster!)
```

### evidence.py
```python
attach_s3_evidence_to_summary() # Finds relevant documents for module
build_evidence_index()          # Creates searchable index
tokenize_text()                 # Breaks text into keywords
```

### ollama_client.py
```python
generate_kpis_with_ollama()    # Sends request to AI
extract_json_from_text()       # Extracts JSON from AI response
```

### kpi_validation.py
```python
validate_and_sanitize_formulas() # Checks if formulas are valid
deduplicate_kpis()               # Removes duplicate KPIs
align_kpis_with_evidence()       # Matches KPIs to data sources
```

### formula_evaluator.py
```python
evaluate_formula_against_dataframe() # Calculates KPI value
populate_kpi_values_from_memory()    # Fills in all KPI values
```

### synthetic_data.py
```python
generate_llm_synthetic_dataframe()   # AI creates fake dataset
create_synthetic_dataset_for_kpi()   # Uploads synthetic data to S3
render_synthetic_pdf()               # Creates PDF evidence
```

### kpi_generator.py
```python
generate_kpis_for_framework()        # Main function - runs everything
generate_kpis_from_module_summaries() # Processes each module
refresh_kpis_after_upload()          # Updates KPIs when new file uploaded
```

## 🎓 How to Customize

### Change Which Modules to Process
**File**: `module_summaries.py`
**Line**: ~515

```python
modules = {
    'policies': ['policies', 'policyversions', ...],
    'compliance': ['compliance', 'complianceapproval'],
    'audit': ['audit', 'audit_findings', ...],
    'risk': ['risk', 'risk_instance', ...],
    'incidents': ['incidents', 'incident_approval'],
    'your_new_module': ['table1', 'table2']  # ADD HERE
}
```

### Change AI Model
**File**: `config.py`
**Line**: ~121

```python
OLLAMA_MODEL = "llama3.1:8b"  # Change to "qwen2.5:14b" or other
```

### Change Database
**File**: `config.py`
**Line**: ~124

```python
DB_CONFIG = {
    'host': 'localhost',      # Change to your host
    'database': 'grc2',       # Change to your database
    'user': 'root',           # Change to your username
    'password': 'your_pass'   # Change to your password
}
```

### Change How Many S3 Documents to Process
**File**: `config.py`
**Line**: ~162

```python
DEFAULT_MAX_S3_DOCUMENTS = 5  # Change to 10, 20, etc.
```

### Change AI Prompt
**File**: `ollama_client.py`
**Line**: ~170

```python
prompt = f"""You are a senior GRC strategist...
[MODIFY THIS ENTIRE PROMPT]
"""
```

### Change Number of KPIs Generated
**File**: `ollama_client.py`
**Line**: ~184 (in prompt)

```python
- Produce exactly 20 KPIs...  # Change 20 to 15, 25, etc.
```

## 🐛 Common Issues & Solutions

### Issue 1: "Cannot connect to database"
**Solution**: Check `config.py` → DB_CONFIG settings

### Issue 2: "Ollama not responding"
**Solution**: 
```bash
# Check if Ollama is running
curl http://13.126.18.17:11434/api/tags
```

### Issue 3: "No S3 documents found"
**Solution**: Check bucket name in `config.py` → TARGET_S3_BUCKET

### Issue 4: "Module not found"
**Solution**: 
```bash
# Make sure you're in the right directory
cd d:/UI_GRC-1
python -m backend.grc.AiKpis.generateFrameworkKpi
```

### Issue 5: "Missing dependencies"
**Solution**:
```bash
pip install -r backend/grc/AiKpis/requirements.txt
```

## 🔍 Debugging Tips

### See What's Happening
All functions print logs like:
```
[INFO] [STEP] Starting database schema retrieval...
[INFO] [SUCCESS] Retrieved 50 policies
[WARNING] [CACHE] Error loading cache file
[ERROR] Could not connect to database
```

### Find Where Something Happens
1. Look for the log message in console
2. Search for that text in the code
3. That's where the action happens!

Example:
```
Console: "[INFO] [QUERY] Fetching policies..."
Search in: database.py
Found at: Line 324
```

## 📚 Learning Path

### Beginner
1. Read `REFACTORING_SUMMARY.md`
2. Understand workflow in this file
3. Run the code once
4. Read `config.py` to understand settings

### Intermediate
1. Read `database.py` - see how data is fetched
2. Read `ollama_client.py` - see how AI is called
3. Modify a simple setting (like max documents)
4. Run and observe changes

### Advanced
1. Read `kpi_generator.py` - understand full pipeline
2. Read `synthetic_data.py` - see data generation
3. Add a new module
4. Modify AI prompt
5. Add new validation rules

## 💡 Pro Tips

1. **Always test with small data first**
   ```bash
   python -m backend.grc.AiKpis.generateFrameworkKpi --max-s3-docs 2
   ```

2. **Use module filter to test one module**
   ```bash
   python -m backend.grc.AiKpis.generateFrameworkKpi --modules policies
   ```

3. **Check logs carefully** - they tell you exactly what's happening

4. **Start with config.py** - most customization happens there

5. **Read docstrings** - every function has explanation

6. **Test incrementally** - change one thing at a time

## 🎯 Your Next Steps

1. ✅ Read this guide completely
2. ✅ Run the code once to see it work
3. ✅ Read `config.py` to understand settings
4. ✅ Try changing one setting (like max documents)
5. ✅ Read one module file (start with `database.py`)
6. ✅ Try adding a new module
7. ✅ Experiment and learn!

## 📞 Need Help?

- Check `README.md` for detailed documentation
- Check `REFACTORING_SUMMARY.md` for migration guide
- Read function docstrings in code
- Search for error messages in code

**Remember**: Every function has comments explaining what it does!

Good luck with your learning! 🚀


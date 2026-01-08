# 🔐 GRC Auto-Decryption Guide

## Problem
Data is encrypted in the database ✅, but showing encrypted (like `gAAAAABpXsv...`) in the frontend ❌

## Solution
Use the **Auto-Decrypt Helper** for all raw SQL queries in GRC views.

---

## ✅ Quick Fix Pattern

### For Views Using Raw SQL Queries

**Before (Returns Encrypted Data ❌):**
```python
with connection.cursor() as cursor:
    cursor.execute(query, params)
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

return Response(results, status=status.HTTP_200_OK)
```

**After (Returns Decrypted Data ✅):**
```python
with connection.cursor() as cursor:
    cursor.execute(query, params)
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

# AUTO-DECRYPT: Automatically decrypt all encrypted fields
from grc.utils.auto_decrypt_helper import decrypt_query_results
results = decrypt_query_results(results, {
    'title': 'Audit',           # Maps 'title' field to Audit model
    'framework': 'Framework',   # Maps 'framework' field to Framework model
    'policy': 'Policy',         # Maps 'policy' field to Policy model
    'auditor': 'Users',         # Maps 'auditor' field to Users model
    # Add all fields that need decryption
})

return Response(results, status=status.HTTP_200_OK)
```

---

## 📋 Step-by-Step Instructions

### Step 1: Import the Helper
```python
from grc.utils.auto_decrypt_helper import decrypt_query_results
```

### Step 2: After Fetching SQL Results
Right after converting SQL results to dictionaries, call `decrypt_query_results`:

```python
results = [dict(zip(columns, row)) for row in cursor.fetchall()]

# Add this line:
results = decrypt_query_results(results, field_model_mapping)
```

### Step 3: Define Field-to-Model Mapping
Create a dictionary mapping your SQL field names to model names:

```python
field_model_mapping = {
    'title': 'Audit',              # SQL field 'title' comes from Audit model
    'framework': 'Framework',      # SQL field 'framework' comes from Framework model
    'policy': 'Policy',            # SQL field 'policy' comes from Policy model
    'subpolicy': 'SubPolicy',      # SQL field 'subpolicy' comes from SubPolicy model
    'auditor': 'Users',            # SQL field 'auditor' comes from Users model
    'reviewer': 'Users',           # SQL field 'reviewer' comes from Users model
    'business_unit': 'Audit',      # SQL field 'business_unit' comes from Audit model
}
```

### Step 4: Pass to Helper
```python
results = decrypt_query_results(results, field_model_mapping)
```

---

## 🎯 Common Field Mappings

### Audit Module
```python
{
    'title': 'Audit',
    'scope': 'Audit',
    'objective': 'Audit',
    'business_unit': 'Audit',
    'evidence': 'Audit',
    'comments': 'Audit',
    'framework': 'Framework',
    'policy': 'Policy',
    'subpolicy': 'SubPolicy',
    'auditor': 'Users',
    'reviewer': 'Users',
    'assignee': 'Users',
}
```

### Compliance Module
```python
{
    'compliance_title': 'Compliance',
    'compliancetitle': 'Compliance',
    'compliance_item_description': 'Compliance',
    'scope': 'Compliance',
    'objective': 'Compliance',
    'business_units_covered': 'Compliance',
    'framework': 'Framework',
    'policy': 'Policy',
    'subpolicy': 'SubPolicy',
}
```

### Policy Module
```python
{
    'policy_name': 'Policy',
    'policyname': 'Policy',
    'policy_description': 'Policy',
    'policydescription': 'Policy',
    'subpolicy_name': 'SubPolicy',
    'subpolicyname': 'SubPolicy',
    'framework_name': 'Framework',
    'frameworkname': 'Framework',
}
```

### Risk Module
```python
{
    'risk_title': 'Risk',
    'risktitle': 'Risk',
    'risk_description': 'Risk',
    'riskdescription': 'Risk',
    'possible_damage': 'Risk',
    'business_impact': 'Risk',
}
```

### Incident Module
```python
{
    'incident_title': 'Incident',
    'incidenttitle': 'Incident',
    'description': 'Incident',
    'affected_business_unit': 'Incident',
    'geographic_location': 'Incident',
}
```

---

## 🔍 How It Works

1. **Detects Encrypted Fields**: Checks `encryption_config.py` to see which fields are encrypted for each model
2. **Maps SQL Fields to Models**: Uses your field_model_mapping to know which model each SQL field comes from
3. **Decrypts Automatically**: Only decrypts fields that are actually encrypted (skips plain text)
4. **Handles Errors Gracefully**: If decryption fails, keeps original value (won't break your API)

---

## ✅ Already Fixed

- ✅ `get_all_audits()` - Audit dashboard list
- ✅ `get_all_audits_public()` - Public audit list
- ✅ `get_my_audits()` - My audits dashboard

---

## 📝 Files That Need Updates

Search for files with raw SQL queries:
```bash
grep -r "cursor.execute" grc_backend/grc/routes/
```

Common files to update:
- `grc/routes/Audit/audit_views.py` ✅ (partially done)
- `grc/routes/Compliance/compliance_views.py`
- `grc/routes/Policy/policy.py`
- `grc/routes/Risk/risk_views.py`
- `grc/routes/Incident/incident_views.py`
- `grc/routes/EventHandling/event_views.py`

---

## 🚀 Benefits

1. **Automatic**: Works for all encrypted fields automatically
2. **No Code Changes**: Just add one line after SQL queries
3. **Safe**: Won't break if decryption fails
4. **Consistent**: Same pattern across all modules
5. **Fast**: Only decrypts what's needed

---

## 💡 Tips

1. **Check Your SQL Query**: Look at your SELECT statement to see which fields you're returning
2. **Check encryption_config.py**: See which fields are encrypted for each model
3. **Map Correctly**: Make sure field names in your mapping match the SQL alias names
4. **Test**: After adding, test the API endpoint to verify data is decrypted

---

## ❓ Troubleshooting

### Data Still Encrypted?
- Check that field names in mapping match SQL alias names (case-sensitive)
- Verify the field is actually encrypted in `encryption_config.py`
- Check logs for decryption errors

### Performance Issues?
- The helper only decrypts fields that are actually encrypted
- It caches model configurations for performance
- If still slow, consider using serializers instead of raw SQL

---

## 📚 Related Files

- `grc/utils/auto_decrypt_helper.py` - The helper function
- `grc/utils/encryption_config.py` - Defines which fields are encrypted
- `grc/utils/data_encryption.py` - Encryption/decryption functions
- `grc/utils/base_serializer.py` - Auto-decrypting serializer (for DRF serializers)


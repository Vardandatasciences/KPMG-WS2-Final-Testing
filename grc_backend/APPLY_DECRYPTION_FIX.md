# 🚀 Quick Start: Apply Decryption Fix

## ONE-STEP FIX

Just restart your Django server:

```bash
# 1. Stop current server (Ctrl+C)

# 2. Restart server
cd grc_backend
python manage.py runserver
```

That's it! The code changes are already applied. You just need to restart to load them.

---

## Test It Works

After restart, open your frontend and check any page with data. You should see:

✅ **Plain text** like "Business Continuity Plan 2024"  
❌ **NOT encrypted** like "gAAAAABpXg..."

---

## Quick Diagnostic

Verify setup without restarting:

```bash
cd grc_backend
python test_encryption_simple.py
```

Should show all ✅ green checkmarks.

---

## If Still Broken

Try these in order:

### 1. Hard refresh browser
- Windows/Linux: `Ctrl+Shift+R`
- Mac: `Cmd+Shift+R`

### 2. Clear Python cache
```powershell
cd grc_backend
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
```

### 3. Run manual fix
```bash
cd grc_backend
python tprm_backend/fix_decryption_properties.py
```

### 4. Check logs
Look at Django server console for errors about:
- Import errors
- Decryption failures
- Missing encryption keys

---

## Need More Help?

See detailed guide: `DECRYPTION_FIX_README.md`

---

**TL;DR: Just restart your Django server!** 🎉


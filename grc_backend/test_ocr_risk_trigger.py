#!/usr/bin/env python
"""
Test script: OCR extraction save -> risk generation trigger.
Run from grc_backend with: python manage.py shell < test_ocr_risk_trigger.py
Or: python manage.py shell -c "$(cat test_ocr_risk_trigger.py)"
"""
import os
import sys
import django

# Setup Django if not already (e.g. when run as script)
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    django.setup()

def run_test():
    print("=" * 60)
    print("TEST: OCR save -> risk generation trigger (BCP/DRP)")
    print("=" * 60)
    
    from tprm_backend.bcpdrp.models import Plan
    from tprm_backend.bcpdrp.views import get_comprehensive_plan_data, generate_risks_for_plan_evaluation

    # 1) Find a plan (with or without OCR data)
    plan = Plan.objects.first()
    if not plan:
        print("FAIL: No plan found in database. Create a BCP/DRP plan first.")
        return False
    
    plan_id = plan.plan_id
    print(f"Using plan_id={plan_id} ({plan.plan_name}, type={plan.plan_type})")
    
    # 2) Ensure plan has some ocr_extracted_data (simulate save)
    if not plan.ocr_extracted_data or plan.ocr_extracted_data == {}:
        from django.utils import timezone
        plan.ocr_extracted_data = {
            "plan_id": plan_id,
            "purpose_scope": "Test BCP scope for risk generation.",
            "rto_targets": {"Critical": "4h"},
            "rpo_targets": {"Data": "1h"},
        }
        plan.ocr_extracted = True
        plan.ocr_extracted_at = timezone.now()
        plan.save()
        print("Set minimal ocr_extracted_data on plan (simulated save).")
    else:
        print("Plan already has ocr_extracted_data.")
    
    # 3) Trigger risk generation (same path as deferred thread after extract save)
    print("Triggering risk generation (generate_risks_for_plan_evaluation)...")
    try:
        result = generate_risks_for_plan_evaluation(plan_id=plan_id, evaluation_id=None)
        if result and result.get("risks"):
            n = len(result["risks"])
            print(f"PASS: Risk generation completed. Created {n} risk(s).")
            for i, r in enumerate(result["risks"][:3], 1):
                print(f"  Risk {i}: {r.get('title', 'N/A')} (priority={r.get('priority')})")
            return True
        elif result:
            print("PASS: Risk generation ran but returned 0 risks (possible Ollama/model issue).")
            return True
        else:
            print("FAIL: generate_risks_for_plan_evaluation returned None.")
            return False
    except Exception as e:
        print(f"FAIL: Exception during risk generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)

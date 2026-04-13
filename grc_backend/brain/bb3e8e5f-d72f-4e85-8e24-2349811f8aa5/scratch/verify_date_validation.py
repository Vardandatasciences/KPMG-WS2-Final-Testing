import os
import sys
import django
import datetime
from django.core.exceptions import ValidationError

# Mock Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grc_backend.settings')
try:
    django.setup()
except Exception as e:
    print(f"Django setup failed (likely environment issue): {e}")

# Import validators
sys.path.append(os.getcwd())
try:
    from grc.routes.Risk.risk_validation import RiskValidator
    from grc.routes.Incident.incident_views import validate_date as incident_validate_date
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_risk_date_validation():
    print("\n--- Testing Risk Date Validation ---")
    today = datetime.date.today()
    
    # Test past date (MitigationDueDate)
    past_date = (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    try:
        RiskValidator.validate_risk_instance_data({'MitigationDueDate': past_date})
        print("❌ Risk FAIL: Past MitigationDueDate accepted")
    except ValidationError:
        print("✅ Risk PASS: Past MitigationDueDate rejected")

    # Test distant future date
    future_date = (today + datetime.timedelta(days=365*11)).strftime('%Y-%m-%d')
    try:
        RiskValidator.validate_risk_instance_data({'MitigationDueDate': future_date})
        print("❌ Risk FAIL: Distant future date (>10y) accepted")
    except ValidationError:
        print("✅ Risk PASS: Distant future date (>10y) rejected")

def test_incident_date_validation():
    print("\n--- Testing Incident Date Validation ---")
    today = datetime.date.today()
    
    # Test future date for incident occurrence
    future_date = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    try:
        from grc.routes.Incident.incident_views import validate_incident_data
        validate_incident_data({'IncidentTitle': 'Test Incident', 'Description': 'Test Description', 'Date': future_date, 'Time': '12:00', 'RiskPriority': 'High'})
        print("❌ Incident FAIL: Future date accepted")
    except ValidationError:
        print("✅ Incident PASS: Future date rejected")

    # Test distant past date
    past_date = (today - datetime.timedelta(days=365*21)).strftime('%Y-%m-%d')
    try:
        validate_incident_data({'IncidentTitle': 'Test Incident', 'Description': 'Test Description', 'Date': past_date, 'Time': '12:00', 'RiskPriority': 'High'})
        print("❌ Incident FAIL: Distant past date (>20y) accepted")
    except ValidationError:
        print("✅ Incident PASS: Distant past date (>20y) rejected")

if __name__ == "__main__":
    test_risk_date_validation()
    test_incident_date_validation()

"""
Utility script to enable SEBI AI Auditor for a framework
Usage: python manage.py shell
>>> from grc.routes.Audit.enable_sebi_auditor import enable_sebi_for_framework
>>> enable_sebi_for_framework(framework_id=123, tenant_id=2)
"""

from django.db import connection
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)


def enable_sebi_for_framework(framework_id: int, tenant_id: int) -> bool:
    """
    Enable SEBI AI Auditor for a framework
    
    Args:
        framework_id: The Framework ID
        tenant_id: The Tenant ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with connection.cursor() as cursor:
            # Check if framework exists
            cursor.execute("""
                SELECT FrameworkId, FrameworkName, data_inventory
                FROM frameworks
                WHERE FrameworkId = %s AND TenantId = %s
            """, [framework_id, tenant_id])
            
            row = cursor.fetchone()
            if not row:
                print(f"❌ Framework {framework_id} not found for tenant {tenant_id}")
                return False
            
            framework_name = row[1] or ''
            data_inventory = row[2] or {}
            
            if not isinstance(data_inventory, dict):
                data_inventory = {}
            
            # Enable SEBI AI Auditor at framework level
            data_inventory['ai_bse_enabled'] = 1
            data_inventory['sebi_ai_auditor_enabled_at'] = timezone.now().isoformat()
            data_inventory['sebi_features'] = {
                'filing_accuracy_verification': True,
                'timeliness_sla_monitoring': True,
                'clause_level_mapping': True,
                'risk_scoring': True,
                'pattern_analysis': True,
                'evidence_pack_generation': True,
                'regulatory_dashboards': True
            }
            
            # Also enable at compliance level (ai_bse_enabled = 1)
            cursor.execute("""
                UPDATE compliance
                SET ai_bse_enabled = 1
                WHERE FrameworkId = %s AND TenantId = %s
            """, [framework_id, tenant_id])
            
            compliance_count = cursor.rowcount
            print(f"   ✅ Enabled ai_bse_enabled=1 for {compliance_count} compliance(s)")
            
            # Update framework
            cursor.execute("""
                UPDATE frameworks
                SET data_inventory = %s
                WHERE FrameworkId = %s AND TenantId = %s
            """, [json.dumps(data_inventory), framework_id, tenant_id])
            
            print(f"✅ SEBI AI Auditor enabled for framework: {framework_name} (ID: {framework_id})")
            print(f"   Tenant ID: {tenant_id}")
            print(f"   Features enabled:")
            for feature, enabled in data_inventory['sebi_features'].items():
                print(f"     - {feature}: {'✅' if enabled else '❌'}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error enabling SEBI AI Auditor: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False


def disable_sebi_for_framework(framework_id: int, tenant_id: int) -> bool:
    """
    Disable SEBI AI Auditor for a framework
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT FrameworkId, FrameworkName, data_inventory
                FROM frameworks
                WHERE FrameworkId = %s AND TenantId = %s
            """, [framework_id, tenant_id])
            
            row = cursor.fetchone()
            if not row:
                print(f"❌ Framework {framework_id} not found")
                return False
            
            framework_name = row[1] or ''
            data_inventory = row[2] or {}
            
            if not isinstance(data_inventory, dict):
                data_inventory = {}
            
            # Disable SEBI AI Auditor
            data_inventory['ai_bse_enabled'] = 0
            
            # Also disable at compliance level
            cursor.execute("""
                UPDATE compliance
                SET ai_bse_enabled = 0
                WHERE FrameworkId = %s AND TenantId = %s
            """, [framework_id, tenant_id])
            
            cursor.execute("""
                UPDATE frameworks
                SET data_inventory = %s
                WHERE FrameworkId = %s AND TenantId = %s
            """, [json.dumps(data_inventory), framework_id, tenant_id])
            
            print(f"✅ SEBI AI Auditor disabled for framework: {framework_name} (ID: {framework_id})")
            return True
            
    except Exception as e:
        logger.error(f"Error disabling SEBI AI Auditor: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False


def list_sebi_enabled_frameworks(tenant_id: int = None) -> list:
    """
    List all frameworks with SEBI AI Auditor enabled
    """
    try:
        with connection.cursor() as cursor:
            if tenant_id:
                cursor.execute("""
                    SELECT FrameworkId, FrameworkName, data_inventory
                    FROM frameworks
                    WHERE TenantId = %s
                    ORDER BY FrameworkName
                """, [tenant_id])
            else:
                cursor.execute("""
                    SELECT FrameworkId, FrameworkName, TenantId, data_inventory
                    FROM frameworks
                    ORDER BY TenantId, FrameworkName
                """)
            
            frameworks = []
            for row in cursor.fetchall():
                framework_id = row[0]
                framework_name = row[1]
                tenant = row[2] if len(row) > 2 else tenant_id
                data_inventory = row[-1] or {}
                
                if isinstance(data_inventory, str):
                    try:
                        data_inventory = json.loads(data_inventory)
                    except:
                        data_inventory = {}
                
                ai_bse_enabled = data_inventory.get('ai_bse_enabled', 0)
                
                if ai_bse_enabled == 1:
                    frameworks.append({
                        'framework_id': framework_id,
                        'framework_name': framework_name,
                        'tenant_id': tenant,
                        'enabled_at': data_inventory.get('sebi_ai_auditor_enabled_at')
                    })
            
            return frameworks
            
    except Exception as e:
        logger.error(f"Error listing SEBI frameworks: {str(e)}")
        return []


if __name__ == '__main__':
    # Example usage
    print("SEBI AI Auditor Management")
    print("=" * 50)
    
    # List enabled frameworks
    frameworks = list_sebi_enabled_frameworks()
    if frameworks:
        print(f"\n✅ Found {len(frameworks)} framework(s) with SEBI AI Auditor enabled:")
        for fw in frameworks:
            print(f"   - {fw['framework_name']} (ID: {fw['framework_id']}, Tenant: {fw['tenant_id']})")
    else:
        print("\n⚠️  No frameworks with SEBI AI Auditor enabled")

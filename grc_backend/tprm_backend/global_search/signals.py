from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import SearchIndex

# Import the actual models with correct paths
try:
    from slas.models import Vendor
except ImportError:
    Vendor = None

try:
    from rfp.models import RFP
except ImportError:
    RFP = None

try:
    from slas.models import Contract
except ImportError:
    Contract = None

try:
    from slas.models import VendorSLA as SLA
except ImportError:
    SLA = None

try:
    from bcpdrp.models import Plan as BCPDRP
except ImportError:
    BCPDRP = None


@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    """Handle user save events for potential indexing."""
    # This is a placeholder - implement based on your user model requirements
    pass


def index_vendor_data(vendor_instance):
    """Index vendor data for search."""
    try:
        SearchIndex.create_or_update(
            entity_type='vendor',
            entity_id=vendor_instance.vendor_id,
            title=vendor_instance.company_name,
            summary=getattr(vendor_instance, 'legal_name', '') or '',
            keywords=f"{getattr(vendor_instance, 'vendor_code', '')} {vendor_instance.status}",
            payload_json={
                'status': vendor_instance.status,
                'vendor_code': getattr(vendor_instance, 'vendor_code', ''),
                'legal_name': getattr(vendor_instance, 'legal_name', ''),
                'company_name': vendor_instance.company_name,
            }
        )
    except Exception as e:
        print(f"Failed to index vendor {vendor_instance.vendor_id}: {e}")


def index_rfp_data(rfp_instance):
    """Index RFP data for search."""
    try:
        entity_id = getattr(rfp_instance, 'rfp_id', None) or getattr(rfp_instance, 'pk', None)
        if entity_id is None:
            print("Skipped indexing RFP because entity_id could not be determined.")
            return

        SearchIndex.create_or_update(
            entity_type='rfp',
            entity_id=entity_id,
            title=getattr(rfp_instance, 'rfp_title', '') or getattr(rfp_instance, 'title', ''),
            summary=getattr(rfp_instance, 'description', '') or '',
            keywords=f"{getattr(rfp_instance, 'status', '')} {getattr(rfp_instance, 'category', '')} {getattr(rfp_instance, 'risk_level', '')}",
            payload_json={
                'status': getattr(rfp_instance, 'status', ''),
                'category': getattr(rfp_instance, 'category', ''),
                'risk_level': getattr(rfp_instance, 'risk_level', ''),
                'submission_deadline': str(getattr(rfp_instance, 'submission_deadline', '')),
                'estimated_value': getattr(rfp_instance, 'estimated_value', ''),
                'currency': getattr(rfp_instance, 'currency', ''),
            }
        )
    except Exception as e:
        print(f"Failed to index RFP {getattr(rfp_instance, 'rfp_id', getattr(rfp_instance, 'pk', 'unknown'))}: {e}")


def index_contract_data(contract_instance):
    """Index contract data for search."""
    try:
        SearchIndex.create_or_update(
            entity_type='contract',
            entity_id=contract_instance.id,
            title=contract_instance.title,
            summary=contract_instance.description or '',
            keywords=f"{contract_instance.status} {getattr(contract_instance, 'category', '')} {contract_instance.vendor_name}",
            payload_json={
                'status': contract_instance.status,
                'category': getattr(contract_instance, 'category', ''),
                'risk_level': getattr(contract_instance, 'risk_level', ''),
                'vendor_name': contract_instance.vendor_name,
                'start_date': str(getattr(contract_instance, 'start_date', '')),
                'end_date': str(getattr(contract_instance, 'end_date', '')),
                'value': getattr(contract_instance, 'value', ''),
            }
        )
    except Exception as e:
        print(f"Failed to index contract {contract_instance.id}: {e}")


def index_sla_data(sla_instance):
    """Index SLA data for search."""
    try:
        # Get vendor name safely
        vendor_name = ''
        try:
            if hasattr(sla_instance, 'vendor') and sla_instance.vendor:
                vendor_name = sla_instance.vendor.company_name
        except Exception:
            pass
        
        # Create summary from available fields
        summary_parts = []
        if hasattr(sla_instance, 'business_service_impacted') and sla_instance.business_service_impacted:
            summary_parts.append(sla_instance.business_service_impacted)
        if hasattr(sla_instance, 'measurement_methodology') and sla_instance.measurement_methodology:
            summary_parts.append(sla_instance.measurement_methodology[:200])
        summary = ' - '.join(summary_parts) if summary_parts else ''
        
        SearchIndex.create_or_update(
            entity_type='sla',
            entity_id=sla_instance.sla_id,
            title=sla_instance.sla_name,
            summary=summary,
            keywords=f"{sla_instance.status} {sla_instance.sla_type} {getattr(sla_instance, 'priority', '')} {getattr(sla_instance, 'compliance_framework', '')} {vendor_name}",
            payload_json={
                'status': sla_instance.status,
                'sla_type': sla_instance.sla_type,
                'priority': getattr(sla_instance, 'priority', ''),
                'compliance_framework': getattr(sla_instance, 'compliance_framework', ''),
                'vendor_name': vendor_name,
                'business_service_impacted': getattr(sla_instance, 'business_service_impacted', ''),
                'approval_status': getattr(sla_instance, 'approval_status', ''),
            }
        )
    except Exception as e:
        print(f"Failed to index SLA {sla_instance.sla_id}: {e}")


def index_bcp_drp_data(bcp_drp_instance):
    """Index BCP/DRP data for search."""
    try:
        # Use plan_name instead of title (Plan model doesn't have title attribute)
        plan_title = getattr(bcp_drp_instance, 'plan_name', '') or getattr(bcp_drp_instance, 'strategy_name', '') or f"Plan {bcp_drp_instance.id}"
        
        # Use plan_scope as summary/description (Plan model doesn't have description attribute)
        plan_summary = getattr(bcp_drp_instance, 'plan_scope', '') or ''
        
        # Build keywords from available fields
        keywords_parts = [
            getattr(bcp_drp_instance, 'status', ''),
            getattr(bcp_drp_instance, 'plan_type', ''),
            getattr(bcp_drp_instance, 'strategy_name', ''),
            getattr(bcp_drp_instance, 'criticality', ''),
        ]
        keywords = ' '.join(filter(None, keywords_parts))
        
        SearchIndex.create_or_update(
            entity_type='bcp_drp',
            entity_id=bcp_drp_instance.id,
            title=plan_title,
            summary=plan_summary,
            keywords=keywords,
            payload_json={
                'status': getattr(bcp_drp_instance, 'status', ''),
                'plan_type': getattr(bcp_drp_instance, 'plan_type', ''),
                'plan_name': getattr(bcp_drp_instance, 'plan_name', ''),
                'strategy_name': getattr(bcp_drp_instance, 'strategy_name', ''),
                'criticality': getattr(bcp_drp_instance, 'criticality', ''),
                'vendor_id': getattr(bcp_drp_instance, 'vendor_id', ''),
                'version': getattr(bcp_drp_instance, 'version', ''),
                'document_date': str(getattr(bcp_drp_instance, 'document_date', '')) if getattr(bcp_drp_instance, 'document_date', None) else '',
                'ocr_extracted': getattr(bcp_drp_instance, 'ocr_extracted', False),
            }
        )
    except Exception as e:
        print(f"Failed to index BCP/DRP {bcp_drp_instance.id}: {e}")


def remove_from_index(entity_type, entity_id):
    """Remove an entity from the search index."""
    try:
        SearchIndex.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id
        ).delete()
    except Exception as e:
        print(f"Failed to remove {entity_type}:{entity_id} from index: {e}")


# Signal handlers for automatic indexing
# Only register signals if models were successfully imported

if Vendor is not None:
    @receiver(post_save, sender=Vendor)
    def handle_vendor_save(sender, instance, created, **kwargs):
        """Handle vendor save events."""
        index_vendor_data(instance)

    @receiver(post_delete, sender=Vendor)
    def handle_vendor_delete(sender, instance, **kwargs):
        """Handle vendor delete events."""
        remove_from_index('vendor', instance.vendor_id)

if RFP is not None:
    @receiver(post_save, sender=RFP)
    def handle_rfp_save(sender, instance, created, **kwargs):
        """Handle RFP save events."""
        index_rfp_data(instance)

    @receiver(post_delete, sender=RFP)
    def handle_rfp_delete(sender, instance, **kwargs):
        """Handle RFP delete events."""
        remove_from_index('rfp', getattr(instance, 'rfp_id', getattr(instance, 'pk', None)))

if Contract is not None:
    @receiver(post_save, sender=Contract)
    def handle_contract_save(sender, instance, created, **kwargs):
        """Handle contract save events."""
        index_contract_data(instance)

    @receiver(post_delete, sender=Contract)
    def handle_contract_delete(sender, instance, **kwargs):
        """Handle contract delete events."""
        remove_from_index('contract', instance.id)

if SLA is not None:
    @receiver(post_save, sender=SLA)
    def handle_sla_save(sender, instance, created, **kwargs):
        """Handle SLA save events."""
        index_sla_data(instance)

    @receiver(post_delete, sender=SLA)
    def handle_sla_delete(sender, instance, **kwargs):
        """Handle SLA delete events."""
        remove_from_index('sla', instance.sla_id)

if BCPDRP is not None:
    @receiver(post_save, sender=BCPDRP)
    def handle_bcp_drp_save(sender, instance, created, **kwargs):
        """Handle BCP/DRP save events."""
        index_bcp_drp_data(instance)

    @receiver(post_delete, sender=BCPDRP)
    def handle_bcp_drp_delete(sender, instance, **kwargs):
        """Handle BCP/DRP delete events."""
        remove_from_index('bcp_drp', instance.id)

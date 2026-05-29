"""
Management command to index existing GRC records into ChromaDB for similarity search.
Usage: python manage.py index_existing_records [--type Framework|Policy|SubPolicy|Compliance] [--tenant_id 2]
"""
import logging

from django.core.management.base import BaseCommand
from grc.models import Framework, Policy, SubPolicy, Compliance
from grc.services.embedding_service import EmbeddingService
from grc.services.vector_store_service import VectorStoreService
from grc.utils.text_cleaner import TextCleaner


class Command(BaseCommand):
    help = 'Index existing GRC records into ChromaDB for similarity search'

    def add_arguments(self, parser):
        parser.add_argument('--type', type=str, default='all',
                            help='Record type: Framework|Policy|SubPolicy|Compliance|all')
        parser.add_argument('--tenant_id', type=int, default=None,
                            help='Only index records for this tenant')
        parser.add_argument('--skip-existing', action='store_true', default=True,
                            help='Skip records already indexed in ChromaDB (default: True)')
        parser.add_argument('--reindex', action='store_true', default=False,
                            help='Force re-index all records even if already indexed')
        parser.add_argument('--fix-policy-framework-ids', action='store_true', default=False,
                            help='Update parent_framework_id metadata for indexed policies (no re-embed)')
        parser.add_argument('--fix-compliance-parent-ids', action='store_true', default=False,
                            help='Update parent_* metadata for indexed compliance records (no re-embed)')
        parser.add_argument('--compliance-ids', type=str, default=None,
                            help='Comma-separated ComplianceIds for --fix-compliance-parent-ids (e.g. 1986,1987)')

    def handle(self, *args, **options):
        if options.get('fix_policy_framework_ids') or options.get('fix_compliance_parent_ids'):
            logging.getLogger('chromadb').setLevel(logging.WARNING)
            self.stdout.write(
                'Note: Chroma "telemetry" errors in the log are harmless — updates still apply.\n'
            )
        record_type = options['type']
        tenant_id = options['tenant_id']
        skip_existing = not options['reindex']

        embedding_service = EmbeddingService()
        vector_store = VectorStoreService()
        text_cleaner = TextCleaner()

        if options.get('fix_policy_framework_ids'):
            self._fix_policy_framework_ids(vector_store, tenant_id)
            stats = vector_store.get_stats()
            self.stdout.write(self.style.SUCCESS(
                f'\nDone (metadata only). ChromaDB has {stats.get("total_embeddings", "?")} embeddings.'
            ))
            return

        if options.get('fix_compliance_parent_ids'):
            self._fix_compliance_parent_ids(
                vector_store, tenant_id, options.get('compliance_ids')
            )
            stats = vector_store.get_stats()
            self.stdout.write(self.style.SUCCESS(
                f'\nDone (metadata only). ChromaDB has {stats.get("total_embeddings", "?")} embeddings.'
            ))
            return

        if record_type in ('Framework', 'all'):
            self._index_frameworks(embedding_service, vector_store, text_cleaner, tenant_id, skip_existing)
        if record_type in ('Policy', 'all'):
            self._index_policies(embedding_service, vector_store, text_cleaner, tenant_id, skip_existing)
        if record_type in ('SubPolicy', 'all'):
            self._index_subpolicies(embedding_service, vector_store, text_cleaner, tenant_id, skip_existing)
        if record_type in ('Compliance', 'all'):
            self._index_compliances(embedding_service, vector_store, text_cleaner, tenant_id, skip_existing)

        stats = vector_store.get_stats()
        self.stdout.write(self.style.SUCCESS(f'\nDone! ChromaDB now has {stats.get("total_embeddings", "?")} embeddings.'))

    def _safe_str(self, value):
        """Convert any value to plain string, handling encrypted list fields."""
        if value is None:
            return ''
        if isinstance(value, list):
            return ' '.join(str(v) for v in value if v)
        return str(value)

    def _index_frameworks(self, embedding_service, vector_store, text_cleaner, tenant_id, skip_existing=True):
        qs = Framework.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        self.stdout.write(f'Indexing {qs.count()} Frameworks...')
        ok = fail = skipped = 0
        for fw in qs:
            if skip_existing and vector_store.embedding_exists(f'framework_{fw.FrameworkId}'):
                skipped += 1
                continue
            try:
                data = {
                    'FrameworkName': self._safe_str(fw.FrameworkName),
                    'FrameworkDescription': self._safe_str(fw.FrameworkDescription),
                    'Category': self._safe_str(fw.Category),
                    'InternalExternal': self._safe_str(fw.InternalExternal),
                    'Identifier': self._safe_str(fw.Identifier),
                }
                cleaned = text_cleaner.clean_framework(data)
                result = embedding_service.generate_embedding(cleaned.embedding_text)
                if result:
                    fw_domain = None
                    if hasattr(fw, 'domain') and fw.domain:
                        raw = self._safe_str(getattr(fw.domain, 'domain_name', None) or str(fw.domain))
                        fw_domain = raw.replace(' ', '').lower() if raw else None
                    vector_store.store_embedding(
                        embedding_id=f'framework_{fw.FrameworkId}',
                        embedding_vector=result,
                        entity_type='Framework',
                        entity_id=fw.FrameworkId,
                        tenant_id=getattr(fw, 'tenant_id', None),
                        domain=fw_domain,
                        category=self._safe_str(fw.Category),
                        name=self._safe_str(fw.FrameworkName),
                    )
                    ok += 1
                    self.stdout.write(f'  ✓ Framework {fw.FrameworkId}: {fw.FrameworkName}')
                else:
                    fail += 1
                    self.stdout.write(self.style.WARNING(f'  ✗ Framework {fw.FrameworkId}: embedding failed'))
            except Exception as e:
                import traceback
                fail += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Framework {fw.FrameworkId}: {e}'))
                self.stdout.write(self.style.ERROR(traceback.format_exc()))
        self.stdout.write(f'Frameworks: {ok} indexed, {skipped} skipped, {fail} failed.')

    def _fix_policy_framework_ids(self, vector_store, tenant_id):
        """Patch ChromaDB metadata so policy search can filter by FrameworkId."""
        qs = Policy.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        updated = skipped = 0
        self.stdout.write(f'Updating parent_framework_id for {qs.count()} policies...')
        for p in qs:
            embedding_id = f'policy_{p.PolicyId}'
            if not vector_store.embedding_exists(embedding_id):
                skipped += 1
                continue
            fw_id = p.FrameworkId_id if p.FrameworkId_id else 0
            if vector_store.update_metadata(embedding_id, {'parent_framework_id': fw_id}):
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f'Framework IDs: {updated} updated, {skipped} not in ChromaDB.'
        ))

    def _compliance_parent_ids(self, compliance):
        subpol = getattr(compliance, 'SubPolicy', None)
        subpol_id = getattr(compliance, 'SubPolicy_id', None) or (
            subpol.SubPolicyId if subpol else 0
        )
        policy_id = 0
        fw_id = 0
        if subpol and getattr(subpol, 'PolicyId', None):
            pol = subpol.PolicyId
            policy_id = getattr(pol, 'PolicyId', None) or pol.pk or 0
            if getattr(pol, 'FrameworkId', None):
                fw_id = getattr(pol, 'FrameworkId_id', None) or pol.FrameworkId.FrameworkId or 0
        return subpol_id or 0, policy_id or 0, fw_id or 0

    def _fix_compliance_parent_ids(self, vector_store, tenant_id, compliance_ids_csv=None):
        qs = Compliance.objects.select_related('SubPolicy__PolicyId__FrameworkId').all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if compliance_ids_csv:
            id_list = [int(x.strip()) for x in compliance_ids_csv.split(',') if x.strip()]
            qs = qs.filter(ComplianceId__in=id_list)
            self.stdout.write(f'Filtering to ComplianceIds: {id_list}')

        chroma_ids = vector_store.get_embedding_ids_for_entity_type('Compliance')
        self.stdout.write(f'Found {len(chroma_ids)} Compliance embeddings in ChromaDB.')

        updates = {}
        skipped = 0
        for c in qs.iterator(chunk_size=500):
            embedding_id = f'compliance_{c.ComplianceId}'
            if embedding_id not in chroma_ids:
                skipped += 1
                continue
            subpol_id, policy_id, fw_id = self._compliance_parent_ids(c)
            updates[embedding_id] = {
                'parent_subpolicy_id': subpol_id,
                'parent_policy_id': policy_id,
                'parent_framework_id': fw_id,
            }

        self.stdout.write(f'Patching {len(updates)} records in batches (do not Ctrl+C)...')
        updated = vector_store.batch_update_metadata(updates, batch_size=200)
        self.stdout.write(self.style.SUCCESS(
            f'Compliance parent IDs: {updated} updated, {skipped} not in ChromaDB.'
        ))

    def _index_policies(self, embedding_service, vector_store, text_cleaner, tenant_id, skip_existing=True):
        qs = Policy.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        self.stdout.write(f'Indexing {qs.count()} Policies...')
        ok = fail = skipped = 0
        for p in qs:
            if skip_existing and vector_store.embedding_exists(f'policy_{p.PolicyId}'):
                skipped += 1
                continue
            try:
                data = {
                    'PolicyName': self._safe_str(p.PolicyName),
                    'PolicyDescription': self._safe_str(p.PolicyDescription),
                    'PolicyType': self._safe_str(getattr(p, 'PolicyType', '')),
                    'PolicyCategory': self._safe_str(getattr(p, 'PolicyCategory', '')),
                }
                cleaned = text_cleaner.clean_policy(data)
                result = embedding_service.generate_embedding(cleaned.embedding_text)
                if result:
                    p_domain = None
                    if hasattr(p, 'domain') and p.domain:
                        raw = self._safe_str(getattr(p.domain, 'domain_name', None) or str(p.domain))
                        p_domain = raw.replace(' ', '').lower() if raw else None
                    tenant_val = getattr(p, 'tenant_id', None)
                    if tenant_val is None and getattr(p, 'tenant', None):
                        tenant_val = p.tenant_id
                    vector_store.store_embedding(
                        embedding_id=f'policy_{p.PolicyId}',
                        embedding_vector=result,
                        entity_type='Policy',
                        entity_id=p.PolicyId,
                        tenant_id=tenant_val,
                        domain=p_domain or 'unknown',
                        category=self._safe_str(getattr(p, 'PolicyCategory', '')),
                        name=self._safe_str(p.PolicyName),
                        parent_framework_id=p.FrameworkId_id,
                    )
                    ok += 1
                    self.stdout.write(f'  ✓ Policy {p.PolicyId}: {p.PolicyName}')
                else:
                    fail += 1
            except Exception as e:
                fail += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Policy {p.PolicyId}: {e}'))
        self.stdout.write(f'Policies: {ok} indexed, {skipped} skipped, {fail} failed.')

    def _index_subpolicies(self, embedding_service, vector_store, text_cleaner, tenant_id, skip_existing=True):
        qs = SubPolicy.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        self.stdout.write(f'Indexing {qs.count()} SubPolicies...')
        ok = fail = skipped = 0
        for sp in qs:
            if skip_existing and vector_store.embedding_exists(f'subpolicy_{sp.SubPolicyId}'):
                skipped += 1
                continue
            try:
                data = {
                    'SubPolicyName': self._safe_str(sp.SubPolicyName),
                    'Description': self._safe_str(sp.Description),
                    'Control': self._safe_str(sp.Control),
                    'Identifier': self._safe_str(sp.Identifier),
                }
                cleaned = text_cleaner.clean_subpolicy(data)
                result = embedding_service.generate_embedding(cleaned.embedding_text)
                if result:
                    tenant_val = getattr(sp, 'tenant_id', None)
                    if tenant_val is None and getattr(sp, 'tenant', None):
                        tenant_val = sp.tenant_id
                    fw_id = sp.PolicyId.FrameworkId_id if getattr(sp, 'PolicyId', None) else 0
                    policy_id = sp.PolicyId_id if getattr(sp, 'PolicyId', None) else 0
                    vector_store.store_embedding(
                        embedding_id=f'subpolicy_{sp.SubPolicyId}',
                        embedding_vector=result,
                        entity_type='SubPolicy',
                        entity_id=sp.SubPolicyId,
                        tenant_id=tenant_val,
                        domain=None,
                        category=None,
                        name=self._safe_str(sp.SubPolicyName),
                        parent_framework_id=fw_id,
                        parent_policy_id=policy_id,
                    )
                    ok += 1
                    self.stdout.write(f'  ✓ SubPolicy {sp.SubPolicyId}: {sp.SubPolicyName}')
                else:
                    fail += 1
            except Exception as e:
                fail += 1
                self.stdout.write(self.style.ERROR(f'  ✗ SubPolicy {sp.SubPolicyId}: {e}'))
        self.stdout.write(f'SubPolicies: {ok} indexed, {skipped} skipped, {fail} failed.')

    def _index_compliances(self, embedding_service, vector_store, text_cleaner, tenant_id, skip_existing=True):
        qs = Compliance.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        self.stdout.write(f'Indexing {qs.count()} Compliance records...')
        ok = fail = skipped = 0
        for c in qs:
            if skip_existing and vector_store.embedding_exists(f'compliance_{c.ComplianceId}'):
                skipped += 1
                continue
            try:
                data = {
                    'ComplianceTitle': self._safe_str(c.ComplianceTitle),
                    'ComplianceItemDescription': self._safe_str(c.ComplianceItemDescription),
                    'ComplianceType': self._safe_str(getattr(c, 'ComplianceType', '')),
                    'Scope': self._safe_str(getattr(c, 'Scope', '')),
                    'Identifier': self._safe_str(getattr(c, 'Identifier', '')),
                }
                cleaned = text_cleaner.clean_compliance(data)
                result = embedding_service.generate_embedding(cleaned.embedding_text)
                if result:
                    subpol_id, policy_id, fw_id = self._compliance_parent_ids(c)
                    tenant_val = getattr(c, 'tenant_id', None)
                    if tenant_val is None and getattr(c, 'tenant', None):
                        tenant_val = c.tenant_id
                    vector_store.store_embedding(
                        embedding_id=f'compliance_{c.ComplianceId}',
                        embedding_vector=result,
                        entity_type='Compliance',
                        entity_id=c.ComplianceId,
                        tenant_id=tenant_val,
                        domain=None,
                        category=None,
                        name=self._safe_str(c.ComplianceTitle),
                        parent_subpolicy_id=subpol_id,
                        parent_policy_id=policy_id,
                        parent_framework_id=fw_id,
                    )
                    ok += 1
                    self.stdout.write(f'  ✓ Compliance {c.ComplianceId}: {c.ComplianceTitle}')
                else:
                    fail += 1
            except Exception as e:
                fail += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Compliance {c.ComplianceId}: {e}'))
        self.stdout.write(f'Compliance: {ok} indexed, {skipped} skipped, {fail} failed.')

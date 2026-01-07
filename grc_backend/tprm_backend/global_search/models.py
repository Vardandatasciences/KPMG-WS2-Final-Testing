from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
import json


# Custom manager for SearchIndex with search methods
class SearchIndexManager(models.Manager):
    def search(self, query, modules=None, filters=None):
        """
        Perform a comprehensive search across ALL database tables and ALL columns.
        
        Args:
            query (str): Search query
            modules (list): List of modules to search in
            filters (dict): Additional filters
        
        Returns:
            QuerySet: Filtered search results from search_index with enhanced data
        """
        from django.db import connection
        from django.db.models import Q
        from django.apps import apps
        
        queryset = self.get_queryset()
        
        # Apply text search using Q objects for better compatibility
        if query:
            search_terms = query.split()
            search_query = Q()
            
            for term in search_terms:
                # Search in basic fields
                basic_search = (
                    Q(title__icontains=term) |
                    Q(summary__icontains=term) |
                    Q(keywords__icontains=term)
                )
                
                # Search in payload_json fields
                payload_search = Q()
                
                # Common payload_json fields to search
                payload_fields = [
                    'status', 'category', 'risk_level', 'vendor_name', 'contact_name',
                    'contact_email', 'website', 'address', 'contract_type', 'service_type',
                    'plan_type', 'deadline', 'budget', 'value', 'currency', 'uptime_target',
                    'response_time', 'resolution_time', 'start_date', 'end_date',
                    'effective_date', 'review_date', 'rto', 'rpo', 'mto'
                ]
                
                for field in payload_fields:
                    try:
                        payload_search |= Q(payload_json__contains={field: term})
                    except:
                        pass
                
                search_query |= (basic_search | payload_search)
            
            queryset = queryset.filter(search_query)
        
        # Filter by modules
        if modules:
            queryset = queryset.filter(entity_type__in=modules)
        
        # Apply additional filters
        if filters:
            if 'date_from' in filters and filters['date_from']:
                from django.utils import timezone
                from datetime import datetime
                try:
                    date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d')
                    date_from = timezone.make_aware(date_from)
                    queryset = queryset.filter(updated_at__gte=date_from)
                except ValueError:
                    pass
            if 'date_to' in filters and filters['date_to']:
                from django.utils import timezone
                from datetime import datetime
                try:
                    date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d')
                    date_to = timezone.make_aware(date_to)
                    queryset = queryset.filter(updated_at__lte=date_to)
                except ValueError:
                    pass
            if 'status' in filters and filters['status']:
                status_filter = filters['status']
                if isinstance(status_filter, list):
                    status_query = Q()
                    for status in status_filter:
                        status_query |= Q(payload_json__status__icontains=status)
                    queryset = queryset.filter(status_query)
                else:
                    queryset = queryset.filter(payload_json__status__icontains=status_filter)
            if 'category' in filters and filters['category']:
                category_filter = filters['category']
                if isinstance(category_filter, list):
                    category_query = Q()
                    for category in category_filter:
                        category_query |= Q(payload_json__category__icontains=category)
                    queryset = queryset.filter(category_query)
                else:
                    queryset = queryset.filter(payload_json__category__icontains=category_filter)
            if 'risk_level' in filters and filters['risk_level']:
                risk_filter = filters['risk_level']
                if isinstance(risk_filter, list):
                    risk_query = Q()
                    for risk in risk_filter:
                        risk_query |= Q(payload_json__risk_level__icontains=risk)
                    queryset = queryset.filter(risk_query)
                else:
                    queryset = queryset.filter(payload_json__risk_level__icontains=risk_filter)
        
        return queryset.order_by('-updated_at')

    def search_all_tables(self, query, modules=None, filters=None):
        """
        Perform a comprehensive search across ALL database tables and ALL columns.
        This method searches the actual data tables, not just the search index.
        
        Args:
            query (str): Search query
            modules (list): List of modules to search in
            filters (dict): Additional filters
        
        Returns:
            list: Combined search results from all tables
        """
        from django.db import connection
        from django.db.models import Q
        from django.apps import apps
        
        if not query:
            return []
        
        search_terms = query.split()
        all_results = []
        
        # Define the tables to search and their corresponding entity types
        table_configs = {
            'vendor': {
                'model_name': 'apps.vendor_core.models.Vendors',
                'entity_type': 'vendor',
                'search_fields': [
                    'company_name', 'legal_name', 'description', 'website', 'business_type',
                    'industry_sector', 'tax_id', 'duns_number', 'annual_revenue', 'employee_count',
                    'headquarters_country', 'headquarters_address', 'vendor_code', 'risk_level', 'status'
                ]
            },
            'rfp': {
                'model_name': 'rfp.models.RFP',
                'entity_type': 'rfp',
                'search_fields': [
                    'rfp_title', 'description', 'rfp_number', 'rfp_type', 'category', 'status',
                    'estimated_value', 'currency', 'geographical_scope', 'criticality_level',
                    'evaluation_method', 'award_justification'
                ]
            },
            'contract': {
                'model_name': 'contracts.models.VendorContract',
                'entity_type': 'contract',
                'search_fields': [
                    'contract_title', 'contract_number', 'contract_type', 'contract_kind', 'status',
                    'contract_value', 'currency', 'governing_law', 'contract_category',
                    'termination_clause_type', 'dispute_resolution_method', 'workflow_stage'
                ]
            },
            'sla': {
                'model_name': 'slas.models.VendorSLA',
                'entity_type': 'sla',
                'search_fields': [
                    'sla_name', 'sla_type', 'status', 'business_service_impacted',
                    'reporting_frequency', 'baseline_period', 'measurement_methodology',
                    'exclusions', 'compliance_framework', 'priority', 'approval_status'
                ]
            },
            'bcp_drp_plans': {
                'model_name': 'bcpdrp.models.Plan',
                'entity_type': 'bcp_drp',
                'search_fields': [
                    'plan_name', 'strategy_name', 'plan_type', 'status', 'plan_scope',
                    'criticality', 'version', 'file_uri', 'mime_type'
                ]
            },
            'bcp_drp_evaluations': {
                'model_name': 'bcpdrp.models.Evaluation',
                'entity_type': 'bcp_drp',
                'search_fields': [
                    'status', 'overall_score', 'quality_score', 'coverage_score',
                    'recovery_capability_score', 'compliance_score', 'evaluator_comments'
                ]
            }
        }
        
        # Filter tables based on modules parameter
        if modules:
            table_configs = {k: v for k, v in table_configs.items() if k in modules}
        
        for table_name, config in table_configs.items():
            try:
                # Get the model - handle different model name formats
                model_name = config['model_name']
                if '.' in model_name:
                    # Handle formats like 'apps.vendor_core.models.Vendors' or 'rfp.models.RFP'
                    parts = model_name.split('.')
                    if len(parts) >= 3 and parts[-2] == 'models':
                        # Format: app.models.ModelName or apps.app.models.ModelName
                        if parts[0] == 'apps':
                            app_label = parts[1]
                        else:
                            app_label = parts[0]
                        model_class = parts[-1]
                    else:
                        # Format: app.ModelName
                        app_label = parts[0]
                        model_class = parts[1]
                else:
                    # Simple format: ModelName (assume current app)
                    app_label = 'global_search'
                    model_class = model_name
                
                model = apps.get_model(app_label, model_class)
                
                # Build search query for this table
                table_query = Q()
                for term in search_terms:
                    term_query = Q()
                    for field in config['search_fields']:
                        try:
                            # Check if field exists in model
                            if hasattr(model, field):
                                term_query |= Q(**{f'{field}__icontains': term})
                        except:
                            continue
                    table_query &= term_query
                
                # Execute search on this table
                table_results = model.objects.filter(table_query)
                
                # Convert results to search index format
                for result in table_results:
                    # Create a search index entry for this result
                    search_entry = self._create_search_entry_from_model(
                        result, config['entity_type'], config['search_fields']
                    )
                    if search_entry:
                        all_results.append(search_entry)
                        
            except Exception as e:
                print(f"Error searching table {table_name}: {e}")
                continue
        
        return all_results

    def _create_search_entry_from_model(self, model_instance, entity_type, search_fields):
        """
        Create a search index entry from a model instance.
        
        Args:
            model_instance: The model instance
            entity_type (str): Type of entity
            search_fields (list): List of searchable fields
        
        Returns:
            dict: Search entry data
        """
        try:
            # Extract title and summary based on entity type
            if entity_type == 'vendor':
                title = getattr(model_instance, 'company_name', None)
                summary = getattr(model_instance, 'description', None)
            elif entity_type == 'rfp':
                title = getattr(model_instance, 'rfp_title', None)
                summary = getattr(model_instance, 'description', None)
            elif entity_type == 'contract':
                title = getattr(model_instance, 'contract_title', None)
                summary = getattr(model_instance, 'contract_number', None)
            elif entity_type == 'sla':
                title = getattr(model_instance, 'sla_name', None)
                summary = getattr(model_instance, 'business_service_impacted', None)
            elif entity_type == 'bcp_drp':
                title = getattr(model_instance, 'plan_name', None) or getattr(model_instance, 'strategy_name', None)
                summary = getattr(model_instance, 'plan_scope', None) or getattr(model_instance, 'evaluator_comments', None)
            else:
                # Fallback to generic fields
                title = getattr(model_instance, 'title', None) or getattr(model_instance, 'name', None) or getattr(model_instance, 'company_name', None)
                summary = getattr(model_instance, 'description', None)
            
            # Build keywords from searchable fields
            keywords = []
            for field in search_fields:
                if hasattr(model_instance, field):
                    value = getattr(model_instance, field)
                    if value and str(value).strip():
                        keywords.append(str(value))
            
            # Build payload_json from model fields
            payload_json = {}
            for field in search_fields:
                if hasattr(model_instance, field):
                    value = getattr(model_instance, field)
                    if value is not None:
                        payload_json[field] = value
            
            # Add common fields based on entity type
            if hasattr(model_instance, 'status'):
                payload_json['status'] = model_instance.status
            if hasattr(model_instance, 'category'):
                payload_json['category'] = model_instance.category
            if hasattr(model_instance, 'risk_level'):
                payload_json['risk_level'] = model_instance.risk_level
            
            # Add entity-specific identifier fields
            if entity_type == 'vendor' and hasattr(model_instance, 'vendor_id'):
                payload_json['entity_primary_key'] = model_instance.vendor_id
            elif entity_type == 'rfp' and hasattr(model_instance, 'rfp_id'):
                payload_json['entity_primary_key'] = model_instance.rfp_id
            elif entity_type == 'contract' and hasattr(model_instance, 'contract_id'):
                payload_json['entity_primary_key'] = model_instance.contract_id
            elif entity_type == 'sla' and hasattr(model_instance, 'sla_id'):
                payload_json['entity_primary_key'] = model_instance.sla_id
            elif entity_type == 'bcp_drp':
                if hasattr(model_instance, 'plan_id'):
                    payload_json['entity_primary_key'] = model_instance.plan_id
                elif hasattr(model_instance, 'evaluation_id'):
                    payload_json['entity_primary_key'] = model_instance.evaluation_id
            
            # Get the correct primary key value
            if entity_type == 'vendor':
                entity_id = getattr(model_instance, 'vendor_id', model_instance.pk)
            elif entity_type == 'rfp':
                entity_id = getattr(model_instance, 'rfp_id', model_instance.pk)
            elif entity_type == 'contract':
                entity_id = getattr(model_instance, 'contract_id', model_instance.pk)
            elif entity_type == 'sla':
                entity_id = getattr(model_instance, 'sla_id', model_instance.pk)
            elif entity_type == 'bcp_drp':
                entity_id = getattr(model_instance, 'plan_id', None) or getattr(model_instance, 'evaluation_id', model_instance.pk)
            else:
                entity_id = model_instance.pk
            
            return {
                'entity_type': entity_type,
                'entity_id': entity_id,
                'title': title or f"{entity_type.title()} {entity_id}",
                'summary': summary or '',
                'keywords': ' '.join(keywords),
                'payload_json': payload_json,
                'updated_at': getattr(model_instance, 'updated_at', None) or getattr(model_instance, 'created_at', None)
            }
            
        except Exception as e:
            print(f"Error creating search entry for {entity_type} {model_instance.id}: {e}")
            return None


class SearchIndex(models.Model):
    """
    Global search index table to store indexed data from all TPRM modules.
    Uses MySQL FULLTEXT indexing for fast text search capabilities.
    """
    
    ENTITY_TYPE_CHOICES = [
        ('vendor', 'Vendor'),
        ('rfp', 'Request for Proposal'),
        ('contract', 'Contract'),
        ('sla', 'Service Legal Agreement'),
        ('bcp_drp', 'BCP/DRP'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link search index to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='search_indexes', null=True, blank=True,
                               help_text="Tenant this search index belongs to")
    
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES,
        help_text="Type of entity (vendor, rfp, contract, etc.)"
    )
    entity_id = models.BigIntegerField(
        help_text="Unique identifier of the entity in its respective module"
    )
    title = models.CharField(
        max_length=255,
        help_text="Title or name of the entity"
    )
    summary = models.TextField(
        blank=True,
        null=True,
        help_text="Brief summary or description of the entity"
    )
    keywords = models.TextField(
        blank=True,
        null=True,
        help_text="Tags, categories, and codes for better searchability"
    )
    payload_json = models.JSONField(
        default=dict,
        blank=True,
        encoder=DjangoJSONEncoder,
        help_text="Additional data for UI-specific purposes (links, highlights, etc.)"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the record was last updated"
    )
    
    # Custom manager
    objects = SearchIndexManager()
    
    class Meta:
        db_table = 'search_index'
        unique_together = ('entity_type', 'entity_id')
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['updated_at']),
        ]
        verbose_name = 'Search Index'
        verbose_name_plural = 'Search Indexes'
    
    def __str__(self):
        return f"{self.get_entity_type_display()}: {self.title} (ID: {self.entity_id})"
    
    @property
    def global_uid(self):
        """Generate a global unique identifier for the entity."""
        return f"{self.entity_type}:{self.entity_id}"
    
    def get_searchable_text(self):
        """Get all searchable text content for this record."""
        text_parts = []
        
        if self.title:
            text_parts.append(self.title)
        
        if self.summary:
            text_parts.append(self.summary)
        
        if self.keywords:
            text_parts.append(self.keywords)
        
        return ' '.join(text_parts)
    
    def update_from_payload(self, payload):
        """
        Update the search index from a JSON payload.
        
        Args:
            payload (dict): JSON payload containing entity data
        """
        self.title = payload.get('title', self.title)
        self.summary = payload.get('summary', self.summary)
        self.keywords = payload.get('keywords', self.keywords)
        
        # Update payload_json with additional data
        if 'payload_json' in payload:
            self.payload_json.update(payload['payload_json'])
        
        self.save()
    
    @classmethod
    def create_or_update(cls, entity_type, entity_id, **kwargs):
        """
        Create or update a search index entry.
        
        Args:
            entity_type (str): Type of entity
            entity_id (int): Entity ID
            **kwargs: Additional fields to set
        
        Returns:
            SearchIndex: The created or updated search index instance
        """
        defaults = {
            'title': kwargs.get('title', ''),
            'summary': kwargs.get('summary', ''),
            'keywords': kwargs.get('keywords', ''),
            'payload_json': kwargs.get('payload_json', {}),
        }
        
        obj, created = cls.objects.update_or_create(
            entity_type=entity_type,
            entity_id=entity_id,
            defaults=defaults
        )
        
        return obj


class SearchAnalytics(models.Model):
    """
    Model to track search analytics and performance metrics.
    """
    
    # MULTI-TENANCY: Link search analytics to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='search_analytics', null=True, blank=True,
                               help_text="Tenant this search analytics belongs to")
    
    query = models.TextField(help_text="Search query performed")
    results_count = models.IntegerField(default=0, help_text="Number of results returned")
    response_time = models.FloatField(help_text="Response time in milliseconds")
    filters_used = models.JSONField(default=dict, help_text="Filters applied to the search")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_analytics'
        indexes = [
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Search Analytics'
        verbose_name_plural = 'Search Analytics'
    
    def __str__(self):
        return f"Search: {self.query[:50]}..."

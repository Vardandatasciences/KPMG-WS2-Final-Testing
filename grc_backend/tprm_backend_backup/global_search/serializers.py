from rest_framework import serializers
from django.db.models import Count
from .models import SearchIndex, SearchAnalytics


class SearchQuerySerializer(serializers.Serializer):
    """Serializer for search query requests."""
    
    q = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Search query string"
    )
    page = serializers.IntegerField(
        min_value=1,
        default=1,
        help_text="Page number for pagination"
    )
    page_size = serializers.IntegerField(
        min_value=-1,  # Allow -1 to disable pagination
        max_value=10000,  # Increased maximum page size
        default=1000,  # Increased default page size
        help_text="Number of results per page (-1 for no pagination)"
    )
    is_finalized = serializers.BooleanField(
        default=False,
        help_text="Whether this is a finalized search (Enter pressed) or live search (typing)"
    )
    status = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Filter by status values"
    )
    category = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Filter by category values"
    )
    risk_level = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Filter by risk level values"
    )


class SearchResultSerializer(serializers.ModelSerializer):
    """Serializer for search results."""
    
    global_uid = serializers.SerializerMethodField()
    module = serializers.CharField(source='entity_type')
    snippet = serializers.SerializerMethodField()
    detailed_info = serializers.SerializerMethodField()
    additional_fields = serializers.SerializerMethodField()
    
    class Meta:
        model = SearchIndex
        fields = [
            'global_uid',
            'module',
            'entity_id',
            'title',
            'snippet',
            'summary',
            'keywords',
            'detailed_info',
            'additional_fields',
            'updated_at',
            'payload_json'
        ]
    
    def get_global_uid(self, obj):
        """Generate global unique identifier."""
        return obj.global_uid
    
    def get_snippet(self, obj):
        """Generate a comprehensive snippet from all searchable content with highlighting."""
        query = self.context.get('query', '')
        search_terms = self.context.get('search_terms', [])
        
        # Get comprehensive searchable text including payload_json data
        text_parts = []
        
        if obj.title:
            text_parts.append(obj.title)
        
        if obj.summary:
            text_parts.append(obj.summary)
        
        if obj.keywords:
            text_parts.append(obj.keywords)
        
        # Add payload_json data to searchable text
        if obj.payload_json:
            for key, value in obj.payload_json.items():
                if isinstance(value, (str, int, float)):
                    text_parts.append(str(value))
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (str, int, float)):
                            text_parts.append(str(sub_value))
        
        text = ' '.join(text_parts)
        
        # Generate snippet with highlighting
        if query and search_terms:
            # Find the best match for snippet generation
            best_match = None
            best_position = -1
            
            for term in search_terms:
                if term.lower() in text.lower():
                    pos = text.lower().find(term.lower())
                    if best_position == -1 or pos < best_position:
                        best_position = pos
                        best_match = term
            
            if best_match and best_position >= 0:
                # Generate snippet around the match
                start = max(0, best_position - 150)
                end = min(len(text), best_position + len(best_match) + 150)
                
                snippet = text[start:end]
                if start > 0:
                    snippet = '...' + snippet
                if end < len(text):
                    snippet = snippet + '...'
                
                # Highlight search terms
                for term in search_terms:
                    import re
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    snippet = pattern.sub(f'<mark>{term}</mark>', snippet)
                
                return snippet
        
        # Fallback to comprehensive summary
        if obj.summary:
            snippet = obj.summary[:300] + '...' if len(obj.summary) > 300 else obj.summary
            # Highlight search terms in summary too
            if search_terms:
                for term in search_terms:
                    import re
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    snippet = pattern.sub(f'<mark>{term}</mark>', snippet)
            return snippet
        
        return obj.title
    
    def get_detailed_info(self, obj):
        """Get detailed information from payload_json for better display."""
        detailed_info = {}
        
        if obj.payload_json:
            # Extract key information based on entity type
            if obj.entity_type == 'vendor':
                detailed_info.update({
                    'status': obj.payload_json.get('status'),
                    'category': obj.payload_json.get('category'),
                    'risk_level': obj.payload_json.get('risk_level'),
                    'contact_email': obj.payload_json.get('contact_email'),
                    'contact_name': obj.payload_json.get('contact_name'),
                    'contact_phone': obj.payload_json.get('contact_phone'),
                    'website': obj.payload_json.get('website'),
                    'address': obj.payload_json.get('address'),
                    'annual_revenue': obj.payload_json.get('annual_revenue'),
                    'employee_count': obj.payload_json.get('employee_count'),
                    'risk_score': obj.payload_json.get('risk_score'),
                })
            elif obj.entity_type == 'rfp':
                detailed_info.update({
                    'status': obj.payload_json.get('status'),
                    'category': obj.payload_json.get('category'),
                    'deadline': obj.payload_json.get('deadline'),
                    'budget': obj.payload_json.get('budget'),
                    'contact_name': obj.payload_json.get('contact_name'),
                    'contact_email': obj.payload_json.get('contact_email'),
                    'published_date': obj.payload_json.get('published_date'),
                    'evaluation_start_date': obj.payload_json.get('evaluation_start_date'),
                    'award_date': obj.payload_json.get('award_date'),
                })
            elif obj.entity_type == 'contract':
                detailed_info.update({
                    'status': obj.payload_json.get('status'),
                    'contract_type': obj.payload_json.get('contract_type'),
                    'vendor_name': obj.payload_json.get('vendor_name'),
                    'start_date': obj.payload_json.get('start_date'),
                    'end_date': obj.payload_json.get('end_date'),
                    'value': obj.payload_json.get('value'),
                    'currency': obj.payload_json.get('currency'),
                    'payment_terms': obj.payload_json.get('payment_terms'),
                    'risk_level': obj.payload_json.get('risk_level'),
                })
            elif obj.entity_type == 'sla':
                detailed_info.update({
                    'status': obj.payload_json.get('status'),
                    'service_type': obj.payload_json.get('service_type'),
                    'vendor_name': obj.payload_json.get('vendor_name'),
                    'uptime_target': obj.payload_json.get('uptime_target'),
                    'response_time': obj.payload_json.get('response_time'),
                    'resolution_time': obj.payload_json.get('resolution_time'),
                    'start_date': obj.payload_json.get('start_date'),
                    'end_date': obj.payload_json.get('end_date'),
                })
            elif obj.entity_type == 'bcp_drp':
                detailed_info.update({
                    'status': obj.payload_json.get('status'),
                    'plan_type': obj.payload_json.get('plan_type'),
                    'vendor_name': obj.payload_json.get('vendor_name'),
                    'effective_date': obj.payload_json.get('effective_date'),
                    'review_date': obj.payload_json.get('review_date'),
                    'last_review_date': obj.payload_json.get('last_review_date'),
                    'rto': obj.payload_json.get('rto'),
                    'rpo': obj.payload_json.get('rpo'),
                    'mto': obj.payload_json.get('mto'),
                })
        
        return detailed_info
    
    def get_additional_fields(self, obj):
        """Get additional fields that might be useful for display."""
        additional_fields = {}
        
        if obj.payload_json:
            # Include any other fields from payload_json that aren't in detailed_info
            detailed_keys = set(self.get_detailed_info(obj).keys())
            for key, value in obj.payload_json.items():
                if key not in detailed_keys and value is not None:
                    additional_fields[key] = value
        
        return additional_fields


class SearchFacetsSerializer(serializers.Serializer):
    """Serializer for search facets/aggregations."""
    
    modules = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Count of results by module type"
    )
    status = serializers.DictField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Count of results by status"
    )


class SearchResponseSerializer(serializers.Serializer):
    """Serializer for complete search response."""
    
    total = serializers.IntegerField(help_text="Total number of results")
    page = serializers.IntegerField(help_text="Current page number")
    page_size = serializers.IntegerField(help_text="Number of results per page")
    grouped_results = serializers.DictField(
        child=SearchResultSerializer(many=True),
        help_text="Search results grouped by entity type"
    )
    entity_type_counts = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Count of results by entity type"
    )
    facets = SearchFacetsSerializer(help_text="Search facets/aggregations")
    query_time = serializers.FloatField(help_text="Query execution time in milliseconds")
    query = serializers.CharField(help_text="Original search query")


class SearchAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for search analytics."""
    
    class Meta:
        model = SearchAnalytics
        fields = [
            'id',
            'query',
            'user_id',
            'results_count',
            'response_time',
            'filters_used',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class IndexUpdateSerializer(serializers.Serializer):
    """Serializer for updating search index entries."""
    
    entity_type = serializers.ChoiceField(
        choices=SearchIndex.ENTITY_TYPE_CHOICES,
        help_text="Type of entity"
    )
    entity_id = serializers.IntegerField(
        help_text="Entity ID"
    )
    title = serializers.CharField(
        max_length=255,
        help_text="Title of the entity"
    )
    summary = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Summary of the entity"
    )
    keywords = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Keywords for search"
    )
    payload_json = serializers.DictField(
        required=False,
        default=dict,
        help_text="Additional payload data"
    )


class BulkIndexUpdateSerializer(serializers.Serializer):
    """Serializer for bulk index updates."""
    
    updates = IndexUpdateSerializer(many=True, help_text="List of index updates")

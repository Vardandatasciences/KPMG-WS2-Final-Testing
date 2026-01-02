import time
from django.db import models
from django.db.models import Count, Avg, Max, Min, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import IntegrityError, DataError
from django.core.exceptions import ValidationError

from .models import SearchIndex, SearchAnalytics
from .serializers import (
    SearchQuerySerializer,
    SearchResponseSerializer,
    SearchResultSerializer,
    SearchAnalyticsSerializer,
    IndexUpdateSerializer,
    BulkIndexUpdateSerializer
)


class SearchPagination(PageNumberPagination):
    """Custom pagination for search results."""
    page_size = 1000  # Increased default page size
    page_size_query_param = 'page_size'
    max_page_size = 10000  # Increased maximum page size


class GlobalSearchViewSet(viewsets.ViewSet):
    """
    Global Search API ViewSet for searching across all TPRM modules.
    """
    permission_classes = [AllowAny]
    pagination_class = SearchPagination
    
    @action(detail=False, methods=['post'], url_path='query')
    def search_query(self, request):
        """
        Perform a comprehensive global search across ALL database tables and ALL columns.
        This search works directly with the actual database tables, not the search index.
        
        POST /api/global-search/query/
        """
        start_time = time.time()
        
        # Validate request data
        serializer = SearchQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = data.get('q', '').strip()
        page = data.get('page', 1)
        page_size = data.get('page_size', 1000)  # Increased default page size
        is_finalized = data.get('is_finalized', False)
        status_filters = data.get('status', [])
        category_filters = data.get('category', [])
        risk_level_filters = data.get('risk_level', [])
        
        # Build filters object
        filters = {}
        if status_filters:
            filters['status'] = status_filters
        if category_filters:
            filters['category'] = category_filters
        if risk_level_filters:
            filters['risk_level'] = risk_level_filters
        
        try:
            # Use direct database search across all tables
            all_results = self._search_all_database_tables(
                query=query,
                modules=[],  # Search all modules
                filters=filters
            )
            
            # Get total count
            total_count = len(all_results)
            
            # Apply pagination (allow -1 to disable pagination)
            if page_size == -1:
                # No pagination - return all results
                paginated_results = all_results
                page_size = total_count
                page = 1
            else:
                start_index = (page - 1) * page_size
                end_index = start_index + page_size
                paginated_results = all_results[start_index:end_index]
            
            # Calculate query time
            query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Track analytics ONLY for finalized searches (when Enter is pressed)
            if is_finalized:
                self._track_search_analytics(
                    query=query,
                    results_count=total_count,
                    response_time=query_time,
                    filters_used=filters
                )
            
            # Group results by module for better organization
            grouped_data = self._group_results_by_module(all_results)
            
            # Prepare response with comprehensive results
            response_data = {
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'results': paginated_results,  # Direct results from database tables
                'grouped_results': grouped_data['grouped_results'],  # Results grouped by module
                'module_counts': grouped_data['module_counts'],  # Count per module
                'total_modules': grouped_data['total_modules'],  # Number of modules with results
                'query_time': query_time,
                'query': query,  # Include the original query in response
                'search_scope': 'all_database_tables'  # Indicate this was a direct database search
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print(f"Direct database search error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Direct database search failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _search_all_database_tables(self, query, modules=None, filters=None):
        """
        Perform a comprehensive search across ALL database tables and ALL columns.
        This method searches the actual data tables directly, not the search index.
        
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
                
                # Apply filters if provided
                if filters:
                    filter_query = Q()
                    
                    # Apply status filter
                    if 'status' in filters and filters['status']:
                        status_filter = Q()
                        for status_value in filters['status']:
                            status_filter |= Q(status=status_value)
                        filter_query &= status_filter
                    
                    # Apply category filter
                    if 'category' in filters and filters['category']:
                        category_filter = Q()
                        for category_value in filters['category']:
                            category_filter |= Q(category=category_value)
                        filter_query &= category_filter
                    
                    # Apply risk_level filter
                    if 'risk_level' in filters and filters['risk_level']:
                        risk_level_filter = Q()
                        for risk_level_value in filters['risk_level']:
                            risk_level_filter |= Q(risk_level=risk_level_value)
                        filter_query &= risk_level_filter
                    
                    # Apply filters to results
                    if filter_query:
                        table_results = table_results.filter(filter_query)
                
                # Convert results to search result format
                for result in table_results:
                    search_entry = self._create_search_result_from_model(
                        result, config['entity_type'], config['search_fields'], search_terms
                    )
                    if search_entry:
                        all_results.append(search_entry)
                        
            except Exception as e:
                print(f"Error searching table {table_name}: {e}")
                continue
        
        # Sort results by updated_at (most recent first)
        # Handle None values by providing a default datetime string
        from datetime import datetime
        default_date = datetime.min.isoformat()
        all_results.sort(key=lambda x: x.get('updated_at') or default_date, reverse=True)
        
        return all_results
    
    def _group_results_by_module(self, results):
        """
        Group search results by module/entity type for better organization.
        
        Args:
            results (list): List of search results
            
        Returns:
            dict: Grouped results with module counts and metadata
        """
        grouped_results = {}
        module_counts = {}
        
        # Define module display names and priorities
        module_info = {
            'vendor': {'display_name': 'Vendors', 'priority': 1, 'icon': 'building'},
            'rfp': {'display_name': 'RFPs', 'priority': 2, 'icon': 'file-text'},
            'contract': {'display_name': 'Contracts', 'priority': 3, 'icon': 'file-signature'},
            'sla': {'display_name': 'SLAs', 'priority': 4, 'icon': 'shield'},
            'bcp_drp': {'display_name': 'BCP/DRP', 'priority': 5, 'icon': 'shield-alt'},
        }
        
        # Group results by module
        for result in results:
            module = result.get('module', 'unknown')
            if module not in grouped_results:
                grouped_results[module] = []
                module_counts[module] = 0
            
            grouped_results[module].append(result)
            module_counts[module] += 1
        
        # Add module metadata
        for module in grouped_results:
            if module in module_info:
                grouped_results[module] = {
                    'results': grouped_results[module],
                    'count': module_counts[module],
                    'display_name': module_info[module]['display_name'],
                    'priority': module_info[module]['priority'],
                    'icon': module_info[module]['icon'],
                }
            else:
                grouped_results[module] = {
                    'results': grouped_results[module],
                    'count': module_counts[module],
                    'display_name': module.title(),
                    'priority': 999,
                    'icon': 'folder',
                }
        
        return {
            'grouped_results': grouped_results,
            'module_counts': module_counts,
            'total_modules': len(grouped_results),
        }

    def _get_datetime_string(self, datetime_obj):
        """
        Convert a datetime object to a string, handling None values.
        
        Args:
            datetime_obj: DateTime object or None
            
        Returns:
            str: ISO formatted datetime string or default minimum date
        """
        if datetime_obj is None:
            from datetime import datetime
            return datetime.min.isoformat()
        
        if hasattr(datetime_obj, 'isoformat'):
            return datetime_obj.isoformat()
        
        return str(datetime_obj)

    def _create_search_result_from_model(self, model_instance, entity_type, search_fields, search_terms=None):
        """
        Create a search result from a model instance.
        
        Args:
            model_instance: The model instance
            entity_type (str): Type of entity
            search_fields (list): List of searchable fields
        
        Returns:
            dict: Search result data
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
            
            # Generate snippet with highlighting
            snippet = self._generate_snippet(model_instance, search_fields, title, summary, keywords, search_terms)
            
            # Generate detailed info based on entity type
            detailed_info = self._generate_detailed_info(model_instance, entity_type, payload_json)
            
            # Generate additional fields
            additional_fields = self._generate_additional_fields(model_instance, detailed_info, payload_json)
            
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
                'global_uid': f"{entity_type}:{entity_id}",
                'module': entity_type,
                'entity_id': entity_id,
                'title': title or f"{entity_type.title()} {entity_id}",
                'snippet': snippet,
                'summary': summary or '',
                'keywords': ' '.join(keywords),
                'detailed_info': detailed_info,
                'additional_fields': additional_fields,
                'updated_at': self._get_datetime_string(getattr(model_instance, 'updated_at', None) or getattr(model_instance, 'created_at', None)),
                'payload_json': payload_json
            }
            
        except Exception as e:
            print(f"Error creating search result for {entity_type} {model_instance.id}: {e}")
            return None

    def _generate_snippet(self, model_instance, search_fields, title, summary, keywords, search_terms=None):
        """Generate a snippet with highlighting from model data."""
        # Combine all searchable text
        text_parts = []
        if title: text_parts.append(title)
        if summary: text_parts.append(summary)
        if keywords: text_parts.append(' '.join(keywords))
        
        # Add all field values
        for field in search_fields:
            if hasattr(model_instance, field):
                value = getattr(model_instance, field)
                if value and str(value).strip():
                    text_parts.append(str(value))
        
        text = ' '.join(text_parts)
        
        # Generate snippet with highlighting
        if search_terms and text:
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
                
                # Highlight all search terms
                for term in search_terms:
                    import re
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    snippet = pattern.sub(f'<mark>{term}</mark>', snippet)
                
                return snippet
        
        # Fallback to simple snippet generation
        if len(text) > 300:
            snippet = text[:300] + "..."
            # Highlight search terms in fallback snippet too
            if search_terms:
                for term in search_terms:
                    import re
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    snippet = pattern.sub(f'<mark>{term}</mark>', snippet)
            return snippet
        return text

    def _generate_detailed_info(self, model_instance, entity_type, payload_json):
        """Generate detailed information based on entity type."""
        detailed_info = {}
        
        if entity_type == 'vendor':
            detailed_info.update({
                'status': payload_json.get('status'),
                'risk_level': payload_json.get('risk_level'),
                'website': payload_json.get('website'),
                'business_type': payload_json.get('business_type'),
                'industry_sector': payload_json.get('industry_sector'),
                'headquarters_country': payload_json.get('headquarters_country'),
                'headquarters_address': payload_json.get('headquarters_address'),
                'annual_revenue': payload_json.get('annual_revenue'),
                'employee_count': payload_json.get('employee_count'),
                'tax_id': payload_json.get('tax_id'),
                'duns_number': payload_json.get('duns_number'),
                'vendor_code': payload_json.get('vendor_code'),
            })
        elif entity_type == 'rfp':
            detailed_info.update({
                'status': payload_json.get('status'),
                'category': payload_json.get('category'),
                'rfp_number': payload_json.get('rfp_number'),
                'rfp_type': payload_json.get('rfp_type'),
                'estimated_value': payload_json.get('estimated_value'),
                'currency': payload_json.get('currency'),
                'geographical_scope': payload_json.get('geographical_scope'),
                'criticality_level': payload_json.get('criticality_level'),
                'evaluation_method': payload_json.get('evaluation_method'),
            })
        elif entity_type == 'contract':
            detailed_info.update({
                'status': payload_json.get('status'),
                'contract_type': payload_json.get('contract_type'),
                'contract_kind': payload_json.get('contract_kind'),
                'contract_number': payload_json.get('contract_number'),
                'contract_value': payload_json.get('contract_value'),
                'currency': payload_json.get('currency'),
                'governing_law': payload_json.get('governing_law'),
                'contract_category': payload_json.get('contract_category'),
                'termination_clause_type': payload_json.get('termination_clause_type'),
                'dispute_resolution_method': payload_json.get('dispute_resolution_method'),
                'workflow_stage': payload_json.get('workflow_stage'),
            })
        elif entity_type == 'sla':
            detailed_info.update({
                'status': payload_json.get('status'),
                'sla_type': payload_json.get('sla_type'),
                'business_service_impacted': payload_json.get('business_service_impacted'),
                'reporting_frequency': payload_json.get('reporting_frequency'),
                'baseline_period': payload_json.get('baseline_period'),
                'measurement_methodology': payload_json.get('measurement_methodology'),
                'compliance_framework': payload_json.get('compliance_framework'),
                'priority': payload_json.get('priority'),
                'approval_status': payload_json.get('approval_status'),
            })
        elif entity_type == 'bcp_drp':
            detailed_info.update({
                'status': payload_json.get('status'),
                'plan_type': payload_json.get('plan_type'),
                'strategy_name': payload_json.get('strategy_name'),
                'criticality': payload_json.get('criticality'),
                'version': payload_json.get('version'),
                'file_uri': payload_json.get('file_uri'),
                'mime_type': payload_json.get('mime_type'),
                'overall_score': payload_json.get('overall_score'),
                'quality_score': payload_json.get('quality_score'),
                'coverage_score': payload_json.get('coverage_score'),
            })
        
        return detailed_info

    def _generate_additional_fields(self, model_instance, detailed_info, payload_json):
        """Generate additional fields that might be useful for display."""
        additional_fields = {}
        detailed_keys = set(detailed_info.keys())
        
        for key, value in payload_json.items():
            if key not in detailed_keys and value is not None:
                additional_fields[key] = value
        
        return additional_fields
    
    @action(detail=False, methods=['post'], url_path='index/update')
    def update_index(self, request):
        """
        Update a single search index entry.
        
        POST /api/global-search/index/update/
        """
        serializer = IndexUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            search_index = SearchIndex.create_or_update(
                entity_type=data['entity_type'],
                entity_id=data['entity_id'],
                title=data['title'],
                summary=data.get('summary', ''),
                keywords=data.get('keywords', ''),
                payload_json=data.get('payload_json', {})
            )
            
            return Response({
                'message': 'Index updated successfully',
                'global_uid': search_index.global_uid
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to update index: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='index/bulk-update')
    def bulk_update_index(self, request):
        """
        Update multiple search index entries in bulk.
        
        POST /api/global-search/index/bulk-update/
        """
        serializer = BulkIndexUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updates = serializer.validated_data['updates']
            updated_count = 0
            
            for update_data in updates:
                SearchIndex.create_or_update(
                    entity_type=update_data['entity_type'],
                    entity_id=update_data['entity_id'],
                    title=update_data['title'],
                    summary=update_data.get('summary', ''),
                    keywords=update_data.get('keywords', ''),
                    payload_json=update_data.get('payload_json', {})
                )
                updated_count += 1
            
            return Response({
                'message': f'Successfully updated {updated_count} index entries'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to bulk update index: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['delete'], url_path='index/delete')
    def delete_index_entry(self, request):
        """
        Delete a search index entry.
        
        DELETE /api/global-search/index/delete/
        """
        entity_type = request.data.get('entity_type')
        entity_id = request.data.get('entity_id')
        
        if not entity_type or not entity_id:
            return Response(
                {'error': 'entity_type and entity_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            deleted_count, _ = SearchIndex.objects.filter(
                entity_type=entity_type,
                entity_id=entity_id
            ).delete()
            
            if deleted_count > 0:
                return Response({
                    'message': 'Index entry deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Index entry not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response(
                {'error': f'Failed to delete index entry: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    @action(detail=False, methods=['get'])
    def search_stats(self, request):
        """Get search statistics."""
        try:
            # Get basic stats
            total_searches = SearchAnalytics.objects.count()
            total_results = SearchAnalytics.objects.aggregate(
                total_results=Sum('results_count')
            )['total_results'] or 0
            
            # Get average response time
            avg_response_time = SearchAnalytics.objects.aggregate(
                avg_time=Avg('response_time')
            )['avg_time'] or 0
            
            # Get searches in last 24 hours
            yesterday = timezone.now() - timedelta(days=1)
            searches_24h = SearchAnalytics.objects.filter(
                created_at__gte=yesterday
            ).count()
            
            return Response({
                'total_searches': total_searches,
                'total_results': total_results,
                'avg_response_time': round(avg_response_time, 2),
                'searches_24h': searches_24h
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to get search stats: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    @action(detail=False, methods=['get'], url_path='dashboard-analytics')
    def dashboard_analytics(self, request):
        """
        Get comprehensive dashboard analytics for real-time monitoring.
        
        GET /api/global-search/dashboard-analytics/
        """
        try:
            # Get time ranges for analytics
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            last_30d = now - timedelta(days=30)
            
            # Search Index Analytics
            total_indexed_records = SearchIndex.objects.count()
            
            # Records by entity type
            records_by_type = SearchIndex.objects.values('entity_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Recent index updates (last 24 hours)
            recent_updates = SearchIndex.objects.filter(
                updated_at__gte=last_24h
            ).count()
            
            # Search Analytics
            total_searches = SearchAnalytics.objects.count()
            searches_24h = SearchAnalytics.objects.filter(
                created_at__gte=last_24h
            ).count()
            searches_7d = SearchAnalytics.objects.filter(
                created_at__gte=last_7d
            ).count()
            
            # Performance metrics
            avg_response_time = SearchAnalytics.objects.aggregate(
                avg_time=Avg('response_time')
            )['avg_time'] or 0
            
            avg_response_time_24h = SearchAnalytics.objects.filter(
                created_at__gte=last_24h
            ).aggregate(avg_time=Avg('response_time'))['avg_time'] or 0
            
            # Zero result searches
            zero_result_searches = SearchAnalytics.objects.filter(
                results_count=0
            ).count()
            
            zero_result_searches_24h = SearchAnalytics.objects.filter(
                results_count=0,
                created_at__gte=last_24h
            ).count()
            
            # Popular search terms (last 7 days)
            popular_searches = SearchAnalytics.objects.filter(
                created_at__gte=last_7d
            ).values('query').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Search trends by hour (last 24 hours)
            hourly_trends = []
            for i in range(24):
                hour_start = now - timedelta(hours=i+1)
                hour_end = now - timedelta(hours=i)
                count = SearchAnalytics.objects.filter(
                    created_at__gte=hour_start,
                    created_at__lt=hour_end
                ).count()
                hourly_trends.append({
                    'hour': hour_start.hour,
                    'count': count
                })
            hourly_trends.reverse()
            
            # Module activity (records by type with recent activity)
            module_activity = []
            for record_type in records_by_type:
                entity_type = record_type['entity_type']
                total_count = record_type['count']
                recent_count = SearchIndex.objects.filter(
                    entity_type=entity_type,
                    updated_at__gte=last_7d
                ).count()
                
                module_activity.append({
                    'module': entity_type,
                    'total_records': total_count,
                    'recent_updates': recent_count,
                    'percentage': round((recent_count / total_count * 100) if total_count > 0 else 0, 1)
                })
            
            # System health metrics
            system_health = {
                'index_health': 'healthy' if total_indexed_records > 0 else 'warning',
                'search_performance': 'good' if avg_response_time < 1000 else 'slow',
                'zero_result_rate': round((zero_result_searches / total_searches * 100) if total_searches > 0 else 0, 1),
                'recent_activity': 'active' if searches_24h > 0 else 'inactive'
            }
            
            analytics = {
                'timestamp': now.isoformat(),
                'search_index': {
                    'total_records': total_indexed_records,
                    'records_by_type': {item['entity_type']: item['count'] for item in records_by_type},
                    'recent_updates_24h': recent_updates,
                    'module_activity': module_activity
                },
                'search_analytics': {
                    'total_searches': total_searches,
                    'searches_24h': searches_24h,
                    'searches_7d': searches_7d,
                    'avg_response_time': round(avg_response_time, 2),
                    'avg_response_time_24h': round(avg_response_time_24h, 2),
                    'zero_result_searches': zero_result_searches,
                    'zero_result_searches_24h': zero_result_searches_24h,
                    'popular_searches': list(popular_searches),
                    'hourly_trends': hourly_trends
                },
                'system_health': system_health
            }
            
            return Response(analytics, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get dashboard analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='live-updates')
    def live_updates(self, request):
        """
        Get live updates for real-time dashboard monitoring.
        
        GET /api/global-search/live-updates/
        """
        try:
            now = timezone.now()
            last_5min = now - timedelta(minutes=5)
            
            # Recent search activity
            recent_searches = SearchAnalytics.objects.filter(
                created_at__gte=last_5min
            ).count()
            
            # Recent index updates
            recent_index_updates = SearchIndex.objects.filter(
                updated_at__gte=last_5min
            ).count()
            
            # Latest search queries
            latest_queries = SearchAnalytics.objects.filter(
                created_at__gte=last_5min
            ).values('query', 'results_count', 'response_time', 'created_at')[:5]
            
            # Latest index changes
            latest_index_changes = SearchIndex.objects.filter(
                updated_at__gte=last_5min
            ).values('entity_type', 'title', 'updated_at')[:5]
            
            live_data = {
                'timestamp': now.isoformat(),
                'recent_searches': recent_searches,
                'recent_index_updates': recent_index_updates,
                'latest_queries': list(latest_queries),
                'latest_index_changes': list(latest_index_changes),
                'is_active': recent_searches > 0 or recent_index_updates > 0
            }
            
            return Response(live_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get live updates: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='filter-options')
    def get_filter_options(self, request):
        """
        Get available filter options for status, category, and risk level.
        
        GET /api/global-search/filter-options/
        """
        try:
            from django.apps import apps
            import logging
            logger = logging.getLogger(__name__)
            
            # Get all models that have these fields
            models_with_filters = {}
            try:
                models_with_filters = {
                    'vendor': apps.get_model('vendor_core', 'Vendors'),
                    'rfp': apps.get_model('rfp', 'RFP'),
                    'contract': apps.get_model('contracts', 'VendorContract'),
                    'sla': apps.get_model('slas', 'VendorSLA'),
                    'bcp_drp_plans': apps.get_model('bcpdrp', 'Plan'),
                    'bcp_drp_evaluations': apps.get_model('bcpdrp', 'Evaluation'),
                }
            except Exception as e:
                logger.warning(f"Error loading models for filter options: {e}")
                models_with_filters = {}
            
            filter_options = {
                'status': set(),
                'category': set(),
                'risk_level': set()
            }
            
            # Collect all unique values from each model
            for model_name, model in models_with_filters.items():
                if model is None:
                    continue
                try:
                    # Get status values
                    if hasattr(model, 'status'):
                        status_values = model.objects.values_list('status', flat=True).distinct()
                        filter_options['status'].update([v for v in status_values if v])
                    
                    # Get category values
                    if hasattr(model, 'category'):
                        category_values = model.objects.values_list('category', flat=True).distinct()
                        filter_options['category'].update([v for v in category_values if v])
                    
                    # Get risk_level values
                    if hasattr(model, 'risk_level'):
                        risk_level_values = model.objects.values_list('risk_level', flat=True).distinct()
                        filter_options['risk_level'].update([v for v in risk_level_values if v])
                        
                except Exception as e:
                    logger.warning(f"Error getting filter options from {model_name}: {e}")
                    continue
            
            # Convert sets to sorted lists
            response_data = {
                'status': sorted(list(filter_options['status'])),
                'category': sorted(list(filter_options['category'])),
                'risk_level': sorted(list(filter_options['risk_level']))
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get filter options: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to get filter options: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def search_history(self, request):
        """Get search history from search_analytics table."""
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 1000))  # Increased default page size
            
            # Get unique queries from search_analytics, ordered by most recent
            from django.db.models import Max
            
            # Get the most recent entry for each unique query
            recent_queries = SearchAnalytics.objects.values('query').annotate(
                latest_created=Max('created_at')
            ).order_by('-latest_created')
            
            # Calculate pagination
            total_count = recent_queries.count()
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            # Get paginated results
            paginated_queries = recent_queries[start_index:end_index]
            
            # Get full details for each query
            results = []
            for query_data in paginated_queries:
                query = query_data['query']
                latest_entry = SearchAnalytics.objects.filter(
                    query=query
                ).order_by('-created_at').first()
                
                if latest_entry:
                    results.append({
                        'query': query,
                        'results_count': latest_entry.results_count,
                        'created_at': latest_entry.created_at.isoformat()
                    })
            
            has_more = end_index < total_count
            
            return Response({
                'results': results,
                'total': total_count,
                'has_more': has_more,
                'page': page,
                'page_size': page_size
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to load search history: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'])
    def clear_search_history(self, request):
        """Clear all search history from search_analytics table."""
        try:
            # Delete all records from search_analytics
            deleted_count = SearchAnalytics.objects.all().delete()[0]
            
            return Response({
                'message': f'Successfully cleared {deleted_count} search history records',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to clear search history: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _track_search_analytics(self, query, results_count, response_time, filters_used):
        """Track search analytics for performance monitoring."""
        try:
            # Validate inputs before creating
            if query is None:
                query = ""
            
            if results_count is None:
                results_count = 0
            elif results_count < 0:
                results_count = 0  # Ensure non-negative
                
            if response_time is None:
                response_time = 0.0
            elif response_time < 0:
                response_time = 0.0  # Ensure non-negative
                
            if filters_used is None:
                filters_used = {}
            
            # Truncate query if it's too long (some databases have limits)
            if len(query) > 10000:  # Reasonable limit
                query = query[:10000] + "..."
            
            # Create the analytics entry
            analytics = SearchAnalytics.objects.create(
                query=query,
                results_count=results_count,
                response_time=response_time,
                filters_used=filters_used
            )
            
            print(f"✅ Search analytics tracked: '{query[:50]}...' ({results_count} results, {response_time}ms)")
            
        except IntegrityError as e:
            print(f"❌ IntegrityError tracking search analytics: {e}")
            print(f"   Query: '{query[:100]}...'")
            print(f"   Results: {results_count}, Time: {response_time}")
        except DataError as e:
            print(f"❌ DataError tracking search analytics: {e}")
            print(f"   Query: '{query[:100]}...'")
            print(f"   Results: {results_count}, Time: {response_time}")
        except ValidationError as e:
            print(f"❌ ValidationError tracking search analytics: {e}")
            print(f"   Query: '{query[:100]}...'")
            print(f"   Results: {results_count}, Time: {response_time}")
        except Exception as e:
            print(f"❌ Unexpected error tracking search analytics: {type(e).__name__}: {e}")
            print(f"   Query: '{query[:100]}...'")
            print(f"   Results: {results_count}, Time: {response_time}")
            import traceback
            traceback.print_exc()


class SearchAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for accessing search analytics data.
    """
    queryset = SearchAnalytics.objects.all()
    serializer_class = SearchAnalyticsSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['created_at']
    search_fields = ['query']
    ordering_fields = ['created_at', 'response_time', 'results_count']
    ordering = ['-created_at']

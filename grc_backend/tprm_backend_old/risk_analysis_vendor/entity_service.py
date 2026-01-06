import logging
from django.db import connections
from django.conf import settings
from typing import Dict, List
# Removed TPRMModule dependency - using direct entity-data-row approach
from .llama_service import LlamaService
# Import models for direct database access as needed

logger = logging.getLogger(__name__)


class EntityDataService:
    """
    Service for managing entity-data-row selections for risk analysis
    
    INTEGRATION GUIDE FOR OTHER MODULES:
    ====================================
    
    To integrate your module (Vendor, SLA, Contract, RFP), follow these steps:
    
    1. ADD YOUR TABLES: Update entity_table_mappings below with your module's tables
    2. ADD DISPLAY NAMES: Update entity_display_names with your module's display name  
    3. ADD LLaMA MAPPING: Update entity_llama_mapping for AI prompt generation
    4. IMPLEMENT DATA METHODS: Add _get_your_table() methods for each of your tables
    5. UPDATE get_rows_for_table(): Add elif conditions for your tables
    
    EXAMPLE FOR VENDOR MODULE:
    --------------------------
    # Step 1: Add tables to mappings
    'vendor_management': ['vendor_profiles', 'vendor_assessments', 'vendor_contracts'],
    
    # Step 2: Add display name
    'vendor_management': 'Vendor Management',
    
    # Step 3: Add LLaMA mapping
    'vendor_management': 'Vendor',
    
    # Step 4: Implement data methods (see examples below)
    def _get_vendor_profiles(self):
        from vendor_module.models import VendorProfile
        # ... implementation similar to _get_bcp_drp_plans()
    
    # Step 5: Update get_rows_for_table()
    elif table_name == 'vendor_profiles':
        return self._get_vendor_profiles()
    
    See INTEGRATION_GUIDE.md for complete examples!
    """
    
    def __init__(self):
        self.llama_service = LlamaService()
        # Define entity to table mappings - standardized for microservice
        # ===================================================================
        # OTHER MODULE TEAMS: ADD YOUR TABLES HERE!
        # ===================================================================
        self.entity_table_mappings = {
            'vendor_management': ['temp_vendor'],  # Added temp_vendor table for vendor risk generation
            'rfp_module': [],         # TODO: Add RFP tables like ['rfp_requests', 'rfp_responses'] 
            'contract_module': [],    # TODO: Add contract tables like ['contracts', 'contract_amendments']
            'sla_module': [],         # TODO: Add SLA tables like ['sla_agreements', 'sla_performance']
        }
        
        # Entity display names mapping
        # ===================================================================
        # OTHER MODULE TEAMS: UPDATE DISPLAY NAMES FOR YOUR MODULES!
        # ===================================================================
        self.entity_display_names = {
            'vendor_management': 'Vendor Management',  # TODO: Customize display name
            'rfp_module': 'RFP Module',               # TODO: Customize display name
            'contract_module': 'Contract Module',     # TODO: Customize display name
            'sla_module': 'SLA Module',               # TODO: Customize display name
        }
        
        # Entity to LLaMA service mapping for proper prompt generation
        # ===================================================================
        # OTHER MODULE TEAMS: ADD YOUR MODULE MAPPING FOR AI PROMPTS!
        # ===================================================================
        self.entity_llama_mapping = {
            'vendor_management': 'Vendor',    # TODO: Add your module's AI prompt name
            'rfp_module': 'RFP',             # TODO: Add your module's AI prompt name
            'contract_module': 'Contract',   # TODO: Add your module's AI prompt name
            'sla_module': 'SLA',             # TODO: Add your module's AI prompt name
        }
    
    def get_available_entities(self) -> List[Dict]:
        """Get list of available entities (modules) with their display names"""
        try:
            entities = []
            for entity_code in self.entity_table_mappings.keys():
                display_name = self.entity_display_names.get(entity_code, entity_code)
                table_count = len(self.entity_table_mappings[entity_code])
                
                entities.append({
                    'code': entity_code,
                    'display_name': display_name,
                    'table_count': table_count,
                    'has_tables': table_count > 0
                })
            
            logger.info(f"Found {len(entities)} available entities")
            return entities
            
        except Exception as e:
            logger.error(f"Error getting available entities: {e}")
            raise
    
    def get_tables_for_entity(self, entity: str) -> List[Dict]:
        """Get list of database tables for a specific entity"""
        try:
            if entity not in self.entity_table_mappings:
                raise ValueError(f"Entity '{entity}' not found")
            
            tables = []
            table_names = self.entity_table_mappings[entity]
            
            # If no tables are defined for this entity, return empty list
            if not table_names:
                logger.info(f"No tables defined for entity {entity}")
                return tables
            
            for table_name in table_names:
                # Get row count for each table
                row_count = self._get_table_row_count(table_name)
                tables.append({
                    'table_name': table_name,
                    'display_name': self._format_table_display_name(table_name),
                    'row_count': row_count
                })
            
            logger.info(f"Found {len(tables)} tables for entity {entity}")
            return tables
            
        except Exception as e:
            logger.error(f"Error getting tables for entity {entity}: {e}")
            raise
    
    def get_rows_for_table(self, table_name: str, limit: int = 100) -> List[Dict]:
        """
        Get list of rows from a specific table for selection using appropriate APIs
        
        INTEGRATION GUIDE FOR OTHER MODULES:
        ====================================
        
        TO ADD YOUR MODULE'S TABLES:
        1. Add elif conditions for each of your tables
        2. Call your corresponding _get_your_table() method
        3. Follow the pattern shown with BCP/DRP examples
        
        EXAMPLE FOR VENDOR MODULE:
        --------------------------
        elif table_name == 'vendor_profiles':
            return self._get_vendor_profiles()
        elif table_name == 'vendor_assessments':
            return self._get_vendor_assessments()
        elif table_name == 'vendor_contracts':
            return self._get_vendor_contracts()
        
        See the implementation examples for your specific table types!
        """
        try:
            # ===================================================================
            # MODULE TEAMS: ADD YOUR TABLE CONDITIONS HERE!
            # ===================================================================
            if table_name == 'temp_vendor':
                return self._get_temp_vendor_data(limit)
            # elif table_name == 'vendor_profiles':
            #     return self._get_vendor_profiles()
            # elif table_name == 'vendor_assessments':
            #     return self._get_vendor_assessments()
            # elif table_name == 'contracts':
            #     return self._get_contracts()
            # elif table_name == 'sla_agreements':
            #     return self._get_sla_agreements()
            # elif table_name == 'rfp_requests':
            #     return self._get_rfp_requests()
            
            raise ValueError(f"Table '{table_name}' not supported")
                
        except Exception as e:
            logger.error(f"Error getting rows for table {table_name}: {e}")
            raise
    
    
    def get_full_row_data(self, table_name: str, row_id: str) -> Dict:
        """Get complete row data for risk analysis using API data"""
        try:
            # Get the rows data using the same method as the dropdown
            rows = self.get_rows_for_table(table_name)
            
            # Find the specific row by ID
            for row in rows:
                if str(row['id']) == str(row_id):
                    # For temp_vendor, the row data is directly in the row dict
                    if table_name == 'temp_vendor':
                        row_data = row
                    else:
                        row_data = row['data']
                    
                    # Convert any datetime objects and decimals to strings for JSON serialization
                    for key, value in row_data.items():
                        if hasattr(value, 'isoformat'):
                            row_data[key] = value.isoformat()
                        elif hasattr(value, '__str__') and str(type(value)).find('Decimal') != -1:
                            row_data[key] = float(value) if value is not None else None
                    
                    logger.info(f"Retrieved full row data for {table_name} ID {row_id}")
                    return row_data
            
            raise ValueError(f"Row with ID {row_id} not found in {table_name}")
                
        except Exception as e:
            logger.error(f"Error getting full row data for {table_name} ID {row_id}: {e}")
            raise
    
    def generate_risks_for_entity_data_row(self, entity: str, table_name: str, row_id: str):
        """Generate risks for specific entity-data-row selection"""
        try:
            # Validate entity exists in our mappings
            if entity not in self.entity_table_mappings:
                raise ValueError(f"Entity '{entity}' not supported. Available entities: {list(self.entity_table_mappings.keys())}")
            
            # Validate table exists for entity
            if table_name not in self.entity_table_mappings[entity]:
                raise ValueError(f"Table '{table_name}' not supported for entity '{entity}'. Available tables: {self.entity_table_mappings[entity]}")
            
            # Get full row data
            row_data = self.get_full_row_data(table_name, row_id)
            
            # Map entity to LLaMA service entity name
            llama_entity = self.entity_llama_mapping.get(entity, entity)
            
            # Generate risks using LLaMA
            module_data = {
                'entity': entity,
                'data': table_name,
                'row': str(row_id),
                'row_data': row_data
            }
            
            risks = self.llama_service.create_risks_from_entity_data_row(
                entity=llama_entity,
                table_name=table_name,
                row_data=row_data,
                module_data=module_data
            )
            
            logger.info(f"Generated {len(risks)} risks for {entity} {table_name} row {row_id}")
            return risks
            
        except Exception as e:
            logger.error(f"Error generating risks for {entity} {table_name} row {row_id}: {e}")
            raise
    
    def _get_table_row_count(self, table_name: str) -> int:
        """Get row count for a table using API data"""
        try:
            rows = self.get_rows_for_table(table_name)
            return len(rows)
        except Exception:
            return 0
    
    def _get_temp_vendor_data(self, limit: int = 100) -> List[Dict]:
        """Get temp vendor data for risk analysis"""
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT id, vendor_code, company_name, legal_name, business_type, 
                           industry_sector, website, annual_revenue, employee_count,
                           headquarters_address, description, risk_level, status,
                           is_critical_vendor, has_data_access, has_system_access,
                           created_at, updated_at
                    FROM temp_vendor 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, [limit])
                
                columns = [col[0] for col in cursor.description]
                rows = []
                
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    # Format for display
                    row_dict['display_name'] = f"{row_dict.get('company_name', 'Unknown')} ({row_dict.get('vendor_code', 'No Code')})"
                    rows.append(row_dict)
                
                return rows
                
        except Exception as e:
            logger.error(f"Error getting temp vendor data: {e}")
            return []

    def _format_table_display_name(self, table_name: str) -> str:
        """Format table name for display"""
        # Convert snake_case to Title Case
        return table_name.replace('_', ' ').title()
    
    def _is_valid_table(self, table_name: str) -> bool:
        """Check if table name is in our allowed list"""
        all_tables = []
        for tables in self.entity_table_mappings.values():
            all_tables.extend(tables)
        return table_name in all_tables

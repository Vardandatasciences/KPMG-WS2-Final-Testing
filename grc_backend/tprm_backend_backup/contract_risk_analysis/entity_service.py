import logging
from django.db import connection
from django.conf import settings
from typing import Dict, List
# Removed TPRMModule dependency - using direct entity-data-row approach
from .llama_service import LlamaService

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
        # ... implementation similar to _get_vendor_contracts()
    
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
            'vendor_management': [],  # TODO: Add vendor tables like ['vendor_profiles', 'vendor_assessments']
            'rfp_module': [],         # TODO: Add RFP tables like ['rfp_requests', 'rfp_responses'] 
            'contract_module': ['vendor_contracts', 'contract_terms', 'contract_clauses'],    # Contract management tables
            'sla_module': [],         # TODO: Add SLA tables like ['sla_agreements', 'sla_performance']
        }
        
        # Entity display names mapping
        # ===================================================================
        # OTHER MODULE TEAMS: UPDATE DISPLAY NAMES FOR YOUR MODULES!
        # ===================================================================
        self.entity_display_names = {
            'vendor_management': 'Vendor Management',  # TODO: Customize display name
            'rfp_module': 'RFP Module',               # TODO: Customize display name
            'contract_module': 'Contract Management', # Contract management display name
            'sla_module': 'SLA Module',               # TODO: Customize display name
        }
        
        # Entity to LLaMA service mapping for proper prompt generation
        # ===================================================================
        # OTHER MODULE TEAMS: ADD YOUR MODULE MAPPING FOR AI PROMPTS!
        # ===================================================================
        self.entity_llama_mapping = {
            'vendor_management': 'Vendor',    # TODO: Add your module's AI prompt name
            'rfp_module': 'RFP',             # TODO: Add your module's AI prompt name
            'contract_module': 'Contract',   # Contract management AI prompt name
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
        3. Follow the pattern shown with Contract examples
        
        EXAMPLE FOR VENDOR MODULE:
        --------------------------
        elif table_name == 'vendor_profiles':
            return self._get_vendor_profiles()
        elif table_name == 'vendor_assessments':
            return self._get_vendor_assessments()
        elif table_name == 'vendor_contracts':
            return self._get_vendor_contracts()
        
        See the _get_vendor_contracts() method below for implementation pattern!
        """
        try:
            # ===================================================================
            # CONTRACT MODULE INTEGRATION
            # ===================================================================
            if table_name == 'vendor_contracts':
                return self._get_vendor_contracts()
            elif table_name == 'contract_terms':
                return self._get_contract_terms()
            elif table_name == 'contract_clauses':
                return self._get_contract_clauses()
            
            # ===================================================================
            # OTHER MODULE TEAMS: ADD YOUR TABLE CONDITIONS HERE!
            # ===================================================================
            # elif table_name == 'vendor_profiles':
            #     return self._get_vendor_profiles()
            # elif table_name == 'vendor_assessments':
            #     return self._get_vendor_assessments()
            # elif table_name == 'sla_agreements':
            #     return self._get_sla_agreements()
            # elif table_name == 'rfp_requests':
            #     return self._get_rfp_requests()
            
            else:
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
            risks = self.llama_service.create_risks_from_entity_data_row(
                entity=llama_entity,
                table_name=table_name,
                row_data=row_data
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
    
    # ===================================================================
    # CONTRACT MODULE DATA METHODS
    # ===================================================================
    
    def _get_vendor_contracts(self) -> List[Dict]:
        """Get vendor contracts for risk analysis selection"""
        try:
            # Import contract models
            from contracts.models import VendorContract
            
            # Get contracts with vendor information
            contracts = VendorContract.objects.select_related('vendor').filter(
                is_archived=False
            ).values(
                'contract_id', 'contract_number', 'contract_title', 'contract_type',
                'contract_kind', 'status', 'priority', 'contract_value', 'currency',
                'start_date', 'end_date', 'vendor__company_name', 'vendor_id',
                'contract_risk_score', 'compliance_status', 'workflow_stage'
            )
            
            result = []
            for contract in contracts:
                # Create user-friendly display text
                vendor_name = contract.get('vendor__company_name', 'Unknown Vendor')
                contract_value = contract.get('contract_value')
                value_text = f"${contract_value:,.2f}" if contract_value else "N/A"
                
                display_text = f"Contract {contract['contract_number']} - {contract['contract_title']} ({vendor_name}) - {value_text}"
                
                result.append({
                    'id': contract['contract_id'],
                    'display_text': display_text,
                    'data': contract
                })
            
            logger.info(f"Retrieved {len(result)} vendor contracts")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching vendor contracts: {e}")
            return []
    
    def _get_contract_terms(self) -> List[Dict]:
        """Get contract terms for risk analysis selection"""
        try:
            # Import contract models
            from contracts.models import ContractTerm, VendorContract
            
            # Get terms with contract information
            terms = ContractTerm.objects.select_related().all().values(
                'term_id', 'contract_id', 'term_title', 'term_category',
                'term_text', 'risk_level', 'compliance_status', 'approval_status',
                'is_standard', 'version_number'
            )
            
            # Get contract data for context
            contract_data = {contract['contract_id']: contract for contract in VendorContract.objects.all().values(
                'contract_id', 'contract_number', 'contract_title', 'vendor_id'
            )}
            
            result = []
            for term in terms:
                contract_info = contract_data.get(term['contract_id'], {})
                contract_number = contract_info.get('contract_number', 'Unknown')
                
                # Create user-friendly display text
                display_text = f"Term {term['term_id']} - {term['term_title']} (Contract: {contract_number}) - {term['term_category']}"
                
                # Combine term and contract data
                combined_data = {**term, 'contract_info': contract_info}
                
                result.append({
                    'id': term['term_id'],
                    'display_text': display_text,
                    'data': combined_data
                })
            
            logger.info(f"Retrieved {len(result)} contract terms")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching contract terms: {e}")
            return []
    
    def _get_contract_clauses(self) -> List[Dict]:
        """Get contract clauses for risk analysis selection"""
        try:
            # Import contract models
            from contracts.models import ContractClause, VendorContract
            
            # Get clauses with contract information
            clauses = ContractClause.objects.select_related().all().values(
                'clause_id', 'contract_id', 'clause_name', 'clause_type',
                'clause_text', 'risk_level', 'legal_category', 'is_standard',
                'version_number'
            )
            
            # Get contract data for context
            contract_data = {contract['contract_id']: contract for contract in VendorContract.objects.all().values(
                'contract_id', 'contract_number', 'contract_title', 'vendor_id'
            )}
            
            result = []
            for clause in clauses:
                contract_info = contract_data.get(clause['contract_id'], {})
                contract_number = contract_info.get('contract_number', 'Unknown')
                
                # Create user-friendly display text
                display_text = f"Clause {clause['clause_id']} - {clause['clause_name']} (Contract: {contract_number}) - {clause['clause_type']}"
                
                # Combine clause and contract data
                combined_data = {**clause, 'contract_info': contract_info}
                
                result.append({
                    'id': clause['clause_id'],
                    'display_text': display_text,
                    'data': combined_data
                })
            
            logger.info(f"Retrieved {len(result)} contract clauses")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching contract clauses: {e}")
            return []
    
    def get_comprehensive_contract_data(self, contract_id: str) -> Dict:
        """
        Get comprehensive contract data including main contract, terms, and clauses
        This method is specifically for contract risk analysis integration
        
        Args:
            contract_id: The contract ID to analyze
            
        Returns:
            Dict containing comprehensive contract data for risk analysis
        """
        try:
            from contracts.models import VendorContract, ContractTerm, ContractClause
            
            # Get main contract data with vendor information
            try:
                contract = VendorContract.objects.select_related('vendor').get(
                    contract_id=contract_id,
                    is_archived=False
                )
                
                contract_data = {
                    'contract_id': contract.contract_id,
                    'contract_number': contract.contract_number,
                    'contract_title': contract.contract_title,
                    'contract_type': contract.contract_type,
                    'contract_kind': contract.contract_kind,
                    'status': contract.status,
                    'priority': contract.priority,
                    'contract_value': float(contract.contract_value) if contract.contract_value else None,
                    'currency': contract.currency,
                    'start_date': contract.start_date.isoformat() if contract.start_date else None,
                    'end_date': contract.end_date.isoformat() if contract.end_date else None,
                    'vendor_id': contract.vendor_id,
                    'vendor_name': contract.vendor.company_name if contract.vendor else None,
                    'contract_risk_score': float(contract.contract_risk_score) if contract.contract_risk_score else None,
                    'compliance_status': contract.compliance_status,
                    'workflow_stage': contract.workflow_stage,
                    'termination_clause_type': contract.termination_clause_type,
                    'liability_cap': float(contract.liability_cap) if contract.liability_cap else None,
                    'insurance_requirements': contract.insurance_requirements,
                    'data_protection_clauses': contract.data_protection_clauses,
                    'dispute_resolution_method': contract.dispute_resolution_method,
                    'governing_law': contract.governing_law,
                    'auto_renewal': contract.auto_renewal,
                    'notice_period_days': contract.notice_period_days,
                    'compliance_framework': contract.compliance_framework
                }
                
            except VendorContract.DoesNotExist:
                logger.error(f"Contract {contract_id} not found or archived")
                return {}
            
            # Get contract terms
            terms = ContractTerm.objects.filter(contract_id=contract_id).values(
                'term_id', 'term_title', 'term_category', 'term_text',
                'risk_level', 'compliance_status', 'approval_status',
                'is_standard', 'version_number'
            )
            terms_list = list(terms)
            
            # Get contract clauses
            clauses = ContractClause.objects.filter(contract_id=contract_id).values(
                'clause_id', 'clause_name', 'clause_type', 'clause_text',
                'risk_level', 'legal_category', 'is_standard', 'version_number'
            )
            clauses_list = list(clauses)
            
            # Combine all data
            comprehensive_data = {
                'contract_info': contract_data,
                'terms': terms_list,
                'clauses': clauses_list,
                'summary': {
                    'total_terms': len(terms_list),
                    'total_clauses': len(clauses_list),
                    'high_risk_terms': len([t for t in terms_list if t.get('risk_level') == 'High']),
                    'high_risk_clauses': len([c for c in clauses_list if c.get('risk_level') == 'High']),
                    'non_compliant_terms': len([t for t in terms_list if t.get('compliance_status') == 'Non-Compliant']),
                }
            }
            
            logger.info(f"Retrieved comprehensive data for contract {contract_id}: {len(terms_list)} terms, {len(clauses_list)} clauses")
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive contract data for {contract_id}: {e}")
            return {}

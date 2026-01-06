"""
Contract Management Admin Interface

This module defines the Django admin interface for contract management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Vendor, VendorContract, ContractTerm, ContractClause


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Admin interface for Vendor model"""
    
    list_display = [
        'vendor_code', 'company_name', 'legal_name', 'risk_level', 
        'status', 'business_criticality', 'is_critical_vendor', 'created_at'
    ]
    list_filter = [
        'risk_level', 'status', 'business_criticality', 'is_critical_vendor',
        'vendor_size_category', 'created_at'
    ]
    search_fields = ['vendor_code', 'company_name', 'legal_name', 'tax_id']
    readonly_fields = ['vendor_id', 'created_at', 'updated_at']
    ordering = ['company_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor_id', 'vendor_code', 'company_name', 'legal_name', 'business_type')
        }),
        ('Financial Information', {
            'fields': ('annual_revenue', 'employee_count', 'tax_id', 'duns_number')
        }),
        ('Location Information', {
            'fields': ('headquarters_country', 'headquarters_address', 'geographic_presence')
        }),
        ('Business Information', {
            'fields': ('description', 'industry_sector', 'website', 'vendor_category_id')
        }),
        ('Risk & Status', {
            'fields': ('risk_level', 'status', 'lifecycle_stage', 'business_criticality')
        }),
        ('Access & Security', {
            'fields': ('is_critical_vendor', 'has_data_access', 'has_system_access', 'data_classification_handled')
        }),
        ('Classification', {
            'fields': ('vendor_size_category', 'preferred_vendor_flag', 'diversity_certification', 'sustainability_rating')
        }),
        ('Relationships', {
            'fields': ('parent_vendor_id', 'vendor_tier_id')
        }),
        ('Assessment', {
            'fields': ('onboarding_date', 'last_assessment_date', 'next_assessment_date')
        }),
        ('Audit', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')
        })
    )


@admin.register(VendorContract)
class VendorContractAdmin(admin.ModelAdmin):
    """Admin interface for VendorContract model"""
    
    list_display = [
        'contract_number', 'contract_title', 'vendor', 'contract_type', 
        'status', 'workflow_stage', 'priority', 'contract_value', 'currency',
        'start_date', 'end_date', 'is_archived', 'created_at'
    ]
    list_filter = [
        'contract_type', 'status', 'workflow_stage', 'priority', 'contract_category',
        'is_archived', 'auto_renewal', 'created_at', 'start_date', 'end_date'
    ]
    search_fields = [
        'contract_number', 'contract_title', 'vendor__company_name', 
        'contract_owner__username', 'legal_reviewer__username'
    ]
    readonly_fields = ['contract_id', 'created_at', 'updated_at', 'is_expired', 'days_until_expiry']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('contract_id', 'contract_number', 'contract_title', 'contract_type', 'contract_kind')
        }),
        ('Vendor Information', {
            'fields': ('vendor', 'vendor_id')
        }),
        ('Contract Hierarchy', {
            'fields': ('parent_contract_id', 'main_contract_id')
        }),
        ('Financial Information', {
            'fields': ('contract_value', 'currency', 'liability_cap')
        }),
        ('Dates & Terms', {
            'fields': ('start_date', 'end_date', 'renewal_terms', 'auto_renewal', 'notice_period_days')
        }),
        ('Status & Workflow', {
            'fields': ('status', 'workflow_stage', 'priority', 'compliance_status')
        }),
        ('Contract Details', {
            'fields': ('contract_category', 'termination_clause_type', 'compliance_framework')
        }),
        ('Legal & Risk', {
            'fields': ('dispute_resolution_method', 'governing_law', 'contract_risk_score')
        }),
        ('JSON Fields', {
            'fields': ('insurance_requirements', 'data_protection_clauses', 'custom_fields'),
            'classes': ('collapse',)
        }),
        ('Assignment', {
            'fields': ('contract_owner', 'legal_reviewer', 'assigned_to')
        }),
        ('File Management', {
            'fields': ('file_path',)
        }),
        ('Archive Information', {
            'fields': ('is_archived', 'archived_date', 'archived_by', 'archive_reason', 'archive_comments', 'can_be_restored'),
            'classes': ('collapse',)
        }),
        ('Computed Fields', {
            'fields': ('is_expired', 'days_until_expiry'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def is_expired(self, obj):
        """Display if contract is expired"""
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
    
    def days_until_expiry(self, obj):
        """Display days until expiry"""
        days = obj.days_until_expiry()
        if days is None:
            return 'N/A'
        elif days < 0:
            return f'Expired ({abs(days)} days ago)'
        else:
            return f'{days} days'
    days_until_expiry.short_description = 'Days Until Expiry'


@admin.register(ContractTerm)
class ContractTermAdmin(admin.ModelAdmin):
    """Admin interface for ContractTerm model"""
    
    list_display = [
        'term_id', 'contract_id', 'term_category', 'term_title', 
        'risk_level', 'compliance_status', 'approval_status', 'is_standard'
    ]
    list_filter = [
        'term_category', 'risk_level', 'compliance_status', 'approval_status',
        'is_standard', 'created_at'
    ]
    search_fields = ['term_id', 'term_title', 'term_text']
    readonly_fields = ['term_id', 'created_at', 'updated_at']
    ordering = ['contract_id', 'term_category', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('term_id', 'contract_id', 'term_category', 'term_title')
        }),
        ('Term Content', {
            'fields': ('term_text',)
        }),
        ('Risk & Compliance', {
            'fields': ('risk_level', 'compliance_status', 'is_standard')
        }),
        ('Approval', {
            'fields': ('approval_status', 'approved_by', 'approved_at')
        }),
        ('Version Control', {
            'fields': ('version_number', 'parent_term_id')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at')
        })
    )


@admin.register(ContractClause)
class ContractClauseAdmin(admin.ModelAdmin):
    """Admin interface for ContractClause model"""
    
    list_display = [
        'clause_id', 'contract_id', 'clause_name', 'clause_type', 
        'risk_level', 'is_standard', 'created_at'
    ]
    list_filter = [
        'clause_type', 'risk_level', 'is_standard', 'created_at'
    ]
    search_fields = ['clause_id', 'clause_name', 'clause_text']
    readonly_fields = ['clause_id', 'created_at', 'updated_at']
    ordering = ['contract_id', 'clause_type', 'clause_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('clause_id', 'contract_id', 'clause_name', 'clause_type')
        }),
        ('Clause Content', {
            'fields': ('clause_text',)
        }),
        ('Risk & Classification', {
            'fields': ('risk_level', 'legal_category', 'is_standard')
        }),
        ('Version Control', {
            'fields': ('version_number',)
        }),
        ('Renewal Fields', {
            'fields': ('notice_period_days', 'auto_renew', 'renewal_terms'),
            'classes': ('collapse',)
        }),
        ('Termination Fields', {
            'fields': ('termination_notice_period', 'early_termination_fee', 'termination_conditions'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at')
        })
    )

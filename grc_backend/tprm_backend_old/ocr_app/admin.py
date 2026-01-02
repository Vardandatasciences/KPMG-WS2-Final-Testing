from django.contrib import admin
from .models import Document, OcrResult, ExtractedData


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['DocumentId', 'Title', 'OriginalFilename', 'Category', 'Department', 'Status', 'CreatedAt']
    list_filter = ['Status', 'Category', 'Department', 'DocType', 'CreatedAt']
    search_fields = ['Title', 'OriginalFilename', 'Description']
    readonly_fields = ['DocumentId', 'CreatedAt', 'UpdatedAt']
    ordering = ['-CreatedAt']


@admin.register(OcrResult)
class OcrResultAdmin(admin.ModelAdmin):
    list_display = ['OcrResultId', 'DocumentId', 'OcrLanguage', 'OcrConfidence', 'OcrEngine', 'CreatedAt']
    list_filter = ['OcrLanguage', 'OcrEngine', 'CreatedAt']
    search_fields = ['DocumentId', 'OcrText']
    readonly_fields = ['OcrResultId', 'CreatedAt']
    ordering = ['-CreatedAt']


@admin.register(ExtractedData)
class ExtractedDataAdmin(admin.ModelAdmin):
    list_display = [
        'ExtractedDataId', 'DocumentId_id', 'sla_name', 'sla_type', 
        'status', 'priority', 'approval_status', 'extraction_confidence', 'CreatedAt'
    ]
    list_filter = ['sla_type', 'status', 'priority', 'approval_status', 'CreatedAt']
    search_fields = ['sla_name', 'vendor_id', 'contract_id', 'business_service_impacted']
    readonly_fields = ['ExtractedDataId', 'CreatedAt', 'UpdatedAt']
    ordering = ['-CreatedAt']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('DocumentId_id', 'OcrResultId_id')
        }),
        ('SLA Basic Information', {
            'fields': ('sla_name', 'vendor_id', 'contract_id', 'sla_type', 'status')
        }),
        ('Dates', {
            'fields': ('effective_date', 'expiry_date')
        }),
        ('Business Details', {
            'fields': ('business_service_impacted', 'reporting_frequency', 'baseline_period')
        }),
        ('Targets and Thresholds', {
            'fields': ('improvement_targets', 'penalty_threshold', 'credit_threshold')
        }),
        ('Methodology and Requirements', {
            'fields': ('measurement_methodology', 'exclusions', 'force_majeure_clauses')
        }),
        ('Compliance and Approval', {
            'fields': ('compliance_framework', 'audit_requirements', 'document_versioning', 
                      'compliance_score', 'priority', 'approval_status')
        }),
        ('Metrics', {
            'fields': ('metrics',)
        }),
        ('Extraction Metadata', {
            'fields': ('raw_extracted_data', 'extraction_confidence', 'extraction_method'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('CreatedAt', 'UpdatedAt'),
            'classes': ('collapse',)
        })
    )

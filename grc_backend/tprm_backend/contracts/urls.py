"""
Contract Management API URLs

This module defines the URL patterns for the contract management API endpoints.
"""

from django.urls import path, include
from . import views

app_name = 'contracts'

urlpatterns = [
    # Authentication Endpoints (MFA removed)
    path('auth/login/', views.simple_login, name='simple-login'),
    path('auth/validate-session/', views.validate_session, name='validate-session'),
    
    # Contract Management Endpoints
    path('contracts/', views.contract_list, name='contract-list'),
    path('contracts/search/', views.contract_search, name='contract-search'),
    path('contracts/stats/', views.contract_stats, name='contract-stats'),
    path('contracts/analytics/', views.contract_analytics, name='contract-analytics'),
    path('contracts/kpi/amendments/', views.contract_amendments_kpi, name='contract-amendments-kpi'),
    path('contracts/kpi/expiring-soon/', views.contracts_expiring_soon_kpi, name='contracts-expiring-soon-kpi'),
    path('contracts/kpi/avg-value-by-type/', views.average_contract_value_by_type_kpi, name='average-contract-value-by-type-kpi'),
    path('contracts/kpi/business-criticality/', views.business_criticality_kpi, name='business-criticality-kpi'),
    path('contracts/kpi/total-liability/', views.total_liability_exposure_kpi, name='total-liability-exposure-kpi'),
    path('contracts/kpi/risk-exposure/', views.contract_risk_exposure_kpi, name='contract-risk-exposure-kpi'),
    path('contracts/kpi/early-termination-rate/', views.early_termination_rate_kpi, name='early-termination-rate-kpi'),
    path('contracts/kpi/time-to-approve/', views.time_to_approve_contract_kpi, name='time-to-approve-contract-kpi'),
    path('contracts/create/', views.contract_create, name='contract-create'),
    path('contracts/<int:contract_id>/', views.contract_detail, name='contract-detail'),
    path('contracts/<int:contract_id>/comprehensive/', views.contract_comprehensive_detail, name='contract-comprehensive-detail'),
    path('contracts/<int:contract_id>/update/', views.contract_update, name='contract-update'),
    path('contracts/<int:contract_id>/delete/', views.contract_delete, name='contract-delete'),
    path('contracts/<int:contract_id>/archive/', views.contract_archive, name='contract-archive'),
    path('contracts/<int:contract_id>/restore/', views.contract_restore, name='contract-restore'),
    
    # Subcontract Management Endpoints
    path('contracts/<int:parent_contract_id>/subcontracts/', views.subcontracts_list, name='subcontracts-list'),
    path('contracts/<int:parent_contract_id>/subcontracts/create/', views.subcontract_create, name='subcontract-create'),
    path('contracts/<int:parent_contract_id>/subcontract-with-versioning/create/', views.create_subcontract_with_versioning, name='create-subcontract-with-versioning'),
    path('contracts/with-subcontract/create/', views.contract_with_subcontract_create, name='contract-with-subcontract-create'),
    
    # Contract Amendments as Contracts Endpoints
    path('contracts/<int:parent_contract_id>/amendments-as-contracts/', views.contract_amendments_as_contracts_list, name='contract-amendments-as-contracts-list'),
    
    # Contract Terms Endpoints
    path('contracts/<int:contract_id>/terms/', views.contract_terms_list, name='contract-terms-list'),
    path('contracts/<int:contract_id>/terms/create/', views.contract_terms_create, name='contract-terms-create'),
    path('contracts/<int:contract_id>/terms/delete-all/', views.contract_terms_delete_all, name='contract-terms-delete-all'),
    path('contracts/<int:contract_id>/terms/<int:term_id>/', views.contract_term_detail, name='contract-term-detail'),
    path('contracts/<int:contract_id>/terms/<int:term_id>/update/', views.contract_term_update, name='contract-term-update'),
    path('contracts/<int:contract_id>/terms/<int:term_id>/delete/', views.contract_term_delete, name='contract-term-delete'),
    
    # Contract Clauses Endpoints
    path('contracts/<int:contract_id>/clauses/', views.contract_clauses_list, name='contract-clauses-list'),
    path('contracts/<int:contract_id>/clauses/create/', views.contract_clauses_create, name='contract-clauses-create'),
    path('contracts/<int:contract_id>/clauses/delete-all/', views.contract_clauses_delete_all, name='contract-clauses-delete-all'),
    path('contracts/<int:contract_id>/clauses/<int:clause_id>/', views.contract_clause_detail, name='contract-clause-detail'),
    path('contracts/<int:contract_id>/clauses/<int:clause_id>/update/', views.contract_clause_update, name='contract-clause-update'),
    path('contracts/<int:contract_id>/clauses/<int:clause_id>/delete/', views.contract_clause_delete, name='contract-clause-delete'),
    
    # Contract Amendments Endpoints
    path('contracts/<int:contract_id>/amendments/create/', views.contract_amendments_create, name='contract-amendments-create'),
    path('contracts/<int:contract_id>/amendments/<int:amendment_id>/', views.contract_amendment_detail, name='contract-amendment-detail'),
    path('contracts/<int:contract_id>/amendments/<int:amendment_id>/update/', views.contract_amendment_update, name='contract-amendment-update'),
    path('contracts/<int:contract_id>/amendments/<int:amendment_id>/delete/', views.contract_amendment_delete, name='contract-amendment-delete'),
    path('contracts/<int:contract_id>/amendments/', views.contract_amendments_list, name='contract-amendments-list'),
    
    # Vendor Contracts Management Endpoints
    path('vendorcontracts/', views.vendor_list, name='vendor-list'),
    path('vendorcontracts/stats/', views.vendor_stats, name='vendor-stats'),
    path('vendorcontracts/<int:vendor_id>/', views.vendor_detail, name='vendor-detail'),
    path('vendorcontracts/<int:vendor_id>/contacts/', views.vendor_contacts_list, name='vendor-contacts-list'),
    path('vendorcontracts/<int:vendor_id>/contacts/create/', views.vendor_contact_create, name='vendor-contact-create'),
    
    # Permission Check Endpoints
    path('permissions/check-contract-create/', views.check_contract_create_permission, name='check-contract-create-permission'),
    
    # Contract Renewal Endpoints
    path('contracts/renewals/', views.contract_renewals_list, name='contract-renewals-list'),
    path('contracts/renewals/create/', views.contract_renewal_create, name='contract-renewal-create'),
    path('contracts/renewals/<int:renewal_id>/', views.contract_renewal_detail, name='contract-renewal-detail'),
    path('contracts/renewals/<int:renewal_id>/update/', views.contract_renewal_update, name='contract-renewal-update'),
    path('contracts/renewals/<int:renewal_id>/delete/', views.contract_renewal_delete, name='contract-renewal-delete'),
    
    # User Management Endpoints
    path('users/', views.users_list, name='users-list'),
    path('users/legal-reviewers/', views.legal_reviewers_list, name='legal-reviewers-list'),
    path('users/approval-users/', views.approval_users_list, name='approval-users-list'),
    
    # Contract Versioning Endpoints
    path('contracts/<int:contract_id>/versions/', views.get_contract_versions, name='contract-versions'),
    path('contracts/<int:contract_id>/create-version/', views.create_contract_version, name='create-contract-version'),
    path('contracts/<int:contract_id>/create-amendment/', views.create_contract_amendment, name='create-contract-amendment'),
    path('contracts/<int:contract_id>/create-subcontract/', views.create_subcontract, name='create-subcontract'),
    path('contracts/<int:contract_id>/upload-ocr/', views.upload_contract_ocr, name='upload-contract-ocr'),
    
    # CORS Test Endpoint
    path('cors-test/', views.cors_test, name='cors-test'),
    
    # Test Endpoints
    path('contracts/<int:contract_id>/test-amendment/', views.test_amendment_creation, name='test-amendment-creation'),
    
    # Contract Risk Analysis Endpoints
    path('contracts/<int:contract_id>/risk-analysis/', views.contract_risk_analysis, name='contract-risk-analysis'),
    path('contracts/<int:contract_id>/risk-summary/', views.contract_risk_summary, name='contract-risk-summary'),
    path('contracts/<int:contract_id>/risks/', views.contract_risks_list, name='contract-risks-list'),
    path('contracts/<int:contract_id>/trigger-contract-risk-analysis/', views.trigger_contract_risk_analysis, name='trigger-contract-risk-analysis'),
    
    # Contract Comparison Endpoints
    path('contracts/<int:contract_id>/compare/<int:amendment_id>/', views.contract_comparison, name='contract-comparison'),
    
    # Contract Approval Endpoints
    path('approvals/', include('tprm_backend.contracts.contractapproval.urls')),
]

"""
URL patterns for the Audits app.
"""
from django.urls import path
from . import views
from . import test_endpoints

urlpatterns = [
    # Contract Audit CRUD
    path('', views.ContractAuditListView.as_view(), name='contract-audit-list'),
    path('<int:pk>/', views.ContractAuditDetailView.as_view(), name='contract-audit-detail'),
    
    # Static Questionnaires
    path('contractquestionnaires/', views.ContractStaticQuestionnaireListView.as_view(), name='contract-questionnaire-list'),
    path('contractquestionnaires/<int:pk>/', views.ContractStaticQuestionnaireDetailView.as_view(), name='contract-questionnaire-detail'),
    
    # Audit Versions
    path('contractversions/', views.ContractAuditVersionListView.as_view(), name='contract-audit-version-list'),
    path('contractversions/<int:pk>/', views.ContractAuditVersionDetailView.as_view(), name='contract-audit-version-detail'),
    
    # Audit Findings
    path('contractfindings/', views.ContractAuditFindingListView.as_view(), name='contract-audit-finding-list'),
    path('contractfindings/<int:pk>/', views.ContractAuditFindingDetailView.as_view(), name='contract-audit-finding-detail'),
    
    # Audit Reports
    path('contractreports/', views.ContractAuditReportListView.as_view(), name='contract-audit-report-list'),
    path('contractreports/<int:pk>/', views.ContractAuditReportDetailView.as_view(), name='contract-audit-report-detail'),
    path('contractreports/upload/', views.upload_contract_audit_report, name='upload-contract-audit-report'),
    path('contractdocuments/upload/', views.upload_contract_audit_document, name='upload-contract-audit-document'),
    
    # Dashboard and utilities
    path('contractdashboard/stats/', views.contract_audit_dashboard_stats, name='contract-audit-dashboard-stats'),
    path('contractavailable-contracts/', views.available_contracts, name='available-contracts'),
    path('contract-terms/<int:contract_id>/', views.contract_terms, name='contract-terms'),
    path('contractquestionnaires-by-term/', views.questionnaires_by_term_title, name='questionnaires-by-term-title'),
    path('contractquestionnaires-by-term-ids/', views.questionnaires_by_term_ids, name='questionnaires-by-term-ids'),
    path('contracttemplates-by-term/', views.templates_by_term, name='templates-by-term'),
    path('contracttemplate/<int:template_id>/questions/', views.template_questions, name='template-questions'),
    path('contractavailable-users/', views.available_users, name='available-users'),
    
    # Audit actions
    path('<int:audit_id>/contractstart/', views.start_audit, name='start-audit'),
    path('<int:audit_id>/contractsubmit-response/', views.submit_contract_audit_response, name='submit-contract-audit-response'),
    path('<int:audit_id>/contractreview/', views.review_contract_audit, name='review-contract-audit'),
    
    # Test endpoints
    path('test-database/', test_endpoints.test_database_connection, name='test-database-connection'),
    path('test-create-finding/', test_endpoints.test_create_finding, name='test-create-finding'),
]

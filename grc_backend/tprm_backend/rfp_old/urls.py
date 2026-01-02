from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_kpi
from . import document_views
from . import views_rfp_responses
from . import views_invitation_generation
from . import views_file_operations
from . import views_evaluation
from . import views_evaluator_assignment
from . import views_committee
from . import rfp_versioning_views
# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'rfps', views.RFPViewSet)
router.register(r'evaluation-criteria', views.RFPEvaluationCriteriaViewSet)
router.register(r'users', views.CustomUserViewSet)
router.register(r'rfp-types', views.RFPTypeCustomFieldsViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # RFP Response endpoints for vendor portal (moved to top to avoid conflicts)
    path('test/', views_rfp_responses.test_endpoint, name='test_endpoint'),
    path('test-risk-analysis/', views_rfp_responses.test_risk_analysis, name='test_risk_analysis'),
    path('rfp-details/', views_rfp_responses.get_rfp_details, name='get_rfp_details'),
    path('rfp-responses/', views_rfp_responses.create_rfp_response, name='create_rfp_response'),
    path('rfp-responses/create-unmatched-vendor/', views_rfp_responses.create_unmatched_vendor, name='create_unmatched_vendor'),
    path('open-rfp/<int:rfp_id>/', views_rfp_responses.get_open_rfp_by_id, name='get_open_rfp_by_id'),
    path('rfp-responses/check-status/', views_rfp_responses.check_submission_status, name='check_submission_status'),
    path('rfp-responses/draft/', views_rfp_responses.save_draft_response, name='save_draft_response'),
    path('rfp-responses/draft/<int:rfp_id>/', views_rfp_responses.get_draft_response, name='get_draft_response'),
    path('rfp-responses/upload-document/', views_rfp_responses.upload_document, name='upload_document'),
    path('rfp-responses/upload-response-asset/', views_rfp_responses.upload_response_asset, name='upload_response_asset'),     
    path('rfp-responses/<int:rfp_id>/documents/', views_rfp_responses.list_documents, name='list_documents'),
    path('rfp-responses/<int:rfp_id>/documents/download/', views_rfp_responses.download_document, name='download_document'),
    path('rfp-responses/<int:rfp_id>/documents/delete/', views_rfp_responses.delete_document, name='delete_document'),
    path('rfp-responses-list/', views_rfp_responses.get_rfp_responses, name='get_rfp_responses'),
    path('rfp-responses-detail/<int:response_id>/', views_rfp_responses.get_rfp_response_by_id, name='get_rfp_response_by_id'),
    
    # Evaluator Assignment endpoints
    path('evaluator-assignments/bulk-assign/', views_evaluator_assignment.bulk_assign_evaluators, name='bulk_assign_evaluators'),
    path('evaluator-assignments/evaluator/<int:evaluator_id>/', views_evaluator_assignment.get_evaluator_assignments, name='get_evaluator_assignments'),
    path('evaluator-assignments/proposal/<int:proposal_id>/', views_evaluator_assignment.get_proposal_assignments, name='get_proposal_assignments'),
    path('evaluator-assignments/<int:assignment_id>/status/', views_evaluator_assignment.update_assignment_status, name='update_assignment_status'),
    path('evaluator-assignments/<int:assignment_id>/remove/', views_evaluator_assignment.remove_assignment, name='remove_assignment'),
    path('evaluators/available/', views_evaluator_assignment.get_available_evaluators, name='get_available_evaluators'),
    
    # Evaluation scores endpoints
    path('rfp-evaluation-scores/', views_evaluation.get_evaluation_scores_bulk, name='get_evaluation_scores_bulk'),
    path('rfp-evaluation-scores/<int:response_id>/save/', views_evaluation.save_evaluation_scores, name='save_evaluation_scores'),
    path('rfp-evaluation-scores/<int:response_id>/', views_evaluation.get_evaluation_scores, name='get_evaluation_scores'),
    # Committee rankings endpoint
    path('rfp/<int:rfp_id>/committee-evaluation/', views_evaluation.save_committee_evaluation, name='save_committee_evaluation'),
    
    # Committee management endpoints
    path('rfp/<int:rfp_id>/committee/', views_committee.create_committee, name='create_committee'),
    path('rfp/<int:rfp_id>/committee/get/', views_committee.get_committee, name='get_committee'),
    path('rfp/<int:rfp_id>/final-evaluation/', views_committee.save_final_evaluation, name='save_final_evaluation'),
    path('rfp/<int:rfp_id>/final-evaluations/', views_committee.get_final_evaluations, name='get_final_evaluations'),
    path('rfp/<int:rfp_id>/consensus-ranking/', views_committee.get_consensus_ranking, name='get_consensus_ranking'),
    path('rfp/<int:rfp_id>/declare-award/', views_committee.declare_award, name='declare_award'),
    
    path('invitations/<str:invitation_id>/', views_rfp_responses.get_invitation_details, name='get_invitation_details'),
    path('open-rfp/<str:rfp_number>/', views_rfp_responses.get_open_rfp_details, name='get_open_rfp_details'),
    path('open-rfp/<str:rfp_number>/create-invitation/', views_rfp_responses.create_open_invitation, name='create_open_invitation'),
    path('rfp/<str:rfp_number>/evaluation-criteria/', views_rfp_responses.get_rfp_evaluation_criteria, name='get_rfp_evaluation_criteria'),
    
    # New invitation generation endpoints
    path('generate-invitations/', views_invitation_generation.generate_invitations_new_format, name='generate_invitations_new_format'),
    path('generate-open-invitation/', views_invitation_generation.generate_open_rfp_invitation, name='generate_open_rfp_invitation'),
    path('invitations-by-rfp/<int:rfp_id>/', views_invitation_generation.get_invitations_by_rfp, name='get_invitations_by_rfp'),
    path('send-invitation-emails/', views_invitation_generation.send_invitation_emails, name='send_invitation_emails'),
    
    # Vendor matching endpoint
    path('rfps/<int:rfp_id>/calculate-match-scores/', views.calculate_vendor_match_scores, name='calculate_vendor_match_scores'),

    # Document generation endpoints
    path('rfps/<int:rfp_id>/download/word/', document_views.generate_rfp_word_document, name='rfp-download-word'),
    path('rfps/<int:rfp_id>/download/pdf/', document_views.generate_rfp_pdf_document, name='rfp-download-pdf'),
    path('rfps/<int:rfp_id>/preview/', document_views.preview_rfp_document, name='rfp-preview'),
    path('generate-document/', document_views.generate_document_from_data, name='generate-document-from-data'),
    
    # Vendor selection endpoints
    path('rfps/<int:rfp_id>/vendors/', views.vendor_selection, name='vendor_selection'),
    path('rfps/<int:rfp_id>/vendors/manual-entry/', views.vendor_manual_entry, name='vendor_manual_entry'),
    path('rfps/<int:rfp_id>/vendors/bulk-upload/', views.vendor_bulk_upload, name='vendor_bulk_upload'),
    path('rfps/<int:rfp_id>/vendors/update-selection/', views.update_vendor_selection, name='update_vendor_selection'),
    path('rfps/<int:rfp_id>/vendors/bulk-select/', views.bulk_select_vendors, name='bulk_select_vendors'),
    path('rfps/<int:rfp_id>/vendors/generate-urls/', views.generate_vendor_urls, name='generate_vendor_urls'),
    path('vendors/sample-csv/', views.get_sample_csv, name='get_sample_csv'),
    path('rfps/<int:rfp_id>/unmatched-vendors/', views.get_unmatched_vendors, name='get_unmatched_vendors'),
    path('rfps/<int:rfp_id>/unmatched-vendors/create/', views.create_unmatched_vendor, name='create_unmatched_vendor'),
    path('rfps/<int:rfp_id>/unmatched-vendors/bulk-upload/', views.unmatched_vendor_bulk_upload, name='unmatched_vendor_bulk_upload'),
    path('rfps/<int:rfp_id>/approved-vendors/', views.get_approved_vendors, name='get_approved_vendors'),
    path('vendors/active/', views.get_all_approved_vendors, name='get_all_approved_vendors'),
    path('vendors/<int:vendor_id>/primary-contact/', views.get_vendor_primary_contact, name='get_vendor_primary_contact'),
    path('rfps/<int:rfp_id>/vendors/invitation/', views.vendor_invitation, name='vendor_invitation'),
    
    # Vendor invitation API endpoints
    path('vendor-invitations/primary-contacts/', views.get_primary_contacts, name='get_primary_contacts'),
    path('vendor-invitations/rfp/<int:rfp_id>/', views.get_invitations_by_rfp, name='get_invitations_by_rfp'),
    path('vendor-invitations/stats/<int:rfp_id>/', views.get_invitation_stats, name='get_invitation_stats'),
    path('vendor-invitations/create/<int:rfp_id>/', views.create_vendor_invitations, name='create_vendor_invitations'),
    path('vendor-invitations/send/<int:rfp_id>/', views.send_vendor_invitations, name='send_vendor_invitations'),
    
    # Vendor response endpoints
    path('vendor-invitations/acknowledge/<str:token>/', views.acknowledge_invitation, name='acknowledge_invitation'),
    path('vendor-invitations/decline/<str:token>/', views.decline_invitation, name='decline_invitation'),
    # ID-tracking acknowledge/decline endpoints
    path('vendor-invitations/ack/<int:rfp_id>/<int:invitation_id>/', views.ack_invitation_with_ids, name='ack_invitation_with_ids'),
    path('vendor-invitations/decline/<int:rfp_id>/<int:invitation_id>/', views.decline_invitation_with_ids, name='decline_invitation_with_ids'),
    
    # S3 File Operations endpoints
    path('s3/health/', views_file_operations.s3_health_check, name='s3_health_check'),
    path('s3/upload/', views_file_operations.upload_file, name='upload_file'),
    path('s3/download/', views_file_operations.download_file, name='download_file'),
    path('s3/export/', views_file_operations.export_data, name='export_data'),
    path('s3/history/', views_file_operations.file_history, name='file_history'),
    path('s3/stats/', views_file_operations.file_stats, name='file_stats'),
    path('s3/files/<int:file_id>/', views_file_operations.get_file_by_id, name='get_file_by_id'),
    path('s3-files/<int:file_id>/', views_file_operations.get_s3_file_by_id, name='get_s3_file_by_id'),
    path('s3/export-rfp/<int:rfp_id>/', views_file_operations.export_rfp_data, name='export_rfp_data'),
    
    # Document Upload endpoint for RFP creation
    path('upload-document/', views.DocumentUploadView.as_view(), name='upload_document'),
    
# Standalone merge endpoint (works without RFP ID)
    path('merge-documents/', views.MergeDocumentsView.as_view(), name='merge-documents-standalone'),
   
    # RFP document management endpoints
    path('rfps/<int:pk>/update-documents/', views.RFPViewSet.as_view({'post': 'update_documents'}), name='rfp-update-documents'),
    path('rfps/<int:pk>/merge-documents/', views.RFPViewSet.as_view({'post': 'merge_documents'}), name='rfp-merge-documents'),
 
    # Award notification endpoints
    path('rfp/<int:rfp_id>/award-notification/', views.AwardNotificationView.as_view(), name='award_notification'),
    path('award-response/<str:token>/', views.AwardResponseView.as_view(), name='award_response'),
    path('vendor-credentials/<int:notification_id>/', views.VendorCredentialsView.as_view(), name='vendor_credentials'),

    # KPI Analytics endpoints
    path('kpi/summary/', views_kpi.get_rfp_kpi_summary, name='get_rfp_kpi_summary'),
    path('kpi/creation-rate/', views_kpi.get_rfp_creation_rate, name='get_rfp_creation_rate'),
    path('kpi/approval-time/', views_kpi.get_rfp_approval_time, name='get_rfp_approval_time'),
    path('kpi/first-time-approval-rate/', views_kpi.get_first_time_approval_rate, name='get_first_time_approval_rate'),
    path('kpi/lifecycle-time/', views_kpi.get_rfp_lifecycle_time, name='get_rfp_lifecycle_time'),
    path('kpi/vendor-response-rate/', views_kpi.get_vendor_response_rate, name='get_vendor_response_rate'),
    path('kpi/new-vs-existing-vendors/', views_kpi.get_new_vs_existing_vendors, name='get_new_vs_existing_vendors'),
    path('kpi/category-performance/', views_kpi.get_category_performance, name='get_category_performance'),
    path('kpi/award-acceptance-rate/', views_kpi.get_award_acceptance_rate, name='get_award_acceptance_rate'),
    path('kpi/vendor-conversion-funnel/', views_kpi.get_vendor_conversion_funnel, name='get_vendor_conversion_funnel'),
    path('kpi/reviewer-workload/', views_kpi.get_reviewer_workload, name='get_reviewer_workload'),
    path('kpi/evaluator-consistency/', views_kpi.get_evaluator_consistency, name='get_evaluator_consistency'),
    path('kpi/evaluator-completion-time/', views_kpi.get_evaluator_completion_time, name='get_evaluator_completion_time'),
    path('kpi/score-distribution/', views_kpi.get_score_distribution, name='get_score_distribution'),
    path('kpi/consensus-quality/', views_kpi.get_consensus_quality, name='get_consensus_quality'),
    path('kpi/criteria-effectiveness/', views_kpi.get_criteria_effectiveness, name='get_criteria_effectiveness'),
    path('kpi/budget-variance/', views_kpi.get_budget_variance, name='get_budget_variance'),
    path('kpi/price-spread/', views_kpi.get_price_spread, name='get_price_spread'),
    path('kpi/process-funnel/', views_kpi.get_process_funnel, name='get_process_funnel'),

    # RFP Versioning endpoints
    path('rfps/<int:rfp_id>/edit_with_versioning/', rfp_versioning_views.edit_rfp_with_versioning, name='edit_rfp_with_versioning'),
    path('rfp-version-history/<int:rfp_id>/', rfp_versioning_views.get_rfp_version_history, name='get_rfp_version_history'),
    path('rfp-version/<str:version_id>/', rfp_versioning_views.get_rfp_version, name='get_rfp_version'),
    path('rfp-rollback/', rfp_versioning_views.rollback_rfp_version, name='rollback_rfp_version'),
    path('rfp-change-requests/<int:rfp_id>/', rfp_versioning_views.get_rfp_change_requests, name='get_rfp_change_requests'),
]
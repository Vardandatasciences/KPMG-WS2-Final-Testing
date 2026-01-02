from django.urls import path, include
from . import views

urlpatterns = [
    # API endpoints
    path('upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('documents/', views.DocumentListView.as_view(), name='document_list'),
    path('documents/<int:document_id>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('extract-sla/', views.SLAExtractionView.as_view(), name='sla_extraction'),
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
    path('csrf-token/', views.get_csrf_token, name='csrf_token'),
    
    # BCP/DRP OCR endpoints
    path('plans/<int:plan_id>/run/', views.BcpDrpOcrRunView.as_view(), name='bcp_drp_ocr_run'),
    path('plans/<int:plan_id>/extract/', views.BcpDrpExtractDataView.as_view(), name='bcp_drp_extract_data'),
    path('plans/<int:plan_id>/extracted-data/', views.BcpDrpExtractedDataView.as_view(), name='bcp_drp_extracted_data'),
    
    # Web pages
    path('', views.index_view, name='index'),
    path('upload-page/', views.upload_view, name='upload_page'),
    path('documents-page/', views.documents_view, name='documents_page'),
    path('document/<int:document_id>/', views.document_detail_view, name='document_detail_page'),
]

"""
BCP/DRP Dashboard API functions
Comprehensive metrics and analytics for the BCP/DRP dashboard
"""
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count, Avg, Sum, Max, Min, Case, When, IntegerField
from django.db.models.functions import TruncMonth, TruncYear, Extract
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from tprm_backend.bcpdrp.models import (
    Plan, BcpDetails, DrpDetails, Evaluation, Questionnaire, Question, 
    TestAssignmentsResponses, BcpDrpApprovals, Users, Dropdown
)
# Import risk models with error handling
try:
    from risk_analysis.models import Risk
    RISK_MODELS_AVAILABLE = True
except ImportError:
    Risk = None
    RISK_MODELS_AVAILABLE = False
from tprm_backend.bcpdrp.utils import success_response, error_response
from tprm_backend.rbac.tprm_decorators import rbac_bcp_drp_required

# Import proper authentication classes from views
from tprm_backend.bcpdrp.views import JWTAuthentication, SimpleAuthenticatedPermission

logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def dashboard_overview(request):
    """
    Get comprehensive dashboard overview with all key metrics
    """
    try:
        logger.info("Starting dashboard overview data collection")
        
        # Plan Management Metrics
        logger.info("Collecting plan metrics...")
        plan_metrics = get_plan_metrics()
        
        # Evaluation Metrics
        logger.info("Collecting evaluation metrics...")
        evaluation_metrics = get_evaluation_metrics()
        
        # Testing Metrics
        logger.info("Collecting testing metrics...")
        testing_metrics = get_testing_metrics()
        
        # Approval Workflow Metrics
        logger.info("Collecting approval metrics...")
        approval_metrics = get_approval_metrics()
        
        # Risk Analysis Metrics
        logger.info("Collecting risk metrics...")
        risk_metrics = get_risk_metrics()
        
        # User Activity Metrics
        logger.info("Collecting user metrics...")
        user_metrics = get_user_metrics()
        
        # Temporal Metrics
        logger.info("Collecting temporal metrics...")
        # MULTI-TENANCY: Get tenant_id from request and pass to temporal metrics
        from tprm_backend.core.tenant_utils import get_tenant_id_from_request
        tenant_id = get_tenant_id_from_request(request)
        temporal_metrics = get_temporal_metrics(tenant_id=tenant_id)
        
        logger.info("Dashboard overview data collection completed successfully")
        
        return success_response({
            'plan_metrics': plan_metrics,
            'evaluation_metrics': evaluation_metrics,
            'testing_metrics': testing_metrics,
            'approval_metrics': approval_metrics,
            'risk_metrics': risk_metrics,
            'user_metrics': user_metrics,
            'temporal_metrics': temporal_metrics,
            'last_updated': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard overview: {str(e)}", exc_info=True)
        return error_response(f"Failed to fetch dashboard data: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_plan_metrics():
    """Get plan management metrics"""
    try:
        # Get plan types from dropdown table
        plan_types = list(Dropdown.objects.filter(source='plan_type').values_list('value', flat=True))
        
        # Basic counts
        total_plans = Plan.objects.count()
        
        # Count plans by type dynamically
        plan_type_counts = {}
        for plan_type in plan_types:
            plan_type_counts[f'{plan_type.lower()}_plans'] = Plan.objects.filter(plan_type=plan_type).count()
        
        # For backward compatibility, keep bcp_plans and drp_plans if they exist
        bcp_plans = plan_type_counts.get('bcp_plans', 0) if 'BCP' in plan_types else 0
        drp_plans = plan_type_counts.get('drp_plans', 0) if 'DRP' in plan_types else 0
        
        # Plan type distribution
        plan_type_distribution = dict(Plan.objects.values('plan_type').annotate(count=Count('plan_id')).values_list('plan_type', 'count'))
        
        # Status distribution
        status_distribution = dict(Plan.objects.values('status').annotate(count=Count('plan_id')).values_list('status', 'count'))
        
        # Criticality distribution
        criticality_distribution = dict(Plan.objects.values('criticality').annotate(count=Count('plan_id')).values_list('criticality', 'count'))
        
        # OCR metrics
        ocr_completed = Plan.objects.filter(ocr_extracted=True).count()
        ocr_rate = (ocr_completed / total_plans * 100) if total_plans > 0 else 0
        
        # Approval metrics
        approved_plans = Plan.objects.filter(status='APPROVED').count()
        rejected_plans = Plan.objects.filter(status='REJECTED').count()
        approval_rate = (approved_plans / (approved_plans + rejected_plans) * 100) if (approved_plans + rejected_plans) > 0 else 0
        
        # Vendor distribution
        vendor_distribution = dict(Plan.objects.values('vendor_id').annotate(count=Count('plan_id')).values_list('vendor_id', 'count'))
        
        # Strategy distribution
        strategy_distribution = dict(Plan.objects.values('strategy_id', 'strategy_name').annotate(count=Count('plan_id')).values_list('strategy_name', 'count'))
        
        # Quality metrics - plans with scope information
        plans_with_details = Plan.objects.filter(
            Q(plan_scope__isnull=False) & ~Q(plan_scope='')
        ).count()
        
        result = {
            'total_plans': total_plans,
            'bcp_plans': bcp_plans,  # For backward compatibility
            'drp_plans': drp_plans,  # For backward compatibility
            'plan_type_distribution': plan_type_distribution,
            'status_distribution': status_distribution,
            'criticality_distribution': criticality_distribution,
            'ocr_completed': ocr_completed,
            'ocr_rate': round(ocr_rate, 2),
            'approved_plans': approved_plans,
            'rejected_plans': rejected_plans,
            'approval_rate': round(approval_rate, 2),
            'vendor_distribution': vendor_distribution,
            'strategy_distribution': strategy_distribution,
            'plans_with_details': plans_with_details,
            'quality_rate': round((plans_with_details / total_plans * 100) if total_plans > 0 else 0, 2)
        }
        
        # Add dynamic plan type counts
        result.update(plan_type_counts)
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating plan metrics: {str(e)}")
        return {}


def get_evaluation_metrics():
    """Get evaluation performance metrics"""
    try:
        # Basic counts
        total_evaluations = Evaluation.objects.count()
        submitted_evaluations = Evaluation.objects.filter(status='SUBMITTED').count()
        
        # Status distribution
        status_distribution = dict(Evaluation.objects.values('status').annotate(count=Count('evaluation_id')).values_list('status', 'count'))
        
        # Score metrics
        avg_overall_score = Evaluation.objects.filter(overall_score__isnull=False).aggregate(avg=Avg('overall_score'))['avg'] or 0
        avg_quality_score = Evaluation.objects.filter(quality_score__isnull=False).aggregate(avg=Avg('quality_score'))['avg'] or 0
        avg_coverage_score = Evaluation.objects.filter(coverage_score__isnull=False).aggregate(avg=Avg('coverage_score'))['avg'] or 0
        avg_recovery_score = Evaluation.objects.filter(recovery_capability_score__isnull=False).aggregate(avg=Avg('recovery_capability_score'))['avg'] or 0
        avg_compliance_score = Evaluation.objects.filter(compliance_score__isnull=False).aggregate(avg=Avg('compliance_score'))['avg'] or 0
        
        # Score distribution
        score_distribution = Evaluation.objects.aggregate(
            excellent=Count('evaluation_id', filter=Q(overall_score__gte=90)),
            good=Count('evaluation_id', filter=Q(overall_score__gte=80, overall_score__lt=90)),
            fair=Count('evaluation_id', filter=Q(overall_score__gte=70, overall_score__lt=80)),
            poor=Count('evaluation_id', filter=Q(overall_score__lt=70))
        )
        
        # Evaluator performance
        evaluator_performance = dict(
            Evaluation.objects.values('assigned_to_user_id')
            .annotate(count=Count('evaluation_id'))
            .values_list('assigned_to_user_id', 'count')
        )
        
        return {
            'total_evaluations': total_evaluations,
            'submitted_evaluations': submitted_evaluations,
            'status_distribution': status_distribution,
            'avg_overall_score': round(avg_overall_score, 2),
            'avg_quality_score': round(avg_quality_score, 2),
            'avg_coverage_score': round(avg_coverage_score, 2),
            'avg_recovery_score': round(avg_recovery_score, 2),
            'avg_compliance_score': round(avg_compliance_score, 2),
            'score_distribution': score_distribution,
            'evaluator_performance': evaluator_performance
        }
        
    except Exception as e:
        logger.error(f"Error calculating evaluation metrics: {str(e)}")
        return {}


def get_testing_metrics():
    """Get testing and questionnaire metrics"""
    try:
        # Questionnaire metrics
        total_questionnaires = Questionnaire.objects.count()
        questionnaire_status_dist = dict(Questionnaire.objects.values('status').annotate(count=Count('questionnaire_id')).values_list('status', 'count'))
        questionnaire_type_dist = dict(Questionnaire.objects.values('plan_type').annotate(count=Count('questionnaire_id')).values_list('plan_type', 'count'))
        
        # Question metrics
        total_questions = Question.objects.count()
        question_type_dist = dict(Question.objects.values('answer_type').annotate(count=Count('question_id')).values_list('answer_type', 'count'))
        required_questions = Question.objects.filter(is_required=True).count()
        optional_questions = Question.objects.filter(is_required=False).count()
        
        # Test assignment metrics
        total_assignments = TestAssignmentsResponses.objects.count()
        assignment_status_dist = dict(TestAssignmentsResponses.objects.values('status').annotate(count=Count('questionnaire_id')).values_list('status', 'count'))
        owner_decision_dist = dict(TestAssignmentsResponses.objects.values('owner_decision').annotate(count=Count('questionnaire_id')).values_list('owner_decision', 'count'))
        
        # Success metrics
        approved_tests = TestAssignmentsResponses.objects.filter(owner_decision='APPROVED').count()
        rejected_tests = TestAssignmentsResponses.objects.filter(owner_decision='REJECTED').count()
        success_rate = (approved_tests / (approved_tests + rejected_tests) * 100) if (approved_tests + rejected_tests) > 0 else 0
        
        # Overdue assignments
        overdue_assignments = TestAssignmentsResponses.objects.filter(
            due_date__lt=timezone.now().date(),
            status__in=['ASSIGNED', 'IN_PROGRESS']
        ).count()
        
        return {
            'total_questionnaires': total_questionnaires,
            'questionnaire_status_dist': questionnaire_status_dist,
            'questionnaire_type_dist': questionnaire_type_dist,
            'total_questions': total_questions,
            'question_type_dist': question_type_dist,
            'required_questions': required_questions,
            'optional_questions': optional_questions,
            'total_assignments': total_assignments,
            'assignment_status_dist': assignment_status_dist,
            'owner_decision_dist': owner_decision_dist,
            'approved_tests': approved_tests,
            'rejected_tests': rejected_tests,
            'success_rate': round(success_rate, 2),
            'overdue_assignments': overdue_assignments
        }
        
    except Exception as e:
        logger.error(f"Error calculating testing metrics: {str(e)}")
        return {}


def get_approval_metrics():
    """Get approval workflow metrics"""
    try:
        # Basic counts
        total_approvals = BcpDrpApprovals.objects.count()
        
        # Status distribution
        status_distribution = dict(BcpDrpApprovals.objects.values('status').annotate(count=Count('approval_id')).values_list('status', 'count'))
        
        # Object type distribution
        object_type_dist = dict(BcpDrpApprovals.objects.values('object_type').annotate(count=Count('approval_id')).values_list('object_type', 'count'))
        
        # Plan type distribution
        plan_type_dist = dict(BcpDrpApprovals.objects.values('plan_type').annotate(count=Count('approval_id')).values_list('plan_type', 'count'))
        
        # Workflow distribution
        workflow_dist = dict(BcpDrpApprovals.objects.values('workflow_name').annotate(count=Count('approval_id')).values_list('workflow_name', 'count'))
        
        # Completion metrics
        completed_approvals = BcpDrpApprovals.objects.filter(status__in=['COMMENTED', 'SKIPPED']).count()
        completion_rate = (completed_approvals / total_approvals * 100) if total_approvals > 0 else 0
        
        # Overdue approvals
        overdue_approvals = BcpDrpApprovals.objects.filter(
            due_date__lt=timezone.now(),
            status='ASSIGNED'
        ).count()
        
        # Assignee performance
        assignee_performance = dict(
            BcpDrpApprovals.objects.values('assignee_id', 'assignee_name')
            .annotate(count=Count('approval_id'))
            .values_list('assignee_name', 'count')
        )
        
        return {
            'total_approvals': total_approvals,
            'status_distribution': status_distribution,
            'object_type_dist': object_type_dist,
            'plan_type_dist': plan_type_dist,
            'workflow_dist': workflow_dist,
            'completed_approvals': completed_approvals,
            'completion_rate': round(completion_rate, 2),
            'overdue_approvals': overdue_approvals,
            'assignee_performance': assignee_performance
        }
        
    except Exception as e:
        logger.error(f"Error calculating approval metrics: {str(e)}")
        return {}


def get_risk_metrics():
    """Get risk analysis metrics"""
    try:
        if not RISK_MODELS_AVAILABLE or Risk is None:
            logger.warning("Risk models not available, returning empty risk metrics")
            return {
                'total_risks': 0,
                'priority_distribution': {},
                'status_distribution': {},
                'type_distribution': {},
                'avg_score': 0,
                'avg_likelihood': 0,
                'avg_impact': 0,
                'avg_exposure': 0,
                'critical_risks': 0,
                'high_score_risks': 0,
                'mitigated_risks': 0,
                'open_risks': 0,
                'score_distribution': {}
            }
        
        # Basic counts
        total_risks = Risk.objects.count()
        
        # Priority distribution
        priority_distribution = dict(Risk.objects.values('priority').annotate(count=Count('id')).values_list('priority', 'count'))
        
        # Status distribution
        status_distribution = dict(Risk.objects.values('status').annotate(count=Count('id')).values_list('status', 'count'))
        
        # Type distribution
        type_distribution = dict(Risk.objects.values('risk_type').annotate(count=Count('id')).values_list('risk_type', 'count'))
        
        # Score metrics
        avg_score = Risk.objects.aggregate(avg=Avg('score'))['avg'] or 0
        avg_likelihood = Risk.objects.aggregate(avg=Avg('likelihood'))['avg'] or 0
        avg_impact = Risk.objects.aggregate(avg=Avg('impact'))['avg'] or 0
        avg_exposure = Risk.objects.aggregate(avg=Avg('exposure_rating'))['avg'] or 0
        
        # Critical risks
        critical_risks = Risk.objects.filter(priority='Critical').count()
        high_score_risks = Risk.objects.filter(score__gte=80).count()
        
        # Mitigation metrics
        mitigated_risks = Risk.objects.filter(status='Mitigated').count()
        open_risks = Risk.objects.filter(status='Open').count()
        
        # Score distribution
        score_distribution = Risk.objects.aggregate(
            critical=Count('id', filter=Q(score__gte=80)),
            high=Count('id', filter=Q(score__gte=60, score__lt=80)),
            medium=Count('id', filter=Q(score__gte=40, score__lt=60)),
            low=Count('id', filter=Q(score__lt=40))
        )
        
        return {
            'total_risks': total_risks,
            'priority_distribution': priority_distribution,
            'status_distribution': status_distribution,
            'type_distribution': type_distribution,
            'avg_score': round(avg_score, 2),
            'avg_likelihood': round(avg_likelihood, 2),
            'avg_impact': round(avg_impact, 2),
            'avg_exposure': round(avg_exposure, 2),
            'critical_risks': critical_risks,
            'high_score_risks': high_score_risks,
            'mitigated_risks': mitigated_risks,
            'open_risks': open_risks,
            'score_distribution': score_distribution
        }
        
    except Exception as e:
        logger.error(f"Error calculating risk metrics: {str(e)}")
        return {
            'total_risks': 0,
            'priority_distribution': {},
            'status_distribution': {},
            'type_distribution': {},
            'avg_score': 0,
            'avg_likelihood': 0,
            'avg_impact': 0,
            'avg_exposure': 0,
            'critical_risks': 0,
            'high_score_risks': 0,
            'mitigated_risks': 0,
            'open_risks': 0,
            'score_distribution': {}
        }


def get_user_metrics():
    """Get user activity metrics"""
    try:
        # Basic user counts
        total_users = Users.objects.count()
        active_users = Users.objects.filter(is_active='Y').count()
        
        # Department distribution
        department_dist = dict(Users.objects.values('department_id').annotate(count=Count('user_id')).values_list('department_id', 'count'))
        
        # Recent activity (last 30 days)
        recent_activity = Users.objects.filter(
            updated_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # User performance metrics
        plan_submissions = dict(
            Plan.objects.filter(submitted_by__isnull=False)
            .values('submitted_by')
            .annotate(count=Count('plan_id'))
            .values_list('submitted_by', 'count')
        )
        
        evaluation_completions = dict(
            Evaluation.objects.filter(status='SUBMITTED')
            .values('assigned_to_user_id')
            .annotate(count=Count('evaluation_id'))
            .values_list('assigned_to_user_id', 'count')
        )
        
        test_assignments = dict(
            TestAssignmentsResponses.objects.values('assigned_to_user_id')
            .annotate(count=Count('questionnaire_id'))
            .values_list('assigned_to_user_id', 'count')
        )
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'department_dist': department_dist,
            'recent_activity': recent_activity,
            'plan_submissions': plan_submissions,
            'evaluation_completions': evaluation_completions,
            'test_assignments': test_assignments
        }
        
    except Exception as e:
        logger.error(f"Error calculating user metrics: {str(e)}")
        return {}


def get_temporal_metrics(tenant_id=None):
    """Get time-based analysis metrics
    MULTI-TENANCY: Optionally filter by tenant_id
    """
    try:
        # Build base filters with date range
        date_filter = Q(submitted_at__gte=timezone.now() - timedelta(days=365))
        if tenant_id:
            date_filter = date_filter & Q(tenant_id=tenant_id)
        
        # Monthly plan submissions (last 12 months)
        monthly_plans = Plan.objects.filter(date_filter).extra(
            select={'month': 'DATE_FORMAT(submitted_at, "%%Y-%%m")'}
        ).values('month').annotate(count=Count('plan_id')).order_by('month')
        
        # Monthly evaluations (last 12 months)
        eval_filter = Q(submitted_at__gte=timezone.now() - timedelta(days=365), status='SUBMITTED')
        if tenant_id:
            eval_filter = eval_filter & Q(tenant_id=tenant_id)
        monthly_evaluations = Evaluation.objects.filter(eval_filter).extra(
            select={'month': 'DATE_FORMAT(submitted_at, "%%Y-%%m")'}
        ).values('month').annotate(count=Count('evaluation_id')).order_by('month')
        
        # Monthly test completions (last 12 months)
        test_filter = Q(submitted_at__gte=timezone.now() - timedelta(days=365), status='SUBMITTED')
        if tenant_id:
            test_filter = test_filter & Q(tenant_id=tenant_id)
        monthly_tests = TestAssignmentsResponses.objects.filter(test_filter).extra(
            select={'month': 'DATE_FORMAT(submitted_at, "%%Y-%%m")'}
        ).values('month').annotate(count=Count('questionnaire_id')).order_by('month')
        
        # Monthly risk creation (last 12 months) - include NULL tenant_id for backward compatibility
        if RISK_MODELS_AVAILABLE and Risk:
            risk_filter = Q(created_at__gte=timezone.now() - timedelta(days=365))
            if tenant_id:
                risk_filter = risk_filter & (Q(tenant_id=tenant_id) | Q(tenant_id__isnull=True))
            monthly_risks = Risk.objects.filter(risk_filter).extra(
                select={'month': 'DATE_FORMAT(created_at, "%%Y-%%m")'}
            ).values('month').annotate(count=Count('id')).order_by('month')
        else:
            monthly_risks = []
        
        return {
            'monthly_plans': list(monthly_plans),
            'monthly_evaluations': list(monthly_evaluations),
            'monthly_tests': list(monthly_tests),
            'monthly_risks': list(monthly_risks)
        }
        
    except Exception as e:
        logger.error(f"Error calculating temporal metrics: {str(e)}", exc_info=True)
        return {
            'monthly_plans': [],
            'monthly_evaluations': [],
            'monthly_tests': [],
            'monthly_risks': []
        }


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def dashboard_plan_metrics(request):
    """Get detailed plan metrics"""
    try:
        metrics = get_plan_metrics()
        return success_response(metrics)
    except Exception as e:
        logger.error(f"Error fetching plan metrics: {str(e)}")
        return error_response("Failed to fetch plan metrics", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def dashboard_evaluation_metrics(request):
    """Get detailed evaluation metrics"""
    try:
        metrics = get_evaluation_metrics()
        return success_response(metrics)
    except Exception as e:
        logger.error(f"Error fetching evaluation metrics: {str(e)}")
        return error_response("Failed to fetch evaluation metrics", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def dashboard_testing_metrics(request):
    """Get detailed testing metrics"""
    try:
        metrics = get_testing_metrics()
        return success_response(metrics)
    except Exception as e:
        logger.error(f"Error fetching testing metrics: {str(e)}")
        return error_response("Failed to fetch testing metrics", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def dashboard_risk_metrics(request):
    """Get detailed risk metrics"""
    try:
        metrics = get_risk_metrics()
        return success_response(metrics)
    except Exception as e:
        logger.error(f"Error fetching risk metrics: {str(e)}")
        return error_response("Failed to fetch risk metrics", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def dashboard_temporal_metrics(request):
    """Get temporal analysis metrics
    MULTI-TENANCY: Filters by tenant_id
    """
    try:
        # MULTI-TENANCY: Get tenant_id from request
        from tprm_backend.core.tenant_utils import get_tenant_id_from_request
        tenant_id = get_tenant_id_from_request(request)
        metrics = get_temporal_metrics(tenant_id=tenant_id)
        return success_response(metrics)
    except Exception as e:
        logger.error(f"Error fetching temporal metrics: {str(e)}", exc_info=True)
        return error_response("Failed to fetch temporal metrics", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def dashboard_kpi_metrics(request):
    """Get KPI-specific metrics for the KPI Dashboard"""
    try:
        logger.info("Starting KPI metrics collection")
        
        # Get all metrics
        plan_metrics = get_plan_metrics()
        evaluation_metrics = get_evaluation_metrics()
        testing_metrics = get_testing_metrics()
        approval_metrics = get_approval_metrics()
        risk_metrics = get_risk_metrics()
        user_metrics = get_user_metrics()
        temporal_metrics = get_temporal_metrics()
        compliance_metrics = get_compliance_metrics()
        
        # Calculate KPI-specific metrics
        kpi_metrics = {
            # Plan KPIs
            'plan_approval_rate': plan_metrics.get('approval_rate', 0),
            'avg_ocr_time': calculate_avg_ocr_time(),
            
            # Testing KPIs
            'test_approval_rate': testing_metrics.get('success_rate', 0),
            'avg_answer_time': calculate_avg_answer_time(),
            
            # Evaluation KPIs
            'evaluation_time': calculate_avg_evaluation_time(),
            
            # Risk KPIs
            'total_risks': risk_metrics.get('total_risks', 0),
            'critical_risks': risk_metrics.get('critical_risks', 0),
            
            # User Activity KPIs
            'active_users': user_metrics.get('active_users', 0),
            'recent_activity': user_metrics.get('recent_activity', 0),
            
            # Temporal KPIs
            'monthly_trends': temporal_metrics,
            
            # Performance KPIs
            'overdue_approvals': approval_metrics.get('overdue_approvals', 0),
            'overdue_assignments': testing_metrics.get('overdue_assignments', 0),
            'completion_rates': {
                'plans': plan_metrics.get('approval_rate', 0),
                'evaluations': calculate_evaluation_completion_rate(),
                'tests': testing_metrics.get('success_rate', 0),
                'approvals': approval_metrics.get('completion_rate', 0)
            },
            
            # Compliance KPIs
            'compliance_metrics': compliance_metrics
        }
        
        logger.info("KPI metrics collection completed successfully")
        return success_response(kpi_metrics)
        
    except Exception as e:
        logger.error(f"Error fetching KPI metrics: {str(e)}", exc_info=True)
        return error_response(f"Failed to fetch KPI metrics: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('view_plans')
def dashboard_evaluation_scores_metrics(request):
    """Get comprehensive evaluation scores metrics for KPI Dashboard"""
    try:
        logger.info("Starting evaluation scores metrics collection")
        
        # Get basic evaluation metrics
        evaluation_metrics = get_evaluation_metrics()
        
        # Calculate additional score breakdown metrics
        score_breakdown = get_evaluation_score_breakdown()
        
        # Calculate weighted score distribution
        weighted_distribution = get_weighted_score_distribution()
        
        # Combine all metrics
        evaluation_scores_metrics = {
            # Overall scores
            'avg_overall_score': evaluation_metrics.get('avg_overall_score', 0),
            'avg_quality_score': evaluation_metrics.get('avg_quality_score', 0),
            'avg_coverage_score': evaluation_metrics.get('avg_coverage_score', 0),
            'avg_recovery_score': evaluation_metrics.get('avg_recovery_score', 0),
            'avg_compliance_score': evaluation_metrics.get('avg_compliance_score', 0),
            
            # Score distribution
            'score_distribution': evaluation_metrics.get('score_distribution', {}),
            'weighted_distribution': weighted_distribution,
            
            # Score breakdown
            'score_breakdown': score_breakdown,
            
            # Total counts
            'total_evaluations': evaluation_metrics.get('total_evaluations', 0),
            'submitted_evaluations': evaluation_metrics.get('submitted_evaluations', 0),
            
            # Status distribution
            'status_distribution': evaluation_metrics.get('status_distribution', {}),
            
            # Evaluator performance
            'evaluator_performance': evaluation_metrics.get('evaluator_performance', {}),
            
            'last_updated': timezone.now().isoformat()
        }
        
        logger.info("Evaluation scores metrics collection completed successfully")
        return success_response(evaluation_scores_metrics)
        
    except Exception as e:
        logger.error(f"Error fetching evaluation scores metrics: {str(e)}", exc_info=True)
        return error_response(f"Failed to fetch evaluation scores metrics: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


def calculate_avg_ocr_time():
    """Calculate average OCR processing time in hours"""
    try:
        from datetime import datetime
        
        # Get plans with OCR completed
        plans = Plan.objects.filter(
            ocr_extracted=True,
            ocr_extracted_at__isnull=False,
            submitted_at__isnull=False
        ).values_list('ocr_extracted_at', 'submitted_at')
        
        if not plans:
            return 0
        
        # Calculate time differences in Python
        total_hours = 0
        count = 0
        
        for ocr_time, submitted_time in plans:
            if ocr_time and submitted_time:
                # Calculate difference in hours
                time_diff = ocr_time - submitted_time
                hours = time_diff.total_seconds() / 3600
                total_hours += hours
                count += 1
        
        if count > 0:
            return round(total_hours / count, 1)
        else:
            return 0
            
    except Exception as e:
        logger.error(f"Error calculating average OCR time: {str(e)}")
        return 0




def calculate_avg_answer_time():
    """Calculate average answer time in hours"""
    try:
        from datetime import datetime
        
        # Get test assignments with answers submitted
        assignments = TestAssignmentsResponses.objects.filter(
            status='SUBMITTED',
            submitted_at__isnull=False,
            assigned_at__isnull=False
        ).values_list('submitted_at', 'assigned_at')
        
        if not assignments:
            return 0
        
        # Calculate time differences in Python
        total_hours = 0
        count = 0
        
        for submitted_time, assigned_time in assignments:
            if submitted_time and assigned_time:
                # Calculate difference in hours
                time_diff = submitted_time - assigned_time
                hours = time_diff.total_seconds() / 3600
                total_hours += hours
                count += 1
        
        if count > 0:
            return round(total_hours / count, 1)
        else:
            return 0
            
    except Exception as e:
        logger.error(f"Error calculating average answer time: {str(e)}")
        return 0




def calculate_avg_evaluation_time():
    """Calculate average evaluation completion time in days"""
    try:
        from datetime import datetime
        
        # Get evaluations that have been submitted
        evaluations = Evaluation.objects.filter(
            status='SUBMITTED',
            submitted_at__isnull=False,
            assigned_at__isnull=False
        ).values_list('submitted_at', 'assigned_at')
        
        if not evaluations:
            return 0
        
        # Calculate time differences in Python
        total_days = 0
        count = 0
        
        for submitted_time, assigned_time in evaluations:
            if submitted_time and assigned_time:
                # Calculate difference in days
                time_diff = submitted_time - assigned_time
                days = time_diff.total_seconds() / 86400
                total_days += days
                count += 1
        
        if count > 0:
            return round(total_days / count, 1)
        else:
            return 0
            
    except Exception as e:
        logger.error(f"Error calculating average evaluation time: {str(e)}")
        return 0




def calculate_evaluation_completion_rate():
    """Calculate evaluation completion rate percentage"""
    try:
        total_evaluations = Evaluation.objects.count()
        completed_evaluations = Evaluation.objects.filter(status='SUBMITTED').count()
        
        if total_evaluations > 0:
            return round((completed_evaluations / total_evaluations) * 100, 1)
        return 0
    except Exception as e:
        logger.error(f"Error calculating evaluation completion rate: {str(e)}")
        return 0


def get_compliance_metrics():
    """Get compliance-specific metrics based on compliance_score field"""
    try:
        from django.db.models import Count, Avg, Case, When, Q
        
        # Compliance score distribution by ranges
        compliance_distribution = Evaluation.objects.aggregate(
            excellent_90_100=Count('evaluation_id', filter=Q(compliance_score__gte=90, compliance_score__lte=100)),
            good_80_89=Count('evaluation_id', filter=Q(compliance_score__gte=80, compliance_score__lt=90)),
            fair_70_79=Count('evaluation_id', filter=Q(compliance_score__gte=70, compliance_score__lt=80)),
            poor_below_70=Count('evaluation_id', filter=Q(compliance_score__lt=70, compliance_score__isnull=False)),
            no_score=Count('evaluation_id', filter=Q(compliance_score__isnull=True))
        )
        
        # Average compliance score
        avg_compliance_score = Evaluation.objects.filter(
            compliance_score__isnull=False
        ).aggregate(avg_score=Avg('compliance_score'))
        
        # Plans meeting compliance threshold (>= 80)
        plans_meeting_threshold = Evaluation.objects.filter(
            compliance_score__gte=80,
            compliance_score__isnull=False
        ).count()
        
        # Total plans with compliance scores
        total_plans_with_scores = Evaluation.objects.filter(
            compliance_score__isnull=False
        ).count()
        
        # Compliance rate (plans meeting threshold / total plans with scores)
        compliance_rate = 0
        if total_plans_with_scores > 0:
            compliance_rate = round((plans_meeting_threshold / total_plans_with_scores) * 100, 1)
        
        return {
            'compliance_score_distribution': {
                'excellent_90_100': compliance_distribution['excellent_90_100'] or 0,
                'good_80_89': compliance_distribution['good_80_89'] or 0,
                'fair_70_79': compliance_distribution['fair_70_79'] or 0,
                'poor_below_70': compliance_distribution['poor_below_70'] or 0,
                'no_score': compliance_distribution['no_score'] or 0
            },
            'average_compliance_score': round(avg_compliance_score['avg_score'] or 0, 2),
            'plans_meeting_threshold': plans_meeting_threshold,
            'total_plans_with_scores': total_plans_with_scores,
            'compliance_rate': compliance_rate
        }
        
    except Exception as e:
        logger.error(f"Error calculating compliance metrics: {str(e)}")
        return {
            'compliance_score_distribution': {
                'excellent_90_100': 0,
                'good_80_89': 0,
                'fair_70_79': 0,
                'poor_below_70': 0,
                'no_score': 0
            },
            'average_compliance_score': 0,
            'plans_meeting_threshold': 0,
            'total_plans_with_scores': 0,
            'compliance_rate': 0
        }


def get_evaluation_score_breakdown():
    """Get detailed score breakdown metrics"""
    try:
        # Score ranges for distribution
        score_breakdown = Evaluation.objects.aggregate(
            excellent_90_100=Count('evaluation_id', filter=Q(overall_score__gte=90)),
            good_80_89=Count('evaluation_id', filter=Q(overall_score__gte=80, overall_score__lt=90)),
            fair_70_79=Count('evaluation_id', filter=Q(overall_score__gte=70, overall_score__lt=80)),
            poor_below_70=Count('evaluation_id', filter=Q(overall_score__lt=70, overall_score__isnull=False)),
            no_score=Count('evaluation_id', filter=Q(overall_score__isnull=True))
        )
        
        # Individual score averages
        score_averages = Evaluation.objects.aggregate(
            avg_quality=Avg('quality_score'),
            avg_coverage=Avg('coverage_score'),
            avg_recovery=Avg('recovery_capability_score'),
            avg_compliance=Avg('compliance_score'),
            avg_overall=Avg('overall_score')
        )
        
        # Score trends (last 6 months)
        six_months_ago = timezone.now() - timedelta(days=180)
        recent_scores = Evaluation.objects.filter(
            submitted_at__gte=six_months_ago,
            overall_score__isnull=False
        ).aggregate(avg_recent=Avg('overall_score'))
        
        return {
            'distribution': score_breakdown,
            'averages': {
                'quality': round(score_averages['avg_quality'] or 0, 2),
                'coverage': round(score_averages['avg_coverage'] or 0, 2),
                'recovery': round(score_averages['avg_recovery'] or 0, 2),
                'compliance': round(score_averages['avg_compliance'] or 0, 2),
                'overall': round(score_averages['avg_overall'] or 0, 2),
                'recent_trend': round(recent_scores['avg_recent'] or 0, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating evaluation score breakdown: {str(e)}")
        return {
            'distribution': {},
            'averages': {
                'quality': 0,
                'coverage': 0,
                'recovery': 0,
                'compliance': 0,
                'overall': 0,
                'recent_trend': 0
            }
        }


def get_weighted_score_distribution():
    """Get weighted score distribution based on the metrics documentation"""
    try:
        # Calculate weighted scores if they exist, otherwise use overall_score
        weighted_distribution = Evaluation.objects.extra(
            select={
                'weighted_range': """
                    CASE 
                        WHEN overall_score >= 90 THEN '90-100'
                        WHEN overall_score >= 80 THEN '80-89'
                        WHEN overall_score >= 70 THEN '70-79'
                        WHEN overall_score >= 60 THEN '60-69'
                        ELSE 'Below 60'
                    END
                """
            }
        ).values('weighted_range').annotate(
            count=Count('evaluation_id')
        ).order_by('weighted_range')
        
        # Convert to dictionary for easier frontend consumption
        distribution_dict = {}
        for item in weighted_distribution:
            distribution_dict[item['weighted_range']] = item['count']
        
        # Calculate percentages
        total_evaluations = sum(distribution_dict.values())
        if total_evaluations > 0:
            distribution_percentages = {
                range_name: round((count / total_evaluations) * 100, 1)
                for range_name, count in distribution_dict.items()
            }
        else:
            distribution_percentages = {}
        
        return {
            'counts': distribution_dict,
            'percentages': distribution_percentages,
            'total': total_evaluations
        }
        
    except Exception as e:
        logger.error(f"Error calculating weighted score distribution: {str(e)}")
        return {
            'counts': {},
            'percentages': {},
            'total': 0
        }


@api_view(['GET'])
def dashboard_test(request):
    """Simple test endpoint to verify API is working"""
    try:
        return success_response({
            'message': 'Dashboard API is working',
            'timestamp': timezone.now().isoformat(),
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error in dashboard test endpoint: {str(e)}")
        return error_response("Dashboard test failed", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def dashboard_debug(request):
    """Debug endpoint without authentication to test basic connectivity"""
    try:
        return Response({
            'message': 'Dashboard API is accessible',
            'timestamp': timezone.now().isoformat(),
            'status': 'success',
            'debug': True
        })
    except Exception as e:
        logger.error(f"Error in dashboard debug endpoint: {str(e)}")
        return Response({
            'error': 'Dashboard debug failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def dashboard_db_test(request):
    """Test database connectivity and basic queries"""
    try:
        # Test basic database queries
        total_plans = Plan.objects.count()
        total_evaluations = Evaluation.objects.count()
        total_questionnaires = Questionnaire.objects.count()
        total_assignments = TestAssignmentsResponses.objects.count()
        total_approvals = BcpDrpApprovals.objects.count()
        total_users = Users.objects.count()
        
        return Response({
            'message': 'Database connectivity test successful',
            'timestamp': timezone.now().isoformat(),
            'status': 'success',
            'database_counts': {
                'plans': total_plans,
                'evaluations': total_evaluations,
                'questionnaires': total_questionnaires,
                'assignments': total_assignments,
                'approvals': total_approvals,
                'users': total_users
            }
        })
    except Exception as e:
        logger.error(f"Error in database test endpoint: {str(e)}")
        return Response({
            'error': 'Database test failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

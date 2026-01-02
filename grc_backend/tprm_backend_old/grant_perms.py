from tprm_backend.rbac.models import RBACTPRM
from tprm_backend.mfa_auth.models import User

username = 'testuser1'
user = User.objects.get(username=username)
rbac, created = RBACTPRM.objects.get_or_create(user_id=user.userid, defaults={'username': username, 'role': 'Admin'})
for field in ['create_bcp_drp_strategy_and_plans', 'view_plans_and_documents', 'assign_plans_for_evaluation', 'approve_or_reject_plan_evaluations', 'ocr_extraction_and_review', 'view_bcp_drp_plan_status', 'create_questionnaire_for_testing', 'review_questionnaire_answers', 'final_approval_of_plan', 'create_questionnaire', 'assign_questionnaires_for_review', 'view_all_questionnaires']:
    setattr(rbac, field, True)
rbac.is_active = 'Y'
rbac.save()
print(f"✓ Granted BCP/DRP permissions to {username} (user_id={user.userid}, role={rbac.role})")
print(f"✓ view_plans_and_documents: {rbac.view_plans_and_documents}")
print(f"✓ approve_or_reject_plan_evaluations: {rbac.approve_or_reject_plan_evaluations}")


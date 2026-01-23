"""
AI Database Service for auditor assignment recommendations
"""
import logging
from django.db import connection
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class AIDatabaseService:
    """Database service for AI recommendation system"""
    
    def __init__(self):
        self.logger = logger
    
    def execute_query(self, query: str, params: tuple = (), fetch_results: bool = True) -> List[Dict[str, Any]]:
        """Execute a database query and return results"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                if fetch_results:
                    columns = [col[0] for col in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                return []
        except Exception as e:
            self.logger.error(f"Database query error: {str(e)}")
            return []
    
    def get_users_for_recommendations(self) -> List[Dict[str, Any]]:
        """Get all users available for auditor/reviewer assignment"""
        query = """
        SELECT 
            UserId,
            UserName,
            Email,
            DepartmentId as Department,
            FirstName,
            LastName,
            IsActive as Status
        FROM users 
        WHERE IsActive = 'Y'
        ORDER BY UserName
        """
        return self.execute_query(query)
    
    def get_user_audit_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Get audit history for a specific user"""
        query = """
        SELECT 
            a.AuditId,
            a.Title as AuditTitle,
            a.AuditType,
            a.Status,
            a.CompletionDate,
            a.ReviewStatus,
            a.BusinessUnit,
            a.Scope,
            a.Objective,
            f.FrameworkName,
            p.PolicyName,
            sp.SubPolicyName,
            CASE 
                WHEN a.Auditor = %s THEN 'Auditor'
                WHEN a.Reviewer = %s THEN 'Reviewer'
                WHEN a.Assignee = %s THEN 'Assignee'
                ELSE 'Other'
            END as AssignedRole
        FROM audit a
        LEFT JOIN frameworks f ON a.FrameworkId = f.FrameworkId
        LEFT JOIN policies p ON a.PolicyId = p.PolicyId
        LEFT JOIN subpolicies sp ON a.SubPolicyId = sp.SubPolicyId
        WHERE a.Auditor = %s OR a.Reviewer = %s OR a.Assignee = %s
        ORDER BY a.AssignedDate DESC
        LIMIT 20
        """
        return self.execute_query(query, (user_id, user_id, user_id, user_id, user_id, user_id))
    
    def get_audit_performance_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get performance metrics for a user based on audit history"""
        query = """
        SELECT 
            COUNT(*) as total_audits,
            SUM(CASE WHEN a.Status = 2 THEN 1 ELSE 0 END) as completed_audits,
            SUM(CASE WHEN a.Status = 1 THEN 1 ELSE 0 END) as in_progress_audits,
            SUM(CASE WHEN a.ReviewStatus = 1 THEN 1 ELSE 0 END) as approved_audits,
            AVG(CASE 
                WHEN a.CompletionDate IS NOT NULL AND a.AssignedDate IS NOT NULL 
                THEN DATEDIFF(a.CompletionDate, a.AssignedDate) 
                ELSE NULL 
            END) as avg_completion_days,
            COUNT(DISTINCT a.FrameworkId) as frameworks_worked,
            COUNT(DISTINCT a.AuditType) as audit_types_worked
        FROM audit a
        WHERE a.Auditor = %s OR a.Reviewer = %s OR a.Assignee = %s
        """
        result = self.execute_query(query, (user_id, user_id, user_id))
        return result[0] if result else {}
    
    def get_user_skills_from_audits(self, user_id: int) -> List[str]:
        """Extract skills from user's audit history"""
        query = """
        SELECT DISTINCT 
            f.FrameworkName,
            p.PolicyName,
            sp.SubPolicyName,
            a.Scope,
            a.Title
        FROM audit a
        LEFT JOIN frameworks f ON a.FrameworkId = f.FrameworkId
        LEFT JOIN policies p ON a.PolicyId = p.PolicyId
        LEFT JOIN subpolicies sp ON a.SubPolicyId = sp.SubPolicyId
        WHERE (a.Auditor = %s OR a.Reviewer = %s OR a.Assignee = %s)
        AND a.Status = 2
        """
        results = self.execute_query(query, (user_id, user_id, user_id))
        
        skills = set()
        for result in results:
            if result['FrameworkName']:
                skills.add(result['FrameworkName'])
            if result['PolicyName']:
                skills.add(result['PolicyName'])
            if result['Scope']:
                skills.add(result['Scope'])
            if result['Title']:
                skills.add(result['Title'])
        
        return list(skills)
    
    def get_training_data_for_ml(self) -> List[Dict[str, Any]]:
        """Get comprehensive training data for ML model"""
        query = """
        SELECT 
            a.AuditId,
            a.Title,
            a.Scope,
            a.AuditType,
            a.Status,
            a.ReviewStatus,
            a.CompletionDate,
            a.AssignedDate,
            a.Auditor,
            a.Reviewer,
            a.Assignee,
            f.FrameworkName,
            p.PolicyName,
            sp.SubPolicyName,
            u_auditor.UserName as AuditorName,
            u_reviewer.UserName as ReviewerName,
            u_assignee.UserName as AssigneeName,
            u_auditor.DepartmentId as AuditorDept,
            u_reviewer.DepartmentId as ReviewerDept,
            u_assignee.DepartmentId as AssigneeDept,
            CASE 
                WHEN a.Status = 2 AND a.ReviewStatus = 1 THEN 1
                ELSE 0
            END as success_score,
            CASE 
                WHEN a.CompletionDate IS NOT NULL AND a.AssignedDate IS NOT NULL 
                THEN DATEDIFF(a.CompletionDate, a.AssignedDate) 
                ELSE NULL 
            END as completion_days
        FROM audit a
        LEFT JOIN frameworks f ON a.FrameworkId = f.FrameworkId
        LEFT JOIN policies p ON a.PolicyId = p.PolicyId
        LEFT JOIN subpolicies sp ON a.SubPolicyId = sp.SubPolicyId
        LEFT JOIN users u_auditor ON a.Auditor = u_auditor.UserId
        LEFT JOIN users u_reviewer ON a.Reviewer = u_reviewer.UserId
        LEFT JOIN users u_assignee ON a.Assignee = u_assignee.UserId
        WHERE a.AssignedDate IS NOT NULL
        ORDER BY a.AssignedDate DESC
        LIMIT 1000
        """
        return self.execute_query(query)
    
    def get_user_skills(self, user_id: int) -> List[str]:
        """Get skills for a specific user"""
        query = """
        SELECT Skills FROM users WHERE UserId = %s
        """
        result = self.execute_query(query, (user_id,))
        if result and result[0].get('Skills'):
            return result[0]['Skills'].split(',')
        return []
    
    def get_ai_system_status(self) -> Dict[str, Any]:
        """Get AI system status and health metrics"""
        try:
            # Check database connectivity
            user_count = self.execute_query("SELECT COUNT(*) as count FROM users")[0]['count']
            
            return {
                'database_connected': True,
                'user_count': user_count,
                'status': 'healthy',
                'last_updated': '2024-01-01T00:00:00Z'
            }
        except Exception as e:
            return {
                'database_connected': False,
                'error': str(e),
                'status': 'error'
            }

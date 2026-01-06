from django.db import models
from django.utils import timezone
from django.conf import settings


class SLAApproval(models.Model):
    """Model for SLA approval workflow"""
    
    OBJECT_TYPE_CHOICES = [
        ('SLA_CREATION', 'SLA Creation'),
        ('SLA_AMENDMENT', 'SLA Amendment'),
        ('SLA_RENEWAL', 'SLA Renewal'),
        ('SLA_TERMINATION', 'SLA Termination'),
    ]
    
    STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMMENTED', 'Commented'),
        ('SKIPPED', 'Skipped'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]
    
    APPROVAL_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    approval_id = models.AutoField(primary_key=True)
    sla_id = models.BigIntegerField(help_text="ID of the SLA being approved")
    workflow_id = models.IntegerField(help_text="ID of the workflow")
    workflow_name = models.CharField(max_length=255, help_text="Name of the workflow")
    assigner_id = models.IntegerField(help_text="ID of the user who assigned the approval")
    assigner_name = models.CharField(max_length=255, help_text="Name of the user who assigned the approval")
    assignee_id = models.IntegerField(help_text="ID of the user assigned to approve")
    assignee_name = models.CharField(max_length=255, help_text="Name of the user assigned to approve")
    object_type = models.CharField(max_length=20, choices=OBJECT_TYPE_CHOICES, help_text="Type of SLA operation")
    assigned_date = models.DateTimeField(default=timezone.now, help_text="Date when approval was assigned")
    due_date = models.DateTimeField(help_text="Due date for approval")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED', help_text="Current status of the approval")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM', help_text="Priority level of the approval")
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='PENDING', help_text="Overall approval status")
    comment_text = models.TextField(blank=True, null=True, help_text="Comments on the approval")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sla_approvals'
        ordering = ['-created_at']
        verbose_name = 'SLA Approval'
        verbose_name_plural = 'SLA Approvals'
    
    def __str__(self):
        return f"SLA Approval {self.approval_id} - {self.workflow_name}"
    
    def is_overdue(self):
        """Check if the approval is overdue"""
        return self.status in ['ASSIGNED', 'IN_PROGRESS'] and timezone.now() > self.due_date
    
    def get_sla(self):
        """Get the associated SLA object"""
        try:
            from slas.models import VendorSLA
            return VendorSLA.objects.get(sla_id=self.sla_id)
        except:
            return None
    
    def get_assigner_user(self):
        """Get the assigner user object"""
        # Return basic user info without MFA dependency
        return {
            'userid': self.assigner_id,
            'username': self.assigner_name,
            'full_name': self.assigner_name
        }
    
    def get_assignee_user(self):
        """Get the assignee user object"""
        # Return basic user info without MFA dependency
        return {
            'userid': self.assignee_id,
            'username': self.assignee_name,
            'full_name': self.assignee_name
        }

"""
User models for Vendor Guard Hub.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    """
    USER_TYPE_CHOICES = [
        ('internal', 'Internal User'),
        ('vendor', 'Vendor User'),
        ('admin', 'Administrator'),
    ]
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='internal',
        help_text=_('Type of user')
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text=_('Phone number')
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Department or team')
    )
    
    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Job position or title')
    )
    
    is_reviewer = models.BooleanField(
        default=False,
        help_text=_('Whether this user can review SLAs')
    )
    
    review_level = models.CharField(
        max_length=20,
        choices=[
            ('manager', 'Manager'),
            ('senior-manager', 'Senior Manager'),
            ('director', 'Director'),
            ('executive', 'Executive'),
            ('c-level', 'C-Level'),
        ],
        blank=True,
        null=True,
        help_text=_('Review level for SLA workflows')
    )
    
    sla_types = models.JSONField(
        default=list,
        blank=True,
        help_text=_('SLA types this user can review')
    )
    
    auto_escalation = models.BooleanField(
        default=True,
        help_text=_('Whether to auto-escalate reviews')
    )
    
    escalation_hours = models.PositiveIntegerField(
        default=24,
        help_text=_('Hours before escalation')
    )
    
    escalation_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='escalation_recipients',
        help_text=_('User to escalate to')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return self.get_full_name() or self.username


class UserProfile(models.Model):
    """
    Extended user profile information.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text=_('User avatar image')
    )
    
    bio = models.TextField(
        blank=True,
        help_text=_('User biography or description')
    )
    
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text=_('User timezone')
    )
    
    notification_preferences = models.JSONField(
        default=dict,
        help_text=_('Notification preferences')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"Profile for {self.user.username}"


class UserSession(models.Model):
    """
    Track user sessions for audit purposes.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session for {self.user.username} at {self.created_at}"

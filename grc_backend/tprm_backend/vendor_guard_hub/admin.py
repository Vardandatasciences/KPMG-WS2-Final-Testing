"""
Django admin configuration for Vendor Guard Hub.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from tprm_backend.users.models import User, UserProfile, UserSession

# Register custom user model
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
admin.site.register(UserSession)

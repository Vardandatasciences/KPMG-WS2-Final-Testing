from rest_framework import permissions


class IsRFPCreatorOrReviewer(permissions.BasePermission):
    """
    Custom permission to only allow creators or assigned reviewers to access an RFP.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow read access to any authenticated user with proper role
        if request.method in permissions.SAFE_METHODS:
            return (
                # Creator can view
                obj.created_by == request.user or
                # Primary reviewer can view
                obj.primary_reviewer_id == request.user.id or
                # Executive reviewer can view
                obj.executive_reviewer_id == request.user.id or
                # Superuser can view
                request.user.is_superuser
            )
        
        # For write operations:
        # - Draft RFPs can only be modified by their creators or superusers
        if obj.status == 'DRAFT':
            return obj.created_by == request.user or request.user.is_superuser
        
        # - RFPs in review can be approved/rejected by reviewers or superusers
        elif obj.status == 'IN_REVIEW':
            return (
                obj.primary_reviewer_id == request.user.id or
                obj.executive_reviewer_id == request.user.id or
                request.user.is_superuser
            )
        
        # - Published or later stage RFPs can only be modified by superusers
        return request.user.is_superuser

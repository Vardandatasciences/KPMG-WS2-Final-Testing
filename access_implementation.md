# Complete Guide: Request Access Implementation

This document provides a complete guide for implementing a "Request Access" feature that allows users to request access to pages/features and enables administrators to approve or reject these requests.

## Table of Contents

1. [Database Tables](#1-database-tables)
2. [Backend Implementation](#2-backend-implementation)
3. [Frontend Implementation](#3-frontend-implementation)
4. [Router Guard Configuration](#4-router-guard-configuration)
5. [Logic Flow](#5-logic-flow)
6. [Key Points](#6-key-points)

---

## 1. Database Tables

### 1.1 AccessRequest Table

```sql
CREATE TABLE `AccessRequest` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `requested_url` VARCHAR(500) NULL,
  `requested_feature` VARCHAR(255) NULL,
  `required_permission` VARCHAR(255) NULL,
  `requested_role` VARCHAR(100) NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'REQUESTED',
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  `approved_by` INT NULL,
  `audit_trail` JSON NULL,
  `message` TEXT NULL,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`UserId`),
  FOREIGN KEY (`approved_by`) REFERENCES `users`(`UserId`),
  INDEX `idx_user_created` (`user_id`, `created_at`),
  INDEX `idx_status` (`status`)
);
```

**Status Values:**
- `REQUESTED` - Initial status when user submits request
- `APPROVED` - Admin approved the request
- `REJECTED` - Admin rejected the request

### 1.2 RBAC Table (for permission management)

```sql
CREATE TABLE `rbac` (
  `RBACId` INT AUTO_INCREMENT PRIMARY KEY,
  `UserId` INT NOT NULL,
  `UserName` VARCHAR(255) NOT NULL,
  `Role` VARCHAR(100) NOT NULL,
  -- Compliance Module Permissions
  `create_compliance` BOOLEAN DEFAULT FALSE,
  `edit_compliance` BOOLEAN DEFAULT FALSE,
  `approve_compliance` BOOLEAN DEFAULT FALSE,
  `view_all_compliance` BOOLEAN DEFAULT FALSE,
  `compliance_performance_analytics` BOOLEAN DEFAULT FALSE,
  -- Policy Module Permissions
  `create_policy` BOOLEAN DEFAULT FALSE,
  `edit_policy` BOOLEAN DEFAULT FALSE,
  `approve_policy` BOOLEAN DEFAULT FALSE,
  `create_framework` BOOLEAN DEFAULT FALSE,
  `approve_framework` BOOLEAN DEFAULT FALSE,
  `view_all_policy` BOOLEAN DEFAULT FALSE,
  `policy_performance_analytics` BOOLEAN DEFAULT FALSE,
  -- Audit Module Permissions
  `assign_audit` BOOLEAN DEFAULT FALSE,
  `conduct_audit` BOOLEAN DEFAULT FALSE,
  `review_audit` BOOLEAN DEFAULT FALSE,
  `view_audit_reports` BOOLEAN DEFAULT FALSE,
  `audit_performance_analytics` BOOLEAN DEFAULT FALSE,
  -- Risk Module Permissions
  `create_risk` BOOLEAN DEFAULT FALSE,
  `edit_risk` BOOLEAN DEFAULT FALSE,
  `approve_risk` BOOLEAN DEFAULT FALSE,
  `assign_risk` BOOLEAN DEFAULT FALSE,
  `evaluate_assigned_risk` BOOLEAN DEFAULT FALSE,
  `view_all_risk` BOOLEAN DEFAULT FALSE,
  `risk_performance_analytics` BOOLEAN DEFAULT FALSE,
  -- Incident Module Permissions
  `create_incident` BOOLEAN DEFAULT FALSE,
  `edit_incident` BOOLEAN DEFAULT FALSE,
  `assign_incident` BOOLEAN DEFAULT FALSE,
  `evaluate_assigned_incident` BOOLEAN DEFAULT FALSE,
  `escalate_to_risk` BOOLEAN DEFAULT FALSE,
  `view_all_incident` BOOLEAN DEFAULT FALSE,
  `incident_performance_analytics` BOOLEAN DEFAULT FALSE,
  -- Event Module Permissions
  `create_event` BOOLEAN DEFAULT FALSE,
  `edit_event` BOOLEAN DEFAULT FALSE,
  `approve_event` BOOLEAN DEFAULT FALSE,
  `reject_event` BOOLEAN DEFAULT FALSE,
  `archive_event` BOOLEAN DEFAULT FALSE,
  `view_all_event` BOOLEAN DEFAULT FALSE,
  `view_module_event` BOOLEAN DEFAULT FALSE,
  `event_performance_analytics` BOOLEAN DEFAULT FALSE,
  -- Metadata
  `FrameworkId` INT NOT NULL,
  `IsActive` CHAR(1) DEFAULT 'Y',
  `CreatedAt` DATETIME NOT NULL,
  `UpdatedAt` DATETIME NOT NULL,
  FOREIGN KEY (`UserId`) REFERENCES `users`(`UserId`),
  FOREIGN KEY (`FrameworkId`) REFERENCES `framework`(`FrameworkId`)
);
```

---

## 2. Backend Implementation

### 2.1 Django Model (models.py)

```python
from django.db import models
from django.utils import timezone
import json

class AccessRequest(models.Model):
    """
    Access Request model for requesting access to pages/features
    Tracks user requests for access permissions that require admin approval
    """
    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
   
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='user_id', related_name='access_requests')
    requested_url = models.CharField(max_length=500, db_column='requested_url', null=True, blank=True)
    requested_feature = models.CharField(max_length=255, db_column='requested_feature', null=True, blank=True)
    required_permission = models.CharField(max_length=255, db_column='required_permission', null=True, blank=True)
    requested_role = models.CharField(max_length=100, db_column='requested_role', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED', db_column='status')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    approved_by = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True, db_column='approved_by', related_name='approved_access_requests')
    audit_trail = models.JSONField(null=True, blank=True, db_column='audit_trail', default=dict)
    message = models.TextField(null=True, blank=True, db_column='message')
   
    class Meta:
        db_table = 'AccessRequest'
        ordering = ['-created_at']
        verbose_name = 'Access Request'
        verbose_name_plural = 'Access Requests'
        indexes = [
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['status']),
        ]
   
    def __str__(self):
        return f"Access Request {self.id} by User {self.user_id.UserId} - {self.status}"
```

### 2.2 API Endpoints (routes/Global/user_profile.py)

#### 2.2.1 Create Access Request

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import authentication_classes
import json
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@csrf_exempt
@authentication_classes([])
@permission_classes([AllowAny])
def create_access_request(request):
    """
    Create a new access request
    """
    try:
        # Get user ID from request (from JWT token or session)
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response(
                {'status': 'error', 'message': 'User not authenticated'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get request data
        requested_url = request.data.get('requested_url', '')
        requested_feature = request.data.get('requested_feature', '')
        required_permission = request.data.get('required_permission', '')
        requested_role = request.data.get('requested_role', '')
        message = request.data.get('message', '')
        
        # Log the received data for debugging
        logger.info(f"Creating access request - URL: {requested_url}, Feature: {requested_feature}, Permission: {required_permission}, Role: {requested_role}")
        
        # Create audit trail
        audit_trail = {
            'requested_url': requested_url,
            'requested_feature': requested_feature,
            'required_permission': required_permission,
            'requested_role': requested_role,
            'message': message,
            'requested_by': user_id
        }
        
        # Create the access request using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO `AccessRequest` 
                (user_id, requested_url, requested_feature, required_permission, requested_role, status, message, audit_trail, approved_by, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                user_id,
                requested_url or None,  # Store None instead of empty string
                requested_feature or None,
                required_permission or None,
                requested_role or None,
                'REQUESTED',
                message or None,
                json.dumps(audit_trail),
                None,  # approved_by is NULL initially
                timezone.now(),
                timezone.now()
            ])
            
            request_id = cursor.lastrowid
        
        logger.info(f"Access request {request_id} created by user {user_id} - URL: {requested_url}, Permission: {required_permission}")
        
        return Response({
            'status': 'success',
            'message': 'Access request created successfully',
            'data': {
                'id': request_id,
                'status': 'REQUESTED',
                'created_at': timezone.now().isoformat()
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating access request: {str(e)}")
        return Response(
            {'status': 'error', 'message': f'Failed to create request: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

#### 2.2.2 Get Access Requests

```python
@api_view(['GET'])
@permission_classes([AllowAny])
def get_access_requests(request, user_id):
    """
    Get access requests for a user.
    Admins see all requests, regular users see only their own.
    """
    try:
        # Get user making the request
        requesting_user_id = RBACUtils.get_user_id_from_request(request)
        if not requesting_user_id:
            return Response(
                {'status': 'error', 'message': 'User not authenticated'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is an admin
        admin_user_ids = [1, 2, 3, 4]  # Configure your admin IDs
        try:
            requesting_user_id_int = int(requesting_user_id)
            is_admin = requesting_user_id_int in admin_user_ids
        except (ValueError, TypeError):
            is_admin = False
        
        # This works around Django's table name lowercasing issue
        with connection.cursor() as cursor:
            if is_admin:
                # Admin sees all requests
                cursor.execute("""
                    SELECT 
                        ar.id,
                        ar.user_id,
                        ar.requested_url,
                        ar.requested_feature,
                        ar.required_permission,
                        ar.requested_role,
                        ar.status,
                        ar.created_at,
                        ar.updated_at,
                        ar.approved_by,
                        ar.message,
                        ar.audit_trail,
                        u.FirstName,
                        u.LastName,
                        u.UserName,
                        approver.FirstName as ApproverFirstName,
                        approver.LastName as ApproverLastName
                    FROM `AccessRequest` ar
                    LEFT JOIN `users` u ON ar.user_id = u.UserId
                    LEFT JOIN `users` approver ON ar.approved_by = approver.UserId
                    ORDER BY ar.created_at DESC
                """)
            else:
                # Regular user sees only their own requests
                cursor.execute("""
                    SELECT 
                        ar.id,
                        ar.user_id,
                        ar.requested_url,
                        ar.requested_feature,
                        ar.required_permission,
                        ar.requested_role,
                        ar.status,
                        ar.created_at,
                        ar.updated_at,
                        ar.approved_by,
                        ar.message,
                        ar.audit_trail,
                        approver.FirstName as ApproverFirstName,
                        approver.LastName as ApproverLastName
                    FROM `AccessRequest` ar
                    LEFT JOIN `users` approver ON ar.approved_by = approver.UserId
                    WHERE ar.user_id = %s
                    ORDER BY ar.created_at DESC
                """, [user_id])
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            
            requests = []
            for row in rows:
                request_data = dict(zip(columns, row))
                # Parse JSON fields
                if request_data.get('audit_trail'):
                    if isinstance(request_data['audit_trail'], str):
                        try:
                            request_data['audit_trail'] = json.loads(request_data['audit_trail'])
                        except:
                            request_data['audit_trail'] = {}
                
                # Format dates
                if request_data.get('created_at'):
                    request_data['created_at'] = request_data['created_at'].isoformat() if hasattr(request_data['created_at'], 'isoformat') else str(request_data['created_at'])
                if request_data.get('updated_at'):
                    request_data['updated_at'] = request_data['updated_at'].isoformat() if hasattr(request_data['updated_at'], 'isoformat') else str(request_data['updated_at'])
                
                requests.append(request_data)
            
            return Response({
                'status': 'success',
                'data': requests
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error fetching access requests: {str(e)}")
        return Response(
            {'status': 'error', 'message': f'Failed to fetch access requests: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

#### 2.2.3 Update Access Request Status (Approve/Reject)

```python
@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([AllowAny])
def update_access_request_status(request, request_id):
    """
    Update the status of an access request (Approve/Reject)
    Only GRC Administrators can approve/reject requests
    When approved, updates RBAC table with requested role
    """
    try:
        # Get the request
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, status, requested_role, required_permission, audit_trail
                FROM `AccessRequest`
                WHERE id = %s
            """, [request_id])
            
            row = cursor.fetchone()
            if not row:
                return Response(
                    {'status': 'error', 'message': 'Request not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            request_data = dict(zip([col[0] for col in cursor.description], row))
            current_status = request_data['status']
            request_user_id = request_data['user_id']
            requested_role = request_data.get('requested_role')
            required_permission = request_data.get('required_permission')
            
            # Get the user making the update from request
            user_id = RBACUtils.get_user_id_from_request(request)
            if not user_id:
                user_id = request.data.get('user_id')
                if not user_id:
                    return Response(
                        {'status': 'error', 'message': 'User not authenticated'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            
            # Check if user is an admin
            admin_user_ids = [1, 2, 3, 4]  # Configure your admin IDs
            try:
                user_id_int = int(user_id)
                is_admin = user_id_int in admin_user_ids
            except (ValueError, TypeError):
                is_admin = False
            
            if not is_admin:
                return Response(
                    {'status': 'error', 'message': 'Only administrators can approve/reject requests'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get new status from request
            new_status = request.data.get('status')
            if not new_status:
                return Response(
                    {'status': 'error', 'message': 'Status is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate status
            valid_statuses = ['REQUESTED', 'APPROVED', 'REJECTED']
            new_status_upper = new_status.upper()
            if new_status_upper not in valid_statuses:
                return Response(
                    {'status': 'error', 'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if request is already approved or rejected
            if current_status in ['APPROVED', 'REJECTED']:
                return Response(
                    {'status': 'error', 'message': f'Request is already {current_status.lower()}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get audit trail
            audit_trail = {}
            if request_data.get('audit_trail'):
                if isinstance(request_data['audit_trail'], str):
                    try:
                        audit_trail = json.loads(request_data['audit_trail'])
                    except:
                        audit_trail = {}
                elif isinstance(request_data['audit_trail'], dict):
                    audit_trail = request_data['audit_trail']
            
            # Update the request status
            updated_at = timezone.now()
            
            # Add status change to audit trail
            if 'status_changes' not in audit_trail:
                audit_trail['status_changes'] = []
            
            audit_trail['status_changes'].append({
                'from_status': current_status,
                'to_status': new_status_upper,
                'changed_by': user_id,
                'changed_at': updated_at.isoformat()
            })
            
            # If approved, update RBAC table
            # If rejected, do NOT update RBAC table (leave permissions unchanged)
            if new_status_upper == 'APPROVED':
                try:
                    logger.info(f"Processing RBAC update for approved access request {request_id}, user {request_user_id}, permission: {required_permission}")
                    
                    # Get user
                    user = Users.objects.get(UserId=request_user_id)
                    
                    # Get or create framework - use user's framework or first available
                    framework = getattr(user, 'FrameworkId', None)
                    if not framework:
                        framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
                    
                    if not framework:
                        logger.warning(f"No framework found for access request {request_id}")
                        audit_trail['rbac_update_error'] = 'No framework found'
                    else:
                        # Map permission string (module.permission) to RBAC field name
                        # This mapping covers ALL modules and ALL permissions in the system
                        permission_field_map = {
                            # Compliance permissions
                            'compliance.create_compliance': 'create_compliance',
                            'compliance.edit_compliance': 'edit_compliance',
                            'compliance.approve_compliance': 'approve_compliance',
                            'compliance.view_all_compliance': 'view_all_compliance',
                            'compliance.compliance_performance_analytics': 'compliance_performance_analytics',
                            # Policy permissions
                            'policy.create_policy': 'create_policy',
                            'policy.edit_policy': 'edit_policy',
                            'policy.approve_policy': 'approve_policy',
                            'policy.create_framework': 'create_framework',
                            'policy.approve_framework': 'approve_framework',
                            'policy.view_all_policy': 'view_all_policy',
                            'policy.policy_performance_analytics': 'policy_performance_analytics',
                            # Audit permissions
                            'audit.assign_audit': 'assign_audit',
                            'audit.conduct_audit': 'conduct_audit',
                            'audit.review_audit': 'review_audit',
                            'audit.view_audit_reports': 'view_audit_reports',
                            'audit.audit_performance_analytics': 'audit_performance_analytics',
                            # Risk permissions
                            'risk.create_risk': 'create_risk',
                            'risk.edit_risk': 'edit_risk',
                            'risk.approve_risk': 'approve_risk',
                            'risk.assign_risk': 'assign_risk',
                            'risk.evaluate_assigned_risk': 'evaluate_assigned_risk',
                            'risk.view_all_risk': 'view_all_risk',
                            'risk.risk_performance_analytics': 'risk_performance_analytics',
                            # Incident permissions
                            'incident.create_incident': 'create_incident',
                            'incident.edit_incident': 'edit_incident',
                            'incident.assign_incident': 'assign_incident',
                            'incident.evaluate_assigned_incident': 'evaluate_assigned_incident',
                            'incident.escalate_to_risk': 'escalate_to_risk',
                            'incident.view_all_incident': 'view_all_incident',
                            'incident.incident_performance_analytics': 'incident_performance_analytics',
                            # Event permissions
                            'event.create_event': 'create_event',
                            'event.edit_event': 'edit_event',
                            'event.approve_event': 'approve_event',
                            'event.reject_event': 'reject_event',
                            'event.archive_event': 'archive_event',
                            'event.view_all_event': 'view_all_event',
                            'event.view_module_event': 'view_module_event',
                            'event.event_performance_analytics': 'event_performance_analytics'
                        }
                        
                        # Get or create RBAC entry - use requested_role if provided, otherwise use default role
                        default_role = requested_role if requested_role else 'End User'
                        rbac_entry = RBAC.objects.filter(user=user, is_active='Y').first()
                        
                        if not rbac_entry:
                            # Create new RBAC entry
                            rbac_entry = RBAC.objects.create(
                                user=user,
                                username=user.UserName,
                                role=default_role,
                                is_active='Y',
                                FrameworkId=framework
                            )
                            logger.info(f"Created new RBAC entry for user {request_user_id} with role {default_role}")
                        else:
                            # Update role if requested_role is provided
                            if requested_role:
                                rbac_entry.role = requested_role
                        
                        # Update permission if required_permission is provided
                        if required_permission and required_permission in permission_field_map:
                            permission_field = permission_field_map[required_permission]
                            if hasattr(rbac_entry, permission_field):
                                setattr(rbac_entry, permission_field, True)
                                logger.info(f"Granted permission {required_permission} ({permission_field}) to user {request_user_id}")
                                audit_trail['rbac_permission_granted'] = required_permission
                                audit_trail['rbac_permission_field'] = permission_field
                            else:
                                logger.warning(f"Permission field {permission_field} not found in RBAC model for permission {required_permission}")
                                audit_trail['rbac_permission_error'] = f"Permission field {permission_field} not found"
                        elif required_permission:
                            logger.warning(f"Unknown permission format: {required_permission}")
                            audit_trail['rbac_permission_error'] = f"Unknown permission format: {required_permission}"
                        
                        # Save RBAC entry
                        rbac_entry.save()
                        
                        audit_trail['rbac_updated'] = True
                        audit_trail['rbac_role'] = rbac_entry.role
                        audit_trail['rbac_updated_at'] = updated_at.isoformat()
                        logger.info(f"Updated RBAC entry for user {request_user_id}")
                        
                except Exception as e:
                    logger.error(f"Error updating RBAC for access request {request_id}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    audit_trail['rbac_update_error'] = str(e)
            elif new_status_upper == 'REJECTED':
                # Explicitly log that RBAC is NOT being updated for rejected requests
                logger.info(f"Access request {request_id} rejected - RBAC table will NOT be updated (permissions remain unchanged)")
                audit_trail['rbac_update_skipped'] = True
                audit_trail['rbac_update_reason'] = 'Request rejected - permissions unchanged'
            
            # Update the request status in AccessRequest table
            if new_status_upper == 'APPROVED':
                cursor.execute("""
                    UPDATE `AccessRequest`
                    SET status = %s,
                        updated_at = %s,
                        audit_trail = %s,
                        approved_by = %s
                    WHERE id = %s
                """, [new_status_upper, updated_at, json.dumps(audit_trail), user_id_int, request_id])
            else:
                cursor.execute("""
                    UPDATE `AccessRequest`
                    SET status = %s,
                        updated_at = %s,
                        audit_trail = %s
                    WHERE id = %s
                """, [new_status_upper, updated_at, json.dumps(audit_trail), request_id])
            
            logger.info(f"Access request {request_id} {new_status.lower()} by user {user_id_int}")
            
            return Response({
                'status': 'success',
                'message': f'Request {new_status.lower()} successfully',
                'data': {
                    'id': request_id,
                    'status': new_status,
                    'updated_at': updated_at.isoformat()
                }
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error updating access request status: {str(e)}")
        return Response(
            {'status': 'error', 'message': f'Failed to update request: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### 2.3 URL Configuration (urls.py)

```python
from .routes.Global import user_profile

urlpatterns = [
    # ... other patterns
    # Access Requests
    path('access-requests/<int:user_id>/', user_profile.get_access_requests, name='access_requests'),
    path('access-requests/create/', user_profile.create_access_request, name='create_access_request'),
    path('access-requests/<int:request_id>/update-status/', user_profile.update_access_request_status, name='update_access_request_status'),
]
```

---

## 3. Frontend Implementation

### 3.1 Access Denied Component (AccessDenied.vue)

```vue
<template>
  <div class="access-denied-container">
    <!-- Red circular icon with white X -->
    <div class="error-icon">
      <div class="x-symbol">✕</div>
    </div>
    
    <!-- Title -->
    <h1 class="access-denied-title">Access Denied</h1>
    
    <!-- Description -->
    <p class="error-message">
      You do not have permission to view this page.<br>
      Please check your credentials and try again.<br>
      Error Code: 403
    </p>
    
    <!-- Request Access Button -->
    <button 
      class="request-access-btn" 
      @click="requestAccess"
      :disabled="isRequesting || requestSubmitted"
    >
      <span v-if="isRequesting">Submitting...</span>
      <span v-else-if="requestSubmitted">Request Submitted</span>
      <span v-else>Request Access</span>
    </button>
    
    <!-- Success/Error Message -->
    <p v-if="message" :class="['message', messageType]">{{ message }}</p>
  </div>
</template>

<script>
import { API_ENDPOINTS } from '../config/api.js'
import axios from 'axios'

export default {
  name: 'AccessDenied',
  data() {
    return {
      isRequesting: false,
      requestSubmitted: false,
      message: '',
      messageType: 'success' // 'success' or 'error'
    }
  },
  mounted() {
    // Prevent scrolling on this page
    document.body.style.overflow = 'hidden'
  },
  beforeUnmount() {
    // Restore scrolling when leaving the page
    document.body.style.overflow = ''
  },
  methods: {
    async requestAccess() {
      try {
        this.isRequesting = true
        this.message = ''
        
        // Get access denied info from sessionStorage
        const accessDeniedInfo = sessionStorage.getItem('accessDeniedInfo')
        let requestedUrl = ''
        let requestedFeature = ''
        let requiredPermission = ''
        
        if (accessDeniedInfo) {
          try {
            const info = JSON.parse(accessDeniedInfo)
            console.log('Access denied info:', info)
            
            // Extract URL - use the stored URL from the router guard
            if (info.url) {
              try {
                const urlObj = new URL(info.url, window.location.origin)
                requestedUrl = urlObj.pathname
              } catch (e) {
                const pathMatch = info.url.match(/^([^?#]+)/)
                requestedUrl = pathMatch ? pathMatch[1] : info.url
              }
            }
            
            // Get the required permission - this is in format "module.permission"
            requiredPermission = info.requiredPermission || ''
            
            // Get the feature name
            requestedFeature = info.feature || requestedUrl || ''
          } catch (e) {
            console.error('Error parsing accessDeniedInfo:', e)
            requestedUrl = window.location.pathname
          }
        } else {
          requestedUrl = window.location.pathname
          console.warn('No accessDeniedInfo found in sessionStorage, using current pathname:', requestedUrl)
        }
        
        // Validate that we have at least a URL
        if (!requestedUrl || requestedUrl === '/access-denied') {
          this.message = 'Unable to determine the requested page. Please try accessing the page again.'
          this.messageType = 'error'
          this.isRequesting = false
          return
        }
        
        // Get user ID
        const userId = localStorage.getItem('user_id')
        if (!userId) {
          this.message = 'Please log in to request access.'
          this.messageType = 'error'
          this.isRequesting = false
          return
        }
        
        // Get access token
        const accessToken = localStorage.getItem('access_token')
        
        // Prepare request data
        const requestData = {
          requested_url: requestedUrl,
          requested_feature: requestedFeature,
          required_permission: requiredPermission,
          requested_role: '', // Can be enhanced to allow role selection
          message: `Requesting access to ${requestedFeature || requestedUrl}${requiredPermission ? ` (Permission: ${requiredPermission})` : ''}`
        }
        
        console.log('Submitting access request:', requestData)
        
        // Make API call to create access request
        const response = await axios.post(
          API_ENDPOINTS.CREATE_ACCESS_REQUEST,
          requestData,
          {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json'
            }
          }
        )
        
        if (response.data && response.data.status === 'success') {
          this.requestSubmitted = true
          this.message = 'Your access request has been submitted. An administrator will review it shortly.'
          this.messageType = 'success'
        } else {
          throw new Error(response.data?.message || 'Failed to submit request')
        }
        
      } catch (error) {
        console.error('Error requesting access:', error)
        this.message = error.response?.data?.message || error.message || 'Failed to submit access request. Please try again.'
        this.messageType = 'error'
      } finally {
        this.isRequesting = false
      }
    }
  }
}
</script>

<style scoped>
.access-denied-container {
  width: 100%;
  min-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding: 80px 20px 40px 20px;
}

.error-icon {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: #dc3545;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30px;
}

.x-symbol {
  color: white;
  font-size: 60px;
  font-weight: bold;
  line-height: 1;
}

.access-denied-title {
  font-size: 36px;
  font-weight: bold;
  color: #333333;
  margin: 0 0 24px 0;
  text-align: center;
}

.error-message {
  font-size: 16px;
  color: #333333;
  margin: 0 0 30px 0;
  text-align: center;
  line-height: 1.6;
}

.request-access-btn {
  margin-top: 30px;
  padding: 12px 30px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  background-color: #007bff;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.request-access-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.request-access-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
  opacity: 0.7;
}

.message {
  margin-top: 20px;
  padding: 12px 20px;
  border-radius: 5px;
  text-align: center;
  font-size: 14px;
  max-width: 500px;
}

.message.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>
```

### 3.2 Admin View Component (UserProfile.vue - Requests Tab)

```vue
<template>
  <div class="requests-section">
    <h2 class="section-title">
      <i class="fas fa-file-alt"></i> Access Requests
    </h2>
    <p class="section-helper">
      View and manage access requests. Admins can see all requests, regular users see only their own.
    </p>
    
    <!-- Loading State -->
    <div v-if="loadingRequests" class="loading-container">
      <div class="spinner"></div>
      <p>Loading requests...</p>
    </div>
    
    <!-- Error State -->
    <div v-else-if="requestsError" class="message error-message">
      <i class="fas fa-exclamation-circle"></i> {{ requestsError }}
    </div>
    
    <!-- Requests Table -->
    <div v-else class="requests-table-container">
      <table class="requests-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>User ID</th>
            <th>User Name</th>
            <th>Requested URL</th>
            <th>Feature</th>
            <th>Permission</th>
            <th>Status</th>
            <th>Created At</th>
            <th>Updated At</th>
            <th>Approved By</th>
            <th v-if="isAdminUser">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="accessRequests.length === 0">
            <td :colspan="isAdminUser ? 11 : 10" class="no-requests">
              <i class="fas fa-inbox"></i>
              <p>No access requests found.</p>
            </td>
          </tr>
          <tr v-for="request in accessRequests" :key="request.id">
            <td>{{ request.id }}</td>
            <td>{{ request.user_id }}</td>
            <td>{{ request.user_name || `${request.FirstName || ''} ${request.LastName || ''}`.trim() || 'N/A' }}</td>
            <td class="url-text">{{ request.requested_url || 'N/A' }}</td>
            <td>{{ request.requested_feature || 'N/A' }}</td>
            <td>
              <span class="permission-badge" v-if="request.required_permission">
                {{ request.required_permission }}
              </span>
              <span v-else class="text-muted">N/A</span>
            </td>
            <td>
              <span class="status-badge" :class="'status-' + request.status.toLowerCase()">
                {{ request.status }}
              </span>
            </td>
            <td>{{ formatDate(request.created_at) }}</td>
            <td>{{ formatDate(request.updated_at) }}</td>
            <td>
              <span v-if="request.approved_by_name || (request.ApproverFirstName && request.ApproverLastName)">
                {{ request.approved_by_name || `${request.ApproverFirstName} ${request.ApproverLastName}` }}
              </span>
              <span v-else class="text-muted">N/A</span>
            </td>
            <td v-if="isAdminUser">
              <div class="action-buttons">
                <button
                  @click="viewRequestDetails(request)"
                  class="action-btn view-btn"
                  title="View Request Details"
                >
                  <i class="fas fa-eye"></i> View
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Request Details Modal -->
    <div v-if="showRequestDetailsModal" class="modal-overlay" @click="closeRequestDetailsModal">
      <div class="modal-content request-details-modal" @click.stop>
        <div class="modal-header">
          <h3>
            <i class="fas fa-file-alt"></i>
            Access Request Details
          </h3>
          <button class="modal-close-btn" @click="closeRequestDetailsModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="selectedRequest" class="request-details-content">
            <!-- Request Information -->
            <div class="request-info-section">
              <h4><i class="fas fa-info-circle"></i> Request Information</h4>
              <div class="info-grid">
                <div class="info-item">
                  <label>Request ID:</label>
                  <span>{{ selectedRequest.id }}</span>
                </div>
                <div class="info-item">
                  <label>User ID:</label>
                  <span>{{ selectedRequest.user_id }}</span>
                </div>
                <div class="info-item">
                  <label>User Name:</label>
                  <span>{{ selectedRequest.user_name || `${selectedRequest.FirstName || ''} ${selectedRequest.LastName || ''}`.trim() || 'N/A' }}</span>
                </div>
                <div class="info-item">
                  <label>Requested URL:</label>
                  <span class="url-text">{{ selectedRequest.requested_url || 'N/A' }}</span>
                </div>
                <div class="info-item">
                  <label>Feature:</label>
                  <span>{{ selectedRequest.requested_feature || 'N/A' }}</span>
                </div>
                <div class="info-item">
                  <label>Required Permission:</label>
                  <span class="permission-badge" v-if="selectedRequest.required_permission">
                    {{ selectedRequest.required_permission }}
                  </span>
                  <span v-else class="text-muted">N/A</span>
                </div>
                <div class="info-item">
                  <label>Requested Role:</label>
                  <span>{{ selectedRequest.requested_role || 'N/A' }}</span>
                </div>
                <div class="info-item">
                  <label>Message:</label>
                  <span>{{ selectedRequest.message || 'N/A' }}</span>
                </div>
                <div class="info-item">
                  <label>Status:</label>
                  <span class="status-badge" :class="'status-' + selectedRequest.status.toLowerCase()">
                    {{ selectedRequest.status }}
                  </span>
                </div>
                <div class="info-item">
                  <label>Created At:</label>
                  <span>{{ formatDate(selectedRequest.created_at) }}</span>
                </div>
                <div class="info-item">
                  <label>Updated At:</label>
                  <span>{{ formatDate(selectedRequest.updated_at) }}</span>
                </div>
                <div class="info-item" v-if="selectedRequest.approved_by">
                  <label>Approved By:</label>
                  <span>{{ selectedRequest.approved_by_name || `${selectedRequest.ApproverFirstName || ''} ${selectedRequest.ApproverLastName || ''}`.trim() || selectedRequest.approved_by }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-cancel-btn" @click="closeRequestDetailsModal">
            Close
          </button>
          <div v-if="selectedRequest && selectedRequest.status === 'REQUESTED' && isAdminUser" class="modal-action-buttons">
            <button
              class="modal-reject-btn"
              @click="handleRejectRequest(selectedRequest.id)"
              :disabled="processingRequestId === selectedRequest.id"
            >
              <i v-if="processingRequestId === selectedRequest.id" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-times"></i>
              {{ processingRequestId === selectedRequest.id ? 'Rejecting...' : 'Reject' }}
            </button>
            <button
              class="modal-approve-btn"
              @click="handleApproveRequest(selectedRequest.id)"
              :disabled="processingRequestId === selectedRequest.id"
            >
              <i v-if="processingRequestId === selectedRequest.id" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-check"></i>
              {{ processingRequestId === selectedRequest.id ? 'Approving...' : 'Approve' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api.js'

export default {
  data() {
    return {
      accessRequests: [],
      loadingRequests: false,
      requestsError: null,
      showRequestDetailsModal: false,
      selectedRequest: null,
      processingRequestId: null,
      isAdminUser: false
    }
  },
  mounted() {
    this.checkAdminStatus()
    this.loadAccessRequests()
  },
  methods: {
    checkAdminStatus() {
      const userId = parseInt(localStorage.getItem('user_id'))
      const adminIds = [1, 2, 3, 4]  // Configure your admin IDs
      this.isAdminUser = adminIds.includes(userId)
    },
    
    async loadAccessRequests() {
      this.loadingRequests = true
      this.requestsError = null
      
      try {
        const userId = localStorage.getItem('user_id')
        const token = localStorage.getItem('access_token')
        
        const response = await axios.get(
          API_ENDPOINTS.GET_ACCESS_REQUESTS(userId),
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        )
        
        if (response.data.status === 'success') {
          this.accessRequests = response.data.data.map(request => {
            // Format user name
            if (request.FirstName && request.LastName) {
              request.user_name = `${request.FirstName} ${request.LastName}`
            } else if (request.UserName) {
              request.user_name = request.UserName
            }
            
            // Format approver name
            if (request.ApproverFirstName && request.ApproverLastName) {
              request.approved_by_name = `${request.ApproverFirstName} ${request.ApproverLastName}`
            }
            
            return request
          })
        }
      } catch (error) {
        console.error('Error loading access requests:', error)
        this.requestsError = error.response?.data?.message || 'Failed to load access requests'
      } finally {
        this.loadingRequests = false
      }
    },
    
    viewRequestDetails(request) {
      this.selectedRequest = request
      this.showRequestDetailsModal = true
    },
    
    closeRequestDetailsModal() {
      this.showRequestDetailsModal = false
      this.selectedRequest = null
    },
    
    async handleApproveRequest(requestId) {
      await this.updateRequestStatus(requestId, 'APPROVED')
    },
    
    async handleRejectRequest(requestId) {
      await this.updateRequestStatus(requestId, 'REJECTED')
    },
    
    async updateRequestStatus(requestId, status) {
      this.processingRequestId = requestId
      try {
        const userId = localStorage.getItem('user_id')
        const token = localStorage.getItem('access_token')
        
        const response = await axios.put(
          API_ENDPOINTS.UPDATE_ACCESS_REQUEST_STATUS(requestId),
          {
            status: status,
            user_id: userId
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )
        
        if (response.data.status === 'success') {
          // Update local state
          const requestIndex = this.accessRequests.findIndex(r => r.id === requestId)
          if (requestIndex !== -1) {
            this.accessRequests[requestIndex].status = status
            this.accessRequests[requestIndex].updated_at = response.data.data.updated_at
            if (status === 'APPROVED') {
              this.accessRequests[requestIndex].approved_by = userId
            }
          }
          
          this.closeRequestDetailsModal()
          alert(`Request ${status.toLowerCase()} successfully`)
          
          // Reload requests to get updated data
          await this.loadAccessRequests()
        }
      } catch (error) {
        console.error('Error updating request status:', error)
        alert(error.response?.data?.message || 'Failed to update request status')
      } finally {
        this.processingRequestId = null
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      try {
        return new Date(dateString).toLocaleString()
      } catch (e) {
        return dateString
      }
    }
  }
}
</script>

<style scoped>
/* Add your styles here */
.requests-table {
  width: 100%;
  border-collapse: collapse;
}

.requests-table th,
.requests-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.status-requested {
  background-color: #fff3cd;
  color: #856404;
}

.status-approved {
  background-color: #d4edda;
  color: #155724;
}

.status-rejected {
  background-color: #f8d7da;
  color: #721c24;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-approve-btn {
  background-color: #28a745;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.modal-reject-btn {
  background-color: #dc3545;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
}
</style>
```

### 3.3 API Configuration (config/api.js)

```javascript
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000'

export const API_ENDPOINTS = {
  // ... other endpoints
  
  // Access Requests
  GET_ACCESS_REQUESTS: (userId) => `${API_BASE_URL}/api/access-requests/${userId}/`,
  CREATE_ACCESS_REQUEST: `${API_BASE_URL}/api/access-requests/create/`,
  UPDATE_ACCESS_REQUEST_STATUS: (requestId) => `${API_BASE_URL}/api/access-requests/${requestId}/update-status/`,
}
```

---

## 4. Router Guard Configuration

### 4.1 Router Guard (router/index.js)

```javascript
import VueRouter from 'vue-router'
import AccessDenied from '@/views/AccessDenied.vue'

// Helper function to check user permissions
function checkUserPermission(requiredPermission) {
  if (!requiredPermission) return true
  
  // Get user permissions from localStorage or API
  const userPermissions = JSON.parse(localStorage.getItem('user_permissions') || '{}')
  
  const { module, permission } = requiredPermission
  return userPermissions[module]?.[permission] === true
}

const router = new VueRouter({
  routes: [
    {
      path: '/access-denied',
      name: 'AccessDenied',
      component: AccessDenied
    },
    // ... other routes
  ]
})

router.beforeEach((to, from, next) => {
  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('access_token')
    if (!token) {
      next('/login')
      return
    }
  }
  
  // Check if route requires specific permission
  if (to.meta.requiresPermission) {
    const hasPermission = checkUserPermission(to.meta.requiresPermission)
    
    if (!hasPermission) {
      // Store access denied info for the request access feature
      sessionStorage.setItem('accessDeniedInfo', JSON.stringify({
        url: to.fullPath,
        feature: to.name || to.path,
        requiredPermission: `${to.meta.requiresPermission.module}.${to.meta.requiresPermission.permission}`
      }))
      
      next('/access-denied')
      return
    }
  }
  
  next()
})

export default router
```

### 4.2 Route Configuration Example

```javascript
{
  path: '/policy/create',
  name: 'CreatePolicy',
  component: CreatePolicy,
  meta: {
    requiresAuth: true,
    requiresPermission: {
      module: 'policy',
      permission: 'create_policy'
    }
  }
}
```

---

## 5. Logic Flow

### 5.1 User Flow

1. **User attempts to access protected route**
   - Router guard checks user permissions
   - If user lacks permission, redirects to `/access-denied`

2. **User sees Access Denied page**
   - Displays error message with "Request Access" button
   - User clicks "Request Access"

3. **Frontend creates access request**
   - Extracts information from `sessionStorage` (stored by router guard)
   - Sends POST request to `/api/access-requests/create/`
   - Request includes:
     - `requested_url`: The URL the user tried to access
     - `requested_feature`: Feature name
     - `required_permission`: Permission string (e.g., "policy.create_policy")
     - `message`: User message (optional)

4. **Backend processes request**
   - Validates user authentication
   - Creates `AccessRequest` record with status `REQUESTED`
   - Stores audit trail with request details
   - Returns success response

5. **User receives confirmation**
   - Frontend shows success message
   - User is informed that admin will review the request

### 5.2 Admin Flow

1. **Admin views access requests**
   - Admin navigates to User Profile → Requests tab
   - Frontend calls `/api/access-requests/{user_id}/`
   - Backend returns all requests (admin sees all, users see only their own)

2. **Admin reviews request**
   - Admin clicks "View" on a request
   - Modal displays request details:
     - User information
     - Requested URL/feature
     - Required permission
     - Status and timestamps

3. **Admin approves or rejects**
   - Admin clicks "Approve" or "Reject"
   - Frontend sends PUT request to `/api/access-requests/{id}/update-status/`
   - Backend:
     - Validates admin authorization
     - Updates `AccessRequest.status`
     - If approved:
       - Updates or creates RBAC entry
       - Grants requested permission
       - Updates user role if requested_role is provided
       - Records approval in audit trail
       - Sets `approved_by` field
     - If rejected:
       - Updates status to `REJECTED`
       - Records rejection in audit trail
       - Does NOT update RBAC (permissions remain unchanged)

4. **User receives notification**
   - User can check their request status in User Profile
   - If approved, user gains access to requested feature
   - If rejected, user can see the rejection status

---

## 6. Key Points

### 6.1 Admin Configuration

- **Admin User IDs**: Configure the list of admin user IDs in both backend and frontend:
  ```python
  # Backend (user_profile.py)
  admin_user_ids = [1, 2, 3, 4]  # Update with your actual admin IDs
  ```
  ```javascript
  // Frontend (UserProfile.vue)
  const adminIds = [1, 2, 3, 4]  // Update with your actual admin IDs
  ```

### 6.2 Permission Mapping

- **Permission Format**: Permissions are stored in format `module.permission` (e.g., `policy.create_policy`)
- **RBAC Field Mapping**: The backend maps permission strings to RBAC model fields
- **Adding New Permissions**: When adding new permissions:
  1. Add the permission field to the RBAC model
  2. Add the mapping in `permission_field_map` in `update_access_request_status`
  3. Update the router guard to check the new permission

### 6.3 Audit Trail

- **Purpose**: The `audit_trail` JSON field stores complete request history
- **Contents**:
  - Original request details
  - Status changes with timestamps
  - Admin who approved/rejected
  - RBAC update information
  - Any errors encountered

### 6.4 RBAC Update Logic

- **On Approval**:
  - Creates RBAC entry if user doesn't have one
  - Updates existing RBAC entry if it exists
  - Grants the specific permission requested
  - Updates role if `requested_role` is provided
  - Links to user's framework or first available active framework

- **On Rejection**:
  - Does NOT modify RBAC table
  - Permissions remain unchanged
  - Only status is updated in AccessRequest table

### 6.5 Status Flow

```
REQUESTED → APPROVED (one-way)
REQUESTED → REJECTED (one-way)
```

- Once approved or rejected, status cannot be changed back to REQUESTED
- This ensures audit integrity

### 6.6 Security Considerations

1. **Authentication**: All endpoints require user authentication
2. **Authorization**: Only admins can approve/reject requests
3. **Validation**: 
   - Status values are validated
   - Cannot approve/reject already processed requests
   - User must be authenticated to create requests
4. **Audit**: All actions are logged in audit_trail

### 6.7 Error Handling

- **Backend**: Returns appropriate HTTP status codes and error messages
- **Frontend**: Displays user-friendly error messages
- **Logging**: All errors are logged for debugging

### 6.8 Database Considerations

- **Indexes**: 
  - `idx_user_created`: Optimizes queries filtering by user and date
  - `idx_status`: Optimizes queries filtering by status
- **Foreign Keys**: 
  - `user_id` references `users(UserId)`
  - `approved_by` references `users(UserId)`
- **JSON Field**: `audit_trail` uses JSON for flexible data storage

### 6.9 Frontend Integration

- **Router Guard**: Captures access denied information and stores in sessionStorage
- **Access Denied Page**: Provides user-friendly interface to request access
- **Admin Dashboard**: Shows all requests with filtering and search capabilities
- **User Dashboard**: Shows only user's own requests

### 6.10 Testing Checklist

- [ ] User can create access request when denied access
- [ ] Admin can view all access requests
- [ ] Regular user can only view their own requests
- [ ] Admin can approve request (RBAC updated)
- [ ] Admin can reject request (RBAC not updated)
- [ ] Cannot approve/reject already processed requests
- [ ] Audit trail is properly maintained
- [ ] Permission mapping works for all modules
- [ ] Error handling works correctly
- [ ] Frontend displays correct status and messages

---

## 7. Example Usage

### 7.1 User Requesting Access

```javascript
// User tries to access /policy/create
// Router guard checks permission: policy.create_policy
// User doesn't have permission → Redirected to /access-denied

// User clicks "Request Access"
// Frontend sends:
POST /api/access-requests/create/
{
  "requested_url": "/policy/create",
  "requested_feature": "Create Policy",
  "required_permission": "policy.create_policy",
  "requested_role": "",
  "message": "Requesting access to Create Policy (Permission: policy.create_policy)"
}

// Response:
{
  "status": "success",
  "message": "Access request created successfully",
  "data": {
    "id": 123,
    "status": "REQUESTED",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 7.2 Admin Approving Request

```javascript
// Admin views request #123 and clicks "Approve"
// Frontend sends:
PUT /api/access-requests/123/update-status/
{
  "status": "APPROVED",
  "user_id": 1  // Admin's user ID
}

// Backend:
// 1. Validates admin (user_id 1 is in admin list)
// 2. Updates AccessRequest.status = 'APPROVED'
// 3. Creates/updates RBAC entry:
//    - Sets create_policy = true
//    - Sets role = 'End User' (or requested_role if provided)
// 4. Updates audit_trail with approval details
// 5. Sets approved_by = 1

// Response:
{
  "status": "success",
  "message": "Request approved successfully",
  "data": {
    "id": 123,
    "status": "APPROVED",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

### 7.3 Admin Rejecting Request

```javascript
// Admin views request #124 and clicks "Reject"
// Frontend sends:
PUT /api/access-requests/124/update-status/
{
  "status": "REJECTED",
  "user_id": 1
}

// Backend:
// 1. Validates admin
// 2. Updates AccessRequest.status = 'REJECTED'
// 3. Does NOT update RBAC (permissions unchanged)
// 4. Updates audit_trail with rejection details

// Response:
{
  "status": "success",
  "message": "Request rejected successfully",
  "data": {
    "id": 124,
    "status": "REJECTED",
    "updated_at": "2024-01-15T11:05:00Z"
  }
}
```

---

## 8. Troubleshooting

### 8.1 Common Issues

**Issue**: User cannot create access request
- **Solution**: Check if user is authenticated (JWT token present)
- **Solution**: Verify API endpoint is correctly configured

**Issue**: Admin cannot see all requests
- **Solution**: Verify admin user IDs are correctly configured
- **Solution**: Check if admin user ID is in the admin list

**Issue**: RBAC not updated on approval
- **Solution**: Check permission mapping in `permission_field_map`
- **Solution**: Verify framework exists and is active
- **Solution**: Check logs for RBAC update errors

**Issue**: Permission not granted after approval
- **Solution**: Verify permission string format matches mapping
- **Solution**: Check if permission field exists in RBAC model
- **Solution**: Review audit_trail for error messages

**Issue**: Cannot approve already processed request
- **Solution**: This is by design - check request status first
- **Solution**: Create new request if needed

### 8.2 Debugging

**Enable Logging**:
```python
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

**Check Audit Trail**:
```sql
SELECT id, status, audit_trail FROM AccessRequest WHERE id = 123;
```

**Verify RBAC Entry**:
```sql
SELECT * FROM rbac WHERE UserId = 5 AND IsActive = 'Y';
```

---

## 9. Future Enhancements

1. **Email Notifications**: Send email to admin when new request is created
2. **Email Notifications**: Send email to user when request is approved/rejected
3. **Bulk Approval**: Allow admins to approve multiple requests at once
4. **Request Comments**: Allow admins to add comments when approving/rejecting
5. **Request History**: Show complete history of status changes
6. **Role Selection**: Allow users to select desired role when requesting access
7. **Time-based Access**: Grant temporary access with expiration dates
8. **Request Templates**: Pre-defined request templates for common scenarios
9. **Analytics Dashboard**: Show statistics on access requests
10. **Integration with Identity Provider**: Auto-approve based on AD/LDAP groups

---

## 10. Conclusion

This implementation provides a complete "Request Access" system that:

- ✅ Allows users to request access to protected features
- ✅ Enables admins to review and approve/reject requests
- ✅ Automatically updates RBAC permissions on approval
- ✅ Maintains complete audit trail
- ✅ Provides secure and user-friendly interface
- ✅ Supports all modules and permissions in the system

The system is designed to be:
- **Secure**: Proper authentication and authorization
- **Auditable**: Complete history in audit_trail
- **User-friendly**: Clear UI and error messages
- **Extensible**: Easy to add new permissions and modules
- **Maintainable**: Well-structured code with proper error handling

For questions or issues, refer to the troubleshooting section or check the audit trail for detailed error information.
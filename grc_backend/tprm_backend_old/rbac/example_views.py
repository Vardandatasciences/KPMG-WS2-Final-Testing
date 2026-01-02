"""
Example Views for TPRM RBAC System

This module demonstrates how to use the RBAC decorators for different TPRM modules.
"""

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.conf import settings
import jwt
from .tprm_decorators import (
    rbac_rfp_required, rbac_contract_required, rbac_vendor_required,
    rbac_risk_required, rbac_compliance_required, rbac_bcp_drp_required,
    rbac_module_required, rbac_admin_required
)
from .tprm_utils import RBACTPRMUtils


class SimpleAuthenticatedPermission(BasePermission):
    """
    Custom permission class that doesn't require is_authenticated attribute
    """
    def has_permission(self, request, view):
        # Just check if user exists in request
        return bool(request.user)


class JWTAuthentication(BaseAuthentication):
    """
    Custom JWT authentication class for DRF
    """
    def authenticate(self, request):
        print(f"[DEBUG] JWT Authentication called for path: {request.path}")
        print(f"[DEBUG] Authorization header: {request.headers.get('Authorization')}")
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            print("[DEBUG] No valid Authorization header found")
            return None
        
        try:
            token = auth_header.split(' ')[1]
            print(f"[DEBUG] Extracted token: {token[:20]}...")
            
            # Use JWT_SECRET_KEY instead of SECRET_KEY
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            print(f"[DEBUG] Decoded payload user_id: {user_id}")
            
            if user_id:
                # Try to find user in MFA User model first (using userid)
                try:
                    from mfa_auth.models import User as MFAUser
                    mfa_user = MFAUser.objects.get(userid=user_id)
                    print(f"[DEBUG] Found MFA user: {mfa_user.username}")
                    
                    # Create a simple user object with required attributes
                    class SimpleUser:
                        def __init__(self, mfa_user):
                            self.id = mfa_user.userid
                            self.username = mfa_user.username
                            self.email = mfa_user.email
                            self.first_name = getattr(mfa_user, 'first_name', '')
                            self.last_name = getattr(mfa_user, 'last_name', '')
                            self.mfa_user = mfa_user
                    
                    simple_user = SimpleUser(mfa_user)
                    print(f"[DEBUG] Created simple user object: {simple_user.username}")
                    return (simple_user, token)
                    
                except MFAUser.DoesNotExist:
                    # Fallback to Django User model
                    try:
                        user = User.objects.get(id=user_id)
                        print(f"[DEBUG] Found Django user: {user.username}")
                        return (user, token)
                    except User.DoesNotExist:
                        print(f"[DEBUG] User with ID {user_id} not found in either model")
                        return None
        except (jwt.InvalidTokenError, IndexError) as e:
            print(f"JWT Authentication error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected JWT authentication error: {e}")
            return None
        
        return None


# RFP Module Example Views
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('ViewRFP')
def list_rfps(request):
    """List all RFPs - requires ViewRFP permission"""
    try:
        # Your RFP listing logic here
        rfps = [
            {"id": 1, "title": "Sample RFP 1", "status": "Draft"},
            {"id": 2, "title": "Sample RFP 2", "status": "Published"}
        ]
        return Response({
            "success": True,
            "message": "RFPs retrieved successfully",
            "data": rfps
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error retrieving RFPs: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('CreateRFP')
def create_rfp(request):
    """Create a new RFP - requires CreateRFP permission"""
    try:
        # Your RFP creation logic here
        rfp_data = request.data
        # Process RFP creation...
        
        return Response({
            "success": True,
            "message": "RFP created successfully",
            "data": {"id": 123, "title": rfp_data.get('title')}
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error creating RFP: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('EditRFP')
def update_rfp(request, rfp_id):
    """Update an existing RFP - requires EditRFP permission"""
    try:
        # Your RFP update logic here
        rfp_data = request.data
        # Process RFP update...
        
        return Response({
            "success": True,
            "message": f"RFP {rfp_id} updated successfully",
            "data": {"id": rfp_id, "title": rfp_data.get('title')}
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error updating RFP: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('DeleteRFP')
def delete_rfp(request, rfp_id):
    """Delete an RFP - requires DeleteRFP permission"""
    try:
        # Your RFP deletion logic here
        # Process RFP deletion...
        
        return Response({
            "success": True,
            "message": f"RFP {rfp_id} deleted successfully"
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error deleting RFP: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Contract Module Example Views
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def list_contracts(request):
    """List all contracts - requires ListContracts permission"""
    try:
        # Your contract listing logic here
        contracts = [
            {"id": 1, "title": "Sample Contract 1", "status": "Active"},
            {"id": 2, "title": "Sample Contract 2", "status": "Expired"}
        ]
        return Response({
            "success": True,
            "message": "Contracts retrieved successfully",
            "data": contracts
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error retrieving contracts: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('CreateContract')
def create_contract(request):
    """Create a new contract - requires CreateContract permission"""
    try:
        # Your contract creation logic here
        contract_data = request.data
        # Process contract creation...
        
        return Response({
            "success": True,
            "message": "Contract created successfully",
            "data": {"id": 456, "title": contract_data.get('title')}
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error creating contract: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('UpdateContract')
def update_contract(request, contract_id):
    """Update an existing contract - requires UpdateContract permission"""
    try:
        # Your contract update logic here
        contract_data = request.data
        # Process contract update...
        
        return Response({
            "success": True,
            "message": f"Contract {contract_id} updated successfully",
            "data": {"id": contract_id, "title": contract_data.get('title')}
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error updating contract: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Vendor Module Example Views
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('ViewVendors')
def list_vendors(request):
    """List all vendors - requires ViewVendors permission"""
    try:
        # Your vendor listing logic here
        vendors = [
            {"id": 1, "name": "Vendor A", "status": "Active"},
            {"id": 2, "name": "Vendor B", "status": "Inactive"}
        ]
        return Response({
            "success": True,
            "message": "Vendors retrieved successfully",
            "data": vendors
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error retrieving vendors: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_vendor_required('CreateVendor')
def create_vendor(request):
    """Create a new vendor - requires CreateVendor permission"""
    try:
        # Your vendor creation logic here
        vendor_data = request.data
        # Process vendor creation...
        
        return Response({
            "success": True,
            "message": "Vendor created successfully",
            "data": {"id": 789, "name": vendor_data.get('name')}
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error creating vendor: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Risk Module Example Views
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_risk_required('ViewRiskAssessments')
def list_risk_assessments(request):
    """List all risk assessments - requires ViewRiskAssessments permission"""
    try:
        # Your risk assessment listing logic here
        assessments = [
            {"id": 1, "title": "Risk Assessment 1", "risk_level": "High"},
            {"id": 2, "title": "Risk Assessment 2", "risk_level": "Medium"}
        ]
        return Response({
            "success": True,
            "message": "Risk assessments retrieved successfully",
            "data": assessments
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error retrieving risk assessments: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_risk_required('CreateRiskAssessments')
def create_risk_assessment(request):
    """Create a new risk assessment - requires CreateRiskAssessments permission"""
    try:
        # Your risk assessment creation logic here
        assessment_data = request.data
        # Process risk assessment creation...
        
        return Response({
            "success": True,
            "message": "Risk assessment created successfully",
            "data": {"id": 101, "title": assessment_data.get('title')}
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error creating risk assessment: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Compliance Module Example Views
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_compliance_required('ViewComplianceStatusOfPlans')
def get_compliance_status(request):
    """Get compliance status - requires ViewComplianceStatusOfPlans permission"""
    try:
        # Your compliance status logic here
        compliance_data = {
            "overall_status": "Compliant",
            "last_audit": "2024-01-15",
            "next_audit": "2024-07-15"
        }
        return Response({
            "success": True,
            "message": "Compliance status retrieved successfully",
            "data": compliance_data
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error retrieving compliance status: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_compliance_required('GenerateComplianceAuditReports')
def generate_compliance_report(request):
    """Generate compliance report - requires GenerateComplianceAuditReports permission"""
    try:
        # Your compliance report generation logic here
        report_params = request.data
        # Process report generation...
        
        return Response({
            "success": True,
            "message": "Compliance report generated successfully",
            "data": {"report_id": "COMP-2024-001", "status": "Generated"}
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error generating compliance report: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# BCP/DRP Module Example Views
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('ViewPlansAndDocuments')
def list_bcp_drp_plans(request):
    """List BCP/DRP plans - requires ViewPlansAndDocuments permission"""
    try:
        # Your BCP/DRP plans listing logic here
        plans = [
            {"id": 1, "title": "BCP Plan 1", "type": "Business Continuity"},
            {"id": 2, "title": "DRP Plan 1", "type": "Disaster Recovery"}
        ]
        return Response({
            "success": True,
            "message": "BCP/DRP plans retrieved successfully",
            "data": plans
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error retrieving BCP/DRP plans: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('CreateBCPDRPStrategyAndPlans')
def create_bcp_drp_plan(request):
    """Create BCP/DRP plan - requires CreateBCPDRPStrategyAndPlans permission"""
    try:
        # Your BCP/DRP plan creation logic here
        plan_data = request.data
        # Process plan creation...
        
        return Response({
            "success": True,
            "message": "BCP/DRP plan created successfully",
            "data": {"id": 202, "title": plan_data.get('title')}
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error creating BCP/DRP plan: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Admin Module Example Views
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_admin_required
def admin_dashboard(request):
    """Admin dashboard - requires admin access"""
    try:
        # Your admin dashboard logic here
        dashboard_data = {
            "total_users": 150,
            "active_sessions": 45,
            "system_status": "Healthy"
        }
        return Response({
            "success": True,
            "message": "Admin dashboard data retrieved successfully",
            "data": dashboard_data
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error retrieving admin dashboard: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_admin_required
def configure_system_settings(request):
    """Configure system settings - requires admin access"""
    try:
        # Your system configuration logic here
        config_data = request.data
        # Process system configuration...
        
        return Response({
            "success": True,
            "message": "System settings configured successfully",
            "data": {"config_id": "SYS-001", "status": "Applied"}
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error configuring system settings: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Combined Permissions Example Views
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_module_required(['RFP', 'Contract'])
def cross_module_report(request):
    """Cross-module report - requires access to both RFP and Contract modules"""
    try:
        # Your cross-module reporting logic here
        report_data = {
            "rfp_count": 25,
            "contract_count": 18,
            "conversion_rate": "72%"
        }
        return Response({
            "success": True,
            "message": "Cross-module report generated successfully",
            "data": report_data
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error generating cross-module report: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_module_required(['Vendor', 'Risk', 'Compliance'])
def vendor_risk_assessment(request):
    """Vendor risk assessment - requires access to Vendor, Risk, and Compliance modules"""
    try:
        # Your vendor risk assessment logic here
        assessment_data = request.data
        # Process vendor risk assessment...
        
        return Response({
            "success": True,
            "message": "Vendor risk assessment completed successfully",
            "data": {"assessment_id": "VRA-001", "risk_score": "Medium"}
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error completing vendor risk assessment: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Utility Views for Testing Permissions
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def test_user_permissions(request):
    """Test endpoint to check user's current permissions"""
    try:
        rbac_utils = RBACTPRMUtils()
        user_id = rbac_utils.get_user_id_from_request(request)
        
        if not user_id:
            return Response({
                "success": False,
                "message": "User not authenticated"
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        permissions = rbac_utils.get_user_permissions_summary(user_id)
        
        return Response({
            "success": True,
            "message": "User permissions retrieved successfully",
            "data": {
                "user_id": user_id,
                "permissions": permissions
            }
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error retrieving user permissions: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def debug_permission_check(request):
    """Debug endpoint to test specific permission checks"""
    try:
        permission_name = request.data.get('permission')
        module_name = request.data.get('module')
        
        if not permission_name:
            return Response({
                "success": False,
                "message": "Permission name is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        rbac_utils = RBACTPRMUtils()
        user_id = rbac_utils.get_user_id_from_request(request)
        
        if not user_id:
            return Response({
                "success": False,
                "message": "User not authenticated"
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if module_name:
            # Convert module name to lowercase for consistency
            module_name_lower = module_name.lower()
            has_access = rbac_utils.has_module_access(user_id, module_name_lower)
            
            # Use permission name as-is (database field names preserve original casing)
            permission_result = rbac_utils.check_permission(user_id, permission_name)
        else:
            # Use permission name as-is (database field names preserve original casing)
            permission_result = rbac_utils.check_permission(user_id, permission_name)
            has_access = None
        
        debug_info = rbac_utils.debug_permission_check(user_id, permission_name, module_name)
        
        return Response({
            "success": True,
            "message": "Permission check completed",
            "data": {
                "user_id": user_id,
                "permission": permission_name,
                "module": module_name,
                "has_permission": permission_result,
                "has_module_access": has_access,
                "debug_info": debug_info
            }
        })
    except Exception as e:
        return Response({
            "success": False,
            "message": f"Error during permission check: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Simple test endpoint for JWT authentication (no RBAC required)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
def test_jwt_auth(request):
    """Simple endpoint to test JWT authentication without RBAC"""
    print(f"[DEBUG] test_jwt_auth called for user: {request.user}")
    print(f"[DEBUG] Request headers: {dict(request.headers)}")
    
    # Handle both simple user objects and Django users
    user_data = {
        "user_id": getattr(request.user, 'id', None),
        "username": getattr(request.user, 'username', 'Unknown'),
        "email": getattr(request.user, 'email', ''),
    }
    
    # Add additional info if available
    if hasattr(request.user, 'first_name'):
        user_data["first_name"] = request.user.first_name
    if hasattr(request.user, 'last_name'):
        user_data["last_name"] = request.user.last_name
    if hasattr(request.user, 'mfa_user'):
        user_data["mfa_user_id"] = request.user.mfa_user.userid
    
    return Response({
        "success": True,
        "message": "JWT authentication successful",
        "data": user_data
    })


# Simple test endpoint with NO authentication required
@api_view(['GET'])
def test_no_auth(request):
    """Simple endpoint to test basic connectivity without any authentication"""
    print(f"[DEBUG] test_no_auth called")
    return Response({
        "success": True,
        "message": "No authentication required - endpoint working",
        "data": {
            "path": request.path,
            "method": request.method,
            "headers": dict(request.headers)
        }
    })

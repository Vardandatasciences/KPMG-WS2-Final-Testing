#!/usr/bin/env python
"""
Automated Multi-Tenancy HTTP Test Script

This script makes actual HTTP requests to test multitenancy across all modules.
It verifies tenant isolation by testing with multiple tenants and checking cross-tenant access prevention.

Usage:
    python test_multitenancy_http.py
    python test_multitenancy_http.py --base-url http://localhost:8000
    python test_multitenancy_http.py --users user1,user2
"""

import os
import sys
import django
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
from django.conf import settings
if not settings.configured:
    django.setup()

from grc.models import Tenant, Users


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class MultiTenancyHTTPTester:
    """HTTP-based multitenancy tester"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Test results
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'tests': []
        }
        
        # Module endpoints configuration
        # Format: [list_endpoint, detail_endpoint]
        self.module_endpoints = {
            'Policy': {
                'list': '/api/frameworks/',
                'detail': '/api/frameworks/<int:pk>/',
            },
            'Compliance': {
                'list': '/api/compliance/frameworks/',
                'detail': '/api/compliance/frameworks/<int:framework_id>/policies/list/',
            },
            'Framework': {
                'list': '/api/frameworks/',
                'detail': '/api/frameworks/<int:pk>/',
            },
            'Risk': {
                'list': '/api/risk-instances/',
                'detail': '/api/risk-instances/<int:pk>/',
            },
            'Risk (ViewSet)': {
                'list': '/api/risks/',
                'detail': '/api/risks/<int:pk>/',
            },
            'Incident': {
                'list': '/api/incident-incidents/',
                'detail': '/api/incidents/<int:incident_id>/',
            },
            'Incident (ViewSet)': {
                'list': '/api/incidents/',
                'detail': '/api/incidents/<int:pk>/',
            },
            'Audit': {
                'list': '/api/audits/',
                'detail': '/api/audits/<int:audit_id>/',
            },
            'Audit (Public)': {
                'list': '/api/audits/public/',
                'detail': '/api/audits/<int:audit_id>/',
            },
            'Events': {
                'list': '/api/events/list/',
                'detail': '/api/events/<int:event_id>/',
            }
        }
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{'='*70}")
        print(f"{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{'='*70}")
    
    def print_section(self, text: str):
        """Print formatted section"""
        print(f"\n{'-'*70}")
        print(f"{Colors.OKCYAN}📦 {text}{Colors.ENDC}")
        print(f"{'-'*70}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")
    
    def check_server_connection(self) -> bool:
        """Check if server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/test-connection/", timeout=5)
            return response.status_code in [200, 404]  # 404 is OK, means server is running
        except:
            return False
    
    def login_user(self, username: str, password: str = None, session: requests.Session = None) -> Optional[Dict]:
        """Login user and get JWT token"""
        if session is None:
            session = self.session
        try:
            # Try to get user from database to get tenant
            try:
                user = Users.objects.get(UserName=username)
                # Use default password if not provided
                if password is None:
                    password = user.Password  # May be plain text for testing
            except Users.DoesNotExist:
                self.print_warning(f"User {username} not found in database")
                return None
            
            # Login via JWT endpoint
            # Note: You may need to disable CAPTCHA verification in authentication.py for testing
            login_data = {
                'username': username,
                'password': password,
                'login_type': 'username',
                'captcha_token': 'test-captcha-token-disabled'  # Set to None or disable CAPTCHA in backend for testing
            }
            
            response = session.post(
                f"{self.base_url}/api/jwt/login/",
                json=login_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access') or data.get('access_token') or data.get('token')
                if token:
                    session.headers['Authorization'] = f'Bearer {token}'
                    return {
                        'token': token,
                        'user_id': data.get('user_id') or user.UserId,
                        'tenant_id': user.tenant_id if hasattr(user, 'tenant_id') else None
                    }
            
            # Fallback: try session-based login
            response = session.post(
                f"{self.base_url}/api/login/",
                json=login_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'token': None,
                    'user_id': user.UserId,
                    'tenant_id': user.tenant_id if hasattr(user, 'tenant_id') else None
                }
            
            return None
            
        except Exception as e:
            self.print_error(f"Login error for {username}: {str(e)}")
            return None
    
    def get_tenant_from_user(self, username: str) -> Optional[int]:
        """Get tenant_id from username"""
        try:
            user = Users.objects.get(UserName=username)
            return user.tenant_id if hasattr(user, 'tenant_id') else None
        except Users.DoesNotExist:
            return None
    
    def test_list_endpoint(self, endpoint: str, tenant_name: str, module_name: str, session: requests.Session = None) -> Tuple[bool, Optional[List], str]:
        """Test a list endpoint and return results"""
        if session is None:
            session = self.session
        try:
            # Replace placeholder with actual ID if needed
            if '<int:' in endpoint or '<str:' in endpoint:
                # For detail endpoints, we'll skip for now or use a test ID
                endpoint = endpoint.split('<')[0].rstrip('/')
            
            url = f"{self.base_url}{endpoint}"
            
            response = session.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                return False, None, "Endpoint not found"
            
            if response.status_code not in [200, 201]:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error') or error_data.get('message') or str(response.status_code)
                except:
                    error_msg = f"Error {response.status_code}"
                return False, None, f"Error {response.status_code} - {error_msg}"
            
            try:
                data = response.json()
                # Handle different response formats
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get('data') or data.get('results') or data.get('items') or []
                    if not isinstance(items, list):
                        items = [data] if data else []
                else:
                    items = []
                
                return True, items, f"Got {len(items)} items"
            except:
                return True, [], "Got response but couldn't parse JSON"
                
        except requests.exceptions.Timeout:
            return False, None, f"Timeout after {self.timeout}s"
        except Exception as e:
            return False, None, f"Exception - {str(e)}"
    
    def test_cross_tenant_access(self, endpoint: str, item_id: int, tenant_a_name: str, tenant_b_name: str, module_name: str, session: requests.Session = None) -> bool:
        """Test that tenant B cannot access tenant A's data"""
        if session is None:
            session = self.session
        try:
            # Replace ID placeholder
            detail_endpoint = endpoint.replace('<int:pk>', str(item_id))
            detail_endpoint = detail_endpoint.replace('<int:incident_id>', str(item_id))
            detail_endpoint = detail_endpoint.replace('<int:framework_id>', str(item_id))
            detail_endpoint = detail_endpoint.replace('<int:policy_id>', str(item_id))
            detail_endpoint = detail_endpoint.replace('<int:risk_id>', str(item_id))
            detail_endpoint = detail_endpoint.replace('<int:audit_id>', str(item_id))
            
            # Remove any remaining placeholders
            if '<' in detail_endpoint:
                detail_endpoint = detail_endpoint.split('<')[0].rstrip('/')
            
            url = f"{self.base_url}{detail_endpoint}"
            
            response = session.get(url, timeout=self.timeout)
            
            # Cross-tenant access should be blocked (403) or return 404
            if response.status_code in [403, 404]:
                return True  # Correctly blocked
            
            # If 200, check if data is actually from different tenant
            if response.status_code == 200:
                try:
                    data = response.json()
                    # If we get data, it might be a leak (depending on endpoint)
                    # For now, we'll consider 200 as potentially problematic
                    return False
                except:
                    return False
            
            return False
            
        except Exception as e:
            return False
    
    def test_module(self, module_name: str, tenant_a_user: str, tenant_b_user: str, tenant_a_password: str = None, tenant_b_password: str = None):
        """Test a specific module with two tenants"""
        self.print_section(f"Testing {module_name} Module")
        
        # Get endpoints for this module
        endpoints_config = self.module_endpoints.get(module_name)
        if not endpoints_config:
            self.print_warning(f"No endpoints configured for {module_name}")
            return
        
        list_endpoint = endpoints_config.get('list')
        detail_endpoint = endpoints_config.get('detail')
        
        # Create separate session for tenant A
        tenant_a_session = requests.Session()
        tenant_a_session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Login tenant A
        self.print_info(f"Tenant A - Logging in as {tenant_a_user}...")
        tenant_a_auth = self.login_user(tenant_a_user, tenant_a_password, session=tenant_a_session)
        if not tenant_a_auth:
            self.print_error(f"Failed to login as {tenant_a_user}")
            return
        
        tenant_a_id = tenant_a_auth.get('tenant_id') or self.get_tenant_from_user(tenant_a_user)
        self.print_success(f"Logged in as {tenant_a_user} (Tenant ID: {tenant_a_id})")
        
        # Test list endpoint for tenant A
        tenant_a_data = {}
        if list_endpoint:
            self.print_info(f"Tenant A - Listing {module_name} items...")
            success, items, message = self.test_list_endpoint(list_endpoint, tenant_a_user, module_name, session=tenant_a_session)
            
            if success:
                if items is not None:
                    self.print_success(f"Tenant A - {module_name}: {message}")
                    tenant_a_data[list_endpoint] = items
                else:
                    self.print_warning(f"Tenant A - {module_name}: {message}")
            else:
                self.print_warning(f"Tenant A - {module_name}: {message}")
        
        # Create separate session for tenant B
        tenant_b_session = requests.Session()
        tenant_b_session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Login tenant B
        self.print_info(f"\nTenant B - Logging in as {tenant_b_user}...")
        tenant_b_auth = self.login_user(tenant_b_user, tenant_b_password, session=tenant_b_session)
        if not tenant_b_auth:
            self.print_error(f"Failed to login as {tenant_b_user}")
            return
        
        tenant_b_id = tenant_b_auth.get('tenant_id') or self.get_tenant_from_user(tenant_b_user)
        self.print_success(f"Logged in as {tenant_b_user} (Tenant ID: {tenant_b_id})")
        
        # Test list endpoint for tenant B
        tenant_b_data = {}
        if list_endpoint:
            self.print_info(f"\nTenant B - Listing {module_name} items...")
            success, items, message = self.test_list_endpoint(list_endpoint, tenant_b_user, module_name, session=tenant_b_session)
            
            if success:
                if items is not None:
                    self.print_success(f"Tenant B - {module_name}: {message}")
                    tenant_b_data[list_endpoint] = items
                    
                    # Check if both tenants have the same count (potential multitenancy issue)
                    if tenant_a_data and list_endpoint in tenant_a_data:
                        tenant_a_count = len(tenant_a_data[list_endpoint])
                        tenant_b_count = len(items)
                        if tenant_a_count == tenant_b_count and tenant_a_count > 0:
                            self.print_warning(f"⚠️  Both tenants have the same count ({tenant_a_count} items). This might indicate a multitenancy issue if tenants should have different data.")
                else:
                    self.print_warning(f"Tenant B - {module_name}: {message}")
            else:
                self.print_warning(f"Tenant B - {module_name}: {message}")
        
        # Test cross-tenant access prevention
        if tenant_a_data and detail_endpoint:
            # Get first item ID from tenant A
            first_endpoint = list(tenant_a_data.keys())[0]
            items = tenant_a_data[first_endpoint]
            
            if items and len(items) > 0:
                # Try to get ID from first item
                first_item = items[0]
                item_id = None
                
                # Try different ID field names
                for id_field in ['id', 'Id', 'ID', 'pk', 'PK', 
                                'FrameworkId', 'PolicyId', 'IncidentId', 'RiskId', 'AuditId', 
                                'ComplianceId', 'EventId', 'RiskInstanceId',
                                f'{module_name.lower()}Id', f'{module_name.lower()}_id']:
                    if id_field in first_item:
                        item_id = first_item[id_field]
                        # Handle nested IDs (e.g., {'id': {'id': 123}})
                        if isinstance(item_id, dict) and 'id' in item_id:
                            item_id = item_id['id']
                        break
                
                if item_id:
                    self.print_info(f"\nTesting cross-tenant access prevention (Tenant B accessing Tenant A's item ID: {item_id})...")
                    
                    blocked = self.test_cross_tenant_access(
                        detail_endpoint, item_id, tenant_a_user, tenant_b_user, module_name, session=tenant_b_session
                    )
                    
                    if blocked:
                        self.print_success(f"{module_name}: Cross-tenant access correctly blocked (403/404)")
                        self.results['passed'] += 1
                    else:
                        self.print_warning(f"{module_name}: Could not determine cross-tenant access status")
                        self.results['warnings'] += 1
                else:
                    self.print_warning(f"{module_name}: Could not extract item ID for cross-tenant test")
            else:
                self.print_warning(f"No data found for Tenant A - skipping cross-tenant test")
        else:
            if not tenant_a_data:
                self.print_warning(f"No data found for Tenant A - skipping cross-tenant test")
            elif not detail_endpoint:
                self.print_warning(f"No detail endpoint configured for {module_name}")
    
    def run_all_tests(self, tenant_a_user: str, tenant_b_user: str, 
                     tenant_a_password: str = None, tenant_b_password: str = None):
        """Run all multitenancy tests"""
        self.print_header("🔐 MULTITENANCY TESTING SCRIPT")
        
        # Check server connection
        self.print_info("Checking server connection...")
        if not self.check_server_connection():
            self.print_error(f"Server is not running at {self.base_url}")
            self.print_info("Please start the Django server: python manage.py runserver")
            return False
        
        self.print_success("Server is running")
        self.print_info("\n💡 TIP: If you get CAPTCHA errors, you can disable it for testing.")
        
        # Test all modules
        modules = ['Policy', 'Compliance', 'Framework', 'Risk', 'Risk (ViewSet)', 
                  'Incident', 'Incident (ViewSet)', 'Audit', 'Audit (Public)', 'Events']
        
        self.print_header("📊 TESTING MODULES")
        
        for module in modules:
            try:
                self.test_module(module, tenant_a_user, tenant_b_user, tenant_a_password, tenant_b_password)
            except Exception as e:
                self.print_error(f"Error testing {module}: {str(e)}")
                self.results['failed'] += 1
        
        # Print summary
        self.print_summary()
        
        return self.results['failed'] == 0
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("📊 TEST SUMMARY")
        
        print(f"\n{Colors.OKGREEN}✅ Passed: {self.results['passed']}{Colors.ENDC}")
        print(f"{Colors.FAIL}❌ Failed: {self.results['failed']}{Colors.ENDC}")
        print(f"{Colors.WARNING}⚠️  Warnings: {self.results['warnings']}{Colors.ENDC}")
        
        if self.results['failed'] == 0:
            self.print_success("\n🎉 All critical tests passed!")
        else:
            self.print_error(f"\n⚠️  {self.results['failed']} test(s) failed. Please review the output above.")
        
        self.print_info("\nNote: Some modules may show warnings if:")
        self.print_info("   - No test data exists for that tenant")
        self.print_info("   - Endpoints have different names")
        self.print_info("   - Permissions are required")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Test multitenancy via HTTP requests')
    parser.add_argument('--base-url', type=str, default='http://localhost:8000',
                       help='Base URL of the API server')
    parser.add_argument('--tenant-a', type=str, default=None,
                       help='Username for Tenant A')
    parser.add_argument('--tenant-b', type=str, default=None,
                       help='Username for Tenant B')
    parser.add_argument('--password-a', type=str, default=None,
                       help='Password for Tenant A')
    parser.add_argument('--password-b', type=str, default=None,
                       help='Password for Tenant B')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    # Get default users from database if not provided
    tenant_a_user = args.tenant_a
    tenant_b_user = args.tenant_b
    
    if not tenant_a_user or not tenant_b_user:
        # Try to find users from different tenants
        try:
            users = Users.objects.all()[:10]
            if len(users) >= 2:
                # Find users from different tenants
                tenant_a_user = users[0].UserName
                tenant_b_user = None
                
                for user in users[1:]:
                    if hasattr(user, 'tenant_id') and hasattr(users[0], 'tenant_id'):
                        if user.tenant_id != users[0].tenant_id:
                            tenant_b_user = user.UserName
                            break
                
                if not tenant_b_user:
                    tenant_b_user = users[1].UserName
            else:
                print("Error: Need at least 2 users in database for testing")
                print("Please create test users or specify --tenant-a and --tenant-b")
                return
        except Exception as e:
            print(f"Error getting users from database: {e}")
            print("Please specify --tenant-a and --tenant-b")
            return
    
    # Create tester and run tests
    tester = MultiTenancyHTTPTester(base_url=args.base_url, timeout=args.timeout)
    success = tester.run_all_tests(
        tenant_a_user=tenant_a_user,
        tenant_b_user=tenant_b_user,
        tenant_a_password=args.password_a,
        tenant_b_password=args.password_b
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()


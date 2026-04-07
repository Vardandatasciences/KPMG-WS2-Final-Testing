import pandas as pd
import os

def generate_home_api_audit():
    print("Generating Complete Home Page API Audit Report with precise network latency...")
    
    # Define the Home Page API Data with latency from your network log
    api_data = [
        {
            "Module/Section": "Core Homepage Data",
            "API Name": "Unified Homepage Data (metrics)",
            "API URL": "/api/homepage/metrics",
            "Method": "GET",
            "Times Called": "1 (On load)",
            "State Management": "HomepageDataService",
            "Storage Location": "dataStore.homepageDataByFramework",
            "Dependency Payload": "frameworkId (optional)",
            "Response Time (ms)": "1.26s"
        },
        {
            "Module/Section": "Dashboard Fallbacks",
            "API Name": "Audit Completion Metrics",
            "API URL": "/api/dashboard/audit-completion-rate/",
            "Method": "GET",
            "Times Called": "1 (On load / Fallback)",
            "State Management": "HomepageDataService",
            "Storage Location": "dataStore.auditorMetrics",
            "Dependency Payload": "frameworkId (optional)",
            "Response Time (ms)": "999ms"
        },
        {
            "Module/Section": "Framework Selection",
            "API Name": "Get Initial Selected Framework",
            "API URL": "/api/frameworks/get-selected/",
            "Method": "GET",
            "Times Called": "1 (On load)",
            "State Management": "Vuex Store / TreeDataService",
            "Storage Location": "state.framework.selectedFrameworkId",
            "Dependency Payload": "userId (from storage)",
            "Response Time (ms)": "782ms"
        },
        {
            "Module/Section": "Background System",
            "API Name": "Notification Fetch (Polling)",
            "API URL": "/api/get-notifications/?user_id={id}",
            "Method": "GET",
            "Times Called": "Every 30-60s (Recurring)",
            "State Management": "Navbar / SessionTimeoutPopup",
            "Storage Location": "None (UI Update Only)",
            "Dependency Payload": "user_id",
            "Response Time (ms)": "897ms"
        },
        {
            "Module/Section": "Initialization",
            "API Name": "Framework Auto Check All",
            "API URL": "/api/change-mgmt/auto-check-all/",
            "Method": "POST",
            "Times Called": "1 (On load)",
            "State Management": "None (Action)",
            "Storage Location": "None (Backend Processing)",
            "Dependency Payload": "{}",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Framework Selection",
            "API Name": "Approved & Active Frameworks",
            "API URL": "/api/frameworks/approved-active/",
            "Method": "GET",
            "Times Called": "1 (Initialization)",
            "State Management": "HomepageDataService",
            "Storage Location": "dataStore.approvedFrameworks",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Framework Selection",
            "API Name": "Set Selected Framework (Change)",
            "API URL": "/api/frameworks/set-selected/",
            "Method": "POST",
            "Times Called": "On framework toggle",
            "State Management": "Vuex Store",
            "Storage Location": "Backend Session",
            "Dependency Payload": "{frameworkId, userId}",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Risks Listing Prefetch",
            "API URL": "/api/risks-for-dropdown/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "RiskDataService",
            "Storage Location": "dataStore.risks",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Risk Instances Prefetch",
            "API URL": "/api/risk-instances/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "RiskDataService",
            "Storage Location": "dataStore.riskInstances",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Compliance Frameworks Prefetch",
            "API URL": "/api/compliance/all-policies/frameworks/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "ComplianceDataService",
            "Storage Location": "dataStore.frameworks",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "All Compliances Prefetch",
            "API URL": "/api/compliance/all-for-audit-management/public/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "ComplianceDataService",
            "Storage Location": "dataStore.compliances",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "My Audits Prefetch",
            "API URL": "/api/my-audits/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "AuditorDataService",
            "Storage Location": "dataStore.audits",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Business Units Prefetch",
            "API URL": "/api/business-units/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "AuditorDataService",
            "Storage Location": "dataStore.businessUnits",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Events List Prefetch",
            "API URL": "/api/events/list/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "EventDataService",
            "Storage Location": "dataStore.events",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Integration Events Prefetch",
            "API URL": "/api/events/integration-events/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "EventDataService",
            "Storage Location": "dataStore.integrationEvents",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Frameworks List Prefetch",
            "API URL": "/api/frameworks/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "PolicyDataService",
            "Storage Location": "dataStore.frameworksList",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Policy Frameworks Prefetch",
            "API URL": "/api/all-policies/frameworks/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "PolicyDataService",
            "Storage Location": "dataStore.policyFrameworks",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Framework Explorer Prefetch",
            "API URL": "/api/framework-explorer/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "PolicyDataService",
            "Storage Location": "dataStore.explorerFrameworks",
            "Dependency Payload": "{}",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Tree Frameworks Prefetch",
            "API URL": "/api/tree/frameworks/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "TreeDataService",
            "Storage Location": "dataStore.frameworks",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Documents List Prefetch",
            "API URL": "/api/documents/list/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "DocumentDataService",
            "Storage Location": "dataStore.documents",
            "Dependency Payload": "{module: 'all'}",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Documents Counts Prefetch",
            "API URL": "/api/documents/counts/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "DocumentDataService",
            "Storage Location": "dataStore.documentCounts",
            "Dependency Payload": "None",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "External Applications Prefetch",
            "API URL": "/api/external-applications/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "IntegrationsDataService",
            "Storage Location": "dataStore.applications",
            "Dependency Payload": "user_id={id}",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "Jira Stored Data Prefetch",
            "API URL": "/api/jira/stored-data/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "IntegrationsDataService",
            "Storage Location": "dataStore.jiraStoredData",
            "Dependency Payload": "user_id={id}",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Background Prefetch",
            "API Name": "BambooHR Stored Data Prefetch",
            "API URL": "/api/bamboohr/stored-data/",
            "Method": "GET",
            "Times Called": "1 (Prefetch)",
            "State Management": "IntegrationsDataService",
            "Storage Location": "dataStore.bamboohrStoredData",
            "Dependency Payload": "user_id={id}",
            "Response Time (ms)": "None"
        },
        {
            "Module/Section": "Interactive Elements",
            "API Name": "Policy Details (Popup View)",
            "API URL": "/api/home/policy-details/{policyId}/",
            "Method": "GET",
            "Times Called": "On user click (legend)",
            "State Management": "HomepageDataService",
            "Storage Location": "None (Direct Return)",
            "Dependency Payload": "policyId",
            "Response Time (ms)": "None"
        }
    ]

    # Create DataFrame
    df = pd.DataFrame(api_data)
    
    # Save to Excel
    output_path = r"c:\Users\Admin\Desktop\GRC_TPRM-1\home_api_audit_network_synced.xlsx"
    df.to_excel(output_path, index=False)
    
    # Update the legacy path as well
    df.to_excel(r"c:\Users\Admin\Desktop\GRC_TPRM-1\home_api_audit_complete.xlsx", index=False)
    
    print(f"Excel report generated successfully: {output_path}")

if __name__ == "__main__":
    generate_home_api_audit()

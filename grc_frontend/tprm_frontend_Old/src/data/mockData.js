// Mock data matching the database schema

export const mockUsers = [
  { user_id: 1, name: "Sarah Johnson", email: "sarah.johnson@company.com", role: "assignee" },
  { user_id: 2, name: "Michael Chen", email: "michael.chen@company.com", role: "auditor" },
  { user_id: 3, name: "Emma Rodriguez", email: "emma.rodriguez@company.com", role: "auditor" },
  { user_id: 4, name: "David Thompson", email: "david.thompson@company.com", role: "reviewer" },
  { user_id: 5, name: "Lisa Wang", email: "lisa.wang@company.com", role: "reviewer" },
  { user_id: 6, name: "James Wilson", email: "james.wilson@company.com", role: "admin" },
];

export const mockSLAs = [
  {
    sla_id: 1,
    title: "Cloud Infrastructure Service Level Agreement",
    description: "SLA for cloud infrastructure services including uptime, response time, and security metrics",
    start_date: "2024-01-01",
    end_date: "2024-12-31",
    status: "approved",
    parties: ["TechCorp Inc.", "CloudProvider Solutions"],
    created_at: "2024-01-01T00:00:00Z"
  },
  {
    sla_id: 2,
    title: "Customer Support Service Agreement",
    description: "Service level agreement for customer support operations",
    start_date: "2024-01-01",
    end_date: "2024-12-31",
    status: "approved",
    parties: ["TechCorp Inc.", "Support Services Ltd"],
    created_at: "2024-01-01T00:00:00Z"
  },
  {
    sla_id: 3,
    title: "Data Processing Service Agreement",
    description: "SLA for data processing and analytics services",
    start_date: "2024-02-01",
    end_date: "2025-01-31",
    status: "approved",
    parties: ["TechCorp Inc.", "DataAnalytics Pro"],
    created_at: "2024-02-01T00:00:00Z"
  }
];

export const mockMetrics = [
  {
    metric_id: 1,
    sla_id: 1,
    name: "System Uptime",
    target_value: "99.9%",
    measurement_unit: "percentage",
    measurement_frequency: "monthly",
    penalty_clause: "0.1% service credit for each 0.1% below target",
    methodology: "Automated monitoring of system availability"
  },
  {
    metric_id: 2,
    sla_id: 1,
    name: "Response Time",
    target_value: "200ms",
    measurement_unit: "milliseconds",
    measurement_frequency: "daily",
    penalty_clause: "5% service credit if average exceeds target",
    methodology: "Application performance monitoring"
  },
  {
    metric_id: 3,
    sla_id: 2,
    name: "First Response Time",
    target_value: "4 hours",
    measurement_unit: "hours",
    measurement_frequency: "weekly",
    penalty_clause: "2% service credit for each hour delay",
    methodology: "Ticketing system timestamp analysis"
  },
  {
    metric_id: 4,
    sla_id: 2,
    name: "Customer Satisfaction Score",
    target_value: "4.5/5",
    measurement_unit: "rating",
    measurement_frequency: "monthly",
    methodology: "Post-interaction customer surveys"
  },
  {
    metric_id: 5,
    sla_id: 3,
    name: "Data Processing Accuracy",
    target_value: "99.95%",
    measurement_unit: "percentage",
    measurement_frequency: "weekly",
    penalty_clause: "1% service credit for each 0.1% below target",
    methodology: "Data validation and quality checks"
  }
];

export const mockQuestions = [
  // System Uptime Questions
  {
    question_id: 1,
    metric_id: 1,
    question_text: "What was the actual system uptime percentage for this period?",
    question_type: "number",
    is_required: true,
    scoring_weightings: 40
  },
  {
    question_id: 2,
    metric_id: 1,
    question_text: "Were there any planned maintenance windows?",
    question_type: "boolean",
    is_required: true,
    scoring_weightings: 10
  },
  {
    question_id: 3,
    metric_id: 1,
    question_text: "Describe any unplanned outages and their root causes",
    question_type: "text",
    is_required: false,
    scoring_weightings: 30
  },
  // Response Time Questions
  {
    question_id: 4,
    metric_id: 2,
    question_text: "What was the average response time?",
    question_type: "number",
    is_required: true,
    scoring_weightings: 50
  },
  {
    question_id: 5,
    metric_id: 2,
    question_text: "Were there any response time spikes above 500ms?",
    question_type: "boolean",
    is_required: true,
    scoring_weightings: 25
  },
  // Support Questions
  {
    question_id: 6,
    metric_id: 3,
    question_text: "What was the average first response time?",
    question_type: "number",
    is_required: true,
    scoring_weightings: 60
  },
  {
    question_id: 7,
    metric_id: 4,
    question_text: "What was the average customer satisfaction score?",
    question_type: "number",
    is_required: true,
    scoring_weightings: 70
  }
];

export const mockAudits = [
  {
    audit_id: 1,
    title: "Q3 2024 Cloud Infrastructure Audit",
    scope: "Review of uptime and response time metrics for Q3",
    assignee_id: 1,
    auditor_id: 2,
    reviewer_id: 4,
    assign_date: "2024-09-01",
    due_date: "2024-09-15",
    frequency: "quarterly",
    status: "in_progress",
    metric_id: 1,
    sla_id: 1,
    review_status: "pending",
    audit_type: "internal",
    business_unit: "IT Operations",
    role: "Infrastructure Auditor",
    responsibility: "Verify system performance metrics",
    created_at: "2024-09-01T09:00:00Z",
    updated_at: "2024-09-05T14:30:00Z"
  },
  {
    audit_id: 2,
    title: "August 2024 Customer Support Review",
    scope: "Monthly review of support response times and satisfaction",
    assignee_id: 1,
    auditor_id: 3,
    reviewer_id: 5,
    assign_date: "2024-09-01",
    due_date: "2024-09-10",
    frequency: "monthly",
    status: "under_review",
    completion_date: "2024-09-08",
    metric_id: 3,
    sla_id: 2,
    review_status: "pending",
    audit_type: "internal",
    business_unit: "Customer Success",
    role: "Support Auditor",
    responsibility: "Review support team performance metrics",
    created_at: "2024-09-01T10:00:00Z",
    updated_at: "2024-09-08T16:45:00Z"
  },
  {
    audit_id: 3,
    title: "Data Processing Accuracy Audit - Week 35",
    scope: "Weekly data accuracy verification",
    assignee_id: 1,
    auditor_id: 2,
    reviewer_id: 4,
    assign_date: "2024-09-02",
    due_date: "2024-09-09",
    frequency: "weekly",
    status: "completed",
    completion_date: "2024-09-07",
    metric_id: 5,
    sla_id: 3,
    review_status: "approved",
    review_date: "2024-09-08",
    audit_type: "internal",
    business_unit: "Data Operations",
    role: "Data Quality Auditor",
    responsibility: "Verify data processing accuracy",
    created_at: "2024-09-02T08:00:00Z",
    updated_at: "2024-09-08T11:20:00Z"
  },
  {
    audit_id: 4,
    title: "Response Time Performance Review",
    scope: "Daily monitoring of API response times",
    assignee_id: 1,
    auditor_id: 3,
    reviewer_id: 5,
    assign_date: "2024-09-10",
    due_date: "2024-09-17",
    frequency: "weekly",
    status: "created",
    metric_id: 2,
    sla_id: 1,
    review_status: "pending",
    audit_type: "internal",
    business_unit: "Platform Engineering",
    role: "Performance Auditor",
    responsibility: "Monitor and verify response time metrics",
    created_at: "2024-09-10T09:00:00Z",
    updated_at: "2024-09-10T09:00:00Z"
  }
];

export const mockAuditFindings = [
  {
    audit_finding_id: 1,
    audit_id: 3,
    metrics_id: 5,
    evidence: "Automated data validation reports, error logs, and correction records",
    user_id: 2,
    how_to_verify: "Review data validation pipeline logs and cross-reference with manual spot checks",
    impact_recommendations: "Implement additional validation rules for edge cases identified",
    details_of_finding: "Data processing accuracy achieved 99.97%, exceeding the target of 99.95%. Minor issues identified in timezone handling for international data sources.",
    comment: "Overall performance excellent with room for improvement in edge case handling",
    check_date: "2024-09-07",
    questionnaire_responses: {
      questions: [],
      responses: {
        "accuracy_percentage": "99.97",
        "edge_cases_identified": "3",
        "corrective_actions": "Implemented timezone normalization"
      },
      status: "completed"
    },
    created_at: "2024-09-07T14:30:00Z",
    updated_at: "2024-09-07T16:45:00Z"
  }
];

// Utility functions to get related data
export const getUserById = (id) => 
  mockUsers.find(user => user.user_id === id);

export const getSLAById = (id) => 
  mockSLAs.find(sla => sla.sla_id === id);

export const getMetricById = (id) => 
  mockMetrics.find(metric => metric.metric_id === id);

export const getMetricsBySLA = (slaId) => 
  mockMetrics.filter(metric => metric.sla_id === slaId);

export const getQuestionsByMetric = (metricId) => 
  mockQuestions.filter(question => question.metric_id === metricId);

export const getAuditsByUser = (userId, role) => {
  if (role === 'auditor') {
    return mockAudits.filter(audit => audit.auditor_id === userId);
  }
  return mockAudits.filter(audit => audit.reviewer_id === userId);
};

export const getAuditsByStatus = (status) => 
  mockAudits.filter(audit => audit.status === status);

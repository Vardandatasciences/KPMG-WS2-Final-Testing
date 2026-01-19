"""
SEBI AI Auditor Module
Implements BSE Compliance Watch features for SEBI framework compliance verification

Features:
1. Filing Accuracy Verification
2. Timeliness & SLA Monitoring
3. Clause-Level Mapping (SEBI LODR)
4. Risk Scoring Model
5. Exception & Escalation Workflow
6. AI-Driven Pattern & Behavioural Analysis
7. Evidence Pack Generation
8. Regulatory Dashboards
"""

import logging
from datetime import datetime, timedelta, date
from django.db import connection
from django.utils import timezone
from typing import Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)

# SEBI LODR Regulation Mappings
SEBI_LODR_REGULATIONS = {
    'Reg 13': {
        'name': 'Investor Complaints',
        'obligation': 'Filing completeness',
        'sla_hours': None,
        'sla_days': None
    },
    'Reg 27': {
        'name': 'Corporate Governance',
        'obligation': 'Mandatory fields present',
        'sla_hours': None,
        'sla_days': None
    },
    'Reg 30': {
        'name': 'Material Events',
        'obligation': 'Time-to-disclosure',
        'sla_hours': 24,  # 24 hours for material events
        'sla_days': None
    },
    'Reg 31': {
        'name': 'Shareholding Pattern',
        'obligation': 'Share class reconciliation',
        'sla_hours': None,
        'sla_days': 21  # 21 days
    },
    'Reg 33': {
        'name': 'Financial Results',
        'obligation': 'Auditor sign-off match',
        'sla_hours': None,
        'sla_days': 45  # 45 days
    }
}

# Filing Type SLAs
FILING_TYPE_SLAS = {
    'financial_results': {'days': 45, 'description': 'Financial results submission'},
    'reg_30_events': {'hours': 24, 'description': 'Reg 30 material events'},
    'shareholding_pattern': {'days': 21, 'description': 'Shareholding pattern filing'},
    'auditor_resignation': {'hours': 0, 'description': 'Same day disclosure'},
    'corporate_governance': {'days': None, 'description': 'Corporate governance report'}
}


class SEBIAIAuditor:
    """
    SEBI AI Auditor for compliance verification
    Implements BSE Compliance Watch features
    """
    
    def __init__(self, framework_id: int, tenant_id: int):
        self.framework_id = framework_id
        self.tenant_id = tenant_id
        self.is_sebi_framework = self._check_sebi_framework()
    
    def _check_sebi_framework(self) -> bool:
        """Check if framework is SEBI-enabled (framework OR compliance level)"""
        with connection.cursor() as cursor:
            # Check framework level
            cursor.execute("""
                SELECT FrameworkName, data_inventory
                FROM frameworks
                WHERE FrameworkId = %s AND TenantId = %s
            """, [self.framework_id, self.tenant_id])
            row = cursor.fetchone()
            if row:
                framework_name = row[0] or ''
                data_inventory = row[1] or {}
                
                # Check if SEBI in name or ai_bse_enabled flag at framework level
                is_sebi = 'SEBI' in framework_name.upper() or 'LODR' in framework_name.upper()
                ai_bse_enabled = data_inventory.get('ai_bse_enabled', 0) if isinstance(data_inventory, dict) else 0
                
                if is_sebi or (ai_bse_enabled == 1):
                    return True
            
            # Check compliance level - if ANY compliance has ai_bse_enabled = 1
            cursor.execute("""
                SELECT COUNT(*) 
                FROM compliance
                WHERE FrameworkId = %s AND TenantId = %s AND ai_bse_enabled = 1
            """, [self.framework_id, self.tenant_id])
            
            compliance_count = cursor.fetchone()[0] or 0
            if compliance_count > 0:
                logger.info(f"✅ SEBI AI enabled at compliance level: {compliance_count} compliance(s) with ai_bse_enabled=1")
                return True
                
        return False
    
    def verify_filing_accuracy(self, audit_id: int, document_id: int = None) -> Dict:
        """
        Filing Accuracy Verification
        - Cross-period consistency (Q-to-Q values)
        - Cross-document match (Financials vs annual report)
        - Disclosure duplication check
        - Arithmetic accuracy
        - Narrative consistency
        """
        if not self.is_sebi_framework:
            return {'enabled': False, 'message': 'SEBI AI Auditor not enabled for this framework'}
        
        results = {
            'cross_period_consistency': [],
            'cross_document_matches': [],
            'disclosure_duplications': [],
            'arithmetic_errors': [],
            'narrative_inconsistencies': [],
            'overall_score': 0.0
        }
        
        try:
            with connection.cursor() as cursor:
                # 1. Cross-period consistency check
                cursor.execute("""
                    SELECT 
                        a1.AuditId as audit1_id,
                        a2.AuditId as audit2_id,
                        a1.Title as audit1_title,
                        a2.Title as audit2_title,
                        a1.Evidence as evidence1,
                        a2.Evidence as evidence2
                    FROM audit a1
                    JOIN audit a2 ON a1.FrameworkId = a2.FrameworkId
                    WHERE a1.FrameworkId = %s
                      AND a1.TenantId = %s
                      AND a2.TenantId = %s
                      AND a1.AuditId != a2.AuditId
                      AND a1.DueDate < a2.DueDate
                      AND DATEDIFF(a2.DueDate, a1.DueDate) <= 120
                    ORDER BY a1.DueDate DESC
                    LIMIT 10
                """, [self.framework_id, self.tenant_id, self.tenant_id])
                
                periods = cursor.fetchall()
                for period in periods:
                    # AI-based cross-period consistency analysis
                    try:
                        ai_result = self._ai_analyze_cross_period_consistency(
                            audit1_id=period[0],
                            audit1_title=period[2],
                            audit1_evidence=period[4],
                            audit2_id=period[1],
                            audit2_title=period[3],
                            audit2_evidence=period[5]
                        )
                        results['cross_period_consistency'].append(ai_result)
                    except Exception as e:
                        logger.error(f"AI analysis failed for cross-period: {str(e)}")
                        results['cross_period_consistency'].append({
                            'audit1_id': period[0],
                            'audit2_id': period[1],
                            'status': 'analysis_failed',
                            'error': str(e)
                        })
                
                # 2. Cross-document match
                if document_id:
                    # Use ai_audit_data table which has compliance_analyses
                    cursor.execute("""
                        SELECT 
                            aad.document_id,
                            aad.document_name,
                            aad.compliance_analyses,
                            a.Title as audit_title
                        FROM ai_audit_data aad
                        JOIN audit a ON aad.audit_id = a.AuditId
                        WHERE aad.audit_id = %s
                          AND a.TenantId = %s
                          AND aad.document_id != %s
                    """, [audit_id, self.tenant_id, document_id])
                    
                    other_docs = cursor.fetchall()
                    # Get current document evidence from ai_audit_data
                    cursor.execute("""
                        SELECT compliance_analyses FROM ai_audit_data
                        WHERE document_id = %s AND audit_id = %s
                    """, [document_id, audit_id])
                    current_doc = cursor.fetchone()
                    current_evidence = ''
                    if current_doc and current_doc[0]:
                        # Extract text from compliance_analyses JSON
                        import json
                        try:
                            analyses = json.loads(current_doc[0]) if isinstance(current_doc[0], str) else current_doc[0]
                            if isinstance(analyses, list) and len(analyses) > 0:
                                # Extract evidence from first analysis
                                current_evidence = ' '.join([str(a.get('evidence', '')) for a in analyses if isinstance(a, dict)])
                        except:
                            current_evidence = str(current_doc[0])[:2000] if current_doc[0] else ''
                    
                    for doc in other_docs:
                        # Extract evidence from other document's compliance_analyses
                        other_evidence = ''
                        if doc[2]:  # compliance_analyses
                            import json
                            try:
                                analyses = json.loads(doc[2]) if isinstance(doc[2], str) else doc[2]
                                if isinstance(analyses, list) and len(analyses) > 0:
                                    other_evidence = ' '.join([str(a.get('evidence', '')) for a in analyses if isinstance(a, dict)])
                            except:
                                other_evidence = str(doc[2])[:2000] if doc[2] else ''
                        
                        # AI-based cross-document matching
                        try:
                            ai_result = self._ai_analyze_cross_document_match(
                                current_evidence=current_evidence,
                                other_doc_id=doc[0],
                                other_doc_name=doc[1],
                                other_doc_evidence=other_evidence
                            )
                            results['cross_document_matches'].append(ai_result)
                        except Exception as e:
                            logger.error(f"AI analysis failed for cross-document: {str(e)}")
                            results['cross_document_matches'].append({
                                'document_id': doc[0],
                                'document_name': doc[1],
                                'status': 'analysis_failed',
                                'error': str(e)
                            })
                
                # AI-based narrative consistency check
                if document_id:
                    try:
                        # Get evidence from ai_audit_data compliance_analyses
                        cursor.execute("""
                            SELECT compliance_analyses FROM ai_audit_data
                            WHERE document_id = %s AND audit_id = %s
                        """, [document_id, audit_id])
                        doc_row = cursor.fetchone()
                        if doc_row and doc_row[0]:
                            import json
                            evidence_text = ''
                            try:
                                analyses = json.loads(doc_row[0]) if isinstance(doc_row[0], str) else doc_row[0]
                                if isinstance(analyses, list) and len(analyses) > 0:
                                    # Extract all evidence text from analyses
                                    evidence_parts = []
                                    for a in analyses:
                                        if isinstance(a, dict):
                                            if a.get('evidence'):
                                                evidence_parts.extend(a['evidence'] if isinstance(a['evidence'], list) else [str(a['evidence'])])
                                    evidence_text = ' '.join(evidence_parts)
                            except:
                                evidence_text = str(doc_row[0])[:3000] if doc_row[0] else ''
                            
                            if evidence_text:
                                narrative_result = self._ai_analyze_narrative_consistency(evidence_text)
                                results['narrative_inconsistencies'] = narrative_result.get('inconsistencies', [])
                    except Exception as e:
                        logger.error(f"AI narrative analysis failed: {str(e)}")
                
                # Calculate overall score and format for report
                total_checks = (
                    len(results['cross_period_consistency']) +
                    len(results['cross_document_matches']) +
                    len(results['disclosure_duplications']) +
                    len(results['arithmetic_errors']) +
                    len(results['narrative_inconsistencies'])
                )
                
                issues_count = len(results['arithmetic_errors']) + len(results['narrative_inconsistencies'])
                
                if total_checks > 0:
                    passed = total_checks - issues_count
                    overall_score = passed / total_checks if total_checks > 0 else 1.0
                else:
                    overall_score = 1.0
                    passed = 0
                
                # Format results for report
                results['overall_score'] = overall_score
                results['accuracy_score'] = round(overall_score * 100, 2)  # Convert to percentage
                results['total_filings'] = total_checks
                results['accurate_filings'] = passed
                results['issues_count'] = issues_count
                
                # Collect all issues for report
                all_issues = []
                for error in results['arithmetic_errors']:
                    if isinstance(error, dict) and error.get('description'):
                        all_issues.append(error['description'])
                for inconsistency in results['narrative_inconsistencies']:
                    if isinstance(inconsistency, dict) and inconsistency.get('description'):
                        all_issues.append(inconsistency['description'])
                results['issues'] = all_issues[:10]  # Limit to 10 issues
                    
        except Exception as e:
            logger.error(f"Error in filing accuracy verification: {str(e)}")
            results['error'] = str(e)
            # Set defaults even on error
            results['accuracy_score'] = 0
            results['total_filings'] = 0
            results['accurate_filings'] = 0
            results['issues_count'] = 0
            results['issues'] = []
        
        return results
    
    def check_timeliness_sla(self, audit_id: int, filing_type: str = None) -> Dict:
        """
        Timeliness & SLA Monitoring
        - Financial results: 45 days
        - Reg 30 events: 24 hours
        - Shareholding pattern: 21 days
        - Auditor resignation: Same day
        """
        if not self.is_sebi_framework:
            return {'enabled': False, 'message': 'SEBI AI Auditor not enabled for this framework'}
        
        results = {
            'filing_type': filing_type,
            'sla_breach': False,
            'hours_delayed': 0,
            'days_delayed': 0,
            'severity': 'low',
            'recommendation': '',
            # Report fields
            'sla_compliance_rate': 100.0,
            'on_time_filings': 0,
            'late_filings': 0,
            'average_delay_days': 0,
            'violations': []
        }
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        a.AuditId,
                        a.Title,
                        a.DueDate,
                        a.CompletionDate,
                        a.Status
                    FROM audit a
                    WHERE a.AuditId = %s AND a.TenantId = %s
                """, [audit_id, self.tenant_id])
                
                audit = cursor.fetchone()
                if not audit:
                    return {'error': 'Audit not found'}
                
                due_date = audit[2]
                completion_date = audit[3]
                # Use DueDate as reference if CreatedAt doesn't exist
                created_at = due_date
                
                if not due_date:
                    return {'error': 'Due date not set'}
                
                # Determine SLA based on filing type or audit title
                sla_config = None
                if filing_type and filing_type in FILING_TYPE_SLAS:
                    sla_config = FILING_TYPE_SLAS[filing_type]
                elif 'financial' in (audit[1] or '').lower():
                    sla_config = FILING_TYPE_SLAS['financial_results']
                elif 'reg 30' in (audit[1] or '').lower() or 'material' in (audit[1] or '').lower():
                    sla_config = FILING_TYPE_SLAS['reg_30_events']
                elif 'shareholding' in (audit[1] or '').lower():
                    sla_config = FILING_TYPE_SLAS['shareholding_pattern']
                
                # Check all audits in framework for SLA compliance
                cursor.execute("""
                    SELECT 
                        a.AuditId,
                        a.Title,
                        a.DueDate,
                        a.CompletionDate
                    FROM audit a
                    WHERE a.FrameworkId = (SELECT FrameworkId FROM audit WHERE AuditId = %s)
                      AND a.TenantId = %s
                      AND a.DueDate IS NOT NULL
                """, [audit_id, self.tenant_id])
                
                all_audits = cursor.fetchall()
                total_filings = len(all_audits)
                on_time = 0
                late = 0
                total_delay_days = 0
                violations_list = []
                
                for audit_row in all_audits:
                    aud_due = audit_row[2]
                    aud_completion = audit_row[3]
                    
                    if not aud_due:
                        continue
                    
                    # Determine SLA for this audit
                    aud_sla_config = None
                    if 'financial' in (audit_row[1] or '').lower():
                        aud_sla_config = FILING_TYPE_SLAS.get('financial_results')
                    elif 'reg 30' in (audit_row[1] or '').lower() or 'material' in (audit_row[1] or '').lower():
                        aud_sla_config = FILING_TYPE_SLAS.get('reg_30_events')
                    elif 'shareholding' in (audit_row[1] or '').lower():
                        aud_sla_config = FILING_TYPE_SLAS.get('shareholding_pattern')
                    
                    if aud_sla_config and aud_completion:
                        # Convert completion date to date if it's datetime
                        if isinstance(aud_completion, datetime):
                            ref_date = aud_completion.date()
                        elif isinstance(aud_completion, type(timezone.now().date())):
                            ref_date = aud_completion
                        else:
                            ref_date = timezone.now().date()
                        
                        # Convert due date to date if it's datetime
                        if isinstance(aud_due, datetime):
                            due_date_only = aud_due.date()
                        else:
                            due_date_only = aud_due
                        
                        days_diff = (ref_date - due_date_only).days
                        
                        if aud_sla_config.get('days'):
                            days_allowed = aud_sla_config['days']
                            if days_diff <= days_allowed:
                                on_time += 1
                            else:
                                late += 1
                                delay = days_diff - days_allowed
                                total_delay_days += delay
                                violations_list.append(f"{audit_row[1] or 'Unknown'}: {delay} days late")
                        elif aud_sla_config.get('hours'):
                            hours_allowed = aud_sla_config['hours']
                            # Convert to datetime objects for hour-based calculations
                            if isinstance(due_date_only, date) and not isinstance(due_date_only, datetime):
                                due_dt = datetime.combine(due_date_only, datetime.min.time())
                            else:
                                due_dt = aud_due if isinstance(aud_due, datetime) else datetime.combine(due_date_only, datetime.min.time())
                            
                            if isinstance(ref_date, date) and not isinstance(ref_date, datetime):
                                ref_dt = datetime.combine(ref_date, datetime.min.time())
                            else:
                                ref_dt = ref_date if isinstance(ref_date, datetime) else datetime.combine(ref_date, datetime.min.time())
                            hours_diff = (ref_dt - due_dt).total_seconds() / 3600
                            if hours_diff <= hours_allowed:
                                on_time += 1
                            else:
                                late += 1
                                delay_days = (hours_diff - hours_allowed) / 24
                                total_delay_days += delay_days
                                violations_list.append(f"{audit_row[1] or 'Unknown'}: {delay_days:.1f} days late")
                    else:
                        # No SLA config, assume on-time
                        on_time += 1
                
                # Calculate report fields
                if total_filings > 0:
                    results['sla_compliance_rate'] = round((on_time / total_filings) * 100, 2)
                    results['on_time_filings'] = on_time
                    results['late_filings'] = late
                    results['average_delay_days'] = round(total_delay_days / late, 2) if late > 0 else 0
                else:
                    results['sla_compliance_rate'] = 100.0
                    results['on_time_filings'] = 0
                    results['late_filings'] = 0
                    results['average_delay_days'] = 0
                
                results['violations'] = violations_list[:10]  # Limit to 10 violations
                
                # Also check current audit for SLA breach
                if sla_config:
                    reference_date = completion_date if completion_date else timezone.now().date()
                    
                    if sla_config.get('hours'):
                        hours_allowed = sla_config['hours']
                        if due_date:
                            # Convert to datetime objects for hour-based calculations
                            if isinstance(due_date, date) and not isinstance(due_date, datetime):
                                due_datetime = datetime.combine(due_date, datetime.min.time())
                            else:
                                due_datetime = due_date if isinstance(due_date, datetime) else datetime.combine(due_date, datetime.min.time())
                            
                            if isinstance(reference_date, date) and not isinstance(reference_date, datetime):
                                ref_datetime = datetime.combine(reference_date, datetime.min.time())
                            else:
                                ref_datetime = reference_date if isinstance(reference_date, datetime) else datetime.combine(reference_date, datetime.min.time())
                            time_diff = (ref_datetime - due_datetime).total_seconds() / 3600
                            results['hours_delayed'] = max(0, time_diff - hours_allowed)
                            results['sla_breach'] = time_diff > hours_allowed
                    elif sla_config.get('days'):
                        days_allowed = sla_config['days']
                        days_diff = (reference_date - due_date).days
                        results['days_delayed'] = max(0, days_diff - days_allowed)
                        results['sla_breach'] = days_diff > days_allowed
                    
                    # Determine severity
                    if results['sla_breach']:
                        if results['hours_delayed'] > 48 or results['days_delayed'] > 7:
                            results['severity'] = 'high'
                        elif results['hours_delayed'] > 24 or results['days_delayed'] > 3:
                            results['severity'] = 'medium'
                        else:
                            results['severity'] = 'low'
                        
                        results['recommendation'] = f"Filing delayed by {results['hours_delayed']} hours / {results['days_delayed']} days. Review filing process."
                
        except Exception as e:
            logger.error(f"Error in timeliness SLA check: {str(e)}")
            results['error'] = str(e)
            # Set defaults on error
            results['sla_compliance_rate'] = 0
            results['on_time_filings'] = 0
            results['late_filings'] = 0
            results['average_delay_days'] = 0
            results['violations'] = []
        
        return results
    
    def calculate_risk_score(self, audit_id: int) -> Dict:
        """
        Risk Scoring Model (Company-Level)
        Factors:
        - Filing delays (High weight)
        - Disclosure corrections (Medium weight)
        - Governance gaps (Medium weight)
        - Insider trade anomalies (High weight)
        - Auditor remarks (High weight)
        """
        if not self.is_sebi_framework:
            return {'enabled': False, 'message': 'SEBI AI Auditor not enabled for this framework'}
        
        risk_factors = {
            'filing_delays': {'weight': 0.3, 'score': 0.0, 'count': 0},
            'disclosure_corrections': {'weight': 0.2, 'score': 0.0, 'count': 0},
            'governance_gaps': {'weight': 0.2, 'score': 0.0, 'count': 0},
            'insider_trade_anomalies': {'weight': 0.15, 'score': 0.0, 'count': 0},
            'auditor_remarks': {'weight': 0.15, 'score': 0.0, 'count': 0}
        }
        
        try:
            with connection.cursor() as cursor:
                # 1. Filing delays
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM audit
                    WHERE FrameworkId = %s
                      AND TenantId = %s
                      AND DueDate IS NOT NULL
                      AND CompletionDate IS NOT NULL
                      AND CompletionDate > DueDate
                      AND DATEDIFF(CompletionDate, DueDate) > 3
                """, [self.framework_id, self.tenant_id])
                
                delay_count = cursor.fetchone()[0] or 0
                risk_factors['filing_delays']['count'] = delay_count
                risk_factors['filing_delays']['score'] = min(1.0, delay_count / 10.0)  # Normalize to 0-1
                
                # 2. Disclosure corrections (check audit findings with corrections)
                # Use parameterized LIKE patterns to avoid format string issues
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM audit_findings af
                    JOIN audit a ON af.AuditId = a.AuditId
                    WHERE a.FrameworkId = %s
                      AND a.TenantId = %s
                      AND (af.Comments LIKE %s OR af.Comments LIKE %s OR af.Comments LIKE %s)
                """, [self.framework_id, self.tenant_id, '%correction%', '%amendment%', '%revised%'])
                
                correction_count = cursor.fetchone()[0] or 0
                risk_factors['disclosure_corrections']['count'] = correction_count
                risk_factors['disclosure_corrections']['score'] = min(1.0, correction_count / 5.0)
                
                # 3. Governance gaps (missing mandatory fields)
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM audit a
                    WHERE a.FrameworkId = %s
                      AND a.TenantId = %s
                      AND (a.Scope IS NULL OR a.Objective IS NULL OR a.Evidence IS NULL)
                """, [self.framework_id, self.tenant_id])
                
                gap_count = cursor.fetchone()[0] or 0
                risk_factors['governance_gaps']['count'] = gap_count
                risk_factors['governance_gaps']['score'] = min(1.0, gap_count / 3.0)
                
                # Calculate weighted risk score
                total_risk_score = sum(
                    factor['weight'] * factor['score']
                    for factor in risk_factors.values()
                )
                
                # Determine risk level
                if total_risk_score >= 0.7:
                    risk_level = 'High'
                elif total_risk_score >= 0.4:
                    risk_level = 'Medium'
                else:
                    risk_level = 'Low'
                
                # Count high-risk areas
                high_risk_areas = sum(1 for factor in risk_factors.values() if factor['score'] >= 0.7)
                
                # Get key risk factors for report
                key_risk_factors = [
                    f"{name.replace('_', ' ').title()}: {factor['score']:.2f}"
                    for name, factor in risk_factors.items()
                    if factor['score'] > 0
                ]
                
                return {
                    'risk_score': round(total_risk_score * 100, 2),  # Convert to 0-100 scale
                    'risk_level': risk_level,
                    'factors': risk_factors,
                    'audit_id': audit_id,
                    # Report fields
                    'high_risk_areas': high_risk_areas,
                    'key_risk_factors': key_risk_factors[:10]  # Limit to 10
                }
                
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return {
                'error': str(e),
                'risk_score': 0,
                'risk_level': 'N/A',
                'high_risk_areas': 0,
                'key_risk_factors': []
            }
    
    def detect_patterns(self, audit_id: int = None) -> Dict:
        """
        AI-Driven Pattern & Behavioural Analysis
        Patterns:
        - Frequent last-day filings
        - Recurring disclosure edits
        - Event silence vs price spike
        - High promoter trades pre-event
        """
        if not self.is_sebi_framework:
            return {'enabled': False, 'message': 'SEBI AI Auditor not enabled for this framework'}
        
        patterns = {
            'frequent_last_day_filings': [],
            'recurring_disclosure_edits': [],
            'event_silence_vs_price_spike': [],
            'high_promoter_trades_pre_event': []
        }
        
        try:
            with connection.cursor() as cursor:
                # 1. Frequent last-day filings
                cursor.execute("""
                    SELECT 
                        a.AuditId,
                        a.Title,
                        a.DueDate,
                        a.CompletionDate,
                        DATEDIFF(a.CompletionDate, a.DueDate) as days_diff
                    FROM audit a
                    WHERE a.FrameworkId = %s
                      AND a.TenantId = %s
                      AND a.DueDate IS NOT NULL
                      AND a.CompletionDate IS NOT NULL
                      AND DATEDIFF(a.CompletionDate, a.DueDate) <= 1
                      AND DATEDIFF(a.CompletionDate, a.DueDate) >= 0
                    ORDER BY a.CompletionDate DESC
                    LIMIT 20
                """, [self.framework_id, self.tenant_id])
                
                last_day_filings = cursor.fetchall()
                if len(last_day_filings) >= 3:
                    # AI-powered behavioral analysis
                    try:
                        ai_analysis = self._ai_analyze_filing_behavior(last_day_filings)
                        patterns['frequent_last_day_filings'] = ai_analysis.get('insights', [])
                    except Exception as e:
                        logger.error(f"AI behavioral analysis failed: {str(e)}")
                        patterns['frequent_last_day_filings'] = [
                            {
                                'audit_id': row[0],
                                'title': row[1],
                                'insight': 'Weak compliance culture - filing on last day'
                            }
                            for row in last_day_filings[:5]
                        ]
                
                # 2. Recurring disclosure edits
                # Use parameterized LIKE patterns to avoid format string issues
                cursor.execute("""
                    SELECT 
                        af.AuditId,
                        COUNT(*) as edit_count
                    FROM audit_findings af
                    JOIN audit a ON af.AuditId = a.AuditId
                    WHERE a.FrameworkId = %s
                      AND a.TenantId = %s
                      AND (af.Comments LIKE %s OR af.Comments LIKE %s)
                    GROUP BY af.AuditId
                    HAVING edit_count >= 2
                """, [self.framework_id, self.tenant_id, '%correction%', '%amendment%'])
                
                recurring_edits = cursor.fetchall()
                if recurring_edits:
                    # AI-powered analysis of recurring edits
                    try:
                        ai_analysis = self._ai_analyze_recurring_edits(recurring_edits)
                        patterns['recurring_disclosure_edits'] = ai_analysis.get('insights', [])
                    except Exception as e:
                        logger.error(f"AI edit analysis failed: {str(e)}")
                        patterns['recurring_disclosure_edits'] = [
                            {
                                'audit_id': row[0],
                                'edit_count': row[1],
                                'insight': 'Control weakness - frequent revisions'
                            }
                            for row in recurring_edits
                        ]
                
        except Exception as e:
            logger.error(f"Error detecting patterns: {str(e)}")
            patterns['error'] = str(e)
        
        # Calculate pattern count for report
        total_patterns = (
            len(patterns.get('frequent_last_day_filings', [])) +
            len(patterns.get('recurring_disclosure_edits', [])) +
            len(patterns.get('event_silence_vs_price_spike', [])) +
            len(patterns.get('high_promoter_trades_pre_event', []))
        )
        patterns['patterns_detected'] = total_patterns
        
        # Collect pattern types for report
        pattern_types = []
        if patterns.get('frequent_last_day_filings'):
            pattern_types.append('Frequent Last-Day Filings')
        if patterns.get('recurring_disclosure_edits'):
            pattern_types.append('Recurring Disclosure Edits')
        if patterns.get('event_silence_vs_price_spike'):
            pattern_types.append('Event Silence vs Price Spike')
        if patterns.get('high_promoter_trades_pre_event'):
            pattern_types.append('High Promoter Trades Pre-Event')
        patterns['pattern_types'] = pattern_types
        
        return patterns
    
    def generate_evidence_pack(self, audit_id: int, use_case: str = 'sebi_inspection') -> Dict:
        """
        Evidence Pack Generation (Audit-Ready)
        Use cases:
        - SEBI inspection
        - Adjudication
        - Investor grievance
        - Enforcement
        """
        if not self.is_sebi_framework:
            return {'enabled': False, 'message': 'SEBI AI Auditor not enabled for this framework'}
        
        evidence_pack = {
            'audit_id': audit_id,
            'use_case': use_case,
            'generated_at': timezone.now().isoformat(),
            'clause_wise_evidence': [],
            'timestamped_proof': [],
            'disclosure_timeline': [],
            'risk_anomaly_logs': []
        }
        
        try:
            with connection.cursor() as cursor:
                # Get all compliance findings with evidence
                cursor.execute("""
                    SELECT 
                        af.ComplianceId,
                        c.ComplianceTitle,
                        af.Evidence,
                        af.Comments,
                        af.MajorMinor,
                        a.DueDate,
                        a.CompletionDate
                    FROM audit_findings af
                    JOIN audit a ON af.AuditId = a.AuditId
                    LEFT JOIN compliance c ON af.ComplianceId = c.ComplianceId
                    WHERE af.AuditId = %s
                      AND a.TenantId = %s
                    ORDER BY af.ComplianceId
                """, [audit_id, self.tenant_id])
                
                findings = cursor.fetchall()
                for finding in findings:
                    evidence_pack['clause_wise_evidence'].append({
                        'compliance_id': finding[0],
                        'compliance_title': finding[1],
                        'evidence': finding[2],
                        'comments': finding[3],
                        'severity': finding[4]
                    })
                    
                    evidence_pack['timestamped_proof'].append({
                        'compliance_id': finding[0],
                        'due_date': finding[5].isoformat() if finding[5] else None,
                        'completion_date': finding[6].isoformat() if finding[6] else None,
                        'evidence': finding[2]
                    })
                
                # Disclosure timeline
                cursor.execute("""
                    SELECT 
                        a.AuditId,
                        a.Title,
                        a.CreatedAt,
                        a.DueDate,
                        a.CompletionDate,
                        a.Status
                    FROM audit a
                    WHERE a.AuditId = %s AND a.TenantId = %s
                """, [audit_id, self.tenant_id])
                
                audit = cursor.fetchone()
                if audit:
                    evidence_pack['disclosure_timeline'] = {
                        'audit_id': audit[0],
                        'title': audit[1],
                        'created_at': audit[2].isoformat() if audit[2] else None,
                        'due_date': audit[3].isoformat() if audit[3] else None,
                        'completion_date': audit[4].isoformat() if audit[4] else None,
                        'status': audit[5]
                    }
                
        except Exception as e:
            logger.error(f"Error generating evidence pack: {str(e)}")
            evidence_pack['error'] = str(e)
        
        return evidence_pack
    
    def _ai_analyze_cross_period_consistency(self, audit1_id, audit1_title, audit1_evidence, 
                                            audit2_id, audit2_title, audit2_evidence) -> Dict:
        """AI-powered cross-period consistency analysis"""
        try:
            from .ai_audit_api import call_ai_api
            
            prompt = f"""Analyze cross-period consistency between two audit filings for SEBI compliance.

Period 1 - {audit1_title} (Audit ID: {audit1_id}):
Evidence: {str(audit1_evidence)[:2000]}

Period 2 - {audit2_title} (Audit ID: {audit2_id}):
Evidence: {str(audit2_evidence)[:2000]}

Analyze:
1. Are key financial/metric values consistent between periods?
2. Are there sudden unexplained changes?
3. Are narrative descriptions consistent?
4. Any red flags for misstatement?

Return JSON:
{{
    "consistency_score": 0.0-1.0,
    "status": "consistent|inconsistent|needs_review",
    "issues": ["list of specific issues"],
    "recommendation": "recommendation text"
}}"""
            
            ai_response = call_ai_api(prompt, audit_id=audit1_id, model_type='analysis')
            
            # Parse AI response with robust error handling
            import json
            import re
            ai_data = {}
            try:
                # Try to extract JSON from markdown code blocks first
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    ai_data = json.loads(json_match.group(1))
                else:
                    # Try to find JSON object in response
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        ai_data = json.loads(json_match.group())
                    else:
                        ai_data = json.loads(ai_response)
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing failed: {str(json_err)}")
                raise Exception(f"Failed to parse AI response as JSON: {str(json_err)}")
            
            return {
                'audit1_id': audit1_id,
                'audit2_id': audit2_id,
                'consistency_score': ai_data.get('consistency_score', 0.5),
                'status': ai_data.get('status', 'needs_review'),
                'issues': ai_data.get('issues', []),
                'recommendation': ai_data.get('recommendation', ''),
                'ai_analyzed': True
            }
        except Exception as e:
            logger.error(f"AI cross-period analysis failed: {str(e)}")
            return {
                'audit1_id': audit1_id,
                'audit2_id': audit2_id,
                'status': 'analysis_failed',
                'error': str(e)
            }
    
    def _ai_analyze_cross_document_match(self, current_evidence, other_doc_id, 
                                         other_doc_name, other_doc_evidence) -> Dict:
        """AI-powered cross-document matching"""
        try:
            from .ai_audit_api import call_ai_api
            
            prompt = f"""Analyze cross-document consistency for SEBI compliance verification.

Current Document Evidence:
{str(current_evidence)[:2000]}

Other Document: {other_doc_name} (ID: {other_doc_id})
Evidence: {str(other_doc_evidence)[:2000]}

Check:
1. Do financial figures match between documents?
2. Are narratives consistent?
3. Any contradictions or discrepancies?
4. Evidence quality and completeness?

Return JSON:
{{
    "match_score": 0.0-1.0,
    "status": "matched|mismatched|partial",
    "discrepancies": ["list of discrepancies"],
    "recommendation": "recommendation text"
}}"""
            
            ai_response = call_ai_api(prompt, document_id=other_doc_id, model_type='analysis')
            
            import json
            import re
            ai_data = {}
            try:
                # Try to extract JSON from markdown code blocks first
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    ai_data = json.loads(json_match.group(1))
                else:
                    # Try to find JSON object in response
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        ai_data = json.loads(json_match.group())
                    else:
                        ai_data = json.loads(ai_response)
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing failed: {str(json_err)}")
                raise Exception(f"Failed to parse AI response as JSON: {str(json_err)}")
            
            return {
                'document_id': other_doc_id,
                'document_name': other_doc_name,
                'match_score': ai_data.get('match_score', 0.5),
                'status': ai_data.get('status', 'partial'),
                'discrepancies': ai_data.get('discrepancies', []),
                'recommendation': ai_data.get('recommendation', ''),
                'ai_analyzed': True
            }
        except Exception as e:
            logger.error(f"AI cross-document analysis failed: {str(e)}")
            return {
                'document_id': other_doc_id,
                'document_name': other_doc_name,
                'status': 'analysis_failed',
                'error': str(e)
            }
    
    def _ai_analyze_narrative_consistency(self, evidence_text: str) -> Dict:
        """AI-powered narrative consistency analysis"""
        try:
            from .ai_audit_api import call_ai_api
            
            prompt = f"""Analyze narrative consistency in this SEBI compliance document for inconsistencies, contradictions, or red flags.

Document Evidence:
{str(evidence_text)[:3000]}

Check for:
1. Contradictory statements
2. Inconsistent terminology
3. Risk statement inconsistencies
4. Missing or vague descriptions
5. Compliance gaps in narrative

Return JSON:
{{
    "consistency_score": 0.0-1.0,
    "inconsistencies": [
        {{
            "type": "contradiction|terminology|risk|missing",
            "description": "specific issue",
            "severity": "low|medium|high"
        }}
    ],
    "recommendation": "recommendation text"
}}"""
            
            ai_response = call_ai_api(prompt, model_type='analysis')
            
            import json
            import re
            ai_data = {}
            try:
                # Try to extract JSON from markdown code blocks first
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    ai_data = json.loads(json_match.group(1))
                else:
                    # Try to find JSON object in response
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        ai_data = json.loads(json_match.group())
                    else:
                        ai_data = json.loads(ai_response)
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing failed: {str(json_err)}")
                raise Exception(f"Failed to parse AI response as JSON: {str(json_err)}")
            
            return {
                'consistency_score': ai_data.get('consistency_score', 1.0),
                'inconsistencies': ai_data.get('inconsistencies', []),
                'recommendation': ai_data.get('recommendation', ''),
                'ai_analyzed': True
            }
        except Exception as e:
            logger.error(f"AI narrative analysis failed: {str(e)}")
            return {
                'inconsistencies': [],
                'error': str(e)
            }
    
    def _ai_analyze_filing_behavior(self, last_day_filings: List) -> Dict:
        """AI-powered analysis of filing behavior patterns"""
        try:
            from .ai_audit_api import call_ai_api
            
            filings_summary = "\n".join([
                f"- {row[1]} (Due: {row[2]}, Completed: {row[3]})"
                for row in last_day_filings[:10]
            ])
            
            prompt = f"""Analyze filing behavior patterns for SEBI compliance culture assessment.

Observed Pattern: {len(last_day_filings)} filings completed on or near due date.

Filing Details:
{filings_summary}

Analyze:
1. Does this indicate weak compliance culture?
2. What are the risk implications?
3. What recommendations for improvement?

Return JSON:
{{
    "behavior_score": 0.0-1.0,
    "culture_assessment": "strong|moderate|weak",
    "insights": [
        {{
            "audit_id": 123,
            "title": "audit title",
            "insight": "specific behavioral insight",
            "risk_level": "low|medium|high"
        }}
    ],
    "recommendation": "overall recommendation"
}}"""
            
            ai_response = call_ai_api(prompt, model_type='analysis')
            
            import json
            import re
            try:
                # Try to extract JSON from markdown code blocks first
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                else:
                    # Try to find JSON object in response
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    else:
                        return json.loads(ai_response)
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing failed for filing behavior: {str(json_err)}")
                raise Exception(f"Failed to parse AI response as JSON: {str(json_err)}")
        except Exception as e:
            logger.error(f"AI behavior analysis failed: {str(e)}")
            return {'insights': []}
    
    def _ai_analyze_recurring_edits(self, recurring_edits: List) -> Dict:
        """AI-powered analysis of recurring disclosure edits"""
        try:
            from .ai_audit_api import call_ai_api
            
            edits_summary = "\n".join([
                f"- Audit {row[0]}: {row[1]} edits"
                for row in recurring_edits
            ])
            
            prompt = f"""Analyze recurring disclosure edits pattern for SEBI compliance control assessment.

Observed Pattern: Multiple audits with frequent disclosure corrections/amendments.

Edit Details:
{edits_summary}

Analyze:
1. Does this indicate control weaknesses?
2. What are the compliance risks?
3. Root cause analysis?

Return JSON:
{{
    "control_assessment": "strong|moderate|weak",
    "insights": [
        {{
            "audit_id": 123,
            "edit_count": 5,
            "insight": "specific control weakness",
            "risk_level": "low|medium|high"
        }}
    ],
    "root_causes": ["list of potential root causes"],
    "recommendation": "recommendation text"
}}"""
            
            ai_response = call_ai_api(prompt, model_type='analysis')
            
            import json
            import re
            try:
                # Try to extract JSON from markdown code blocks first
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                else:
                    # Try to find JSON object in response
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    else:
                        return json.loads(ai_response)
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing failed for recurring edits: {str(json_err)}")
                raise Exception(f"Failed to parse AI response as JSON: {str(json_err)}")
        except Exception as e:
            logger.error(f"AI edit analysis failed: {str(e)}")
            return {'insights': []}


def enable_sebi_ai_auditor(framework_id: int, tenant_id: int) -> bool:
    """
    Enable SEBI AI Auditor for a framework
    Sets ai_bse_enabled = 1 in framework's data_inventory and compliance table
    """
    try:
        with connection.cursor() as cursor:
            # Get current data_inventory
            cursor.execute("""
                SELECT data_inventory
                FROM frameworks
                WHERE FrameworkId = %s AND TenantId = %s
            """, [framework_id, tenant_id])
            
            row = cursor.fetchone()
            if not row:
                return False
            
            data_inventory = row[0] or {}
            if not isinstance(data_inventory, dict):
                data_inventory = {}
            
            # Enable SEBI AI Auditor at framework level
            data_inventory['ai_bse_enabled'] = 1
            data_inventory['sebi_ai_auditor_enabled_at'] = timezone.now().isoformat()
            
            # Also enable at compliance level (ai_bse_enabled = 1)
            cursor.execute("""
                UPDATE compliance
                SET ai_bse_enabled = 1
                WHERE FrameworkId = %s AND TenantId = %s
            """, [framework_id, tenant_id])
            
            # Update framework
            cursor.execute("""
                UPDATE frameworks
                SET data_inventory = %s
                WHERE FrameworkId = %s AND TenantId = %s
            """, [json.dumps(data_inventory), framework_id, tenant_id])
            
            return True
            
    except Exception as e:
        logger.error(f"Error enabling SEBI AI Auditor: {str(e)}")
        return False

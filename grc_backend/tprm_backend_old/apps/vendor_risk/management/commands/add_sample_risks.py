"""
Management command to add sample vendor risks to the database
"""
from django.core.management.base import BaseCommand
from django.db import connection
import json


class Command(BaseCommand):
    help = 'Add sample vendor risks to the database'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if risks already exist
            cursor.execute("SELECT COUNT(*) FROM risk_tprm WHERE entity = 'vendor'")
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'Found {existing_count} existing vendor risks. Skipping.')
                )
                return
            
            # Sample risk data
            sample_risks = [
                {
                    'id': 'R-1001',
                    'title': 'Data Breach Risk',
                    'description': 'Risk of unauthorized access to sensitive vendor data',
                    'likelihood': 3,
                    'impact': 4,
                    'score': 16,
                    'priority': 'High',
                    'ai_explanation': 'Based on vendor security assessment, there is moderate likelihood of data breach due to insufficient access controls.',
                    'suggested_mitigations': json.dumps([
                        'Implement multi-factor authentication',
                        'Regular security audits',
                        'Data encryption at rest'
                    ]),
                    'status': 'Open',
                    'assigned_to': None,
                    'created_by': 1,
                    'exposure_rating': 3,
                    'risk_type': 'Current',
                    'entity': 'vendor',
                    'data': 'vendor_data',
                    'row': '5'  # ACME Corporation vendor ID
                },
                {
                    'id': 'R-1002',
                    'title': 'Compliance Violation',
                    'description': 'Risk of non-compliance with industry regulations',
                    'likelihood': 2,
                    'impact': 5,
                    'score': 20,
                    'priority': 'High',
                    'ai_explanation': 'Vendor may not meet regulatory requirements for data handling and privacy.',
                    'suggested_mitigations': json.dumps([
                        'Regular compliance audits',
                        'Staff training on regulations',
                        'Documentation of processes'
                    ]),
                    'status': 'Open',
                    'assigned_to': None,
                    'created_by': 1,
                    'exposure_rating': 3,
                    'risk_type': 'Current',
                    'entity': 'vendor',
                    'data': 'vendor_data',
                    'row': '5'  # ACME Corporation vendor ID
                },
                {
                    'id': 'R-1003',
                    'title': 'Financial Instability',
                    'description': 'Risk of vendor financial difficulties affecting service delivery',
                    'likelihood': 2,
                    'impact': 3,
                    'score': 12,
                    'priority': 'Medium',
                    'ai_explanation': 'Vendor financial health indicators show potential concerns.',
                    'suggested_mitigations': json.dumps([
                        'Regular financial reviews',
                        'Diversify vendor portfolio',
                        'Monitor payment terms'
                    ]),
                    'status': 'Open',
                    'assigned_to': None,
                    'created_by': 1,
                    'exposure_rating': 3,
                    'risk_type': 'Current',
                    'entity': 'vendor',
                    'data': 'vendor_data',
                    'row': '5'  # ACME Corporation vendor ID
                },
                {
                    'id': 'R-1004',
                    'title': 'Service Disruption',
                    'description': 'Risk of vendor service interruption affecting business operations',
                    'likelihood': 4,
                    'impact': 4,
                    'score': 32,
                    'priority': 'High',
                    'ai_explanation': 'High likelihood of service disruption based on vendor reliability metrics.',
                    'suggested_mitigations': json.dumps([
                        'Implement backup systems',
                        'Service level agreements',
                        'Regular vendor monitoring'
                    ]),
                    'status': 'Open',
                    'assigned_to': None,
                    'created_by': 1,
                    'exposure_rating': 3,
                    'risk_type': 'Current',
                    'entity': 'vendor',
                    'data': 'vendor_data',
                    'row': '5'  # ACME Corporation vendor ID
                },
                {
                    'id': 'R-1005',
                    'title': 'Cybersecurity Threat',
                    'description': 'Risk of cyber attacks targeting vendor systems',
                    'likelihood': 3,
                    'impact': 5,
                    'score': 30,
                    'priority': 'High',
                    'ai_explanation': 'Vendor systems may be vulnerable to cyber attacks.',
                    'suggested_mitigations': json.dumps([
                        'Regular security assessments',
                        'Penetration testing',
                        'Incident response planning'
                    ]),
                    'status': 'Open',
                    'assigned_to': None,
                    'created_by': 1,
                    'exposure_rating': 3,
                    'risk_type': 'Current',
                    'entity': 'vendor',
                    'data': 'vendor_data',
                    'row': '5'  # ACME Corporation vendor ID
                }
            ]
            
            # Insert sample risks
            for risk in sample_risks:
                cursor.execute("""
                    INSERT INTO risk_tprm (
                        id, title, description, likelihood, impact, score, priority,
                        ai_explanation, suggested_mitigations, status, assigned_to,
                        created_by, exposure_rating, risk_type, entity, data, row,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        NOW(), NOW()
                    )
                """, [
                    risk['id'], risk['title'], risk['description'], risk['likelihood'],
                    risk['impact'], risk['score'], risk['priority'], risk['ai_explanation'],
                    risk['suggested_mitigations'], risk['status'], risk['assigned_to'],
                    risk['created_by'], risk['exposure_rating'], risk['risk_type'],
                    risk['entity'], risk['data'], risk['row']
                ])
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully added {len(sample_risks)} sample vendor risks.')
            )

"""
Django management command to populate data_inventory field for Policy, Compliance, 
Audit, Incident, Risk, RiskInstance, Event, Framework, and SubPolicy models.

This script maps each field in these models to data types: personal, confidential, or regular.

Data Type Classifications:
    - personal: Information that can identify individuals (names, user IDs, emails, etc.)
    - confidential: Sensitive business information (financial data, risk ratings, impact assessments, etc.)
    - regular: General operational data (status, dates, descriptions, etc.)

Usage:
    # Populate only records with empty data_inventory
    python manage.py populate_data_inventory
    
    # Update all records (including those with existing data_inventory)
    python manage.py populate_data_inventory --update-existing
    
    # Dry run to see what would be updated without making changes
    python manage.py populate_data_inventory --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from grc.models import Policy, Compliance, Audit, Incident, Risk, Event, Framework, SubPolicy, RiskInstance


class Command(BaseCommand):
    help = 'Populate data_inventory field for Policy, Compliance, Audit, Incident, Risk, and Event models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing data_inventory values (default: only populate empty fields)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )

    def handle(self, *args, **options):
        update_existing = options['update_existing']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        # Define data inventory mappings for each model
        mappings = {
            'Policy': self.get_policy_data_inventory(),
            'Compliance': self.get_compliance_data_inventory(),
            'Audit': self.get_audit_data_inventory(),
            'Incident': self.get_incident_data_inventory(),
            'Risk': self.get_risk_data_inventory(),
            'RiskInstance': self.get_riskinstance_data_inventory(),
            'Event': self.get_event_data_inventory(),
            'Framework': self.get_framework_data_inventory(),
            'SubPolicy': self.get_subpolicy_data_inventory(),
        }

        total_updated = 0

        with transaction.atomic():
            # Process Policy
            updated = self.process_model(
                Policy, 
                mappings['Policy'], 
                'Policy',
                update_existing,
                dry_run
            )
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(f'✓ Policy: {updated} records processed'))

            # Process Compliance
            updated = self.process_model(
                Compliance, 
                mappings['Compliance'], 
                'Compliance',
                update_existing,
                dry_run
            )
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(f'✓ Compliance: {updated} records processed'))

            # Process Audit
            updated = self.process_model(
                Audit, 
                mappings['Audit'], 
                'Audit',
                update_existing,
                dry_run
            )
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(f'✓ Audit: {updated} records processed'))

            # Process Incident
            updated = self.process_model(
                Incident, 
                mappings['Incident'], 
                'Incident',
                update_existing,
                dry_run
            )
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(f'✓ Incident: {updated} records processed'))

            # Process Risk
            updated = self.process_model(
                Risk, 
                mappings['Risk'], 
                'Risk',
                update_existing,
                dry_run
            )
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(f'✓ Risk: {updated} records processed'))

            # Process RiskInstance
            updated = self.process_model(
                RiskInstance, 
                mappings['RiskInstance'], 
                'RiskInstance',
                update_existing,
                dry_run
            )
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(f'✓ RiskInstance: {updated} records processed'))

            # Process Event
            updated = self.process_model(
                Event, 
                mappings['Event'], 
                'Event',
                update_existing,
                dry_run
            )
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(f'✓ Event: {updated} records processed'))

            # Process Framework
            updated = self.process_model(
                Framework, 
                mappings['Framework'], 
                'Framework',
                update_existing,
                dry_run
            )
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(f'✓ Framework: {updated} records processed'))

            # Process SubPolicy
            updated = self.process_model(
                SubPolicy, 
                mappings['SubPolicy'], 
                'SubPolicy',
                update_existing,
                dry_run
            )
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(f'✓ SubPolicy: {updated} records processed'))

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\nDRY RUN: Would update {total_updated} records'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully updated {total_updated} records'))

    def process_model(self, model_class, data_inventory_mapping, model_name, update_existing, dry_run):
        """Process a model and update data_inventory field"""
        queryset = model_class.objects.all()
        
        if not update_existing:
            queryset = queryset.filter(data_inventory__isnull=True) | queryset.filter(data_inventory={})

        count = queryset.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING(f'  No {model_name} records to process'))
            return 0

        if not dry_run:
            queryset.update(data_inventory=data_inventory_mapping)
        
        return count

    def get_policy_data_inventory(self):
        """Define data inventory mapping for Policy model"""
        return {
            "PolicyId": "regular",
            "FrameworkId": "regular",
            "CurrentVersion": "regular",
            "Status": "regular",
            "PolicyDescription": "regular",
            "PolicyName": "regular",
            "StartDate": "regular",
            "EndDate": "regular",
            "Department": "regular",
            "CreatedByName": "personal",
            "CreatedByDate": "regular",
            "Applicability": "regular",
            "DocURL": "confidential",
            "Scope": "regular",
            "Objective": "regular",
            "Identifier": "regular",
            "PermanentTemporary": "regular",
            "ActiveInactive": "regular",
            "Reviewer": "personal",
            "CoverageRate": "confidential",
            "AcknowledgedUserIds": "personal",
            "AcknowledgementCount": "regular",
            "PolicyType": "regular",
            "PolicyCategory": "regular",
            "PolicySubCategory": "regular",
            "Entities": "confidential",
        }

    def get_compliance_data_inventory(self):
        """Define data inventory mapping for Compliance model"""
        return {
            "ComplianceId": "regular",
            "SubPolicy": "regular",
            "ComplianceTitle": "regular",
            "ComplianceItemDescription": "regular",
            "ComplianceType": "regular",
            "Scope": "regular",
            "Objective": "regular",
            "BusinessUnitsCovered": "confidential",
            "IsRisk": "regular",
            "PossibleDamage": "confidential",
            "mitigation": "confidential",
            "Criticality": "confidential",
            "MandatoryOptional": "regular",
            "ManualAutomatic": "regular",
            "Impact": "confidential",
            "Probability": "confidential",
            "MaturityLevel": "regular",
            "ActiveInactive": "regular",
            "PermanentTemporary": "regular",
            "CreatedByName": "personal",
            "CreatedByDate": "regular",
            "ComplianceVersion": "regular",
            "Status": "regular",
            "Identifier": "regular",
            "Applicability": "regular",
            "PreviousComplianceVersionId": "regular",
            "PotentialRiskScenarios": "confidential",
            "RiskType": "regular",
            "RiskCategory": "regular",
            "RiskBusinessImpact": "confidential",
            "FrameworkId": "regular",
        }

    def get_audit_data_inventory(self):
        """Define data inventory mapping for Audit model"""
        return {
            "AuditId": "regular",
            "Title": "regular",
            "Scope": "regular",
            "Objective": "regular",
            "BusinessUnit": "confidential",
            "Role": "regular",
            "Responsibility": "regular",
            "Assignee": "personal",
            "Auditor": "personal",
            "Reviewer": "personal",
            "FrameworkId": "regular",
            "PolicyId": "regular",
            "SubPolicyId": "regular",
            "DueDate": "regular",
            "Frequency": "regular",
            "Status": "regular",
            "CompletionDate": "regular",
            "ReviewStatus": "regular",
            "ReviewerComments": "confidential",
            "AuditType": "regular",
            "Evidence": "confidential",
            "Comments": "confidential",
            "AssignedDate": "regular",
            "Reports": "confidential",
            "ReviewStartDate": "regular",
            "ReviewDate": "regular",
        }

    def get_incident_data_inventory(self):
        """Define data inventory mapping for Incident model"""
        return {
            "IncidentId": "regular",
            "IncidentTitle": "regular",
            "Description": "confidential",
            "Mitigation": "confidential",
            "FrameworkId": "regular",
            "AuditId": "regular",
            "ComplianceId": "regular",
            "Date": "regular",
            "Time": "regular",
            "UserId": "personal",
            "Origin": "regular",
            "Comments": "confidential",
            "RiskCategory": "regular",
            "IncidentCategory": "regular",
            "RiskPriority": "confidential",
            "Attachments": "confidential",
            "CreatedAt": "regular",
            "Status": "regular",
            "IdentifiedAt": "regular",
            "RepeatedNot": "regular",
            "CostOfIncident": "confidential",
            "ReopenedNot": "regular",
            "RejectionSource": "regular",
            "AffectedBusinessUnit": "confidential",
            "SystemsAssetsInvolved": "confidential",
            "GeographicLocation": "regular",
            "Criticality": "confidential",
            "InitialImpactAssessment": "confidential",
            "InternalContacts": "personal",
            "ExternalPartiesInvolved": "personal",
            "RegulatoryBodies": "regular",
            "RelevantPoliciesProceduresViolated": "confidential",
            "ControlFailures": "confidential",
            "LessonsLearned": "confidential",
            "IncidentClassification": "confidential",
            "PossibleDamage": "confidential",
            "AssignerId": "personal",
            "ReviewerId": "personal",
            "MitigationDueDate": "regular",
            "AssignedDate": "regular",
            "AssignmentNotes": "confidential",
            "IncidentFormDetails": "confidential",
            "MitigationCompletedDate": "regular",
        }

    def get_risk_data_inventory(self):
        """Define data inventory mapping for Risk model (using display names as per user example)"""
        return {
            "Category": "personal",
            "Risk Type": "regular",
            "Risk Title": "regular",
            "Criticality": "personal",
            "Risk Impact": "confidential",
            "Compliance ID": "personal",
            "Risk Priority": "regular",
            "Business Impact": "regular",
            "Possible Damage": "regular",
            "Risk Likelihood": "confidential",
            "Risk Mitigation": "regular",
            "Risk Description": "regular",
            "Risk Multiplier X": "confidential",
            "Risk Multiplier Y": "confidential",
            "Risk Exposure Rating": "confidential",
        }

    def get_riskinstance_data_inventory(self):
        """Define data inventory mapping for RiskInstance model"""
        return {
            "RiskInstanceId": "regular",
            "RiskId": "regular",
            "IncidentId": "regular",
            "ComplianceId": "personal",
            "RiskTitle": "regular",
            "RiskDescription": "regular",
            "PossibleDamage": "regular",
            "RiskPriority": "regular",
            "Criticality": "personal",
            "Category": "personal",
            "Origin": "regular",
            "ReportedBy": "personal",
            "RiskLikelihood": "confidential",
            "RiskImpact": "confidential",
            "RiskExposureRating": "confidential",
            "RiskMultiplierX": "confidential",
            "RiskMultiplierY": "confidential",
            "Appetite": "confidential",
            "RiskResponseType": "regular",
            "RiskResponseDescription": "confidential",
            "RiskMitigation": "confidential",
            "RiskType": "regular",
            "RiskOwner": "personal",
            "BusinessImpact": "regular",
            "UserId": "personal",
            "MitigationDueDate": "regular",
            "ModifiedMitigations": "confidential",
            "MitigationCompletedDate": "regular",
            "ReviewerCount": "regular",
            "RiskFormDetails": "confidential",
            "RecurrenceCount": "regular",
            "CreatedAt": "regular",
            "Reviewer": "personal",
            "ReviewerId": "personal",
            "FirstResponseAt": "regular",
            "FrameworkId": "regular",
            "RiskStatus": "regular",
            "MitigationStatus": "regular",
        }

    def get_event_data_inventory(self):
        """Define data inventory mapping for Event model"""
        return {
            "EventId": "regular",
            "EventTitle": "regular",
            "EventId_Generated": "regular",
            "Description": "regular",
            "FrameworkId": "regular",
            "FrameworkName": "regular",
            "Module": "regular",
            "LinkedRecordType": "regular",
            "LinkedRecordId": "regular",
            "LinkedRecordName": "regular",
            "Category": "regular",
            "EventType": "regular",
            "SubEventType": "regular",
            "Owner": "personal",
            "Reviewer": "personal",
            "RecurrenceType": "regular",
            "Frequency": "regular",
            "StartDate": "regular",
            "EndDate": "regular",
            "Status": "regular",
            "Evidence": "confidential",
            "DynamicFieldsData": "confidential",
            "CreatedBy": "personal",
            "CreatedAt": "regular",
            "UpdatedAt": "regular",
            "ApprovedAt": "regular",
            "Comments": "confidential",
            "Priority": "confidential",
            "IsTemplate": "regular",
        }

    def get_framework_data_inventory(self):
        """Define data inventory mapping for Framework model"""
        return {
            "FrameworkId": "regular",
            "FrameworkName": "regular",
            "CurrentVersion": "regular",
            "FrameworkDescription": "regular",
            "EffectiveDate": "regular",
            "CreatedByName": "personal",
            "CreatedByDate": "regular",
            "Category": "regular",
            "DocURL": "confidential",
            "Identifier": "regular",
            "StartDate": "regular",
            "EndDate": "regular",
            "Status": "regular",
            "ActiveInactive": "regular",
            "Reviewer": "personal",
            "InternalExternal": "regular",
            "Amendment": "confidential",
            "latestAmmendmentDate": "regular",
            "latestComparisionCheckDate": "regular",
        }

    def get_subpolicy_data_inventory(self):
        """Define data inventory mapping for SubPolicy model"""
        return {
            "SubPolicyId": "regular",
            "PolicyId": "regular",
            "SubPolicyName": "regular",
            "CreatedByName": "personal",
            "CreatedByDate": "regular",
            "Identifier": "regular",
            "Description": "regular",
            "Status": "regular",
            "PermanentTemporary": "regular",
            "Control": "confidential",
            "FrameworkId": "regular",
        }


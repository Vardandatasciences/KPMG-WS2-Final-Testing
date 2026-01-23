from django.core.management.base import BaseCommand
from grc.models import Compliance, Risk


class Command(BaseCommand):
    help = 'Sync existing compliance records with risk records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )

    def handle(self, *args, **options):
        
        dry_run = options['dry_run']
        
        self.stdout.write("Starting compliance-risk sync...")
        
        # Get only approved and active compliances
        compliances = Compliance.objects.filter(Status='Approved', ActiveInactive='Active')
        total_compliances = compliances.count()
        
        self.stdout.write(f"Found {total_compliances} approved and active compliance records")
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        for compliance in compliances:
            try:
                # Check if risk record exists
                risk = Risk.objects.filter(ComplianceId=compliance.ComplianceId).first()
                
                if not risk:
                    # Create risk record
                    if not dry_run:
                        # Start with just ComplianceId to ensure it works
                        risk_data = {
                            'ComplianceId': compliance.ComplianceId
                        }
                        
                        # Add other fields only if they have values
                        if compliance.Criticality:
                            risk_data['Criticality'] = compliance.Criticality
                        if compliance.PotentialRiskScenarios:
                            risk_data['PossibleDamage'] = compliance.PotentialRiskScenarios
                        if compliance.RiskCategory:
                            risk_data['Category'] = compliance.RiskCategory
                        if compliance.RiskType:
                            risk_data['RiskType'] = compliance.RiskType
                        if compliance.RiskBusinessImpact:
                            risk_data['BusinessImpact'] = compliance.RiskBusinessImpact
                        
                        Risk.objects.create(**risk_data)
                        created_count += 1
                        self.stdout.write(f"✓ Created risk record for compliance {compliance.ComplianceId}")
                    else:
                        self.stdout.write(f"[DRY RUN] Would create risk record for compliance {compliance.ComplianceId}")
                else:
                    # Update existing risk record with latest compliance data
                    if not dry_run:
                        if compliance.Criticality:
                            risk.Criticality = compliance.Criticality
                        if compliance.PotentialRiskScenarios:
                            risk.PossibleDamage = compliance.PotentialRiskScenarios
                        if compliance.RiskCategory:
                            risk.Category = compliance.RiskCategory
                        if compliance.RiskType:
                            risk.RiskType = compliance.RiskType
                        if compliance.RiskBusinessImpact:
                            risk.BusinessImpact = compliance.RiskBusinessImpact
                        risk.save()
                        updated_count += 1
                        self.stdout.write(f"✓ Updated risk record {risk.RiskId} for compliance {compliance.ComplianceId}")
                    else:
                        self.stdout.write(f"[DRY RUN] Would update risk record {risk.RiskId} for compliance {compliance.ComplianceId}")
                        
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Error processing compliance {compliance.ComplianceId}: {str(e)}")
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("SYNC SUMMARY:")
        self.stdout.write(f"Total compliances processed: {total_compliances}")
        self.stdout.write(f"Risk records created: {created_count}")
        self.stdout.write(f"Risk records updated: {updated_count}")
        self.stdout.write(f"Errors: {error_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("This was a DRY RUN - no changes were made"))
        else:
            self.stdout.write(self.style.SUCCESS("Sync completed successfully!")) 
"""
Management command to check and identify CharField fields that need length increases
for encryption support.

Encrypted values can be 3-4x longer than plain text, so fields need to be increased.
"""

from django.core.management.base import BaseCommand
from django.apps import apps
import ast
import os

class Command(BaseCommand):
    help = 'Check which CharField fields need length increases for encryption'

    def handle(self, *args, **options):
        # Import encryption config
        from grc.utils.encryption_config import ENCRYPTED_FIELDS_CONFIG
        
        # Get models.py path
        models_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'models.py'
        )
        
        self.stdout.write("=" * 80)
        self.stdout.write("CHECKING ENCRYPTED FIELD LENGTHS")
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        # Read models.py
        with open(models_path, 'r', encoding='utf-8') as f:
            models_content = f.read()
        
        # Parse models.py to find field definitions
        issues = []
        recommendations = []
        
        for model_name, encrypted_fields in ENCRYPTED_FIELDS_CONFIG.items():
            try:
                # Get the model class
                model_class = apps.get_model('grc', model_name)
                
                self.stdout.write(f"\n📋 Model: {model_name}")
                self.stdout.write(f"   Encrypted fields: {', '.join(encrypted_fields)}")
                
                for field_name in encrypted_fields:
                    try:
                        field = model_class._meta.get_field(field_name)
                        
                        # Check if it's a CharField
                        if hasattr(field, 'max_length'):
                            max_length = field.max_length
                            
                            # Check if length is too small for encryption
                            # Encrypted values can be 3-4x longer, so we need at least 500
                            if max_length < 500:
                                issues.append({
                                    'model': model_name,
                                    'field': field_name,
                                    'current_length': max_length,
                                    'recommended_length': 1000 if max_length < 100 else 500
                                })
                                
                                self.stdout.write(
                                    f"   ⚠️  {field_name}: max_length={max_length} (TOO SMALL for encryption!)"
                                )
                                self.stdout.write(
                                    f"      → Recommend: {1000 if max_length < 100 else 500}"
                                )
                            else:
                                self.stdout.write(
                                    f"   ✅ {field_name}: max_length={max_length} (OK)"
                                )
                        elif hasattr(field, 'max_length') and field.max_length is None:
                            # TextField - no length limit, OK
                            self.stdout.write(f"   ✅ {field_name}: TextField (no limit, OK)")
                        else:
                            # Not a CharField, might be TextField
                            self.stdout.write(f"   ℹ️  {field_name}: {type(field).__name__} (check manually)")
                            
                    except Exception as e:
                        self.stdout.write(f"   ❌ {field_name}: Error - {str(e)}")
                        
            except Exception as e:
                self.stdout.write(f"\n❌ Model {model_name}: Error - {str(e)}")
        
        # Summary
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 80)
        
        if issues:
            self.stdout.write(f"\n⚠️  Found {len(issues)} fields that need length increases:\n")
            
            for issue in issues:
                self.stdout.write(
                    f"  {issue['model']}.{issue['field']}: "
                    f"{issue['current_length']} → {issue['recommended_length']}"
                )
            
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write("RECOMMENDED CHANGES")
            self.stdout.write("=" * 80)
            self.stdout.write("\nUpdate these fields in models.py:\n")
            
            # Group by model
            by_model = {}
            for issue in issues:
                if issue['model'] not in by_model:
                    by_model[issue['model']] = []
                by_model[issue['model']].append(issue)
            
            for model_name, model_issues in by_model.items():
                self.stdout.write(f"\n# {model_name}")
                for issue in model_issues:
                    self.stdout.write(
                        f"    {issue['field']} = models.CharField(max_length={issue['recommended_length']})"
                    )
        else:
            self.stdout.write("\n✅ All encrypted CharField fields have sufficient length!")
        
        self.stdout.write("\n" + "=" * 80)



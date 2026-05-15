"""
Quick script to check source_module values in SystemIdentifiedRiskQueue table
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grc_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grc.settings')
django.setup()

from grc.models import SystemIdentifiedRiskQueue
from django.db import models

print("=" * 60)
print("Checking source_module values in SystemIdentifiedRiskQueue")
print("=" * 60)

# Get distinct source_module values
source_modules = SystemIdentifiedRiskQueue.objects.values('source_module').distinct()
print("\nDistinct source_module values:")
for item in source_modules:
    print(f"  - {item['source_module']}")

# Count by source_module
print("\nCount by source_module:")
counts = SystemIdentifiedRiskQueue.objects.values('source_module').annotate(
    count=models.Count('id')
).order_by('-count')

from django.db.models import Count
counts = SystemIdentifiedRiskQueue.objects.values('source_module').annotate(
    count=Count('id')
).order_by('-count')

for item in counts:
    print(f"  {item['source_module']}: {item['count']}")

# Get total count
total = SystemIdentifiedRiskQueue.objects.count()
print(f"\nTotal records: {total}")

print("\n" + "=" * 60)

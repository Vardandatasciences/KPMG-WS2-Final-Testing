import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
try:
    django.setup()
except Exception as e:
    print("Could not setup django:", e)

from grc.models import Framework
frameworks = Framework.objects.all()
print(f"Total frameworks found: {len(frameworks)}")
for fw in frameworks:
    print(f"ID: {fw.FrameworkId} | Name: {fw.FrameworkName} | InternalExternal: {fw.InternalExternal} | Status: {fw.Status} | ActiveInactive: {fw.ActiveInactive}")

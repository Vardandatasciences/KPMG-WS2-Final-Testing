from grc.models import Framework
total = Framework.objects.filter(Status='Approved', ActiveInactive='Active').count()
print(f'Total Approved/Active Frameworks in DB: {total}')

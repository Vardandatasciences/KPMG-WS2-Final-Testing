from django.db import connections

cursor = connections['default'].cursor()

cursor.execute("SELECT `row`, LENGTH(`row`) FROM risk_tprm WHERE data=%s AND risk_tprm.row=%s", ['temp_vendor', '50'])
print(cursor.fetchall())

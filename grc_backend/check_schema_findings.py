import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection

def check_table():
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE audit_findings")
        columns = cursor.fetchall()
        print("Table: audit_findings")
        for col in columns:
            print(col)

if __name__ == "__main__":
    check_table()

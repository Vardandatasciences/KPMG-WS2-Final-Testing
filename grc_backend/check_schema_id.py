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
            if col[0] == 'AuditFindingsId':
                print(f"FOUND: {col}")
            else:
                # Print the first few columns just in case
                pass
        
        # Also print the first 5 columns regardless
        print("\nFirst 5 columns:")
        for col in columns[:5]:
            print(col)

if __name__ == "__main__":
    check_table()

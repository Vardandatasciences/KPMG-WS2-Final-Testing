import os
import sys
import django
from django.db import connection

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def check_column_type():
    with connection.cursor() as cursor:
        # Check column types for 'audit' table
        cursor.execute("DESCRIBE audit")
        rows = cursor.fetchall()
        print("Column types for 'audit' table:")
        for row in rows:
            print(f"Field: {row[0]}, Type: {row[1]}")

if __name__ == "__main__":
    check_column_type()

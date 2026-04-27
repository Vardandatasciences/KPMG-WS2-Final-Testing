from django.db import connection

def check_table(table_name):
    print(f"\n--- Columns in {table_name} ---")
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DESCRIBE {table_name}")
            for row in cursor.fetchall():
                print(row)
    except Exception as e:
        print(f"Error checking {table_name}: {e}")

check_table('users')
check_table('risk')
check_table('incidents')
check_table('django_migrations')

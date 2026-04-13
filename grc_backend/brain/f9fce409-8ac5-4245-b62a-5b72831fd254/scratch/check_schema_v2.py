import mysql.connector
import os

# Possible DB names from research
db_names = ['tprm_integration', 'grc', 'vardaangrc']

for db_name in db_names:
    try:
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'root'),
            'database': db_name
        }
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DESCRIBE notifications")
        columns = cursor.fetchall()
        print(f"Columns in '{db_name}.notifications' table:")
        for col in columns:
            print(col)
        conn.close()
        break
    except Exception as e:
        print(f"Failed to connect to '{db_name}': {e}")

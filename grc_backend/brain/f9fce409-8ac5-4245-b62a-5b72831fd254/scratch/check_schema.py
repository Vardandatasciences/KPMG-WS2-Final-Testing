import mysql.connector
import os

db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'grc')
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DESCRIBE notifications")
    columns = cursor.fetchall()
    print("Columns in 'notifications' table:")
    for col in columns:
        print(col)
    conn.close()
except Exception as e:
    print(f"Error: {e}")

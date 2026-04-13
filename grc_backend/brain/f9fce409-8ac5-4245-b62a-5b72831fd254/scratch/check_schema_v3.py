import mysql.connector
import os

db_config = {
    'host': '13.205.15.232',
    'user': 'grc_user',
    'password': 'Vardaan123',
    'database': 'grc2',
    'port': 3306
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DESCRIBE notifications")
    columns = cursor.fetchall()
    print("Columns in 'grc2.notifications' table:")
    for col in columns:
        print(col)
    conn.close()
except Exception as e:
    print(f"Error: {e}")

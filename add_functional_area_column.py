"""
Script to add missing functional_area column to risk_instance table
"""
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.environ.get("DB_HOST", "34.93.23.105"),
    'user': os.environ.get("DB_USER", "grc_user"),
    'password': os.environ.get("DB_PASSWORD", "MyP@ssw0rd!"),
    'database': os.environ.get("DB_NAME", "grc2"),
    'port': int(os.environ.get("DB_PORT", "3306")),
    'auth_plugin': 'caching_sha2_password'
}

def add_functional_area_column():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'risk_instance' 
            AND COLUMN_NAME = 'functional_area'
        """, (DB_CONFIG['database'],))
        
        column_exists = cursor.fetchone()[0]
        
        if column_exists:
            print("✓ Column 'functional_area' already exists in risk_instance table")
            return
        
        # Add the column
        alter_sql = """
            ALTER TABLE risk_instance 
            ADD COLUMN functional_area VARCHAR(100) NULL DEFAULT NULL
        """
        
        cursor.execute(alter_sql)
        connection.commit()
        
        print("✓ Successfully added 'functional_area' column to risk_instance table")
        
    except Error as e:
        print(f"✗ Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    add_functional_area_column()

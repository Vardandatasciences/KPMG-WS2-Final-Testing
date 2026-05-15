"""
Simple script to check source_module values using direct MySQL connection
"""
import mysql.connector
import os

# Use database settings from backend/settings.py defaults
db_config = {
    'HOST': os.environ.get("DB_HOST", "34.93.23.105"),
    'USER': os.environ.get("DB_USER", "grc_user"),
    'PASSWORD': os.environ.get("DB_PASSWORD", "MyP@ssw0rd!"),
    'NAME': os.environ.get("DB_NAME", "grc2"),
    'PORT': os.environ.get("DB_PORT", "3306")
}

print("=" * 60)
print("Checking source_module values in SystemIdentifiedRiskQueue")
print("=" * 60)
print(f"Database: {db_config['NAME']} @ {db_config['HOST']}")

try:
    # Connect to database
    conn = mysql.connector.connect(
        host=db_config['HOST'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        database=db_config['NAME'],
        port=int(db_config['PORT'])
    )
    
    cursor = conn.cursor(dictionary=True)
    
    # Get distinct source_module values
    cursor.execute("SELECT DISTINCT source_module FROM grc2_systemidentifiedriskqueue WHERE source_module IS NOT NULL")
    print("\nDistinct source_module values:")
    for row in cursor.fetchall():
        print(f"  - {row['source_module']}")
    
    # Count by source_module
    cursor.execute("""
        SELECT source_module, COUNT(*) as count 
        FROM grc2_systemidentifiedriskqueue 
        WHERE source_module IS NOT NULL
        GROUP BY source_module 
        ORDER BY count DESC
    """)
    print("\nCount by source_module:")
    for row in cursor.fetchall():
        print(f"  {row['source_module']}: {row['count']}")
    
    # Get total count
    cursor.execute("SELECT COUNT(*) as total FROM grc2_systemidentifiedriskqueue")
    total = cursor.fetchone()['total']
    print(f"\nTotal records: {total}")
    
    # Check for NULL source_module
    cursor.execute("SELECT COUNT(*) as null_count FROM grc2_systemidentifiedriskqueue WHERE source_module IS NULL")
    null_count = cursor.fetchone()['null_count']
    print(f"Records with NULL source_module: {null_count}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

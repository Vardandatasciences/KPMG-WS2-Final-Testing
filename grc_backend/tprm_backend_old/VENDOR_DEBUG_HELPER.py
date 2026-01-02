"""
Helper script to debug vendor filtering issues
Run this to see what's in the database
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from django.db import connections

def debug_vendor_data():
    """Check what's actually in the database"""
    
    with connections['default'].cursor() as cursor:
        print("\n" + "="*80)
        print("VENDOR FILTERING DEBUG")
        print("="*80 + "\n")
        
        # 1. Check data sources in risk_tprm
        print("1. DATA SOURCES IN RISK_TPRM:")
        cursor.execute("SELECT DISTINCT `data`, COUNT(*) as cnt FROM risk_tprm GROUP BY `data`")
        for row in cursor.fetchall():
            print(f"   - {row[0]}: {row[1]} risks")
        
        # 2. Check sample vendor IDs
        print("\n2. SAMPLE VENDOR IDs IN TEMP_VENDOR:")
        cursor.execute("SELECT id, company_name FROM temp_vendor LIMIT 10")
        for row in cursor.fetchall():
            print(f"   - ID: {row[0]}, Name: {row[1]}")
        
        # 3. Check what rows exist in risk_tprm for temp_vendor
        print("\n3. VENDOR ROW VALUES IN RISK_TPRM (temp_vendor data):")
        cursor.execute("SELECT DISTINCT `row` FROM risk_tprm WHERE `data` = 'temp_vendor'")
        rows = cursor.fetchall()
        print(f"   Found {len(rows)} unique row values: {[r[0] for r in rows]}")
        
        # 4. Check risk count by vendor
        print("\n4. RISK COUNT BY VENDOR (temp_vendor):")
        cursor.execute("""
            SELECT `row`, COUNT(*) as risk_count 
            FROM risk_tprm 
            WHERE `data` = 'temp_vendor' AND entity IN ('vendor', 'vendor_management')
            GROUP BY `row` 
            ORDER BY risk_count DESC
            LIMIT 20
        """)
        for row in cursor.fetchall():
            print(f"   - Vendor ID {row[0]}: {row[1]} risks")
        
        # 5. Test a specific filter
        print("\n5. TEST: Filtering for vendor_id = 1")
        cursor.execute("""
            SELECT id, title, priority 
            FROM risk_tprm 
            WHERE entity IN ('vendor', 'vendor_management') 
            AND `data` = 'temp_vendor' 
            AND `row` = %s
            LIMIT 5
        """, ['1'])
        test_results = cursor.fetchall()
        print(f"   Found {len(test_results)} risks:")
        for row in test_results:
            print(f"   - {row[0]}: {row[1]} ({row[2]})")
        
        # 6. Check if there's any data at all
        print("\n6. TOTAL RISK COUNT:")
        cursor.execute("SELECT COUNT(*) FROM risk_tprm WHERE entity IN ('vendor', 'vendor_management')")
        total = cursor.fetchone()[0]
        print(f"   Total vendor risks: {total}")
        
        cursor.execute("SELECT COUNT(*) FROM risk_tprm WHERE `data` = 'temp_vendor'")
        temp_vendor_risks = cursor.fetchone()[0]
        print(f"   Temp vendor risks: {temp_vendor_risks}")
        
        # 7. Sample actual risk records
        print("\n7. SAMPLE RISK RECORDS (first 5):")
        cursor.execute("""
            SELECT id, title, `data`, `row`, entity 
            FROM risk_tprm 
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"   - ID: {row[0]}, Data: {row[2]}, Row: {row[3]}, Entity: {row[4]}")

if __name__ == '__main__':
    debug_vendor_data()


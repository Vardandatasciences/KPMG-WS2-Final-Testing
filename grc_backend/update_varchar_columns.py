"""
Script to update VARCHAR/CHAR columns in MySQL database to support encryption.

This script:
1. Finds all VARCHAR/CHAR columns with length <= 45 or < 1000
2. Updates them to minimum 1000 characters (or 1500 to account for encryption overhead)
3. Accounts for encryption overhead (Fernet encryption adds ~33% overhead)

Usage:
    python update_varchar_columns.py

Environment Variables:
    DB_NAME: Database name (default: grc2)
    DB_USER: Database user
    DB_PASSWORD: Database password
    DB_HOST: Database host (default: localhost)
    DB_PORT: Database port (default: 3306)
"""

import os
import sys
import logging
from typing import List, Dict, Tuple
import mysql.connector
from mysql.connector import Error
from mysql.connector.cursor import MySQLCursor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Encryption overhead: Fernet encryption with base64 encoding adds ~33% overhead
# Using 1500 as safe default to account for encryption overhead
ENCRYPTION_OVERHEAD_FACTOR = 1.5  # 50% overhead for safety
MIN_COLUMN_LENGTH = 1000
RECOMMENDED_COLUMN_LENGTH = 1500  # Accounts for encryption overhead

# For indexed columns: MySQL InnoDB with utf8mb4 has max index key length of 3072 bytes
# utf8mb4 uses 4 bytes per character, so max indexed VARCHAR is 767 characters
MAX_INDEXED_VARCHAR_LENGTH = 767  # Safe for utf8mb4 indexes

# For non-indexed columns that need encryption but are in large tables
# Use TEXT instead of VARCHAR to avoid row size limits
TEXT_THRESHOLD = 500  # If column needs > 500 chars and table has many columns, use TEXT


def get_db_connection():
    """Get MySQL database connection using environment variables or Django settings."""
    try:
        # Try to get from Django settings first
        try:
            import django
            from django.conf import settings
            django.setup()
            
            db_config = settings.DATABASES['default']
            connection = mysql.connector.connect(
                host=db_config.get('HOST', 'localhost'),
                port=db_config.get('PORT', 3306),
                user=db_config.get('USER', 'root'),
                password=db_config.get('PASSWORD', ''),
                database=db_config.get('NAME', 'grc2'),
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            logger.info(f"Connected to database using Django settings: {db_config.get('NAME')}")
            return connection
        except Exception as e:
            logger.debug(f"Could not use Django settings: {e}")
            # Fall back to environment variables
            pass
        
        # Use environment variables
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=int(os.environ.get('DB_PORT', 3306)),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'grc2'),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        logger.info(f"Connected to database using environment variables: {os.environ.get('DB_NAME', 'grc2')}")
        return connection
        
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        raise


def find_small_varchar_columns(connection, db_name: str) -> List[Dict]:
    """
    Find all VARCHAR/CHAR columns with length <= 45 or < 1000.
    Also checks if columns are indexed.
    
    Returns:
        List of dictionaries with table_name, column_name, data_type, character_maximum_length, is_indexed
    """
    cursor = connection.cursor(dictionary=True)
    
    query = """
        SELECT 
            c.TABLE_NAME,
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            c.COLUMN_TYPE,
            CASE 
                WHEN s.INDEX_NAME IS NOT NULL THEN 1 
                ELSE 0 
            END as IS_INDEXED,
            s.INDEX_NAME,
            s.NON_UNIQUE
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT DISTINCT
                TABLE_SCHEMA,
                TABLE_NAME,
                COLUMN_NAME,
                INDEX_NAME,
                NON_UNIQUE
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = %s
        ) s ON c.TABLE_SCHEMA = s.TABLE_SCHEMA 
           AND c.TABLE_NAME = s.TABLE_NAME 
           AND c.COLUMN_NAME = s.COLUMN_NAME
        WHERE c.TABLE_SCHEMA = %s
            AND c.DATA_TYPE IN ('varchar', 'char')
            AND (
                c.CHARACTER_MAXIMUM_LENGTH IS NULL 
                OR c.CHARACTER_MAXIMUM_LENGTH <= 45 
                OR c.CHARACTER_MAXIMUM_LENGTH < 1000
            )
        ORDER BY c.TABLE_NAME, c.COLUMN_NAME
    """
    
    cursor.execute(query, (db_name, db_name))
    columns = cursor.fetchall()
    cursor.close()
    
    return columns


def get_table_column_count(connection, db_name: str, table_name: str) -> int:
    """Get the number of columns in a table."""
    cursor = connection.cursor()
    query = """
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
    """
    cursor.execute(query, (db_name, table_name))
    count = cursor.fetchone()[0]
    cursor.close()
    return count


def calculate_new_length(current_length: int, is_indexed: bool = False, 
                       table_column_count: int = 0) -> Tuple[int, str]:
    """
    Calculate new column length accounting for encryption overhead and constraints.
    
    Args:
        current_length: Current column length
        is_indexed: Whether the column is part of an index
        table_column_count: Number of columns in the table (for row size considerations)
        
    Returns:
        Tuple of (new_length, data_type) where data_type is 'VARCHAR', 'CHAR', or 'TEXT'
    """
    if current_length is None:
        current_length = 0
    
    # For indexed columns, we must respect MySQL's index key length limit
    if is_indexed:
        # Indexed columns: max 767 for utf8mb4 to fit in 3072 byte index limit
        if current_length <= 45:
            return MAX_INDEXED_VARCHAR_LENGTH, 'VARCHAR'
        elif current_length < MAX_INDEXED_VARCHAR_LENGTH:
            return MAX_INDEXED_VARCHAR_LENGTH, 'VARCHAR'
        else:
            # Already at or above max indexed length, keep it
            return current_length, 'VARCHAR'
    
    # For non-indexed columns
    if current_length <= 45:
        # Small columns: check if table has many columns (row size concern)
        if table_column_count > 20:  # Large table, use TEXT to avoid row size issues
            return None, 'TEXT'
        else:
            return RECOMMENDED_COLUMN_LENGTH, 'VARCHAR'
    elif current_length < MIN_COLUMN_LENGTH:
        # Medium columns: check table size
        if table_column_count > 20:
            return None, 'TEXT'
        else:
            return RECOMMENDED_COLUMN_LENGTH, 'VARCHAR'
    else:
        # Already >= 1000, calculate with overhead
        new_length = int(current_length * ENCRYPTION_OVERHEAD_FACTOR)
        if new_length > 65535 or table_column_count > 20:
            # Too large for VARCHAR or table has many columns, use TEXT
            return None, 'TEXT'
        return max(new_length, RECOMMENDED_COLUMN_LENGTH), 'VARCHAR'


def generate_alter_statement(table_name: str, column_name: str, new_length: int, 
                             new_data_type: str, is_nullable: str, column_default: str) -> str:
    """
    Generate ALTER TABLE statement to modify column.
    
    Args:
        table_name: Table name
        column_name: Column name
        new_length: New column length (None for TEXT)
        new_data_type: New data type ('VARCHAR', 'CHAR', or 'TEXT')
        is_nullable: 'YES' or 'NO'
        column_default: Default value or None
        
    Returns:
        ALTER TABLE SQL statement
    """
    # Determine if column should be nullable
    nullable_clause = "NULL" if is_nullable == 'YES' else "NOT NULL"
    
    # Handle default value (TEXT columns can't have DEFAULT in MySQL)
    default_clause = ""
    if new_data_type != 'TEXT' and column_default is not None:
        if column_default.upper() in ('CURRENT_TIMESTAMP', 'CURRENT_TIMESTAMP()'):
            default_clause = f"DEFAULT {column_default}"
        elif isinstance(column_default, str) and column_default.startswith("'") and column_default.endswith("'"):
            default_clause = f"DEFAULT {column_default}"
        elif column_default == '':
            default_clause = "DEFAULT ''"
        else:
            default_clause = f"DEFAULT '{column_default}'"
    
    # Build column definition
    if new_data_type == 'TEXT':
        column_def = f"`{column_name}` TEXT {nullable_clause}"
    elif new_length:
        column_def = f"`{column_name}` {new_data_type}({new_length}) {nullable_clause} {default_clause}".strip()
    else:
        column_def = f"`{column_name}` {new_data_type} {nullable_clause} {default_clause}".strip()
    
    alter_sql = f"ALTER TABLE `{table_name}` MODIFY COLUMN {column_def}"
    
    return alter_sql


def update_column(connection, table_name: str, column_name: str, new_length: int,
                  new_data_type: str, is_nullable: str, column_default: str) -> Tuple[bool, str]:
    """
    Update a single column's length.
    
    Returns:
        (success: bool, message: str)
    """
    try:
        cursor = connection.cursor()
        
        alter_sql = generate_alter_statement(
            table_name, column_name, new_length, 
            new_data_type, is_nullable, column_default
        )
        
        logger.info(f"Executing: {alter_sql}")
        cursor.execute(alter_sql)
        connection.commit()
        cursor.close()
        
        if new_data_type == 'TEXT':
            return True, f"Successfully updated {table_name}.{column_name} to TEXT"
        else:
            return True, f"Successfully updated {table_name}.{column_name} to {new_data_type}({new_length})"
        
    except Error as e:
        error_msg = f"Error updating {table_name}.{column_name}: {str(e)}"
        logger.error(error_msg)
        connection.rollback()
        return False, error_msg


def main(dry_run=False):
    """
    Main function to update all small VARCHAR/CHAR columns.
    
    Args:
        dry_run: If True, only show what would be changed without making actual changes
    """
    connection = None
    
    try:
        # Get database connection
        connection = get_db_connection()
        db_name = connection.database
        
        logger.info(f"Scanning database '{db_name}' for small VARCHAR/CHAR columns...")
        if dry_run:
            logger.info("DRY RUN MODE: No changes will be made to the database.")
        
        # Find all small columns
        columns = find_small_varchar_columns(connection, db_name)
        
        if not columns:
            logger.info("No columns found that need updating. All columns are already >= 1000 characters.")
            return
        
        logger.info(f"Found {len(columns)} columns that need updating:")
        
        # Group by table for better reporting
        table_groups = {}
        for col in columns:
            table_name = col['TABLE_NAME']
            if table_name not in table_groups:
                table_groups[table_name] = []
            table_groups[table_name].append(col)
        
        # Get table column counts for row size calculations
        table_column_counts = {}
        for table_name in table_groups.keys():
            table_column_counts[table_name] = get_table_column_count(connection, db_name, table_name)
        
        # Print summary
        for table_name, cols in table_groups.items():
            logger.info(f"  {table_name}: {len(cols)} columns (total columns in table: {table_column_counts[table_name]})")
            for col in cols:
                current_len = col['CHARACTER_MAXIMUM_LENGTH'] or 0
                current_len_display = col['CHARACTER_MAXIMUM_LENGTH'] if col['CHARACTER_MAXIMUM_LENGTH'] is not None else 'NULL'
                is_indexed = col.get('IS_INDEXED', 0) == 1
                col_count = table_column_counts[table_name]
                new_len, new_type = calculate_new_length(current_len, is_indexed, col_count)
                
                if new_type == 'TEXT':
                    logger.info(f"    - {col['COLUMN_NAME']}: {col['DATA_TYPE']}({current_len_display}) -> TEXT {'[INDEXED - will use 767]' if is_indexed else ''}")
                else:
                    logger.info(f"    - {col['COLUMN_NAME']}: {col['DATA_TYPE']}({current_len_display}) -> {new_type}({new_len}) {'[INDEXED]' if is_indexed else ''}")
        
        # Ask for confirmation
        print("\n" + "="*80)
        print(f"Found {len(columns)} columns to update across {len(table_groups)} tables.")
        print(f"All columns will be updated to minimum {MIN_COLUMN_LENGTH} characters.")
        print(f"Recommended length: {RECOMMENDED_COLUMN_LENGTH} characters (accounts for encryption overhead).")
        if dry_run:
            print("DRY RUN MODE: No actual changes will be made.")
        print("="*80)
        
        if dry_run:
            logger.info("\nDRY RUN: Showing what would be changed (no actual updates performed).")
            # Show what would be changed
            for col in columns:
                current_len = col['CHARACTER_MAXIMUM_LENGTH'] or 0
                is_indexed = col.get('IS_INDEXED', 0) == 1
                table_name = col['TABLE_NAME']
                col_count = table_column_counts.get(table_name, 0)
                new_len, new_type = calculate_new_length(current_len, is_indexed, col_count)
                alter_sql = generate_alter_statement(
                    col['TABLE_NAME'], col['COLUMN_NAME'], new_len,
                    new_type, col['IS_NULLABLE'], col['COLUMN_DEFAULT']
                )
                logger.info(f"Would execute: {alter_sql}")
            return
        
        response = input("\nDo you want to proceed with the updates? (yes/no): ").strip().lower()
        if response not in ('yes', 'y'):
            logger.info("Update cancelled by user.")
            return
        
        # Update columns
        success_count = 0
        error_count = 0
        errors = []
        
        logger.info("\nStarting column updates...")
        
        for col in columns:
            table_name = col['TABLE_NAME']
            column_name = col['COLUMN_NAME']
            current_length = col['CHARACTER_MAXIMUM_LENGTH']
            is_nullable = col['IS_NULLABLE']
            column_default = col['COLUMN_DEFAULT']
            is_indexed = col.get('IS_INDEXED', 0) == 1
            col_count = table_column_counts.get(table_name, 0)
            
            new_length, new_data_type = calculate_new_length(current_length, is_indexed, col_count)
            
            success, message = update_column(
                connection, table_name, column_name, new_length,
                new_data_type, is_nullable, column_default
            )
            
            if success:
                success_count += 1
                logger.info(f"✓ {message}")
            else:
                error_count += 1
                errors.append(message)
                logger.error(f"✗ {message}")
        
        # Print summary
        print("\n" + "="*80)
        print("UPDATE SUMMARY")
        print("="*80)
        print(f"Total columns found: {len(columns)}")
        print(f"Successfully updated: {success_count}")
        print(f"Errors: {error_count}")
        
        if errors:
            print("\nErrors encountered:")
            for error in errors:
                print(f"  - {error}")
        
        print("="*80)
        
    except Error as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nUpdate interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if connection and connection.is_connected():
            connection.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Update VARCHAR/CHAR columns in MySQL database to support encryption'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making actual changes'
    )
    args = parser.parse_args()
    
    # Add Django project to path if needed
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Try to setup Django if possible
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
            django.setup()
    except:
        pass  # Continue without Django if not available
    
    main(dry_run=args.dry_run)


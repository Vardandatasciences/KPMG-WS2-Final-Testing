"""
Database operations for KPI Generator
"""
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
from decimal import Decimal

from .config import DB_CONFIG


def connect_to_database():
    """Establish connection to MySQL database."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print(f"[INFO] Connected to MySQL database: {DB_CONFIG['database']}")
            return connection
    except Error as e:
        print(f"[ERROR] Could not connect to database: {e}")
        return None


def get_framework_info(connection, framework_id):
    """Get framework metadata (name, description, category, etc.) for the specified framework_id."""
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    FrameworkId,
                    FrameworkName,
                    FrameworkDescription,
                    Category,
                    InternalExternal,
                    Identifier,
                    Status,
                    CurrentVersion
                FROM frameworks
                WHERE FrameworkId = %s
                """,
                (framework_id,)
            )
        except Error as e:
            print(f"[WARNING] Error fetching extended framework metadata: {e}")
            print("[INFO] Falling back to basic framework fields (FrameworkId, FrameworkName)")
            cursor.execute(
                "SELECT FrameworkId, FrameworkName FROM frameworks WHERE FrameworkId = %s",
                (framework_id,)
            )
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            print(f"[INFO] Framework: ID={result['FrameworkId']}, Name={result['FrameworkName']}")
            return result
        else:
            print(f"[ERROR] Framework with ID {framework_id} not found")
            return None
    except Error as e:
        print(f"[ERROR] Error fetching framework info: {e}")
        return None


def get_database_schema(connection, framework_id):
    """Get database schema information (tables, columns, data types).
    For tables with FrameworkId column, only count rows for the specified framework_id."""
    print(f"[INFO] [STEP] Starting database schema retrieval...")
    print(f"[INFO] [CONFIG] Filtering row counts by FrameworkId={framework_id} where applicable")
    schema_info = {}
    try:
        cursor = connection.cursor()
        
        # Get all tables
        print(f"[INFO] [QUERY] Getting list of all tables...")
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"[INFO] [SUCCESS] Found {len(tables)} tables in database")
        
        print(f"[INFO] [PROCESS] Processing schema for each table...")
        for idx, table in enumerate(tables, 1):
            if idx % 10 == 0:  # Log every 10 tables
                print(f"[INFO] [PROGRESS] Processing table {idx}/{len(tables)}: {table}...")
            
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            column_names = [col[0] for col in columns]
            
            schema_info[table] = {
                'columns': column_names,
                'column_details': [
                    {
                        'name': col[0],
                        'type': col[1],
                        'null': col[2],
                        'key': col[3],
                        'default': col[4],
                        'extra': col[5]
                    }
                    for col in columns
                ]
            }
            
            # Get row count - filter by FrameworkId if column exists
            has_framework_id = 'FrameworkId' in column_names or 'frameworkid' in [c.lower() for c in column_names]
            
            if has_framework_id:
                # Find the actual column name (case-sensitive check)
                framework_id_col = None
                for col_name in column_names:
                    if col_name.lower() == 'frameworkid':
                        framework_id_col = col_name
                        break
                
                if framework_id_col:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {framework_id_col} = %s", (framework_id,))
                        row_count = cursor.fetchone()[0]
                        print(f"[INFO] [QUERY] Table {table}: {row_count} rows (filtered by FrameworkId={framework_id})")
                    except Error as e:
                        print(f"[WARNING] [QUERY] Error counting rows for {table} with FrameworkId filter: {e}")
                        # Fallback to total count
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        row_count = cursor.fetchone()[0]
                        print(f"[INFO] [QUERY] Table {table}: {row_count} rows (total, FrameworkId filter failed)")
                else:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    print(f"[INFO] [QUERY] Table {table}: {row_count} rows (no FrameworkId column)")
            else:
                # Table doesn't have FrameworkId column, count all rows
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                print(f"[INFO] [QUERY] Table {table}: {row_count} rows (no FrameworkId column)")
            
            schema_info[table]['row_count'] = row_count
        
        cursor.close()
        
        # Summary
        tables_with_framework = sum(1 for v in schema_info.values() if 'FrameworkId' in v['columns'] or 'frameworkid' in [c.lower() for c in v['columns']])
        print(f"[INFO] [COMPLETE] Retrieved schema for {len(tables)} tables with {sum(len(v['columns']) for v in schema_info.values())} total columns")
        print(f"[INFO] [COMPLETE] {tables_with_framework} tables have FrameworkId column (filtered by FrameworkId={framework_id})")
        
        return schema_info
    except Error as e:
        print(f"[ERROR] Error fetching database schema: {e}")
        return {}


def get_framework_data(connection, framework_id):
    """Get all data related to the framework."""
    print(f"[INFO] [STEP] Starting data retrieval from database for Framework ID {framework_id}...")
    data = {
        'policies': [],
        'subpolicies': [],
        'compliances': [],
        'risks': [],
        'incidents': [],
        'audits': []
    }
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get Policies
        print(f"[INFO] [QUERY] Fetching policies...")
        cursor.execute("""
            SELECT PolicyId, PolicyName, PolicyDescription, PolicyType, 
                   PolicyCategory, Scope, Objective
            FROM policies 
            WHERE FrameworkId = %s 
        """, (framework_id,))
        data['policies'] = cursor.fetchall()
        print(f"[INFO] [SUCCESS] Retrieved {len(data['policies'])} policies")
        
        # Get Subpolicies
        print(f"[INFO] [QUERY] Fetching subpolicies...")
        cursor.execute("""
            SELECT SubPolicyId, PolicyId, SubPolicyName, Description, Control
            FROM subpolicies 
            WHERE FrameworkId = %s 
        """, (framework_id,))
        data['subpolicies'] = cursor.fetchall()
        print(f"[INFO] [SUCCESS] Retrieved {len(data['subpolicies'])} subpolicies")
        
        # Get Compliances
        print(f"[INFO] [QUERY] Fetching compliances...")
        cursor.execute("""
            SELECT ComplianceId, SubPolicyId, ComplianceTitle, 
                   ComplianceItemDescription, ComplianceType, Criticality
            FROM compliance 
            WHERE FrameworkId = %s 
        """, (framework_id,))
        data['compliances'] = cursor.fetchall()
        print(f"[INFO] [SUCCESS] Retrieved {len(data['compliances'])} compliances")
        
        # Get Risks
        print(f"[INFO] [QUERY] Fetching risks...")
        cursor.execute("""
            SELECT RiskId, ComplianceId, RiskTitle, RiskDescription, 
                   Category, Criticality, RiskImpact, RiskLikelihood
            FROM risk 
            WHERE FrameworkId = %s 
        """, (framework_id,))
        data['risks'] = cursor.fetchall()
        print(f"[INFO] [SUCCESS] Retrieved {len(data['risks'])} risks")
        
        # Get Incidents
        print(f"[INFO] [QUERY] Fetching incidents...")
        cursor.execute("""
            SELECT IncidentId, IncidentTitle, Description, RiskCategory, 
                   Criticality, Status, CostOfIncident
            FROM incidents 
            WHERE FrameworkId = %s 
        """, (framework_id,))
        data['incidents'] = cursor.fetchall()
        print(f"[INFO] [SUCCESS] Retrieved {len(data['incidents'])} incidents")
        
        # Get Audits
        print(f"[INFO] [QUERY] Fetching audits...")
        cursor.execute("""
            SELECT AuditId, Title, Status, CompletionDate, ReviewStatus
            FROM audit 
            WHERE FrameworkId = %s 
        """, (framework_id,))
        data['audits'] = cursor.fetchall()
        print(f"[INFO] [SUCCESS] Retrieved {len(data['audits'])} audits")
        print(f"[INFO] [COMPLETE] Finished retrieving all framework data")
        
        cursor.close()
        return data
    except Error as e:
        print(f"[ERROR] Error fetching framework data: {e}")
        return data


def get_other_tables_data(connection, framework_id, schema_info):
    """Get data from all other tables (excluding kpis and the 6 main tables already covered)."""
    print(f"[INFO] [STEP] Starting data retrieval from other database tables...")
    
    # Tables to exclude (already covered or target table)
    excluded_tables = {
        'kpis',  # Target table - we're generating for this
        'policies',
        'subpolicies',
        'compliance',
        'risk',
        'incidents',
        'audit',
        'frameworks'  # Already fetched separately
    }
    
    other_tables_data = {}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get all table names from schema
        all_tables = list(schema_info.keys())
        
        # Filter out excluded tables (case-insensitive)
        tables_to_process = [
            table for table in all_tables
            if table.lower() not in [ex.lower() for ex in excluded_tables]
        ]
        
        print(f"[INFO] [CONFIG] Processing {len(tables_to_process)} other tables (excluding {len(excluded_tables)} excluded tables)")
        
        for table_idx, table_name in enumerate(tables_to_process, 1):
            try:
                def _quote_identifier(identifier: str) -> str:
                    return f"`{identifier.replace('`', '``')}`"

                # Check if table has FrameworkId column
                columns = schema_info[table_name]['columns']
                has_framework_id = 'FrameworkId' in columns or 'frameworkid' in [c.lower() for c in columns]
                
                # Get column names for SELECT
                column_list = ', '.join(_quote_identifier(col) for col in columns)
                table_quoted = _quote_identifier(table_name)
                
                # Build query - filter by FrameworkId if column exists
                if has_framework_id:
                    framework_id_col = None
                    for col_name in columns:
                        if col_name.lower() == 'frameworkid':
                            framework_id_col = col_name
                            break
                    
                    if framework_id_col:
                        framework_col_quoted = _quote_identifier(framework_id_col)
                        query = f"SELECT {column_list} FROM {table_quoted} WHERE {framework_col_quoted} = %s"
                        cursor.execute(query, (framework_id,))
                        print(f"[INFO] [QUERY] [{table_idx}/{len(tables_to_process)}] Fetching {table_name} (filtered by FrameworkId={framework_id})...")
                    else:
                        query = f"SELECT {column_list} FROM {table_quoted}"
                        cursor.execute(query)
                        print(f"[INFO] [QUERY] [{table_idx}/{len(tables_to_process)}] Fetching {table_name} (all rows)...")
                else:
                    query = f"SELECT {column_list} FROM {table_quoted}"
                    cursor.execute(query)
                    print(f"[INFO] [QUERY] [{table_idx}/{len(tables_to_process)}] Fetching {table_name} (all rows, no FrameworkId column)...")
                
                rows = cursor.fetchall()
                other_tables_data[table_name] = rows
                print(f"[INFO] [SUCCESS] Retrieved {len(rows)} rows from {table_name}")
                
            except Error as e:
                print(f"[WARNING] [ERROR] Error fetching data from {table_name}: {e}")
                other_tables_data[table_name] = []
                continue
            except Exception as e:
                print(f"[WARNING] [ERROR] Unexpected error fetching data from {table_name}: {e}")
                other_tables_data[table_name] = []
                continue
        
        cursor.close()
        
        total_rows = sum(len(rows) for rows in other_tables_data.values())
        print(f"[INFO] [COMPLETE] Finished retrieving data from other tables. Total: {total_rows} rows across {len(other_tables_data)} tables")
        
        return other_tables_data
    except Error as e:
        print(f"[ERROR] Error fetching other tables data: {e}")
        return {}


def ensure_kpis_module_column(connection) -> None:
    """Ensure the kpis table contains a Module column."""
    try:
        db_name = DB_CONFIG.get('database')
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME='kpis' AND COLUMN_NAME='Module'
            """,
            (db_name,)
        )
        exists = cursor.fetchone()[0] if cursor else 0
        if not exists:
            print("[INFO] [DB] Adding 'Module' column to kpis table...")
            cursor.execute("ALTER TABLE kpis ADD COLUMN Module VARCHAR(255) NULL")
            connection.commit()
            print("[INFO] [DB] 'Module' column added to kpis table.")
        cursor.close()
    except Error as exc:
        print(f"[WARNING] [DB] Unable to ensure Module column on kpis table: {exc}")
    except Exception as exc:
        print(f"[WARNING] [DB] Unexpected error ensuring Module column: {exc}")


def _normalize_db_value(value: Any) -> Any:
    """Convert complex KPI fields to types accepted by MySQL."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, int, float, str)):
        return value
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)
    return str(value)


def write_kpis_to_database(connection,
                           schema_info: Dict[str, Any],
                           framework_info: Dict[str, Any],
                           kpis: List[Dict[str, Any]]) -> int:
    """Insert or update KPI records in the kpis table."""
    # Re-establish connection if it timed out during upstream processing
    if connection and hasattr(connection, "is_connected") and not connection.is_connected():
        try:
            connection.ping(reconnect=True, attempts=3, delay=5)
            print("[INFO] [DB_WRITE] Reconnected to database before writing KPIs.")
        except Exception as exc:
            print(f"[WARNING] [DB_WRITE] Unable to reconnect to database: {exc}")
            return 0

    if not kpis:
        print("[WARNING] [DB_WRITE] No KPIs supplied for database insertion.")
        return 0

    if not connection or not connection.is_connected():
        print("[WARNING] [DB_WRITE] Cannot write KPIs – database connection unavailable.")
        return 0

    kpi_table_info = schema_info.get('kpis') or {}
    kpi_columns = kpi_table_info.get('columns') or []
    if not kpi_columns:
        print("[WARNING] [DB_WRITE] kpis table schema not available; skipping database write.")
        return 0

    column_lookup = {col.lower(): col for col in kpi_columns}

    def has_column(name: str) -> bool:
        return name.lower() in column_lookup

    upserted = 0
    cursor = connection.cursor()
    try:
        for kpi in kpis:
            name = (kpi.get('Name') or '').strip()
            if not name:
                print("[WARNING] [DB_WRITE] Skipping KPI with empty name.")
                continue

            module = kpi.get('Module') or kpi.get('module') or None
            now = datetime.now()
            record: Dict[str, Any] = {}

            if has_column('FrameworkId'):
                record[column_lookup['frameworkid']] = framework_info.get('FrameworkId')
            if has_column('FrameworkName'):
                record[column_lookup['frameworkname']] = framework_info.get('FrameworkName')
            if has_column('Module'):
                record[column_lookup['module']] = _normalize_db_value(module)
            if has_column('Name'):
                record[column_lookup['name']] = name[:255]
            if has_column('Description'):
                record[column_lookup['description']] = _normalize_db_value(kpi.get('Description'))
            if has_column('Value'):
                val = kpi.get('Value')
                if isinstance(val, (dict, list)):
                    val = _normalize_db_value(val)
                elif isinstance(val, Decimal):
                    val = float(val)
                record[column_lookup['value']] = val
            if has_column('DataType'):
                record[column_lookup['datatype']] = _normalize_db_value(kpi.get('DataType'))
            if has_column('FromWhereToAccessData'):
                record[column_lookup['fromwheretoaccessdata']] = _normalize_db_value(kpi.get('FromWhereToAccessData'))
            if has_column('Formula'):
                record[column_lookup['formula']] = _normalize_db_value(kpi.get('Formula'))
            if has_column('DisplayType'):
                record[column_lookup['displaytype']] = _normalize_db_value(kpi.get('DisplayType'))
            if has_column('AuditTrail'):
                record[column_lookup['audittrail']] = _normalize_db_value(kpi.get('AuditTrail'))
            if has_column('CreatedAt'):
                record[column_lookup['createdat']] = now
            if has_column('UpdatedAt'):
                record[column_lookup['updatedat']] = now

            existing_id = None
            try:
                cursor.execute(
                    "SELECT Id FROM kpis WHERE FrameworkId=%s AND LOWER(Name)=LOWER(%s) LIMIT 1",
                    (framework_info.get('FrameworkId'), name)
                )
                row = cursor.fetchone()
                if row:
                    existing_id = row[0]
            except Error as exc:
                print(f"[WARNING] [DB_WRITE] Failed to check existing KPI '{name}': {exc}")
                continue

            if existing_id is not None:
                update_record = record.copy()
                if has_column('CreatedAt'):
                    update_record.pop(column_lookup['createdat'], None)
                if has_column('UpdatedAt'):
                    update_record[column_lookup['updatedat']] = now

                if not update_record:
                    continue

                set_clause = ", ".join(f"`{col}`=%s" for col in update_record.keys())
                sql = f"UPDATE kpis SET {set_clause} WHERE Id=%s"
                params = list(update_record.values()) + [existing_id]
                try:
                    cursor.execute(sql, params)
                    upserted += 1
                except Error as exc:
                    print(f"[WARNING] [DB_WRITE] Failed to update KPI '{name}': {exc}")
                    continue
            else:
                insert_columns = list(record.keys())
                if not insert_columns:
                    print(f"[WARNING] [DB_WRITE] No columns to insert for KPI '{name}'.")
                    continue
                placeholders = ", ".join(["%s"] * len(insert_columns))
                sql = (
                    f"INSERT INTO kpis ({', '.join(f'`{col}`' for col in insert_columns)}) "
                    f"VALUES ({placeholders})"
                )
                params = [record[col] for col in insert_columns]
                try:
                    cursor.execute(sql, params)
                    upserted += 1
                except Error as exc:
                    print(f"[WARNING] [DB_WRITE] Failed to insert KPI '{name}': {exc}")
                    continue

        connection.commit()
        print(f"[INFO] [DB_WRITE] Upserted {upserted} KPI records into database.")
        return upserted
    finally:
        try:
            cursor.close()
        except Exception:
            pass


def save_schema_metadata(schema_info, framework_id, output_dir):
    """Save schema metadata to JSON file for reference and validation."""
    metadata_file = output_dir / f"schema_metadata_framework_{framework_id}.json"
    try:
        # Create a clean metadata structure
        metadata = {
            'framework_id': framework_id,
            'generated_at': datetime.now().isoformat(),
            'tables': {}
        }
        
        for table_name, table_info in schema_info.items():
            metadata['tables'][table_name] = {
                'columns': table_info.get('columns', []),
                'row_count': table_info.get('row_count', 0),
                'column_count': len(table_info.get('columns', []))
            }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"[INFO] [SCHEMA_METADATA] Saved schema metadata to: {metadata_file}")
        return metadata_file
    except Exception as e:
        print(f"[WARNING] [SCHEMA_METADATA] Failed to save schema metadata: {e}")
        return None


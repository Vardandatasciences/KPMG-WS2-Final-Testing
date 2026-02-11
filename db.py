import mysql.connector
from mysql.connector import Error

def get_db_table_names():
    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(
            host='34.93.23.105',  # Replace with your MySQL host (e.g., localhost or IP address)
            user='grc_user',  # Replace with your MySQL username
            password='MyP@ssw0rd!',  # Replace with your MySQL password
            database='grc2'  # Replace with your database name
        )

        if connection.is_connected():
            print("Connected to MySQL database")

            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")  # This query retrieves all table names in the database

            # Fetch all table names
            tables = cursor.fetchall()
            print("Tables in the database:")
            for table in tables:
                print(table[0])  # Each item in the list is a tuple with the table name at index 0

    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

if __name__ == "__main__":
    get_db_table_names()

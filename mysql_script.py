import mysql.connector

def main():
    conn = mysql.connector.connect(
        host="34.93.23.105",
        user="grc_user",
        password="MyP@ssw0rd!",
        database="grc2",
        port=3306,
    )

    cur = conn.cursor()
    cur.execute("SELECT DATABASE(), CURRENT_USER(), USER();")
    rows = cur.fetchall()
    print("Result:", rows)

    cur.execute("SHOW TABLES;")
    tables = cur.fetchall()
    print("Tables:", tables)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
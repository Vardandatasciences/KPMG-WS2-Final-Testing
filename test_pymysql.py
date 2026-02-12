import pymysql

def main():
    conn = pymysql.connect(
        host="34.93.23.105",
        user="grc_user",
        password="MyP@ssw0rd!",
        database="grc2",
        port=3306,
    )
    with conn.cursor() as cur:
        cur.execute("SELECT DATABASE(), CURRENT_USER();")
        print("Result:", cur.fetchall())
    conn.close()

if __name__ == "__main__":
    main()
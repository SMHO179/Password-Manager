import psycopg2

DB_CONFIG = {
    "dbname": "testdb",
    "user": "testuser",
    "password": "1234",
    "host": "localhost",
    "port": 5432
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def save_password(site, username, password):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO passwords (site, username, password) VALUES (%s, %s, %s)",
            (site, username, password)
        )
        conn.commit()
        print("Saved successfully!")

    except Exception as e:
        conn.rollback()
        print("Error:", e)

    finally:
        cur.close()
        conn.close()


def main():
    print("=== Password Saver ===")

    site = input("Site: ")
    username = input("Username: ")
    password = input("Password: ")

    save_password(site, username, password)


if __name__ == "__main__":
    main()

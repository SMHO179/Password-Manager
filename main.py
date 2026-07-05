import psycopg2

try:
    conn = psycopg2.connect(
        dbname="testdb",
        user="testuser",
        password="1234",
        host="localhost",
        port=5432
    )
    print("ok !! connected")
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print("Error:", e)

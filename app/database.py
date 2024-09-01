import mysql.connector

def get_db():
    conn = mysql.connector.connect(
        host="db",
        user="user",
        password="pass",
        database="adventure",
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
    )
    return conn

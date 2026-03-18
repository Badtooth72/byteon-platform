import os
import pyodbc
from pymongo import MongoClient


SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USERNAME = os.getenv("SQL_USERNAME")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/auth_db")

if not all([SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD]):
    raise RuntimeError("Missing one or more SQL_* environment variables")

print(f"Connecting to SQL Server: {SQL_SERVER} / DB: {SQL_DATABASE}")

sql_conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    f"UID={SQL_USERNAME};"
    f"PWD={SQL_PASSWORD};"
    f"TrustServerCertificate=yes;"
    f"Connection Timeout=5;"
)

cursor = sql_conn.cursor()

cursor.execute("""
    SELECT
        net_userid,
        forename,
        surname,
        current_yeargroup,
        class_name
    FROM View_Students_Computing
    WHERE net_userid IS NOT NULL
""")

rows = cursor.fetchall()
print(f"Fetched {len(rows)} student rows from SQL")

mongo = MongoClient(MONGO_URI)
auth_db = mongo.get_database()
users = auth_db["users"]

updated = 0

for row in rows:
    username = (str(row.net_userid).strip().lower() if row.net_userid else "")
    if not username:
        continue

    users.update_one(
        {"username": username},
        {
            "$set": {
                "forename": (row.forename or "").strip(),
                "surname": (row.surname or "").strip(),
                "current_yeargroup": str(row.current_yeargroup or "").strip(),
                "class_name": (row.class_name or "").strip(),
            },
            "$setOnInsert": {
                "activities": {},
                "display_name": username,
                "login_count": 0,
            },
        },
        upsert=True,
    )
    updated += 1

print(f"Updated {updated} Mongo user records")
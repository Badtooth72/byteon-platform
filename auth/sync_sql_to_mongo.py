import os
import pyodbc
from pymongo import MongoClient

# Load environment variables
server = os.getenv("SQL_SERVER")
database = os.getenv("SQL_DATABASE")
username = os.getenv("SQL_USERNAME")
password = os.getenv("SQL_PASSWORD")

# SQL Server connection
sql_conn = pyodbc.connect(
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password}'
)

cursor = sql_conn.cursor()

# Updated query with all required fields
cursor.execute("""
    SELECT 
        net_userid, 
        forename, 
        surname, 
        reg_grp, 
        house, 
        current_yeargroup, 
        Name AS class_name
    FROM View_Students_Computing 
""")

rows = cursor.fetchall()

# Connect to MongoDB
mongo = MongoClient("mongodb://mongo:27017/")
auth_db = mongo["auth_db"]
users = auth_db["users"]

# Sync each student
for row in rows:
    net_userid, forename, surname, reg_grp, house, yeargroup, class_name = row
    net_userid = net_userid.lower()  # ✅ Normalize to lowercase

    users.update_one(
        {"username": net_userid},
        {"$set": {
            "forename": forename,
            "surname": surname,
            "reg_grp": reg_grp,
            "house": house,
            "current_yeargroup": yeargroup,
            "class_name": class_name
        }},
        upsert=True
    )


print("✅ MongoDB updated with full student details.")


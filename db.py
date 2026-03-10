import os
import mysql.connector

db = mysql.connector.connect(
    host=os.environ.get("DB_HOST", "localhost"),      # use env variable or default for local testing
    user=os.environ.get("DB_USER", "root"),           # same here
    password=os.environ.get("DB_PASSWORD", ""),       # same here
    database=os.environ.get("DB_NAME", "voting_db")   # same here
)

cursor = db.cursor(dictionary=True)
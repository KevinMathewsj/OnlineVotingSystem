import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Math@2003",
    database="voting_db"
)

cursor = db.cursor(dictionary=True)

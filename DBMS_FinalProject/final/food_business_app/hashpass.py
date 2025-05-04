""" 
IMPORTANT: 
ONLY RUN THIS SCRIPT THE FIRST TIME, 
AFTER CREATING THE DATABASE WITH setup_db.py.
THIS SCRIPT HASHES THE ADMIN CREDENTIALS.
"""
from werkzeug.security import generate_password_hash
import sqlite3
import os

# Define path to your actual database
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'food_business.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Set your admin username and current plain-text password
admin_username = 'Admin'
plain_password = 'Heisenberg'  # your actual admin password

# Generate hash
hashed_password = generate_password_hash(plain_password)

# Connect to database and update password using the correct connection
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("UPDATE Users SET Password = ? WHERE Username = ?", (hashed_password, admin_username))
conn.commit()
conn.close()

print("Admin password updated to hashed version.")

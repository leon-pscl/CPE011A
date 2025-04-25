import sqlite3
import os

# Get the absolute path to the current directory
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'orders.db')

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT,
        quantity INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()

print("Database and table created successfully!")

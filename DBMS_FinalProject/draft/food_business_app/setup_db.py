import sqlite3
import os
from datetime import datetime

# Define the database path (same as the one used in app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'food_business.db')

# Create the database directory if it doesn't exist
if not os.path.exists(os.path.dirname(DB_PATH)):
    os.makedirs(os.path.dirname(DB_PATH))

# Create a connection to the database
conn = sqlite3.connect(DB_PATH)

# Enable foreign key support in SQLite
conn.execute('PRAGMA foreign_keys = ON')

cursor = conn.cursor()

# Create tables
cursor.execute('''CREATE TABLE IF NOT EXISTS Menu_Items (
    Item_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Item_Name TEXT NOT NULL,
    Item_Type TEXT CHECK(Item_Type IN ('Mainstay', 'Special')) NOT NULL,
    Price REAL NOT NULL,
    Available_For TEXT CHECK(Available_For IN ('1A', '2A', 'both')) NOT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Customers (
    Customer_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Office TEXT NOT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Orders (
    Order_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Customer_ID INTEGER,
    Order_Type TEXT CHECK(Order_Type IN ('Walk-in', 'Office')) NOT NULL,
    Date DATE NOT NULL,
    Time_Ordered TIME NOT NULL,
    Time_Delivered TIME,
    Delivered BOOLEAN NOT NULL,
    FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID)
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Order_Items (
    OrderItem_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Order_ID INTEGER,
    Item_ID INTEGER,
    Quantity INTEGER NOT NULL,
    FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID),
    FOREIGN KEY (Item_ID) REFERENCES Menu_Items(Item_ID)
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Special_Requests (
    Request_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Customer_ID INTEGER,
    Request_Item TEXT NOT NULL,
    Request_Date DATE NOT NULL,
    Time_Ordered DATETIME NOT NULL,
    Time_Delivered DATETIME,
    Approved BOOLEAN NOT NULL,
    FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID)
)''')

# Insert sample walk-in items (beverages)
sample_items = [
    ("Coke", "Special", 1.50, "2A"),
    ("Pepsi", "Special", 1.50, "2A"),
    ("Lemonade", "Special", 1.80, "2A"),
    ("Iced Tea", "Special", 1.70, "2A")
]

# Insert sample items into the Menu_Items table
for item in sample_items:
    cursor.execute("INSERT INTO Menu_Items (Item_Name, Item_Type, Price, Available_For) VALUES (?, ?, ?, ?)", item)

# Commit changes and close the connection
conn.commit()
conn.close()

print(f"Database and tables created at {DB_PATH}")

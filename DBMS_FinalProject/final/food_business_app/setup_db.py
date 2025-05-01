import sqlite3
import os

# Define the database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'food_business.db')

# Create the database directory if it doesn't exist
if not os.path.exists(os.path.dirname(DB_PATH)):
    os.makedirs(os.path.dirname(DB_PATH))

# Create a connection to the database
conn = sqlite3.connect(DB_PATH)
conn.execute('PRAGMA foreign_keys = ON')
cursor = conn.cursor()

# ===== Users table with role support =====
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    User_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    First_Name TEXT NOT NULL,
    Last_Name TEXT NOT NULL,
    Full_Name TEXT NOT NULL,
    Username TEXT UNIQUE NOT NULL,
    Password TEXT NOT NULL,
    Address TEXT NOT NULL,
    Contact TEXT NOT NULL,
    Role TEXT CHECK(Role IN ('admin', 'user')) NOT NULL DEFAULT 'user'
)
''')

# ===== Menu_Items table =====
cursor.execute('''
CREATE TABLE IF NOT EXISTS Menu_Items (
    Item_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Item_Name TEXT NOT NULL,
    Category TEXT CHECK(Category IN ('Coffee', 'Tea', 'Dessert')) NOT NULL,
    Price REAL NOT NULL
)
''')

# ===== Customers table =====
cursor.execute('''
CREATE TABLE IF NOT EXISTS Customers (
    Customer_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Address TEXT NOT NULL
)
''')

# ===== Orders and Order_Items tables =====
cursor.execute('''
CREATE TABLE IF NOT EXISTS Orders (
    Order_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Customer_ID INTEGER,
    Order_Type TEXT CHECK(Order_Type IN ('Dine-in', 'Takeout')) NOT NULL,
    Date DATE NOT NULL,
    Time_Ordered TIME NOT NULL,
    Time_Delivered TIME,
    Delivered BOOLEAN NOT NULL,
    FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Order_Items (
    OrderItem_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Order_ID INTEGER,
    Item_ID INTEGER,
    Quantity INTEGER NOT NULL,
    FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID),
    FOREIGN KEY (Item_ID) REFERENCES Menu_Items(Item_ID)
)
''')

# ===== Special_Requests table =====
cursor.execute('''
CREATE TABLE IF NOT EXISTS Special_Requests (
    Request_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Customer_ID INTEGER,
    Request_Item TEXT NOT NULL,
    Request_Date DATE NOT NULL,
    Time_Ordered DATETIME NOT NULL,
    Time_Delivered DATETIME,
    Approved BOOLEAN NOT NULL,
    FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID)
)
''')

# ===== Insert sample menu items =====

sample_items = [
    ("Brewed Coffee", "Coffee", 55.00),
    ("Cappuccino", "Coffee", 70.00),
    ("Latte", "Coffee", 75.00),
    ("Iced Americano", "Coffee", 65.00),
    ("Hot Tea", "Tea", 50.00),
    ("Milk Tea", "Tea", 60.00),
    ("Chocolate Cake", "Dessert", 85.00),
    ("Banana Muffin", "Dessert", 40.00)
]

for item in sample_items:
    cursor.execute('''
        INSERT INTO Menu_Items (Item_Name, Category, Price)
        VALUES (?, ?, ?)
    ''', item)

# ===== Insert one admin account (optional) =====
cursor.execute("SELECT * FROM Users WHERE Username = 'admin'")
if not cursor.fetchone():
    cursor.execute('''
        INSERT INTO Users (First_Name, Last_Name, Full_Name, Username, Password, Address, Contact, Role)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ("Admin", "User", "Admin User", "admin", "admin098", "HQ", "09123456789", "admin"))


conn.commit()
conn.close()
print(f"Database and tables created at {DB_PATH}")

import sqlite3
import os
import datetime

# Define the database path (reuse same logic as setup_db.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'food_business.db')


def insert_sale(order_id, payment_method='Cash', payment_status='Paid'):
    """
    Inserts a new sale for the given order ID.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    cursor = conn.cursor()

    # Calculate total order amount
    cursor.execute('''
        SELECT SUM(Menu_Items.Price * Order_Items.Quantity)
        FROM Order_Items
        JOIN Menu_Items ON Order_Items.Item_ID = Menu_Items.Item_ID
        WHERE Order_Items.Order_ID = ?
    ''', (order_id,))
    result = cursor.fetchone()
    total_amount = result[0]

    if total_amount is None:
        print(f"[ERROR] No items found for Order ID {order_id}.")
        conn.close()
        return

    # Insert sale
    sale_date = datetime.date.today()
    cursor.execute('''
        INSERT INTO Sales (Order_ID, Total_Amount, Payment_Method, Payment_Status, Sale_Date)
        VALUES (?, ?, ?, ?, ?)
    ''', (order_id, total_amount, payment_method, payment_status, sale_date))

    conn.commit()
    print(f"[INFO] Sale recorded for Order ID {order_id}: PHP {total_amount:.2f}")
    conn.close()


def view_sales():
    """
    Prints a summary of all sales.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            Sales.Sale_ID,
            Sales.Sale_Date,
            Orders.Order_ID,
            IFNULL(Customers.Name, 'N/A') AS Customer_Name,
            GROUP_CONCAT(Menu_Items.Item_Name || ' (x' || Order_Items.Quantity || ')', ', ') AS Items,
            Sales.Total_Amount,
            Sales.Payment_Method,
            Sales.Payment_Status
        FROM Sales
        JOIN Orders ON Sales.Order_ID = Orders.Order_ID
        LEFT JOIN Customers ON Orders.Customer_ID = Customers.Customer_ID
        LEFT JOIN Order_Items ON Orders.Order_ID = Order_Items.Order_ID
        LEFT JOIN Menu_Items ON Order_Items.Item_ID = Menu_Items.Item_ID
        GROUP BY Sales.Sale_ID
        ORDER BY Sales.Sale_Date DESC
    ''')

    sales = cursor.fetchall()

    if not sales:
        print("[INFO] No sales found.")
    else:
        print("\n=== Sales Report ===")
        for sale in sales:
            print(f"Sale ID: {sale[0]} | Date: {sale[1]} | Order ID: {sale[2]} | Customer: {sale[3]}")
            print(f"Items: {sale[4]}")
            print(f"Total: PHP {sale[5]:.2f} | Method: {sale[6]} | Status: {sale[7]}")
            print("-" * 60)

    conn.close()

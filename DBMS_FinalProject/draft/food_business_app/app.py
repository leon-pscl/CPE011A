from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'food_business.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Home route where customers can place orders and special orders
@app.route('/', methods=['GET', 'POST'])
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch menu items
    cursor.execute("SELECT * FROM Menu_Items WHERE Available_For IN ('1A', 'both')")
    menu_items = cursor.fetchall()

    if request.method == 'POST':
        customer_name = request.form['customer_name']
        office = request.form['office']
        selected_items = request.form.getlist('item')
        quantities = request.form.getlist('quantity')
        special_order = request.form['special_order']
        delivery_date = request.form['delivery_date']

        if not selected_items and not special_order:
            return "No items selected or special order."

        # Insert customer (or find if exists)
        cursor.execute("SELECT Customer_ID FROM Customers WHERE Name = ? AND Office = ?", (customer_name, office))
        customer = cursor.fetchone()
        if customer:
            customer_id = customer['Customer_ID']
        else:
            cursor.execute("INSERT INTO Customers (Name, Office) VALUES (?, ?)", (customer_name, office))
            conn.commit()
            customer_id = cursor.lastrowid

        # Insert order
        now = datetime.now()
        order_date = now.date()
        order_time = now.time().strftime('%H:%M:%S')  # Convert time to string format
        cursor.execute(
            "INSERT INTO Orders (Customer_ID, Order_Type, Date, Time_Ordered, Delivered) VALUES (?, ?, ?, ?, ?)",
            (customer_id, 'Office', order_date, order_time, False)
        )
        conn.commit()
        order_id = cursor.lastrowid

        # Insert ordered items
        for item_id, quantity in zip(selected_items, quantities):
            if int(quantity) > 0:
                cursor.execute(
                    "INSERT INTO Order_Items (Order_ID, Item_ID, Quantity) VALUES (?, ?, ?)",
                    (order_id, item_id, quantity)
                )

        # Insert special order if provided
        if special_order:
            cursor.execute(
                "INSERT INTO Special_Requests (Customer_ID, Request_Item, Request_Date, Time_Ordered, Approved) VALUES (?, ?, ?, ?, ?)",
                (customer_id, special_order, delivery_date, now, False)
            )

        conn.commit()
        conn.close()
        return redirect(url_for('order_success'))

    return render_template('home.html', menu_items=menu_items)


# Route to show success message after placing an order
@app.route('/order_success')
def order_success():
    return render_template('order_success.html')

# Owner Dashboard - View orders and delivery status
@app.route('/owner_dashboard')
def owner_dashboard():
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch all orders, including walk-in orders
    cursor.execute('''SELECT Orders.Order_ID, Customers.Name, Orders.Order_Type, Orders.Date, Orders.Time_Ordered, Orders.Time_Delivered, Orders.Delivered 
                      FROM Orders 
                      JOIN Customers ON Orders.Customer_ID = Customers.Customer_ID''')
    orders = cursor.fetchall()

    # Close the connection
    conn.close()

    return render_template('owner_dashboard.html', orders=orders)


# View all orders for the owner
@app.route('/view_orders')
def view_orders():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all orders
    cursor.execute("""
        SELECT Orders.Order_ID, Orders.Date, Orders.Time_Ordered, Orders.Delivered, Customers.Name
        FROM Orders
        JOIN Customers ON Orders.Customer_ID = Customers.Customer_ID
    """)
    orders = cursor.fetchall()
    conn.close()

    return render_template('view_orders.html', orders=orders)

# Update delivery status (mark as delivered or not)
@app.route('/update_delivery_status/<int:order_id>', methods=['POST'])
def update_delivery_status(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Delivered FROM Orders WHERE Order_ID = ?", (order_id,))
    order = cursor.fetchone()

    if order:
        new_status = not order['Delivered']
        cursor.execute("UPDATE Orders SET Delivered = ? WHERE Order_ID = ?", (new_status, order_id))
        conn.commit()
    conn.close()
    return redirect(url_for('view_orders'))

# View special requests for the owner
@app.route('/view_special_requests')
def view_special_requests():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all special requests
    cursor.execute("""
        SELECT Special_Requests.Request_ID, Special_Requests.Request_Item, Special_Requests.Request_Date, Special_Requests.Approved, Customers.Name
        FROM Special_Requests
        JOIN Customers ON Special_Requests.Customer_ID = Customers.Customer_ID
    """)
    requests = cursor.fetchall()
    conn.close()

    return render_template('view_special_requests.html', requests=requests)

# Approve or disapprove special requests
@app.route('/approve_special_request/<int:request_id>', methods=['POST'])
def approve_special_request(request_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Approved FROM Special_Requests WHERE Request_ID = ?", (request_id,))
    request = cursor.fetchone()

    if request:
        new_status = not request['Approved']
        cursor.execute("UPDATE Special_Requests SET Approved = ? WHERE Request_ID = ?", (new_status, request_id))
        conn.commit()
    conn.close()
    return redirect(url_for('view_special_requests'))

# Input Walk-In Order (Owner)
@app.route('/input_walk_in_order', methods=['GET', 'POST'])
def input_walk_in_order():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        item_id = request.form['order_items']
        quantity = request.form['quantity']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert walk-in order
        cursor.execute("SELECT Customer_ID FROM Customers WHERE Name = ?", (customer_name,))
        customer = cursor.fetchone()
        if not customer:
            cursor.execute("INSERT INTO Customers (Name, Office) VALUES (?, ?)", (customer_name, 'N/A'))
            conn.commit()
            customer_id = cursor.lastrowid
        else:
            customer_id = customer['Customer_ID']

        cursor.execute(
            "INSERT INTO Orders (Customer_ID, Order_Type, Date, Time_Ordered, Delivered) VALUES (?, ?, ?, ?, ?)",
            (customer_id, 'Walk-in', datetime.now().date(), datetime.now().time(), False)
        )
        conn.commit()
        order_id = cursor.lastrowid

        # Insert walk-in order items
        cursor.execute(
            "INSERT INTO Order_Items (Order_ID, Item_ID, Quantity) VALUES (?, ?, ?)", (order_id, item_id, quantity)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('owner_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch menu items
    cursor.execute("SELECT * FROM Menu_Items WHERE Available_For = '2A'")
    menu_items = cursor.fetchall()
    conn.close()

    return render_template('owner_dashboard.html', menu_items=menu_items)

if __name__ == '__main__':
    app.run(debug=True)

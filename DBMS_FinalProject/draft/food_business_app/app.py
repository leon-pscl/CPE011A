from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'food_business.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    full_name = session.get('full_name')
    address = session.get('address')

    conn = get_db_connection()
    cursor = conn.cursor()
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

        # Check if customer exists
        cursor.execute("SELECT Customer_ID FROM Customers WHERE Name = ? AND Office = ?", (customer_name, office))
        customer = cursor.fetchone()
        if customer:
            customer_id = customer['Customer_ID']
        else:
            cursor.execute("INSERT INTO Customers (Name, Office) VALUES (?, ?)", (customer_name, office))
            conn.commit()
            customer_id = cursor.lastrowid

        now = datetime.now()
        order_date = now.date().isoformat()                      # Convert to string
        order_time = now.time().strftime("%H:%M:%S")             # Convert to string

        # Insert into Orders with formatted date/time
        cursor.execute(
            "INSERT INTO Orders (Customer_ID, Order_Type, Date, Time_Ordered, Delivered) VALUES (?, ?, ?, ?, ?)",
            (customer_id, 'Office', order_date, order_time, False)
        )
        conn.commit()
        order_id = cursor.lastrowid

        # Insert order items
        for item_id, quantity in zip(selected_items, quantities):
            if int(quantity) > 0:
                cursor.execute("INSERT INTO Order_Items (Order_ID, Item_ID, Quantity) VALUES (?, ?, ?)",
                               (order_id, item_id, quantity))

        # Insert special request (if any)
        if special_order:
            cursor.execute(
                "INSERT INTO Special_Requests (Customer_ID, Request_Item, Request_Date, Time_Ordered, Approved) VALUES (?, ?, ?, ?, ?)",
                (customer_id, special_order, delivery_date, order_time, False)  # Use same order_time
            )

        conn.commit()
        conn.close()
        return redirect(url_for('order_success'))

    return render_template('home.html', menu_items=menu_items, full_name=full_name, address=address)

if __name__ == '__main__':
    app.run(debug=True)

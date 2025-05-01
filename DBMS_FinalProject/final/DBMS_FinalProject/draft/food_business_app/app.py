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

# ===== RGSTR INTERFACE =====
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first = request.form['first_name']
        last = request.form['last_name']
        birthdate = request.form['birthdate']
        address = request.form['address']
        contact = request.form['contact']
        password = request.form['password']

        full_name = f"{first} {last}"
        username = f"{first[0].lower()}{last.lower()}"
        role = request.form['role']


        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Users WHERE Username = ?", (username,))
        if cursor.fetchone():
            flash("Username already exists.")
            return redirect(url_for('register'))

        cursor.execute('''
            INSERT INTO Users (First_Name, Last_Name, Full_Name, Username, Password, Birthdate, Address, Contact, Role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first, last, full_name, username, password, birthdate, address, contact, role))
        conn.commit()
        conn.close()

        flash("Registration successful! Your username is: " + username)
        return render_template('success.html', username=username)

    return render_template('register.html')
# ===========================

# ===== LOGIN INTERFACE =====
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Username = ? AND Password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = user['Username']
            session['full_name'] = user['Full_Name']
            session['address'] = user['Address']
            session['role'] = user['Role']
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
# ===========================

@app.route('/', methods=['GET', 'POST'])
def home():
    user_logged_in = 'user' in session

    if user_logged_in and session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    full_name = session.get('full_name') if user_logged_in else None
    address = session.get('address') if user_logged_in else None

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT * FROM Menu_Items")
    menu_items_raw = cursor.fetchall()
    menu_items = list({item['Item_ID']: item for item in menu_items_raw}.values())

    if request.method == 'POST':
        if not user_logged_in:
            return redirect(url_for('login'))

        customer_name = full_name
        selected_items = request.form.getlist('item')
        special_order = request.form['special_order']
        delivery_date = request.form['delivery_date']
        order_type = request.form['order_type']

        if not selected_items and not special_order:
            return "No items selected or special order."

        cursor.execute("SELECT Customer_ID FROM Customers WHERE Name = ? AND Address = ?", (customer_name, address))
        customer = cursor.fetchone()
        if customer:
            customer_id = customer['Customer_ID']
        else:
            cursor.execute("INSERT INTO Customers (Name, Address) VALUES (?, ?)", (customer_name, address))
            conn.commit()
            customer_id = cursor.lastrowid

        now = datetime.now()
        date_str = now.date().isoformat()
        time_str = now.time().isoformat()
        now_str = now.isoformat()

        cursor.execute(
            "INSERT INTO Orders (Customer_ID, Order_Type, Date, Time_Ordered, Delivered) VALUES (?, ?, ?, ?, ?)",
            (customer_id, order_type, date_str, time_str, False)
        )
        conn.commit()
        order_id = cursor.lastrowid

        for item_id in selected_items:
            quantity = request.form.get(f'quantity_{item_id}', 0)
            if int(quantity) > 0:
                cursor.execute(
                    "INSERT INTO Order_Items (Order_ID, Item_ID, Quantity) VALUES (?, ?, ?)",
                    (order_id, item_id, quantity)
                )

        if special_order:
            cursor.execute(
                "INSERT INTO Special_Requests (Customer_ID, Request_Item, Request_Date, Time_Ordered, Approved) VALUES (?, ?, ?, ?, ?)",
                (customer_id, special_order, delivery_date, now_str, False)
            )

        conn.commit()
        conn.close()
        return redirect(url_for('order_success'))

    conn.close()
    return render_template(
        'home.html',
        menu_items=menu_items,
        full_name=full_name,
        address=address,
        user_logged_in=user_logged_in
    )


@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.Order_ID, c.Name AS Customer_Name, c.Address, o.Date, o.Time_Ordered, o.Delivered
        FROM Orders o
        JOIN Customers c ON o.Customer_ID = c.Customer_ID
        ORDER BY o.Date DESC, o.Time_Ordered DESC
    """)
    orders = cursor.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', orders=orders)

@app.route('/order_success')
def order_success():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the most recent order by the current user
    full_name = session.get('full_name')
    address = session.get('address')

    cursor.execute("""
        SELECT c.Customer_ID FROM Customers c
        WHERE c.Name = ? AND c.Address = ?
    """, (full_name, address))
    customer = cursor.fetchone()

    if not customer:
        return render_template('order_success.html', order_items=[], special=None)

    customer_id = customer['Customer_ID']

    cursor.execute("""
        SELECT * FROM Orders
        WHERE Customer_ID = ?
        ORDER BY Date DESC, Time_Ordered DESC
        LIMIT 1
    """, (customer_id,))
    latest_order = cursor.fetchone()

    if not latest_order:
        return render_template('order_success.html', order_items=[], special=None)

    order_id = latest_order['Order_ID']

    # Fetch regular items
    cursor.execute("""
        SELECT m.Item_Name, oi.Quantity, m.Price
        FROM Order_Items oi
        JOIN Menu_Items m ON m.Item_ID = oi.Item_ID
        WHERE oi.Order_ID = ?
    """, (order_id,))
    order_items = cursor.fetchall()

    # Fetch special request if any
    cursor.execute("""
        SELECT Request_Item FROM Special_Requests
        WHERE Customer_ID = ? AND Request_Date = ? AND Time_Ordered = ?
    """, (customer_id, latest_order['Date'], latest_order['Time_Ordered']))
    special = cursor.fetchone()

    conn.close()

    return render_template('order_success.html', order_items=order_items, special=special)


if __name__ == '__main__':
    app.run(debug=True)
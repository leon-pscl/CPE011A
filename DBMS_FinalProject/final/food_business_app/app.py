from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'food_business.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def generate_unique_username(first_name, last_name, cursor):
    cleaned_last_name = re.sub(r'[^A-Za-z0-9]', '', last_name)
    base_username = (first_name[0] + cleaned_last_name).lower()
    username = base_username
    count = 1

    cursor.execute("SELECT Username FROM Users WHERE Username LIKE ?", (f"{base_username}%",))
    existing_usernames = [row["Username"] for row in cursor.fetchall()]

    while username in existing_usernames:
        username = f"{base_username}{count}"
        count += 1

    return username
#fetch values from CATEGORIES table
def get_categories():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT Category_Name FROM Categories")
    categories = cursor.fetchall()
    conn.close()
    return categories

#add menu items
def add_menu_item(item_name, category, price):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Menu_Items (Item_Name, Category, Price) 
        VALUES (?, ?, ?)
    ''', (item_name, category, price))
    conn.commit()
    conn.close()


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        address = request.form["address"]
        contact = request.form["contact"]
        password = request.form["password"]
        role = request.form["role"]

        names = full_name.split()
        if len(names) < 2:
            flash("Please enter both first and last name.")
            return redirect(url_for("register"))

        first_name = names[0]
        last_name = " ".join(names[1:])

        conn = get_db_connection()
        cursor = conn.cursor()
        username = generate_unique_username(first_name, last_name, cursor)

        cursor.execute(''' 
            INSERT INTO Users (First_Name, Last_Name, Full_Name, Username, Password, Address, Contact, Role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, full_name, username, password, address, contact, role))

        conn.commit()
        conn.close()
        return render_template("success.html", username=username)

    return render_template("register.html")


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
            flash("Invalid username or password.", 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/', methods=['GET', 'POST'])
def home():
    user_logged_in = 'user' in session
    if user_logged_in and session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    full_name = session.get('full_name')
    address = session.get('address')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT * FROM Menu_Items")
    menu_items = list({item['Item_ID']: item for item in cursor.fetchall()}.values())

    if request.method == 'POST':
        if not user_logged_in:
            conn.close()
            return redirect(url_for('login'))

        customer_name = full_name
        selected_items = request.form.getlist('item')
        special_order = request.form['special_order']
        delivery_date = request.form['delivery_date']
        order_type = request.form['order_type']

        if not selected_items and not special_order:
            conn.close()
            flash("No items or special request submitted.")
            return redirect(url_for('home'))

        cursor.execute("SELECT Customer_ID FROM Customers WHERE Name = ? AND Address = ?", (customer_name, address))
        customer = cursor.fetchone()

        if customer:
            customer_id = customer['Customer_ID']
        else:
            cursor.execute("INSERT INTO Customers (Name, Address) VALUES (?, ?)", (customer_name, address))
            conn.commit()
            customer_id = cursor.lastrowid

        now = datetime.now()
        cursor.execute(
            "INSERT INTO Orders (Customer_ID, Order_Type, Date, Time_Ordered, Delivered) VALUES (?, ?, ?, ?, ?)",
            (customer_id, order_type, now.date(), now.time().isoformat(), False)
        )
        conn.commit()
        order_id = cursor.lastrowid

        for item_id in selected_items:
            quantity = int(request.form.get(f'quantity_{item_id}', 0))
            if quantity > 0:
                cursor.execute(
                    "INSERT INTO Order_Items (Order_ID, Item_ID, Quantity) VALUES (?, ?, ?)",
                    (order_id, item_id, quantity)
                )

        if special_order:
            cursor.execute(
                "INSERT INTO Special_Requests (Customer_ID, Request_Item, Request_Date, Time_Ordered, Approved) VALUES (?, ?, ?, ?, ?)",
                (customer_id, special_order, delivery_date, now.isoformat(), False)
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
    
     # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    cursor.execute("""
        SELECT o.Order_ID, c.Name AS Customer_Name, c.Address, o.Date, o.Time_Ordered, o.Delivered
        FROM Orders o
        JOIN Customers c ON o.Customer_ID = c.Customer_ID
        ORDER BY o.Date DESC, o.Time_Ordered DESC
    """)
    
    # Fetch orders with pagination
    cursor.execute("""
        SELECT o.Order_ID, c.Name AS Customer_Name, c.Address, o.Date, o.Time_Ordered, o.Delivered
        FROM Orders o
        JOIN Customers c ON o.Customer_ID = c.Customer_ID
        ORDER BY o.Date DESC, o.Time_Ordered DESC
        LIMIT ? OFFSET ?
    """, (per_page, offset))
    orders = cursor.fetchall()

    # Count total orders for pagination links
    cursor.execute("SELECT COUNT(*) FROM Orders")
    total_orders = cursor.fetchone()[0]
    total_pages = (total_orders // per_page) + (1 if total_orders % per_page else 0)
    
    orders = cursor.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', orders=orders, total_pages=total_pages, current_page=page)
#change if order has been delivered
@app.route('/mark_delivered/<int:order_id>', methods=['POST'])
def mark_delivered(order_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Orders SET Delivered = 1 WHERE Order_ID = ?", (order_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/order_details/<int:order_id>')
def order_details(order_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch order details
    cursor.execute("""
        SELECT oi.Item_ID, mi.Item_Name, oi.Quantity, mi.Price
        FROM Order_Items oi
        JOIN Menu_Items mi ON oi.Item_ID = mi.Item_ID
        WHERE oi.Order_ID = ?
    """, (order_id,))
    order_items = cursor.fetchall()

    # Fetch any special requests for this order
    cursor.execute("""
        SELECT Special_Request
        FROM Special_Requests
        WHERE Order_ID = ?
    """, (order_id,))
    special_requests = cursor.fetchall()

    conn.close()

    return render_template('order_details.html', order_id=order_id, order_items=order_items, special_requests=special_requests)

@app.route('/order_success')
def order_success():
    if 'user' not in session:
        return redirect(url_for('login'))

    full_name = session.get('full_name')
    address = session.get('address')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Customer_ID FROM Customers
        WHERE Name = ? AND Address = ?
    """, (full_name, address))

    customer = cursor.fetchone()
    if not customer:
        conn.close()
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
        conn.close()
        return render_template('order_success.html', order_items=[], special=None)

    order_id = latest_order['Order_ID']

    cursor.execute("""
        SELECT m.Item_Name, oi.Quantity, m.Price
        FROM Order_Items oi
        JOIN Menu_Items m ON m.Item_ID = oi.Item_ID
        WHERE oi.Order_ID = ?
    """, (order_id,))
    order_items = cursor.fetchall()

    cursor.execute("""
        SELECT Request_Item FROM Special_Requests
        WHERE Customer_ID = ? AND Request_Date = ? AND Time_Ordered = ?
    """, (customer_id, latest_order['Date'], latest_order['Time_Ordered']))
    special = cursor.fetchone()

    conn.close()
    return render_template('order_success.html', order_items=order_items, special=special)




@app.route('/menu-management', methods=['GET', 'POST'])
def menu_management():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Handle adding a new item
    if request.method == 'POST':
        item_name = request.form['item_name']
        category = request.form['category']
        price = request.form['price']

        cursor.execute("INSERT INTO Menu_Items (Item_Name, Category, Price) VALUES (?, ?, ?)",
                       (item_name, category, price))
        conn.commit()
        conn.close()
        flash('Menu item added successfully.', 'success')
        return redirect(url_for('menu_management'))

    # Check for edit request
    edit_id = request.args.get('edit_id')
    item_to_edit = None
    if edit_id:
        cursor.execute("SELECT * FROM Menu_Items WHERE Item_ID = ?", (edit_id,))
        item_to_edit = cursor.fetchone()

    # Show all menu items
    cursor.execute("SELECT * FROM Menu_Items")
    menu_items = cursor.fetchall()
    conn.close()

    return render_template('menu_management.html', menu_items=menu_items, item_to_edit=item_to_edit)

#edit menu items
@app.route('/menu-management/edit/<int:item_id>', methods=['POST'])
def edit_menu_item(item_id):
    item_name = request.form['item_name']
    category = request.form['category']
    price = request.form['price']

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE Menu_Items SET Item_Name = ?, Category = ?, Price = ? WHERE Item_ID = ?",
                   (item_name, category, price, item_id))
    conn.commit()
    conn.close()

    flash('Menu item updated successfully.', 'success')
    return redirect(url_for('menu_management'))

# delete menu items
@app.route('/menu-management/delete/<int:item_id>', methods=['POST'])
def delete_menu_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Menu_Items WHERE Item_ID = ?", (item_id,))
    conn.commit()
    conn.close()

    flash('Menu item deleted successfully.', 'info')
    return redirect(url_for('menu_management'))



@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    flash("You have been logged out.", "info")  # Flash a message to indicate successful logout
    return redirect(url_for('login'))  # Redirect to the login page


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime
import re
from werkzeug.security import generate_password_hash, check_password_hash

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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Category_Name FROM Categories")
    categories = cursor.fetchall()
    conn.close()
    return categories

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        address = request.form["address"]
        contact = request.form["contact"]
        password = generate_password_hash(request.form["password"]) #Hashed password for security
        role = "user"

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
        cursor.execute("SELECT * FROM Users WHERE Username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['Password'], password):
            session['user'] = user['Username']
            session['full_name'] = user['Full_Name']
            session['address'] = user['Address']
            session['contact'] = user['Contact']
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
        contact = session.get('contact')
        selected_items = request.form.getlist('item_ids[]')
        requested_delivery_time = request.form['requested_delivery_time']
        order_type = request.form['order_type']

        cursor.execute("SELECT Customer_ID FROM Customers WHERE Name = ? AND Address = ?", (customer_name, address))
        customer = cursor.fetchone()

        if customer:
            customer_id = customer['Customer_ID']
        else:
            cursor.execute('''INSERT INTO Customers (Name, Address, Phone) VALUES (?, ?, ?)''', (full_name, address, contact))
            conn.commit()
            customer_id = cursor.lastrowid

        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        cursor.execute(
            "INSERT INTO Orders (Customer_ID, Order_Type, Date, Time_Ordered, Delivered, Requested_Delivery_Time) VALUES (?, ?, ?, ?, ?, ?)",
            (customer_id, order_type, now.date(), now.time().isoformat(), False, requested_delivery_time)
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

@app.route('/special_requests', methods=['GET', 'POST'])
def special_requests():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_logged_in = 'user' in session
    full_name = session.get('full_name')
    address = session.get('address')
    contact = session.get('contact')
    
    if request.method == 'POST':
        request_item = request.form['special_request']
        if len(request_item) > 0:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''SELECT Customer_ID FROM Customers WHERE Name = ? AND Address = ?''', (full_name, address))
            customer = cursor.fetchone()

            if customer:
                customer_id = customer['Customer_ID']
            else:
                cursor.execute('''INSERT INTO Customers (Name, Address, Phone) VALUES (?, ?, ?)''', (full_name, address, contact))
                conn.commit()
                customer_id = cursor.lastrowid

            now = datetime.now()
            date_str = now.strftime('%d-%m-%Y')
            time_str = now.strftime('%H:%M:%S')

            # Insert into Special_Requests table, ensuring proper date and time handling
            cursor.execute('''INSERT INTO Special_Requests (Customer_ID, Request_Item, Request_Date, Request_Time, Time_Ordered, Approved) 
                  VALUES (?, ?, ?, ?, ?, ?)''', 
                (customer_id, request_item, now.strftime('%Y-%m-%d'), now.time().isoformat(), now.isoformat(), False))

            conn.commit()
            conn.close()

            flash("Special request added successfully.", "success")
            return redirect(url_for('request_success'))  # Redirect to request_success page

        else:
            flash("Please enter a special request.", "error")
            return redirect(url_for('special_requests'))

    return render_template('special_requests.html', user_logged_in=user_logged_in, full_name=full_name, address=address)

@app.route('/request_success')
def request_success():
    # Check if the user is logged in, if not, redirect them to login
    if 'user' not in session:
        return redirect(url_for('login'))

    user_logged_in = 'user' in session
    return render_template('request_success.html', user_logged_in=user_logged_in)


"""FOR REQUEST MANAGEMENT PAGE"""
from datetime import datetime

@app.route('/request_management')
def request_management():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(''' 
        SELECT 
            sr.Request_ID AS id,
            c.Name AS customer_name,
            c.Phone AS customer_phone,
            sr.Request_Item AS special_request,
            sr.Request_Date AS request_date,
            sr.Request_Time AS request_time,
            sr.Time_Ordered AS time_ordered,
            sr.Time_Delivered AS time_delivered,
            sr.Approved AS approved,
            sr.Time_Approved AS time_approved,
            sr.Time_Rejected AS time_rejected,
            sr.Price AS price,  -- Added this line to select the price
            CASE 
                WHEN sr.Time_Rejected IS NOT NULL THEN 1 
                ELSE 0 
            END AS rejected
        FROM Special_Requests sr
        JOIN Customers c ON sr.Customer_ID = c.Customer_ID
        ORDER BY sr.Time_Ordered DESC
    ''')

    requests = cursor.fetchall()

    # Convert sqlite3.Row objects to dictionaries to allow item assignment
    requests_dict = [dict(request) for request in requests]

    # Format time_ordered for each request
    for request in requests_dict:
        if request['time_ordered']:
            # Convert the string to a datetime object, allowing for fractional seconds
            try:
                time_ordered_obj = datetime.strptime(request['time_ordered'], '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                # Fallback in case there's no fractional part
                time_ordered_obj = datetime.strptime(request['time_ordered'], '%Y-%m-%dT%H:%M:%S')
            
            # Then format it
            request['time_ordered'] = time_ordered_obj.strftime('%d %B %Y | %H:%M:%S')

    conn.close()

    return render_template('request_management.html', requests=requests_dict, user_logged_in=True)




from datetime import datetime

@app.route('/approve_request/<int:request_id>')
def approve_request(request_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Proper format for database storage
    cursor.execute('''
        UPDATE Special_Requests
        SET Approved = 1,
            Time_Approved = ?
        WHERE Request_ID = ?
    ''', (now, request_id))

    conn.commit()
    conn.close()

    flash("Request approved.", "success")
    return redirect(url_for('request_management'))


@app.route('/reject_request/<int:request_id>')
def reject_request(request_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Proper format for database storage
    cursor.execute('''
        UPDATE Special_Requests
        SET Approved = 0,
            Time_Rejected = ?
        WHERE Request_ID = ?
    ''', (now, request_id))

    conn.commit()
    conn.close()

    flash("Request rejected.", "warning")
    return redirect(url_for('request_management'))


@app.route('/mark_special_request_delivered/<int:request_id>', methods=['POST'])
def mark_special_request_delivered(request_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Proper format for database storage

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE Special_Requests
        SET Time_Delivered = ?
        WHERE Request_ID = ?
    ''', (current_time, request_id))

    conn.commit()
    conn.close()

    next_url = request.form.get('next')
    return redirect(next_url or url_for('request_management'))


@app.route('/edit_request_time/<int:request_id>', methods=['POST'])
def edit_request_time(request_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    new_date = request.form['request_date']
    new_time = request.form['request_time']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE Special_Requests
        SET Request_Date = ?, Request_Time = ?
        WHERE Request_ID = ?
    ''', (new_date, new_time, request_id))

    conn.commit()
    conn.close()

    flash("Requested delivery time updated.", "success")
    return redirect(url_for('request_management'))

@app.route('/update_price/<int:request_id>', methods=['POST'])
def update_price(request_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    price = request.form['price']
    try:
        price = float(price)
    except ValueError:
        flash("Invalid price entered.", "danger")
        return redirect(url_for('request_management'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE Special_Requests
        SET Price = ?
        WHERE Request_ID = ?
    ''', (price, request_id))

    conn.commit()
    conn.close()

    flash("Price updated successfully.", "success")
    return redirect(url_for('request_management'))


"""END REQUEST MANAGEMENT PAGE"""
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Pagination for orders
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    # Count total orders
    cursor.execute("SELECT COUNT(*) FROM Orders")
    total_orders = cursor.fetchone()[0]
    total_pages = (total_orders + per_page - 1) // per_page

    # Fetch orders with customer name and address from Customers table
    cursor.execute(""" 
        SELECT o.Order_ID, o.Date, o.Time_Ordered, o.Delivered, o.Time_Delivered, 
        c.Name AS Customer_Name, c.Address
        FROM Orders o
        LEFT JOIN Customers c ON o.Customer_ID = c.Customer_ID
        ORDER BY o.Date DESC, o.Time_Ordered DESC
        LIMIT ? OFFSET ?
    """, (per_page, offset))

    orders = cursor.fetchall()

    # Count pending special requests (requests that have not been approved)
    cursor.execute("SELECT COUNT(*) FROM Special_Requests WHERE Approved = 0")
    pending_requests = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'admin_dashboard.html',
        orders=orders,
        current_page=page,
        total_pages=total_pages,
        pending_requests=pending_requests  # Passing the number of pending special requests
    )

@app.route('/mark_delivered/<int:order_id>', methods=['POST'])
def mark_delivered(order_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the current time for the delivery timestamp
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Update the order status to delivered and set the time delivered
    cursor.execute('''
        UPDATE Orders 
        SET Delivered = 1, Time_Delivered = ? 
        WHERE Order_ID = ?
    ''', (current_time, order_id))

    conn.commit()
    conn.close()

    # After updating, redirect to the admin dashboard
    next_url = request.form.get('next')
    return redirect(next_url or url_for('admin_dashboard'))


@app.route('/order_details/<int:order_id>')
def order_details(order_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch order items for the given order ID
    cursor.execute('''
        SELECT oi.Quantity, mi.Item_Name, mi.Price
        FROM Order_Items oi
        JOIN Menu_Items mi ON oi.Item_ID = mi.Item_ID
        WHERE oi.Order_ID = ?
    ''', (order_id,))
    order_items = cursor.fetchall()

    # Fetch delivery-related order info and customer info
    cursor.execute('''
        SELECT o.Requested_Delivery_Time, o.Delivered, o.Time_Delivered, c.Name
        FROM Orders o
        JOIN Customers c ON o.Customer_ID = c.Customer_ID
        WHERE o.Order_ID = ?
    ''', (order_id,))
    order_meta = cursor.fetchone()

    conn.close()
    
    # Extract data from order_meta
    requested_delivery_time = order_meta['Requested_Delivery_Time'] if order_meta else None
    delivered = order_meta['Delivered'] if order_meta else None
    time_delivered = order_meta['Time_Delivered'] if order_meta else None
    customer_name = order_meta['Name'] if order_meta else None
    
    return render_template('order_details.html',
                        order_id=order_id,
                        order_items=order_items,
                        requested_delivery_time=requested_delivery_time,
                        delivered=delivered,
                        time_delivered=time_delivered,
                        customer_name=customer_name)
@app.route('/order_success')
def order_success():
    if 'user' not in session:
        return redirect(url_for('login'))

    full_name = session.get('full_name')
    address = session.get('address')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the customer ID
    cursor.execute("""
        SELECT Customer_ID FROM Customers
        WHERE Name = ? AND Address = ?
    """, (full_name, address))
    customer = cursor.fetchone()

    if not customer:
        conn.close()
        return render_template('order_success.html', order_items=[], requested_delivery_time=None)

    customer_id = customer['Customer_ID']

    # Get the most recent order
    cursor.execute("""
        SELECT * FROM Orders
        WHERE Customer_ID = ?
        ORDER BY Date DESC, Time_Ordered DESC
        LIMIT 1
    """, (customer_id,))
    latest_order = cursor.fetchone()

    if not latest_order:
        conn.close()
        return render_template('order_success.html', order_items=[], requested_delivery_time=None)

    order_id = latest_order['Order_ID']

    # Get the ordered menu items
    cursor.execute("""
        SELECT m.Item_Name, oi.Quantity, m.Price
        FROM Order_Items oi
        JOIN Menu_Items m ON m.Item_ID = oi.Item_ID
        WHERE oi.Order_ID = ?
    """, (order_id,))
    order_items = cursor.fetchall()

    # Format the requested delivery time if available
    requested_delivery_time = latest_order['Requested_Delivery_Time']
    if requested_delivery_time:
        requested_delivery_time = datetime.strptime(requested_delivery_time, '%H:%M').strftime('%I:%M %p')

    conn.close()

    return render_template('order_success.html', order_items=order_items, requested_delivery_time=requested_delivery_time)


#add menu items
def add_menu_item(item_name, category, price):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(''' 
        INSERT INTO Menu_Items (Item_Name, Category, Price) 
        VALUES (?, ?, ?)
    ''', (item_name, category, price))
    conn.commit()
    conn.close()
    
@app.route('/menu_management', methods=['GET', 'POST'])
def menu_management():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        if 'delete_item_id' in request.form:
            # Deleting a menu item
            item_id = request.form.get('delete_item_id')
            cursor.execute('DELETE FROM Menu_Items WHERE Item_ID = ?', (item_id,))
            conn.commit()
            flash('Menu item deleted successfully!')
        else:
            # Adding or Editing a menu item
            item_id = request.form.get('item_id')
            item_name = request.form.get('item_name')
            category = request.form.get('category')
            price = request.form.get('price')

            if item_id:
                # Editing
                cursor.execute("""
                    UPDATE Menu_Items
                    SET Item_Name = ?, Category = ?, Price = ?
                    WHERE Item_ID = ?
                """, (item_name, category, price, item_id))
                flash('Menu item updated successfully!')
            else:
                # Adding
                cursor.execute("""
                    INSERT INTO Menu_Items (Item_Name, Category, Price)
                    VALUES (?, ?, ?)
                """, (item_name, category, price))
                flash('Menu item added successfully!')

            conn.commit()

    # Fetch menu items
    cursor.execute("""
    SELECT Item_ID, Item_Name, Category, Price 
    FROM Menu_Items
    ORDER BY 
        CASE Category
            WHEN 'Regulars' THEN 1
            WHEN 'Specials' THEN 2
            WHEN 'Beverages' THEN 3
            WHEN 'Extras' THEN 4
            ELSE 5
        END
""")

    menu_items = cursor.fetchall()

    # Handle Edit Form
    item_to_edit = None
    if request.args.get('edit_id'):
        cursor.execute('SELECT * FROM Menu_Items WHERE Item_ID = ?', (request.args.get('edit_id'),))
        item_to_edit = cursor.fetchone()

    conn.close()

    return render_template('menu_management.html', menu_items=menu_items, item_to_edit=item_to_edit)

#SALES SUMMARY PAGE
@app.route('/sales_summary', methods=['GET', 'POST'])
def sales_summary():
    # Ensure the user is an admin
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    # Establish database connection
    conn = get_db_connection()

    # Fetch the customer names for the Special Requests filter
    customer_names = conn.execute("""
        SELECT DISTINCT c.Name 
        FROM Special_Requests sr
        JOIN Customers c ON sr.Customer_ID = c.Customer_ID
    """).fetchall()

    # Fetch the menu items for the Regular Orders filter
    menu_items = conn.execute("""
        SELECT Item_Name 
        FROM Menu_Items
    """).fetchall()

    # Process Special Requests filter
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    customer_name_filter = request.args.get('customer_name')

    # Base query for special requests
    special_request_query = """
        SELECT sr.Request_Item AS request_item,
               sr.Price AS price,
               sr.Time_Delivered AS time_delivered,
               c.Name AS customer_name
        FROM Special_Requests sr
        JOIN Customers c ON sr.Customer_ID = c.Customer_ID
        WHERE sr.Time_Delivered IS NOT NULL
    """

    # Add date and customer filters to the query if specified
    if start_date:
        special_request_query += f" AND sr.Time_Delivered >= '{start_date}'"
    if end_date:
        special_request_query += f" AND sr.Time_Delivered <= '{end_date}'"
    if customer_name_filter:
        special_request_query += f" AND c.Name = '{customer_name_filter}'"

    # Fetch filtered special requests
    delivered_requests = conn.execute(special_request_query).fetchall()

    # Calculate the total revenue from special requests
    total_special_sales = sum(req['price'] for req in delivered_requests)

    # Regular Orders Sales: Fetching data for delivered regular orders
    item_filter = request.args.get('item_filter')
    regular_orders_query = """
        SELECT mi.Item_Name AS item_name,
               mi.Price AS item_price,
               oi.Quantity AS quantity,
               (oi.Quantity * mi.Price) AS total_price,
               o.Date AS order_date,
               o.Time_Ordered AS time_ordered,
               o.Time_Delivered AS time_delivered,
               c.Name AS customer_name
        FROM Order_Items oi
        JOIN Menu_Items mi ON oi.Item_ID = mi.Item_ID
        JOIN Orders o ON oi.Order_ID = o.Order_ID
        JOIN Customers c ON o.Customer_ID = c.Customer_ID
        WHERE o.Delivered = 1
    """

    if start_date:
        regular_orders_query += f" AND o.Time_Delivered >= '{start_date}'"
    if end_date:
        regular_orders_query += f" AND o.Time_Delivered <= '{end_date}'"
    if item_filter:
        regular_orders_query += f" AND mi.Item_Name = '{item_filter}'"

    regular_orders = conn.execute(regular_orders_query).fetchall()

    # Calculate the total revenue from regular orders
    total_regular_sales = sum(row['total_price'] for row in regular_orders)

    # Combined Total Sales
    total_overall_sales = total_special_sales + total_regular_sales

    # Close the database connection
    conn.close()

    # Render the sales summary page with the data
    return render_template(
        'sales_summary.html',
        delivered_requests=delivered_requests,
        regular_orders=regular_orders,
        total_special_sales=total_special_sales,
        total_regular_sales=total_regular_sales,
        total_overall_sales=total_overall_sales,
        customer_names=customer_names,
        menu_items=menu_items,
        start_date=start_date,
        end_date=end_date,
        item_filter=item_filter,
        customer_name_filter=customer_name_filter
    )
@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    flash("You have been logged out.", "info")  # Flash a message to indicate successful logout
    return redirect(url_for('login'))  # Redirect to the login page

print(f"Database and tables created at {DB_PATH}")

if __name__ == '__main__':
    app.run(debug=True)

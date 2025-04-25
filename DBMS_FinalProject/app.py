from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'orders.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders').fetchall()
    conn.close()
    return render_template('index.html', orders=orders)

@app.route('/add', methods=['POST'])
def add_order():
    item_name = request.form['item_name']
    quantity = request.form['quantity']

    conn = get_db_connection()
    conn.execute('INSERT INTO orders (item_name, quantity) VALUES (?, ?)',
                 (item_name, quantity))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/search', methods=['POST'])
def search():
    search_date = request.form['search_date']

    conn = get_db_connection()
    orders = conn.execute(''' 
        SELECT * FROM orders
        WHERE DATE(timestamp) = ?
    ''', (search_date,)).fetchall()
    conn.close()

    return render_template('index.html', orders=orders, search_date=search_date)

if __name__ == '__main__':
    app.run(debug=True)

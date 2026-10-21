import sqlite3
from datetime import datetime

# Database file name
DB_NAME = "tailor_shop.db"

def get_db_connection():
    """Connect to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_NAME)
    # Enable accessing columns by name (e.g. row['name'])
    conn.row_factory = sqlite3.Row
    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Create database tables automatically on first run and apply safe schema updates."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Customers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT
        );
    ''')

    # 2. Measurements Table (Base creation if not existing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            garment_type TEXT,
            unit TEXT DEFAULT 'Inches',
            fit_type TEXT DEFAULT 'Regular',
            date_taken TEXT,
            neck REAL,
            shoulder REAL,
            chest REAL,
            waist REAL,
            sleeve REAL,
            cuff REAL,
            shirt_length REAL,
            trouser_length REAL,
            trouser_waist REAL,
            hip REAL,
            thigh REAL,
            knee REAL,
            bottom_paancha REAL,
            rise REAL,
            notes TEXT,
            created_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
        );
    ''')

    # Safely migrate/add missing columns to existing measurements table if needed
    safe_upgrade_measurements_table(cursor)

    # 3. Orders Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            due_date TEXT,
            price REAL,
            status TEXT DEFAULT 'Pending',
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
        );
    ''')

    conn.commit()

    # Check if database is empty, seed initial sample data for easy testing
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        seed_sample_data(conn)

    conn.close()

def safe_upgrade_measurements_table(cursor):
    """Safely check for missing columns in measurements table and alter table without losing data."""
    cursor.execute("PRAGMA table_info(measurements)")
    columns = [row[1] for row in cursor.fetchall()]

    new_columns = {
        "garment_type": "TEXT",
        "unit": "TEXT DEFAULT 'Inches'",
        "fit_type": "TEXT DEFAULT 'Regular'",
        "date_taken": "TEXT",
        "cuff": "REAL",
        "shirt_length": "REAL",
        "trouser_length": "REAL",
        "trouser_waist": "REAL",
        "thigh": "REAL",
        "knee": "REAL",
        "bottom_paancha": "REAL",
        "rise": "REAL",
        "created_at": "TEXT"
    }

    for col_name, col_type in new_columns.items():
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE measurements ADD COLUMN {col_name} {col_type};")

def seed_sample_data(conn):
    """Seed initial sample data so the app has working demo records."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    cursor = conn.cursor()

    # Sample Customers
    cursor.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", ("Alice Smith", "+1 555-0192", "123 Main St"))
    cursor.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", ("Robert Johnson", "+1 555-0143", "456 Elm St"))
    cursor.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", ("Claire Davies", "+1 555-0188", "789 Oak Ave"))
    cursor.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", ("Michael Brown", "+1 555-0165", "321 Pine Rd"))

    # Sample Measurements
    cursor.execute('''
        INSERT INTO measurements (customer_id, garment_type, unit, fit_type, date_taken, neck, shoulder, chest, waist, sleeve, cuff, shirt_length, notes)
        VALUES (1, 'Kameez', 'Inches', 'Slim', ?, 15.0, 17.5, 38.0, 32.0, 24.0, 9.0, 38.0, 'Prefers slim fit kameez')
    ''', (today_str,))
    
    cursor.execute('''
        INSERT INTO measurements (customer_id, garment_type, unit, fit_type, date_taken, trouser_length, trouser_waist, hip, thigh, knee, bottom_paancha, rise, notes)
        VALUES (1, 'Trouser', 'Inches', 'Regular', ?, 39.0, 32.0, 40.0, 24.0, 18.0, 15.0, 11.5, 'Shalwar with 15 inch paancha')
    ''', (today_str,))

    # Sample Orders
    cursor.execute("INSERT INTO orders (customer_id, item, due_date, price, status, notes) VALUES (1, '3-Piece Wedding Suit', '2026-09-28', 450.00, 'In Progress', 'Navy blue wool')")
    cursor.execute("INSERT INTO orders (customer_id, item, due_date, price, status, notes) VALUES (2, 'Custom Leather Jacket', '2026-09-25', 280.00, 'Pending', 'Black leather')")
    cursor.execute("INSERT INTO orders (customer_id, item, due_date, price, status, notes) VALUES (3, 'Evening Silk Gown', '2026-09-22', 350.00, 'Ready', 'Emerald green')")
    cursor.execute("INSERT INTO orders (customer_id, item, due_date, price, status, notes) VALUES (4, 'Formal Business Shirt', '2026-09-20', 85.00, 'Delivered', 'White cotton')")

    conn.commit()

# --- Dashboard Queries ---

def get_dashboard_stats():
    """Fetch count statistics for dashboard cards."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending'")
    pending_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Ready'")
    ready_orders = cursor.fetchone()[0]

    conn.close()
    return {
        "total_customers": total_customers,
        "pending_orders": pending_orders,
        "ready_orders": ready_orders
    }

def get_recent_orders(limit=5, search_query=None):
    """Fetch recent orders with customer name for dashboard table, optionally filtered by search."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT orders.id, orders.customer_id, customers.name AS customer_name, orders.item, orders.due_date, orders.price, orders.status
        FROM orders
        JOIN customers ON orders.customer_id = customers.id
    '''
    params = []

    if search_query:
        query += " WHERE (customers.name LIKE ? OR orders.item LIKE ? OR orders.id LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])

    query += " ORDER BY orders.id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    orders = cursor.fetchall()
    conn.close()
    return orders

# --- Customers Queries ---

def get_all_customers(search_query=None):
    """Fetch all customers, optionally filtered by search query."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if search_query:
        query = "SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? ORDER BY id DESC"
        cursor.execute(query, (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM customers ORDER BY name ASC")
    customers = cursor.fetchall()
    conn.close()
    return customers

def get_customer_by_id(customer_id):
    """Fetch a single customer by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    customer = cursor.fetchone()
    conn.close()
    return customer

def add_customer(name, phone, address):
    """Add a new customer to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", (name, phone, address))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_customer(customer_id, name, phone, address):
    """Update an existing customer's details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET name = ?, phone = ?, address = ? WHERE id = ?", (name, phone, address, customer_id))
    conn.commit()
    conn.close()

def delete_customer(customer_id):
    """Delete a customer and related records via CASCADE."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()

# --- Measurements Queries ---

def get_measurements_by_customer_id(customer_id):
    """Fetch all body measurement records for a specific customer, newest first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM measurements WHERE customer_id = ? ORDER BY id DESC", (customer_id,))
    measurements = cursor.fetchall()
    conn.close()
    return measurements

def get_measurement_by_id(measurement_id):
    """Fetch a single measurement record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM measurements WHERE id = ?", (measurement_id,))
    measurement = cursor.fetchone()
    conn.close()
    return measurement

def add_measurement(customer_id, data):
    """Add a new measurement record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO measurements (
            customer_id, garment_type, unit, fit_type, date_taken,
            neck, shoulder, chest, waist, sleeve, cuff, shirt_length,
            trouser_length, trouser_waist, hip, thigh, knee, bottom_paancha, rise, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        customer_id, data.get('garment_type'), data.get('unit', 'Inches'), data.get('fit_type', 'Regular'), data.get('date_taken'),
        data.get('neck'), data.get('shoulder'), data.get('chest'), data.get('waist'), data.get('sleeve'), data.get('cuff'), data.get('shirt_length'),
        data.get('trouser_length'), data.get('trouser_waist'), data.get('hip'), data.get('thigh'), data.get('knee'), data.get('bottom_paancha'), data.get('rise'), data.get('notes')
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_measurement(measurement_id, data):
    """Update an existing measurement record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE measurements SET
            garment_type = ?, unit = ?, fit_type = ?, date_taken = ?,
            neck = ?, shoulder = ?, chest = ?, waist = ?, sleeve = ?, cuff = ?, shirt_length = ?,
            trouser_length = ?, trouser_waist = ?, hip = ?, thigh = ?, knee = ?, bottom_paancha = ?, rise = ?, notes = ?
        WHERE id = ?
    ''', (
        data.get('garment_type'), data.get('unit', 'Inches'), data.get('fit_type', 'Regular'), data.get('date_taken'),
        data.get('neck'), data.get('shoulder'), data.get('chest'), data.get('waist'), data.get('sleeve'), data.get('cuff'), data.get('shirt_length'),
        data.get('trouser_length'), data.get('trouser_waist'), data.get('hip'), data.get('thigh'), data.get('knee'), data.get('bottom_paancha'), data.get('rise'), data.get('notes'),
        measurement_id
    ))
    conn.commit()
    conn.close()

def delete_measurement(measurement_id):
    """Delete a measurement record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM measurements WHERE id = ?", (measurement_id,))
    conn.commit()
    conn.close()

# --- Orders Queries ---

def get_all_orders(search_query=None, status_filter=None):
    """Fetch all orders joined with customer names, optionally filtered by search or status."""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = '''
        SELECT orders.id, orders.customer_id, customers.name AS customer_name, customers.phone AS customer_phone,
               orders.item, orders.due_date, orders.price, orders.status, orders.notes
        FROM orders
        JOIN customers ON orders.customer_id = customers.id
    '''
    params = []
    conditions = []

    if search_query:
        conditions.append("(customers.name LIKE ? OR orders.item LIKE ? OR orders.id LIKE ?)")
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])

    if status_filter and status_filter != 'All':
        conditions.append("orders.status = ?")
        params.append(status_filter)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY orders.id DESC"

    cursor.execute(sql, params)
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_order_by_id(order_id):
    """Fetch a single order joined with customer name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT orders.id, orders.customer_id, customers.name AS customer_name, customers.phone AS customer_phone,
               orders.item, orders.due_date, orders.price, orders.status, orders.notes
        FROM orders
        JOIN customers ON orders.customer_id = customers.id
        WHERE orders.id = ?
    ''', (order_id,))
    order = cursor.fetchone()
    conn.close()
    return order

def add_order(customer_id, item, due_date, price, status, notes):
    """Add a new order to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (customer_id, item, due_date, price, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (customer_id, item, due_date, price, status, notes))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_order(order_id, customer_id, item, due_date, price, status, notes):
    """Update existing order record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders SET customer_id = ?, item = ?, due_date = ?, price = ?, status = ?, notes = ?
        WHERE id = ?
    ''', (customer_id, item, due_date, price, status, notes, order_id))
    conn.commit()
    conn.close()

def delete_order(order_id):
    """Delete an order by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

def delete_all_orders():
    """Delete all orders from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders")
    conn.commit()
    conn.close()

def get_orders_by_customer_id(customer_id):
    """Fetch all orders belonging to a specific customer."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE customer_id = ? ORDER BY id DESC", (customer_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders

# --- Reports & Analytics Queries ---

def get_reports_data():
    """Fetch complete shop reports & analytics statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending'")
    pending_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'In Progress'")
    in_progress_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Ready'")
    ready_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Delivered'")
    delivered_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Cancelled'")
    cancelled_count = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(price) FROM orders")
    res = cursor.fetchone()[0]
    total_revenue = res if res is not None else 0.0

    conn.close()

    return {
        "total_customers": total_customers,
        "total_orders": total_orders,
        "pending_count": pending_count,
        "in_progress_count": in_progress_count,
        "ready_count": ready_count,
        "delivered_count": delivered_count,
        "cancelled_count": cancelled_count,
        "total_revenue": total_revenue
    }

if __name__ == "__main__":
    init_db()
    print("Database functions updated with search support.")

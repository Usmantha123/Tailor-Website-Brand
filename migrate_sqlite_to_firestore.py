import sqlite3
import firebase_db

def migrate():
    """One-time migration script to copy existing SQLite data into Firebase Firestore."""
    if not firebase_db.is_initialized:
        print("❌ Cannot run migration: Firebase is not initialized.")
        print("Details:", firebase_db.init_error)
        return

    sqlite_db_path = "tailor_shop.db"
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("🚀 Starting SQLite to Firestore Migration...")

    # 1. Migrate Customers
    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()
    customer_id_map = {} # Maps SQLite ID -> Firestore ID

    print(f"📦 Migrating {len(customers)} customers...")
    for c in customers:
        cust_dict = dict(c)
        old_id = cust_dict.pop("id")
        
        # Add to Firestore
        doc_ref = firebase_db.db.collection("customers").document(str(old_id))
        doc_ref.set(cust_dict)
        customer_id_map[str(old_id)] = str(old_id)
        print(f"  ✓ Customer '{cust_dict.get('name')}' migrated with ID {old_id}")

    # 2. Migrate Measurements
    cursor.execute("SELECT * FROM measurements")
    measurements = cursor.fetchall()
    print(f"📦 Migrating {len(measurements)} measurement records...")
    for m in measurements:
        m_dict = dict(m)
        old_id = m_dict.pop("id")
        # Ensure customer_id is stored as string
        m_dict["customer_id"] = str(m_dict["customer_id"])
        
        firebase_db.db.collection("measurements").document(str(old_id)).set(m_dict)
        print(f"  ✓ Measurement #{old_id} for Customer #{m_dict['customer_id']} migrated.")

    # 3. Migrate Orders
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    print(f"📦 Migrating {len(orders)} orders...")
    for o in orders:
        o_dict = dict(o)
        old_id = o_dict.pop("id")
        o_dict["customer_id"] = str(o_dict["customer_id"])
        
        # Fetch customer name if missing
        if "customer_name" not in o_dict:
            cust = firebase_db.get_document("customers", o_dict["customer_id"])
            if cust:
                o_dict["customer_name"] = cust.get("name", "Unknown")

        firebase_db.db.collection("orders").document(str(old_id)).set(o_dict)
        print(f"  ✓ Order #{old_id} migrated.")

    # 4. Migrate Payments
    cursor.execute("SELECT * FROM payments")
    payments = cursor.fetchall()
    print(f"📦 Migrating {len(payments)} payments...")
    for p in payments:
        p_dict = dict(p)
        old_id = p_dict.pop("id")
        p_dict["order_id"] = str(p_dict["order_id"])
        if "customer_id" in p_dict:
            p_dict["customer_id"] = str(p_dict["customer_id"])

        firebase_db.db.collection("payments").document(str(old_id)).set(p_dict)
        print(f"  ✓ Payment #{old_id} migrated.")

    conn.close()
    print("✅ Migration to Firebase Firestore completed successfully!")

if __name__ == "__main__":
    migrate()

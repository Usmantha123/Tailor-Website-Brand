import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Global variables for tracking initialization state and error message
db = None
is_initialized = False
init_error = None

def init_firebase():
    """Initialize Firebase Admin SDK using serviceAccountKey.json or environment variable."""
    global db, is_initialized, init_error
    import json
    
    # Check if JSON key is provided in environment variables (for Vercel/Cloud deployment)
    env_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY") or os.getenv("FIREBASE_KEY_JSON")
    key_dict = None
    if env_key:
        try:
            key_dict = json.loads(env_key)
        except Exception as e:
            print(f"[Firebase Warning] Failed to parse FIREBASE_SERVICE_ACCOUNT_KEY: {e}")

    key_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
    
    if not key_dict and not os.path.exists(key_path):
        is_initialized = False
        init_error = "serviceAccountKey.json file is missing and FIREBASE_SERVICE_ACCOUNT_KEY environment variable is not set."
        print(f"[Firebase Warning] {init_error}")
        return False

    try:
        if not firebase_admin._apps:
            if key_dict:
                cred = credentials.Certificate(key_dict)
            else:
                cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        is_initialized = True
        init_error = None
        print("[Firebase] Connected to Firestore successfully.")
        return True
    except Exception as e:
        is_initialized = False
        init_error = f"Failed to connect to Firebase: {str(e)}"
        print(f"[Firebase Error] {init_error}")
        return False

# Initialize on module load
init_firebase()

# ==============================================================================
# Helper CRUD Functions for Firestore Collections
# ==============================================================================

def add_document(collection_name, data_dict):
    """Add a new document to a Firestore collection."""
    if not is_initialized or db is None:
        raise RuntimeError(init_error or "Firestore not connected.")

    if "created_at" not in data_dict or not data_dict["created_at"]:
        data_dict["created_at"] = datetime.now().isoformat()

    doc_ref = db.collection(collection_name).add(data_dict)
    return doc_ref[1].id

def get_document(collection_name, doc_id):
    """Fetch a single document by ID from a Firestore collection."""
    if not is_initialized or db is None:
        return None

    doc = db.collection(collection_name).document(str(doc_id)).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None

def get_all(collection_name, order_by_field=None, descending=True):
    """Fetch all documents from a Firestore collection as a list of dictionaries."""
    if not is_initialized or db is None:
        return []

    query = db.collection(collection_name)
    if order_by_field:
        direction = firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING
        query = query.order_by(order_by_field, direction=direction)

    docs = query.stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results

def update_document(collection_name, doc_id, data_dict):
    """Update fields of an existing document in Firestore."""
    if not is_initialized or db is None:
        raise RuntimeError(init_error or "Firestore not connected.")

    db.collection(collection_name).document(str(doc_id)).update(data_dict)

def delete_document(collection_name, doc_id):
    """Delete a document by ID from a Firestore collection."""
    if not is_initialized or db is None:
        raise RuntimeError(init_error or "Firestore not connected.")

    db.collection(collection_name).document(str(doc_id)).delete()

def delete_all_orders(reset_counter=False):
    """Delete all documents in the 'orders' Firestore collection in batches."""
    if not is_initialized or db is None:
        raise RuntimeError(init_error or "Firestore not connected.")

    docs = db.collection("orders").stream()
    count = 0
    batch = db.batch()
    batch_count = 0

    for doc in docs:
        batch.delete(doc.reference)
        count += 1
        batch_count += 1
        if batch_count >= 400:
            batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()

    if reset_counter:
        try:
            db.collection("counters").document("order_counter").set({"next_number": 1})
        except Exception:
            pass

    return count

def delete_orders_by_ids(order_ids):
    """Delete multiple orders by their document IDs using batching."""
    if not is_initialized or db is None:
        raise RuntimeError(init_error or "Firestore not connected.")

    if not order_ids:
        return 0

    count = 0
    batch = db.batch()
    batch_count = 0

    for oid in order_ids:
        oid_str = str(oid).strip()
        if not oid_str:
            continue
        ref = db.collection("orders").document(oid_str)
        batch.delete(ref)
        count += 1
        batch_count += 1
        if batch_count >= 400:
            batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()

    return count

def query_by_field(collection_name, field_name, value):
    """Query documents in a collection where field_name == value."""
    if not is_initialized or db is None:
        return []

    docs = db.collection(collection_name).where(field_name, "==", str(value)).stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results

def search_collection(collection_name, search_query):
    """Search documents by matching customer name, item, or phone."""
    all_docs = get_all(collection_name)
    if not search_query:
        return all_docs

    search_lower = search_query.lower()
    filtered = []
    for doc in all_docs:
        name = str(doc.get("name", "") or doc.get("customer_name", "")).lower()
        phone = str(doc.get("phone", "") or doc.get("customer_phone", "")).lower()
        item = str(doc.get("item", "")).lower()
        doc_id = str(doc.get("id", "")).lower()

        if search_lower in name or search_lower in phone or search_lower in item or search_lower in doc_id:
            filtered.append(doc)
    return filtered

def generate_customer_number():
    """
    Atomically generate a unique customer number like H141.
    Uses a Firestore counter document (counters/customer_counter) so
    two saves at the same time can NEVER get the same number.
    """
    if not is_initialized or db is None:
        raise RuntimeError(init_error or "Firestore not connected.")

    counter_ref = db.collection("counters").document("customer_counter")

    @firestore.transactional
    def increment(transaction):
        """Read the counter, add 1, write it back — all atomically."""
        snap = counter_ref.get(transaction=transaction)
        if snap.exists:
            current = snap.to_dict().get("next_number", 101)
        else:
            # First time: scan existing customers to find the max
            import re
            customers = get_all("customers")
            max_num = 100
            for c in customers:
                num_str = c.get("customer_number", "")
                if num_str:
                    match = re.search(r'\d+', str(num_str))
                    if match:
                        val = int(match.group())
                        if val > max_num:
                            max_num = val
            current = max_num + 1

        # Write the NEXT number back (current + 1)
        transaction.set(counter_ref, {"next_number": current + 1})
        return current

    transaction = db.transaction()
    next_num = increment(transaction)

    # Safety: if this number somehow already exists, keep trying
    candidate = f"H{next_num}"
    while get_customer_by_number(candidate):
        next_num += 1
        candidate = f"H{next_num}"
        # Also update the counter so future calls skip this number
        counter_ref.set({"next_number": next_num + 1})

    return candidate

def get_customer_by_number(customer_number):
    """Find customer document by customer_number string (case-insensitive)."""
    if not customer_number:
        return None
    c_num_clean = str(customer_number).strip().upper()
    customers = get_all("customers")
    for c in customers:
        if str(c.get("customer_number", "")).strip().upper() == c_num_clean:
            return c
        if str(c.get("id", "")).strip().lower() == c_num_clean.lower():
            return c
    return None

def get_customer_by_phone(phone):
    """Find customer document by phone number string."""
    if not phone:
        return None
    phone_clean = str(phone).strip().replace("-", "").replace(" ", "")
    customers = get_all("customers")
    for c in customers:
        c_phone = str(c.get("phone", "")).strip().replace("-", "").replace(" ", "")
        if c_phone and c_phone == phone_clean:
            return c
    return None

def generate_order_number():
    """
    Atomically generate a unique order number like ORD-0012.
    Uses a Firestore counter document (counters/order_counter).
    """
    if not is_initialized or db is None:
        raise RuntimeError(init_error or "Firestore not connected.")

    counter_ref = db.collection("counters").document("order_counter")

    @firestore.transactional
    def increment(transaction):
        """Read the counter, add 1, write it back — all atomically."""
        snap = counter_ref.get(transaction=transaction)
        if snap.exists:
            current = snap.to_dict().get("next_number", 1)
        else:
            # First time: scan existing orders to find the max
            import re
            orders = get_all("orders")
            max_num = 0
            for o in orders:
                num_str = o.get("order_number", "")
                if num_str:
                    match = re.search(r'\d+', str(num_str))
                    if match:
                        val = int(match.group())
                        if val > max_num:
                            max_num = val
            current = max_num + 1

        transaction.set(counter_ref, {"next_number": current + 1})
        return current

    transaction = db.transaction()
    next_num = increment(transaction)
    return f"ORD-{next_num:04d}"

def search_customers_live(query=""):
    """Search customers by name, phone, or customer_number for live suggestions."""
    customers = get_all("customers")
    if not query:
        return customers[:15]
    
    q_lower = str(query).strip().lower()
    results = []
    for c in customers:
        name = str(c.get("name", "")).lower()
        phone = str(c.get("phone", "")).lower()
        c_num = str(c.get("customer_number", "")).lower()
        if q_lower in name or q_lower in phone or q_lower in c_num:
            results.append(c)
    return results

# ==============================================================================
# Business Analytics & Statistics Helpers for App
# ==============================================================================

def get_dashboard_stats():
    """Fetch count statistics and today's income for dashboard stat cards."""
    customers = get_all("customers")
    orders = get_all("orders")
    payments = get_all("payments")

    total_customers = len(customers)
    pending_orders = sum(1 for o in orders if o.get("status") in ["زیر تکمیل", "Pending", "In Progress"])
    ready_orders = sum(1 for o in orders if o.get("status") in ["تیار", "Ready"])

    # Calculate today's income (آج کی آمدنی) using real payment & order data
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_income = 0.0

    # 1. Check direct payment receipts for today
    for p in payments:
        p_date = str(p.get("date") or p.get("created_at") or "")[:10]
        if p_date == today_str:
            today_income += float(p.get("amount", 0) or 0)

    # 2. Fallback: Sum advance / prices of orders recorded today
    if today_income == 0:
        for o in orders:
            o_date = str(o.get("order_date") or o.get("created_at") or "")[:10]
            if o_date == today_str:
                adv = float(o.get("advance", 0) or 0)
                prc = float(o.get("price", 0) or 0)
                today_income += adv if adv > 0 else prc

    return {
        "total_customers": total_customers,
        "pending_orders": pending_orders,
        "ready_orders": ready_orders,
        "today_income": today_income
    }

def get_reports_data():
    """Fetch complete shop analytics data for reports page."""
    customers = get_all("customers")
    orders = get_all("orders")

    total_customers = len(customers)
    total_orders = len(orders)
    
    pending_count = sum(1 for o in orders if o.get("status") == "Pending")
    in_progress_count = sum(1 for o in orders if o.get("status") == "In Progress")
    ready_count = sum(1 for o in orders if o.get("status") == "Ready")
    delivered_count = sum(1 for o in orders if o.get("status") == "Delivered")
    cancelled_count = sum(1 for o in orders if o.get("status") == "Cancelled")

    total_revenue = sum(float(o.get("price", 0)) for o in orders)

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
    if is_initialized:
        print("Firebase test client ready.")
    else:
        print("Firebase initialization failed:", init_error)

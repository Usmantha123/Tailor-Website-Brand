"""
fix_duplicates.py
-----------------
Scan all customers in Firestore for DUPLICATE customer numbers (e.g. two H140).
This script only READS data - it changes NOTHING.
Run with:  python fix_duplicates.py
"""

import sys
import os

# Add project root so we can import firebase_db
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firebase_db

def find_duplicate_customer_numbers():
    """Find customers that share the same customer_number."""
    print("\n=== Scanning customers for duplicate customer numbers ===\n")
    
    # Load all customers from Firestore
    customers = firebase_db.get_all("customers")
    print(f"Total customers found: {len(customers)}\n")

    # Group customers by their customer_number
    seen = {}  # customer_number -> list of customer docs
    for c in customers:
        num = str(c.get("customer_number", "")).strip().upper()
        if not num:
            num = "(MISSING)"
        seen.setdefault(num, []).append(c)

    # Find groups with more than 1 customer
    duplicates_found = False
    for num, group in sorted(seen.items()):
        if len(group) > 1:
            duplicates_found = True
            print(f"⚠️  DUPLICATE: {num}  ({len(group)} records)")
            print("-" * 50)
            for i, c in enumerate(group):
                print(f"  [{i+1}] Firestore ID : {c.get('id', 'N/A')}")
                print(f"      نام           : {c.get('name', '—')}")
                print(f"      فون           : {c.get('phone', '—')}")
                print(f"      پتہ            : {c.get('address', '—')}")
                print(f"      Created At   : {c.get('created_at', '—')[:19]}")
                print()

    if not duplicates_found:
        print("✅ No duplicate customer numbers found!")

def find_all_used_numbers():
    """List all currently used customer numbers."""
    import re
    customers = firebase_db.get_all("customers")
    nums = set()
    for c in customers:
        num_str = c.get("customer_number", "")
        if num_str:
            m = re.search(r'\d+', str(num_str))
            if m:
                nums.add(int(m.group()))
    return nums

def find_orders_for_customer_number(cust_num):
    """Find all orders linked to a customer number."""
    orders = firebase_db.get_all("orders")
    matched = []
    for o in orders:
        if str(o.get("customer_number", "")).strip().upper() == cust_num.strip().upper():
            matched.append(o)
    return matched

def show_order_links():
    """Show which orders are linked to each duplicate customer number."""
    print("\n=== Checking orders linked to each customer ===\n")
    customers = firebase_db.get_all("customers")
    
    # Group customers by number
    seen = {}
    for c in customers:
        num = str(c.get("customer_number", "")).strip().upper()
        if not num:
            continue
        seen.setdefault(num, []).append(c)

    # Only show for duplicates
    for num, group in sorted(seen.items()):
        if len(group) > 1:
            orders = find_orders_for_customer_number(num)
            print(f"Orders linked to {num}: {len(orders)}")
            for o in orders:
                print(f"  - Order #{o.get('order_number','?')} | {o.get('customer_name','?')} | {o.get('order_date','?')} | Status: {o.get('status','?')}")
            print()

if __name__ == "__main__":
    if not firebase_db.is_initialized:
        print("❌ Firebase not connected:", firebase_db.init_error)
        sys.exit(1)

    find_duplicate_customer_numbers()
    show_order_links()
    print("\n--- No data was changed. Review the list above and tell me which record to keep. ---\n")

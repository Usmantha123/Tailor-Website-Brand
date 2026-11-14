import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
import firebase_db
import database # Kept for migration / legacy fallback

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask web application
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "tailor_craft_default_secret_key_2026")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def parse_float(val):
    """Helper function to parse float inputs safely, returning None if empty."""
    if not val or str(val).strip() == "":
        return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0

# ==============================================================================
# Security & Firebase Protection Hook (Login feature removed)
# ==============================================================================

@app.before_request
def require_firebase_check():
    """Check Firebase connection status before processing requests (Login disabled)."""
    open_endpoints = ["firebase_error", "static", "login", "logout"]
    if request.endpoint in open_endpoints or (request.path and request.path.startswith("/static")):
        return None

    # Check Firebase connection status
    if not firebase_db.is_initialized:
        return redirect(url_for("firebase_error"))

    return None

@app.route("/login")
@app.route("/logout")
def login_logout_redirect():
    """Login feature removed: redirect directly to main dashboard."""
    return redirect(url_for("dashboard"))

@app.route("/firebase-error")
def firebase_error():
    """Friendly fallback error page when serviceAccountKey.json is missing or Firestore is unreachable."""
    return render_template("firebase_error.html", error_message=firebase_db.init_error)

# ==============================================================================
# Main Dashboard Route
# ==============================================================================

@app.route("/")
def dashboard():
    """Home: آج کی ڈیلیوری — orders due today or overdue that are not delivered."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    this_month = datetime.now().strftime("%Y-%m")

    all_orders = firebase_db.get_all("orders")

    # Orders due today or earlier that are NOT delivered
    pending_delivery = []
    for o in all_orders:
        due = str(o.get("due_date", "") or "").strip()
        status = str(o.get("status", "") or "").strip()
        if due and due <= today_str and status not in ["ترسیل شدہ", "Delivered"]:
            o["is_overdue"] = due < today_str
            pending_delivery.append(o)

    # Sort: overdue first, then by due date
    pending_delivery.sort(key=lambda o: o.get("due_date", ""))

    # Count cards
    in_progress_count = sum(1 for o in all_orders if o.get("status") in ["زیر تکمیل", "In Progress"])
    ready_count       = sum(1 for o in all_orders if o.get("status") in ["تیار", "Ready"])
    delivered_month   = sum(
        1 for o in all_orders
        if o.get("status") in ["ترسیل شدہ", "Delivered"]
        and str(o.get("order_date") or o.get("created_at") or "")[:7] == this_month
    )

    return render_template(
        "dashboard.html",
        pending_delivery=pending_delivery,
        in_progress_count=in_progress_count,
        ready_count=ready_count,
        delivered_month=delivered_month,
        today_str=today_str
    )

@app.route("/hello")
def hello():
    """Alias hello route redirecting to dashboard."""
    return dashboard()

# ==============================================================================
# Redirect legacy Customers route to Orders List
# ==============================================================================

@app.route("/customers")
def customers():
    """Redirect legacy customers page to Orders List."""
    return redirect(url_for("orders"))

@app.route("/customers/<customer_id>")
def customer_detail(customer_id):
    """Redirect customer detail page to Orders List."""
    return redirect(url_for("orders"))

# ==============================================================================
# Measurements Routes (New, Save, Edit, Delete)
# ==============================================================================

@app.route("/customers/<customer_id>/measurements/new", methods=["GET", "POST"])
def new_measurement(customer_id):
    """GET: Render empty bilingual measurement form. POST: Save measurement in Firestore."""
    customer = firebase_db.get_document("customers", customer_id)
    if not customer:
        flash("Customer not found.", "warning")
        return redirect(url_for("customers"))

    if request.method == "POST":
        today_default = datetime.now().strftime('%Y-%m-%d')
        data = {
            'customer_id': str(customer_id),
            'garment_type': request.form.get('garment_type', 'Kameez'),
            'unit': request.form.get('unit', 'Inches'),
            'fit_type': request.form.get('fit_type', 'Regular'),
            'date_taken': request.form.get('date_taken') or today_default,
            'neck': parse_float(request.form.get('neck')),
            'shoulder': parse_float(request.form.get('shoulder')),
            'chest': parse_float(request.form.get('chest')),
            'waist': parse_float(request.form.get('waist')),
            'sleeve': parse_float(request.form.get('sleeve')),
            'cuff': parse_float(request.form.get('cuff')),
            'shirt_length': parse_float(request.form.get('shirt_length')),
            'trouser_length': parse_float(request.form.get('trouser_length')),
            'trouser_waist': parse_float(request.form.get('trouser_waist')),
            'hip': parse_float(request.form.get('hip')),
            'thigh': parse_float(request.form.get('thigh')),
            'knee': parse_float(request.form.get('knee')),
            'bottom_paancha': parse_float(request.form.get('bottom_paancha')),
            'rise': parse_float(request.form.get('rise')),
            'notes': request.form.get('notes', '').strip(),
            'created_at': datetime.now().isoformat()
        }
        firebase_db.add_document("measurements", data)
        flash("Measurement record saved in Firestore! / ناپ محفوظ ہو گیا", "success")
        return redirect(url_for("customer_detail", customer_id=customer_id))

    today_str = datetime.now().strftime('%Y-%m-%d')
    return render_template("measurement_form.html", customer=customer, measurement=None, today_str=today_str)

@app.route("/measurements/<measurement_id>/edit", methods=["GET", "POST"])
def edit_measurement(measurement_id):
    """GET: Render pre-filled measurement form. POST: Update measurement in Firestore."""
    measurement = firebase_db.get_document("measurements", measurement_id)
    if not measurement:
        flash("Measurement record not found.", "warning")
        return redirect(url_for("customers"))

    customer = firebase_db.get_document("customers", measurement['customer_id'])

    if request.method == "POST":
        today_default = datetime.now().strftime('%Y-%m-%d')
        data = {
            'garment_type': request.form.get('garment_type', 'Kameez'),
            'unit': request.form.get('unit', 'Inches'),
            'fit_type': request.form.get('fit_type', 'Regular'),
            'date_taken': request.form.get('date_taken') or today_default,
            'neck': parse_float(request.form.get('neck')),
            'shoulder': parse_float(request.form.get('shoulder')),
            'chest': parse_float(request.form.get('chest')),
            'waist': parse_float(request.form.get('waist')),
            'sleeve': parse_float(request.form.get('sleeve')),
            'cuff': parse_float(request.form.get('cuff')),
            'shirt_length': parse_float(request.form.get('shirt_length')),
            'trouser_length': parse_float(request.form.get('trouser_length')),
            'trouser_waist': parse_float(request.form.get('trouser_waist')),
            'hip': parse_float(request.form.get('hip')),
            'thigh': parse_float(request.form.get('thigh')),
            'knee': parse_float(request.form.get('knee')),
            'bottom_paancha': parse_float(request.form.get('bottom_paancha')),
            'rise': parse_float(request.form.get('rise')),
            'notes': request.form.get('notes', '').strip()
        }
        firebase_db.update_document("measurements", measurement_id, data)
        flash("Measurement record updated in Firestore! / ناپ کی ترمیم مکمل ہو گئی", "success")
        return redirect(url_for("customer_detail", customer_id=measurement['customer_id']))

    today_str = datetime.now().strftime('%Y-%m-%d')
    return render_template("measurement_form.html", customer=customer, measurement=measurement, today_str=today_str)

@app.route("/measurements/<measurement_id>/delete", methods=["POST"])
def delete_measurement_route(measurement_id):
    """Delete measurement record from Firestore."""
    measurement = firebase_db.get_document("measurements", measurement_id)
    if measurement:
        customer_id = measurement['customer_id']
        firebase_db.delete_document("measurements", measurement_id)
        flash("Measurement record deleted from Firestore.", "info")
        return redirect(url_for("customer_detail", customer_id=customer_id))
    return redirect(url_for("customers"))

# ==============================================================================
# Orders Management Routes (List, New, Edit, Delete)
# ==============================================================================

@app.route("/orders")
def orders():
    """Display orders list sorted newest first with search and status filters from Firestore."""
    search_query = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "All").strip()
    
    # Fetch all orders sorted by created_at descending (newest first!)
    all_orders = firebase_db.get_all("orders", order_by_field="created_at", descending=True)
    
    # Filter by search query if provided
    if search_query:
        s_lower = search_query.lower()
        filtered = []
        for o in all_orders:
            o_num = str(o.get("order_number", "")).lower()
            c_num = str(o.get("customer_number", "")).lower()
            name = str(o.get("customer_name", "") or o.get("name", "")).lower()
            phone = str(o.get("customer_phone", "") or o.get("phone", "")).lower()
            if s_lower in o_num or s_lower in c_num or s_lower in name or s_lower in phone:
                filtered.append(o)
        all_orders = filtered

    # Filter by status if provided
    if status_filter and status_filter != "All":
        all_orders = [o for o in all_orders if o.get("status") == status_filter]

    return render_template("orders.html", orders=all_orders, search_query=search_query, current_status=status_filter)

@app.route("/orders/new", methods=["GET"])
def new_order():
    """Renders the main single-screen Urdu Desktop Order/Measurement Form."""
    customer_number = request.args.get("customer_number", "").strip()
    order_id = request.args.get("order_id", "").strip()
    
    customer = None
    order = None
    measurements = {}

    if order_id:
        order = firebase_db.get_document("orders", order_id)
        if order:
            measurements = order.get("measurements", {})
            customer_number = order.get("customer_number", "")
            customer = {
                "name": order.get("customer_name", ""),
                "phone": order.get("customer_phone", ""),
                "address": order.get("address", ""),
                "customer_number": customer_number
            }

    if not order and customer_number:
        customer = firebase_db.get_customer_by_number(customer_number)
        if customer:
            measurements = customer.get("measurements", {})
            customer_number = customer.get("customer_number", customer_number)
        else:
            flash(f"کسٹمر نمبر {customer_number} نہیں ملا۔ نیا فارم تیار ہے۔", "warning")
            customer_number = firebase_db.generate_customer_number()
    elif not order:
        customer_number = firebase_db.generate_customer_number()

    return render_template(
        "order_form.html",
        customer=customer,
        order=order,
        customer_number=customer_number,
        measurements=measurements
    )

@app.route("/orders/save", methods=["POST"])
def save_order_form():
    """Process Save button submit for the single-screen order/measurement form."""
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    customer_number = request.form.get("customer_number", "").strip()
    editing_order_id = request.form.get("editing_order_id", "").strip()
    due_date = request.form.get("due_date", "").strip()
    price = parse_float(request.form.get("price", "0"))
    advance = parse_float(request.form.get("advance", "0"))

    # Step 1: Validation - Name is required (Phone is optional)
    if not name:
        flash("گاہک کا نام درج کرنا لازمی ہے۔", "danger")
        return redirect(url_for("new_order", customer_number=customer_number))

    # Collect shirt, shalwar, dropdown options and checkboxes
    measurements_data = {
        # Shirt (قمیض)
        "shirt_length": request.form.get("shirt_length", "").strip(),
        "sleeve": request.form.get("sleeve", "").strip(),
        "shoulder": request.form.get("shoulder", "").strip(),
        "collar_size": request.form.get("collar_size", "").strip(),
        "chest": request.form.get("chest", "").strip(),
        "armpit": request.form.get("armpit", "").strip(),
        "daaman": request.form.get("daaman", "").strip(),
        "daaman_type": request.form.get("daaman_type", "دامن گول").strip(),
        # Shalwar (شلوار)
        "shalwar_length": request.form.get("shalwar_length", "").strip(),
        "paancha": request.form.get("paancha", "").strip(),
        "asan": request.form.get("asan", "").strip(),
        "shalwar_gheer": request.form.get("shalwar_gheer", "").strip(),
        "chaak": request.form.get("chaak", "").strip(),
        # Dropdowns & Custom Options
        "patti": request.form.get("patti", "").strip(),
        "patti_size": request.form.get("patti_size", "").strip(),
        "patti_length": request.form.get("patti_length", "").strip(),
        "paancha_patti": request.form.get("paancha_patti", "").strip(),
        "stitching": request.form.get("stitching", "").strip(),
        "extra_1": request.form.get("extra_1", "").strip(),
        "extra_2": request.form.get("extra_2", "").strip(),
        "cuff_type": request.form.get("cuff_type", "").strip(),
        "cuff_size": request.form.get("cuff_size", "").strip(),
        "collar_nok": request.form.get("collar_nok", "").strip(),
        "moora": request.form.get("moora", "").strip(),
        # Checkboxes Group A
        "baghair_plate": True if request.form.get("baghair_plate") else False,
        "baghair_label": True if request.form.get("baghair_label") else False,
        "chaak_patti_button": True if request.form.get("chaak_patti_button") else False,
        "chamak_taar": True if request.form.get("chamak_taar") else False,
        "steel_button": True if request.form.get("steel_button") else False,
        # Checkboxes Group B
        "front_pocket": True if request.form.get("front_pocket") else False,
        "side_pocket_1": True if request.form.get("side_pocket_1") else False,
        "side_pocket_2": True if request.form.get("side_pocket_2") else False,
        "shalwar_pocket": True if request.form.get("shalwar_pocket") else False,
        "front_pocket_kaaj": True if request.form.get("front_pocket_kaaj") else False,
        "cuff_1_kaaj": True if request.form.get("cuff_1_kaaj") else False,
        "cuff_2_kaaj": True if request.form.get("cuff_2_kaaj") else False,
        "stud_kaaj": True if request.form.get("stud_kaaj") else False,
    }

    # Step 2: Customer Lookup — check phone if provided, then customer_number, then name
    existing_customer = None
    if phone:
        existing_customer = firebase_db.get_customer_by_phone(phone)
    if not existing_customer and customer_number:
        existing_customer = firebase_db.get_customer_by_number(customer_number)
    if not existing_customer and not phone and name:
        for c in firebase_db.get_all("customers"):
            if str(c.get("name", "")).strip().lower() == name.lower():
                existing_customer = c
                break

    if existing_customer:
        # Reuse existing customer and update details + latest measurements
        cust_id = existing_customer["id"]
        customer_number = existing_customer.get("customer_number", customer_number)
        firebase_db.update_document("customers", cust_id, {
            "name": name,
            "phone": phone,
            "address": address,
            "customer_number": customer_number,
            "measurements": measurements_data,
            "updated_at": datetime.now().isoformat()
        })
    else:
        # Create NEW customer — generate number NOW (atomic, unique)
        customer_number = firebase_db.generate_customer_number()

        cust_id = firebase_db.add_document("customers", {
            "customer_number": customer_number,
            "name": name,
            "phone": phone,
            "address": address,
            "measurements": measurements_data,
            "created_at": datetime.now().isoformat()
        })

    # Step 3: Create NEW order document (or update if editing an existing order document)
    if editing_order_id:
        firebase_db.update_document("orders", editing_order_id, {
            "customer_id": str(cust_id),
            "customer_number": customer_number,
            "customer_name": name,
            "customer_phone": phone,
            "address": address,
            "due_date": due_date,
            "price": price,
            "advance": advance,
            "measurements": measurements_data,
            "updated_at": datetime.now().isoformat()
        })
    else:
        # Create NEW order document
        order_number = firebase_db.generate_order_number()
        firebase_db.add_document("orders", {
            "order_number": order_number,
            "customer_id": str(cust_id),
            "customer_number": customer_number,
            "customer_name": name,
            "customer_phone": phone,
            "address": address,
            "due_date": due_date,
            "price": price,
            "advance": advance,
            "order_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "زیر تکمیل",  # Default status: In Progress
            "measurements": measurements_data,
            "created_at": datetime.now().isoformat()
        })

    # Step 5: Show green "محفوظ ہو گیا" and redirect
    flash("محفوظ ہو گیا", "success")
    # If "پرچی نکالیں" was clicked, redirect to the slip page
    if request.form.get("_print") == "1" and not editing_order_id:
        # We need the order id — find latest order for this customer
        try:
            recent = firebase_db.get_all("orders", order_by_field="created_at", descending=True)
            for o in recent:
                if o.get("customer_phone") == phone:
                    return redirect(url_for("view_order", order_id=o["id"]))
        except Exception:
            pass
    return redirect(url_for("orders"))

@app.route("/orders/<order_id>")
def view_order(order_id):
    """View read-only detailed printable slip page for an order."""
    order = firebase_db.get_document("orders", order_id)
    if not order:
        flash("آرڈر نہیں ملا۔", "warning")
        return redirect(url_for("orders"))
    
    measurements = order.get("measurements", {})
    return render_template("order_view.html", order=order, measurements=measurements)

@app.route("/orders/<order_id>/edit", methods=["GET"])
def edit_order(order_id):
    """Open main desktop form pre-filled with order data for editing."""
    return redirect(url_for("new_order", order_id=order_id))

@app.route("/orders/<order_id>/status", methods=["POST"])
def update_order_status(order_id):
    """Update status of an order. Returns JSON so AJAX fetch works."""
    from flask import jsonify
    new_status = request.form.get("status", "زیر تکمیل").strip()
    order = firebase_db.get_document("orders", order_id)
    if order:
        firebase_db.update_document("orders", order_id, {"status": new_status})
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 404

@app.route("/orders/<order_id>/delete", methods=["POST"])
def delete_order_route(order_id):
    """Delete an order from Firestore."""
    order = firebase_db.get_document("orders", order_id)
    if order:
        firebase_db.delete_document("orders", order_id)
        flash("آرڈر کامیابی کے ساتھ حذف کر دیا گیا۔", "info")
    return redirect(url_for("orders"))

@app.route("/orders/delete-all", methods=["POST"])
def delete_all_orders_route():
    """Delete all orders from Firestore."""
    try:
        reset_counter = request.form.get("reset_counter") == "1"
        count = firebase_db.delete_all_orders(reset_counter=reset_counter)
        flash(f"تمام آرڈرز ({count}) کامیابی کے ساتھ حذف کر دیے گئے۔", "success")
    except Exception as e:
        flash(f"آرڈرز حذف کرنے میں خرابی: {str(e)}", "danger")
    return redirect(url_for("orders"))

@app.route("/orders/bulk-delete", methods=["POST"])
def bulk_delete_orders_route():
    """Delete selected orders from Firestore."""
    order_ids = request.form.getlist("order_ids")
    if not order_ids:
        flash("حذف کرنے کے لیے کوئی آرڈر منتخب نہیں کیا گیا۔", "warning")
        return redirect(url_for("orders"))
    try:
        count = firebase_db.delete_orders_by_ids(order_ids)
        flash(f"منتخب کردہ ({count}) آرڈرز کامیابی کے ساتھ حذف کر دیے گئے۔", "success")
    except Exception as e:
        flash(f"آرڈرز حذف کرنے میں خرابی: {str(e)}", "danger")
    return redirect(url_for("orders"))

# ==============================================================================
# Customer Data JSON API Endpoints for Form Interactivity & Live Search
# ==============================================================================

@app.route("/api/customer/by-number/<customer_number>")
def api_get_customer_by_number(customer_number):
    """Fetch customer details and saved measurements by customer number."""
    from flask import jsonify
    cust = firebase_db.get_customer_by_number(customer_number)
    if not cust:
        return jsonify({"success": False, "error": "کسٹمر نہیں ملا"}), 404

    return jsonify({
        "success": True,
        "customer": {
            "id": cust.get("id"),
            "customer_number": cust.get("customer_number", customer_number),
            "name": cust.get("name", ""),
            "phone": cust.get("phone", ""),
            "address": cust.get("address", ""),
            "measurements": cust.get("measurements", {})
        }
    })

@app.route("/api/customers/live-search")
def api_customers_live_search():
    """Live search suggestions endpoint by name or phone."""
    from flask import jsonify
    query = request.args.get("q", "").strip()
    results = firebase_db.search_customers_live(query)
    formatted = []
    for c in results:
        formatted.append({
            "id": c.get("id", ""),
            "customer_number": c.get("customer_number", c.get("id", "")),
            "name": c.get("name", ""),
            "phone": c.get("phone", ""),
            "address": c.get("address", ""),
            "measurements": c.get("measurements", {})
        })
    return jsonify(formatted)

@app.route("/api/customer/by-name/<path:name>")
def api_get_customer_by_name(name):
    """Return customer data + measurements by exact name."""
    from flask import jsonify
    name_clean = str(name).strip().lower()
    for c in firebase_db.get_all("customers"):
        if str(c.get("name", "")).strip().lower() == name_clean:
            return jsonify({
                "found": True,
                "name": c.get("name", ""),
                "phone": c.get("phone", ""),
                "address": c.get("address", ""),
                "customer_number": c.get("customer_number", ""),
                "measurements": c.get("measurements", {})
            })
    return jsonify({"found": False}), 404

@app.route("/api/customer/next-number")
def api_next_customer_number():
    """Returns the next auto-generated customer number."""
    from flask import jsonify
    next_num = firebase_db.generate_customer_number()
    return jsonify({"customer_number": next_num})

@app.route("/api/customer/by-phone/<path:phone>")
def api_get_customer_by_phone(phone):
    """Return customer data + measurements by phone number (for wizard auto-fill)."""
    from flask import jsonify
    cust = firebase_db.get_customer_by_phone(phone)
    if not cust:
        return jsonify({"found": False}), 404
    return jsonify({
        "found": True,
        "name": cust.get("name", ""),
        "address": cust.get("address", ""),
        "customer_number": cust.get("customer_number", ""),
        "measurements": cust.get("measurements", {})
    })

# ==============================================================================
# Reports & Analytics Route
# ==============================================================================

@app.route("/reports")
def reports():
    """Display business analytics & reports overview from Firestore."""
    reports_data = firebase_db.get_reports_data()
    recent_orders = firebase_db.get_all("orders")[:10]
    return render_template("reports.html", reports=reports_data, recent_orders=recent_orders)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

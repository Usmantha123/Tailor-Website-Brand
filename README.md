# 🧵 TailorCraft Management System - Firebase Firestore Integration

A simple, bilingual (Urdu/English) web application for tailor shop management built with **Python Flask** and **Google Firebase Firestore**.

---

## 📁 Project Structure

```
Tailor Management/
├── app.py                            # Main Flask app with Firestore routes & session auth
├── firebase_db.py                    # Firebase Admin SDK & Firestore helper CRUD functions
├── database.py                        # Legacy SQLite database code (kept as backup)
├── migrate_sqlite_to_firestore.py    # One-time script to copy SQLite records to Firestore
├── serviceAccountKey.json            # Firebase Service Account Credentials (GIT-IGNORED)
├── .env                              # Admin credentials & secret key (GIT-IGNORED)
├── .gitignore                        # Security gitignore rule file
├── requirements.txt                  # Python dependencies (Flask, firebase-admin, python-dotenv)
├── README.md                         # Project setup and usage documentation
├── static/
│   ├── css/
│   │   └── style.css                # Styling stylesheet (modern theme + Urdu font support)
│   └── js/
│       └── main.js                  # Client JS (modals, tabs, dynamic form filters)
└── templates/                        # HTML Jinja2 templates
    ├── base.html                    # Layout master with sidebar navigation & RTL toggle
    ├── login.html                   # Admin staff login view
    ├── firebase_error.html          # Fallback page if serviceAccountKey.json is missing
    ├── dashboard.html               # Main dashboard with stat cards & recent activity
    ├── customers.html               # Customers directory table & add/edit modals
    ├── customer_detail.html         # Customer profile with Measurements, Orders & Financials
    ├── measurement_form.html        # Bilingual Urdu/English (ناپ لیں) measurement form
    ├── orders.html                  # Tailoring orders management overview
    ├── order_form.html              # Create & edit tailoring order form
    ├── payments.html                # Payment records overview table
    └── reports.html                 # Business reports & analytics dashboard
```

---

## 🔐 Credentials & Security Setup

### 1. Place Firebase Key File
Place your Firebase Service Account Key file in the root directory:
```
d:\Tailor Managament\serviceAccountKey.json
```
*(Note: Never commit `serviceAccountKey.json` to GitHub! It is listed in `.gitignore`).*

### 2. Configure Environment Variables (`.env`)
Create a `.env` file in your root folder:
```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
SECRET_KEY=tailor_craft_super_secret_key_2026
```

---

## 🚀 How to Run on Windows (Using `py` Launcher)

Follow these simple step-by-step instructions in Windows PowerShell or Command Prompt.

### Step 1: Open Terminal in Project Directory
```powershell
cd "d:\Tailor Managament"
```

### Step 2: Create & Activate Virtual Environment
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
py -m pip install -r requirements.txt
```

### Step 4: Run the Application
```powershell
py app.py
```

### Step 5: Open Web Browser
Navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

Login using your credentials:
- **Username**: `admin`
- **Password**: `admin123`

---

## 📦 (Optional) Migrate Old SQLite Data to Firestore

If you have existing data in `tailor_shop.db` and want to copy it to your Firebase Cloud database, run:
```powershell
py migrate_sqlite_to_firestore.py
```

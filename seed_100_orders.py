import firebase_db
import random
from datetime import datetime, timedelta

def main():
    if not firebase_db.is_initialized:
        print("Firebase not initialized!")
        return

    db = firebase_db.db

    # 1. Read existing counters
    cust_counter_ref = db.collection("counters").document("customer_counter")
    cust_snap = cust_counter_ref.get()
    next_cust_num = 101
    if cust_snap.exists:
        next_cust_num = cust_snap.to_dict().get("next_number", 101)
    else:
        # scan existing
        import re
        for c in firebase_db.get_all("customers"):
            num_str = c.get("customer_number", "")
            match = re.search(r'\d+', str(num_str))
            if match:
                val = int(match.group())
                if val >= next_cust_num:
                    next_cust_num = val + 1

    order_counter_ref = db.collection("counters").document("order_counter")
    order_snap = order_counter_ref.get()
    next_order_num = 1
    if order_snap.exists:
        next_order_num = order_snap.to_dict().get("next_number", 1)
    else:
        import re
        for o in firebase_db.get_all("orders"):
            num_str = o.get("order_number", "")
            match = re.search(r'\d+', str(num_str))
            if match:
                val = int(match.group())
                if val >= next_order_num:
                    next_order_num = val + 1

    print(f"Current Customer counter starts at: H{next_cust_num}")
    print(f"Current Order counter starts at: ORD-{next_order_num:04d}")

    # Pakistani Names
    first_names = [
        "محمد", "علی", "عثمان", "بلال", "حمزہ", "ذیشان", "فرحان", "عمران", "اسد", "کامران",
        "شہزاد", "وقاص", "رضوان", "بابر", "شاہین", "حارث", "شاداب", "فخر", "نسیم", "افتخار",
        "دانش", "سلمان", "عامر", "صائم", "عبداللہ", "سعود", "خرم", "اظہر", "مصباح", "یونس",
        "سعید", "انضمام", "شعیب", "وسیم", "وقار", "عبدالرزاق", "شاہد", "عمر", "جنید", "وہاب",
        "یاسر", "سرفراز", "عابد", "شان", "زمان", "احسان", "عباس", "طارق", "ارسلان", "کاشف"
    ]
    last_names = [
        "خان", "احمد", "علی", "ملک", "صدیقی", "اشرف", "محمود", "بٹ", "قریشی", "اکرم",
        "گجر", "اعظم", "آفریدی", "رؤف", "زمان", "شاہ", "عزیز", "آغا", "جمال", "ایوب",
        "شفیق", "شکیل", "منظور", "الحق", "انور", "اختر", "رزاق", "گل", "میر", "ریاض",
        "رحمٰن", "جاوید", "اقبال", "بشیر", "ندیم", "وحید", "چوہدری", "راجپوت", "انصاری", "مغل"
    ]

    addresses = [
        "جی نائن مرکز، اسلام آباد",
        "ڈی ایچ اے فیز 5، لاہور",
        "گلشن اقبال، بلاک 4، کراچی",
        "سیٹلائٹ ٹاؤن، راولپنڈی",
        "ایف ٹین تھری، گلی 12، اسلام آباد",
        "کینٹ ایریا، سیالکوٹ",
        "ماڈل ٹاؤن، سی بلاک، لاہور",
        "جوہر ٹاؤن، فیز 2، لاہور",
        "نارتھ ناظم آباد، کراچی",
        "واپڈا ٹاؤن، گوجرانوالہ",
        "سول لائنز، فیصل آباد",
        "یونیورسٹی روڈ، پشاور",
        "گلگشت کالونی، ملتان",
        "چنگی نمبر 9، ملتان",
        "صدر بازار، راولپنڈی",
        "ایف سیون ٹو، اسلام آباد",
        "بحریہ ٹاؤن، فیز 4، راولپنڈی",
        "کلفٹن، بلاک 2، کراچی",
        "پیپلز کالونی، فیصل آباد",
        "علامہ اقبال ٹاؤن، لاہور"
    ]

    pattis = ["سادہ پٹی", "بٹن پٹی", "زپ پٹی", "بین پٹی"]
    patti_sizes = ["1 انچ", "1.25 انچ", "1.5 انچ"]
    patti_lengths = ["12 انچ", "13 انچ", "14 انچ"]
    paancha_pattis = ["سادہ", "سلائی والی", "بٹن والی"]
    stitchings = ["سنگل سلائی", "ڈبل سلائی"]
    cuff_types = ["کف گول", "کف چوکور"]
    cuff_sizes = ["2.25 انچ", "2.5 انچ", "2.75 انچ"]
    collar_noks = ["کالر 1", "کالر 2", "کالر 3"]

    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    used_phones = set()

    orders_to_create = []
    customers_to_create = []

    for i in range(100):
        c_num = f"H{next_cust_num + i}"
        o_num = f"ORD-{(next_order_num + i):04d}"

        # Unique Pakistani phone number
        while True:
            prefix = random.choice(["0300", "0301", "0302", "0303", "0304", "0305", "0312", "0313", "0321", "0322", "0331", "0332", "0333", "0345", "0346"])
            suffix = f"{random.randint(1000000, 9999999)}"
            phone = f"{prefix}{suffix}"
            if phone not in used_phones:
                used_phones.add(phone)
                break

        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        address = random.choice(addresses)

        # Measurements
        measurements = {
            "shirt_length": str(random.choice([38, 38.5, 39, 39.5, 40, 40.5, 41, 42, 42.5])),
            "sleeve": str(random.choice([22, 22.5, 23, 23.5, 24, 24.5, 25])),
            "shoulder": str(random.choice([17, 17.5, 18, 18.5, 19, 19.5])),
            "collar_size": str(random.choice([14.5, 15, 15.5, 16, 16.5, 17])),
            "chest": str(random.choice([36, 38, 39, 40, 41, 42, 43, 44])),
            "armpit": str(random.choice([9, 9.5, 10, 10.5, 11])),
            "daaman": str(random.choice([21, 22, 22.5, 23, 23.5, 24, 25])),
            "daaman_type": random.choice(["گول", "سیدھا"]),
            "shalwar_length": str(random.choice([37, 38, 38.5, 39, 39.5, 40, 41])),
            "paancha": str(random.choice([14, 14.5, 15, 15.5, 16, 16.5, 17])),
            "asan": str(random.choice([14, 15, 15.5, 16, 16.5, 17])),
            "shalwar_gheer": str(random.choice([20, 21, 22, 23, 24])),
            "chaak": str(random.choice([12, 12.5, 13, 13.5, 14])),
            "patti": random.choice(pattis),
            "patti_size": random.choice(patti_sizes),
            "patti_length": random.choice(patti_lengths),
            "paancha_patti": random.choice(paancha_pattis),
            "stitching": random.choice(stitchings),
            "extra_1": "",
            "extra_2": "",
            "cuff_type": random.choice(cuff_types),
            "cuff_size": random.choice(cuff_sizes),
            "collar_nok": random.choice(collar_noks),
            "moora": str(random.choice([9, 9.5, 10])),
            "baghair_plate": random.choice([True, False]),
            "baghair_label": random.choice([True, False]),
            "chaak_patti_button": random.choice([True, False]),
            "chamak_taar": random.choice([True, False]),
            "steel_button": random.choice([True, False]),
            "front_pocket": random.choice([True, True, False]),
            "side_pocket_1": random.choice([True, False]),
            "side_pocket_2": random.choice([True, False]),
            "shalwar_pocket": random.choice([True, False]),
            "front_pocket_kaaj": random.choice([True, False]),
            "cuff_1_kaaj": random.choice([True, False]),
            "cuff_2_kaaj": random.choice([True, False]),
            "stud_kaaj": random.choice([True, False])
        }

        # Status distribution:
        # ~50 "زیر تکمیل" (In Progress)
        # ~25 "تیار" (Ready)
        # ~25 "ترسیل شدہ" (Delivered)
        if i < 50:
            status = "زیر تکمیل"
            # Some overdue (days -5 to -1), some today (0), some upcoming (+1 to +10)
            if i < 15:
                due_delta = -random.randint(1, 5) # Overdue!
            elif i < 25:
                due_delta = 0 # Due today!
            else:
                due_delta = random.randint(1, 12) # Future
        elif i < 75:
            status = "تیار"
            due_delta = random.randint(-1, 5)
        else:
            status = "ترسیل شدہ"
            due_delta = -random.randint(1, 10)

        due_date = (today + timedelta(days=due_delta)).strftime("%Y-%m-%d")
        order_date = (today - timedelta(days=random.randint(1, 15))).strftime("%Y-%m-%d")

        price = random.choice([2000, 2200, 2500, 2800, 3000, 3500, 4000, 4500, 5000])
        if status == "ترسیل شدہ":
            advance = price # Fully paid
        else:
            advance = random.choice([0, 500, 1000, 1500, 2000])
            if advance > price:
                advance = price // 2

        # Customer record
        cust_id = f"cust_{c_num.lower()}"
        cust_doc = {
            "id": cust_id,
            "customer_number": c_num,
            "name": name,
            "phone": phone,
            "address": address,
            "measurements": measurements,
            "created_at": order_date + "T10:00:00"
        }
        customers_to_create.append(cust_doc)

        # Order record
        order_doc = {
            "order_number": o_num,
            "customer_id": cust_id,
            "customer_number": c_num,
            "customer_name": name,
            "customer_phone": phone,
            "address": address,
            "due_date": due_date,
            "price": float(price),
            "advance": float(advance),
            "order_date": order_date,
            "status": status,
            "measurements": measurements,
            "created_at": order_date + "T10:30:00"
        }
        orders_to_create.append(order_doc)

    print(f"Generated 100 customers and 100 orders.")
    print("Writing in batches of 400 operations to Firestore...")

    # Write in batches
    # Firestore allows up to 500 writes per batch.
    # 100 customers + 100 orders = 200 writes, can fit in 1 batch.
    batch = db.batch()
    for c in customers_to_create:
        doc_ref = db.collection("customers").document(c["id"])
        batch.set(doc_ref, c)

    for o in orders_to_create:
        doc_ref = db.collection("orders").document()
        batch.set(doc_ref, o)

    # Also update counters
    batch.set(cust_counter_ref, {"next_number": next_cust_num + 100})
    batch.set(order_counter_ref, {"next_number": next_order_num + 100})

    batch.commit()
    print(" Successfully committed 100 test orders and customers to Firestore!")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""Seed realistic demo data into YFG Accounting database.
Inserts: 3 companies, 5 persons, 3 contracts, 3 proformas, 4 invoices,
plus company contacts and descriptions. Idempotent — checks for existing
records with the same code before inserting."""
import sys, json, sqlite3, hashlib
sys.path.insert(0, '/home/z/my-project/upload/extracted/YFG-Accounting')
from app.main import password_hash, uid, now

DB_PATH = '/home/z/my-project/upload/extracted/YFG-Accounting/data/yfg.sqlite3'
ATTACH_DIR = '/home/z/my-project/upload/extracted/YFG-Accounting/data/attachments'

con = sqlite3.connect(DB_PATH)
con.row_factory = sqlite3.Row

def exists(table, code_val, code_field='code'):
    return con.execute(f"SELECT id FROM {table} WHERE {code_field}=?", (code_val,)).fetchone()

# Reset admin password (known good)
admin_user = con.execute("SELECT id FROM users WHERE username='admin'").fetchone()
if not admin_user:
    print("Admin user not found! Run /api/setup first.")
    sys.exit(1)
admin_id = admin_user['id']
con.execute("UPDATE users SET password_hash=? WHERE username='admin'", (password_hash('admin123'),))
print(f"Reset admin password (user_id={admin_id})")

# Also reset emp1/emp2/emp3/emp4/emp5 passwords
for un in ['emp1', 'emp2', 'emp3', 'emp4', 'emp5']:
    con.execute(f"UPDATE users SET password_hash=? WHERE username=?", (password_hash('emp123'), un))
print("Reset employee passwords")

# ===== COMPANIES (3 realistic Iranian companies) =====
companies = [
    {
        'code': '1001', 'name': 'شرکت بازرگانی پارس آریا',
        'kind': 'LEGAL', 'national_id': '14003254678', 'phone': '021-88991234',
        'address': 'تهران، خیابان ولیعصر، بالاتر از پارک‌وی، پلاک ۱۴۲، طبقه ۴',
        'postal_code': '1963773344', 'manager_name': 'محمد رضایی', 'manager_phone': '09121110001',
        'description': 'شرکت فعال در حوزه واردات و توزیع قطعات یدکی خودرو. حسابرسی سالانه دارد و گزارش‌های مالی ماهانه تهیه می‌شود. حساسیت بالا روی اسناد هزینه.',
    },
    {
        'code': '1002', 'name': 'فروشگاه زنجیره‌ای رفاه',
        'kind': 'LEGAL', 'national_id': '10762543198', 'phone': '021-66445566',
        'address': 'تهران، خیابان جمهوری، روبروی دانشگاه تهران، ساختمان مرکزی رفاه',
        'postal_code': '1314766543', 'manager_name': 'فاطمه احمدی', 'manager_phone': '09121110002',
        'description': 'فروشگاه زنجیره‌ای با ۴۲ شعبه در سراسر کشور. گزارش فروش روزانه و موجودی انبار ماهانه. حسابرسی مالی سالانه.',
    },
    {
        'code': '1003', 'name': 'علی محمدی',  # حقیقی (REAL)
        'kind': 'REAL', 'first_name': 'علی', 'last_name': 'محمدی',
        'national_id': '0098765432', 'phone': '09153334455',
        'address': 'مشهد، بلوار سجاد، نبش سجاد ۲۵، ساختمان پزشکان',
        'postal_code': '9183744556', 'manager_name': 'علی محمدی', 'manager_phone': '09153334455',
        'description': 'پزشک متخصص، مشاور مالیاتی سالانه. نیاز به گزارش دارایی و سرمایه‌گذاری شخصی.',
    },
]

company_ids = {}
for c in companies:
    existing = exists('companies', c['code'])
    if existing:
        company_ids[c['code']] = existing['id']
        # Update fields
        con.execute("""UPDATE companies SET name=?, kind=?, first_name=?, last_name=?, national_id=?, phone=?, address=?, postal_code=?, manager_name=?, manager_phone=?, description=? WHERE id=?""",
                    (c['name'], c['kind'], c.get('first_name',''), c.get('last_name',''),
                     c['national_id'], c['phone'], c['address'], c['postal_code'],
                     c['manager_name'], c['manager_phone'], c['description'], existing['id']))
        print(f"Updated company {c['code']}: {c['name']}")
    else:
        cid = uid()
        con.execute("""INSERT INTO companies (id,code,name,active,created_at,kind,first_name,last_name,national_id,phone,address,postal_code,manager_name,manager_phone,description)
                       VALUES(?,?,?,1,?,?,?,?,?,?,?,?,?,?,?)""",
                    (cid, c['code'], c['name'], now(), c['kind'],
                     c.get('first_name',''), c.get('last_name',''),
                     c['national_id'], c['phone'], c['address'], c['postal_code'],
                     c['manager_name'], c['manager_phone'], c['description']))
        company_ids[c['code']] = cid
        print(f"Created company {c['code']}: {c['name']}")

# ===== COMPANY CONTACTS (multiple per company) =====
contacts = [
    ('1001', 'PHONE', 'تلفن دفتر مرکزی', '021-88991234', 'ساعات کاری ۸ تا ۱۷'),
    ('1001', 'MOBILE', 'همراه مدیرعامل', '09121110001', 'تماس اضطراری ۲۴ ساعته'),
    ('1001', 'EMAIL', 'ایمیل دفتر', 'info@parsaria.ir', 'پاسخ در ۲۴ ساعت'),
    ('1001', 'WEBSITE', 'وب‌سایت شرکت', 'www.parsaria.ir', ''),
    ('1002', 'PHONE', 'مرکز تماس', '021-66445566', 'تماس با مرکز پشتیبانی'),
    ('1002', 'MOBILE', 'همراه مدیرمالی', '09121110002', ''),
    ('1002', 'FAX', 'فاکس', '021-66445577', ''),
    ('1002', 'EMAIL', 'ایمیل مالی', 'finance@refah.ir', 'ارسال فاکتورها'),
    ('1003', 'MOBILE', 'همراه شخصی', '09153334455', 'تماس مستقیم'),
    ('1003', 'EMAIL', 'ایمیل', 'ali.mohammadi@example.com', ''),
]

for comp_code, ct, label, val, notes in contacts:
    comp_id = company_ids[comp_code]
    # Check if exists
    existing = con.execute("SELECT id FROM company_contacts WHERE company_id=? AND value=?", (comp_id, val)).fetchone()
    if existing:
        continue
    con.execute("INSERT INTO company_contacts (id,company_id,contact_type,label,value,notes,created_by,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (uid(), comp_id, ct, label, val, notes, admin_id, now()))
print(f"Inserted {len(contacts)} company contacts")

# ===== PERSONS (5 real persons as customers) =====
persons = [
    {'code': 'P001', 'first_name': 'مهدی', 'last_name': 'کریمی', 'national_id': '0098712345', 'phone': '09123334456', 'email': 'm.karimi@example.com', 'address': 'تهران، نیاوران', 'postal_code': '1987766543', 'notes': 'مشتری ثابت، پرداخت منظم', 'company_code': '1001'},
    {'code': 'P002', 'first_name': 'زهرا', 'last_name': 'حسینی', 'national_id': '0098719876', 'phone': '09151112233', 'email': 'z.hosseini@example.com', 'address': 'شیراز، خیابان زند', 'postal_code': '7134812345', 'notes': 'مالک فروشگاه', 'company_code': '1002'},
    {'code': 'P003', 'first_name': 'حسن', 'last_name': 'علیپور', 'national_id': '0087612345', 'phone': '09191110022', 'email': 'h.alipour@example.com', 'address': 'اصفهان، چهارباغ', 'postal_code': '8145612345', 'notes': '', 'company_code': None},
    {'code': 'P004', 'first_name': 'مریم', 'last_name': 'عباسی', 'national_id': '0098744556', 'phone': '09178889900', 'email': 'm.abbasi@example.com', 'address': 'تبریز، خیابان امام', 'postal_code': '5163812345', 'notes': 'مشاوره مالیاتی نیاز دارد', 'company_code': None},
    {'code': 'P005', 'first_name': 'رضا', 'last_name': 'صادقی', 'national_id': '0098798765', 'phone': '09367778899', 'email': 'r.sadeghi@example.com', 'address': 'کرج، بلوار طalar', 'postal_code': '3198765432', 'notes': '', 'company_code': None},
]

person_ids = {}
for p in persons:
    linked_id = company_ids.get(p['company_code']) if p['company_code'] else None
    if exists('persons', p['code']):
        existing = exists('persons', p['code'])
        person_ids[p['code']] = existing['id']
        con.execute("UPDATE persons SET first_name=?,last_name=?,national_id=?,phone=?,email=?,address=?,postal_code=?,notes=?,linked_company_id=? WHERE id=?",
                    (p['first_name'], p['last_name'], p['national_id'], p['phone'], p['email'], p['address'], p['postal_code'], p['notes'], linked_id, existing['id']))
        print(f"Updated person {p['code']}: {p['first_name']} {p['last_name']}")
    else:
        pid = uid()
        con.execute("""INSERT INTO persons (id,code,first_name,last_name,national_id,phone,email,address,postal_code,notes,linked_company_id,active,created_by,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (pid, p['code'], p['first_name'], p['last_name'], p['national_id'], p['phone'], p['email'], p['address'], p['postal_code'], p['notes'], linked_id, 1, admin_id, now()))
        person_ids[p['code']] = pid
        print(f"Created person {p['code']}: {p['first_name']} {p['last_name']}")

# ===== CONTRACTS (3 active/inactive mix) =====
contracts = [
    {
        'code': 'C1402-001', 'title': 'حسابرسی مالی سال ۱۴۰۲ - شرکت بازرگانی پارس آریا',
        'company_code': '1001', 'person_code': 'P001',
        'start_date': '2023-12-01', 'end_date': '2024-04-30',
        'value_amount': 750000000, 'currency': 'IRR', 'status': 'COMPLETED',
        'contract_type': 'audit', 'subject': 'حسابرسی کامل اسناد مالی سال ۱۴۰۲',
        'notes': 'گزارش نهایی تحویل شد. کار تکمیل شد.',
    },
    {
        'code': 'C1403-001', 'title': 'حسابداری ماهانه - شرکت بازرگانی پارس آریا',
        'company_code': '1001', 'person_code': 'P001',
        'start_date': '2024-01-01', 'end_date': '2024-12-31',
        'value_amount': 480000000, 'currency': 'IRR', 'status': 'ACTIVE',
        'contract_type': 'accounting', 'subject': 'ثبت دفاتر روزنامه و کل، اعلامیه مالیاتی، تهیه گزارش ماهانه',
        'notes': 'قرارداد سالانه، صورتحساب ماهانه صادر می‌شود.',
    },
    {
        'code': 'C1403-002', 'title': 'گزارش مالی ماهانه - فروشگاه زنجیره‌ای رفاه',
        'company_code': '1002', 'person_code': 'P002',
        'start_date': '2024-03-01', 'end_date': '2025-02-28',
        'value_amount': 1200000000, 'currency': 'IRR', 'status': 'ACTIVE',
        'contract_type': 'accounting', 'subject': 'گزارش فروش، موجودی انبار، مالیات',
        'notes': 'گزارش‌گیری از ۴۲ شعبه.',
    },
]

contract_ids = {}
for c in contracts:
    comp_id = company_ids.get(c['company_code'])
    person_id = person_ids.get(c['person_code'])
    if exists('contracts', c['code']):
        existing = exists('contracts', c['code'])
        contract_ids[c['code']] = existing['id']
        con.execute("UPDATE contracts SET title=?,company_id=?,person_id=?,start_date=?,end_date=?,value_amount=?,currency=?,status=?,contract_type=?,subject=?,notes=?,updated_at=? WHERE id=?",
                    (c['title'], comp_id, person_id, c['start_date'], c['end_date'], c['value_amount'], c['currency'], c['status'], c['contract_type'], c['subject'], c['notes'], now(), existing['id']))
        print(f"Updated contract {c['code']}: {c['title']}")
    else:
        cid = uid()
        con.execute("""INSERT INTO contracts (id,code,title,company_id,person_id,start_date,end_date,value_amount,currency,status,contract_type,subject,notes,attachment_id,created_by,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (cid, c['code'], c['title'], comp_id, person_id, c['start_date'], c['end_date'],
                     c['value_amount'], c['currency'], c['status'], c['contract_type'], c['subject'], c['notes'],
                     None, admin_id, now(), now()))
        contract_ids[c['code']] = cid
        print(f"Created contract {c['code']}: {c['title']} ({c['status']})")

# ===== PROFORMAS (3 with items) =====
proformas = [
    {
        'code': 'PF1403-001', 'title': 'پیش فاکتور خدمات حسابداری فروردین ۱۴۰۳',
        'company_code': '1001', 'contract_code': 'C1403-001',
        'issue_date': '2024-04-01', 'valid_until': '2024-05-01',
        'status': 'ACCEPTED', 'currency': 'IRR',
        'items': [
            {'description': 'ثبت دفاتر روزنامه و کل', 'qty': 1, 'unit_price': 30000000},
            {'description': 'تهیه گزارش مالی ماهانه', 'qty': 1, 'unit_price': 10000000},
            {'description': 'محاسبه و اظهار مالیات', 'qty': 1, 'unit_price': 5000000},
        ],
        'notes': 'پیش‌فاکتور ماه اول',
    },
    {
        'code': 'PF1403-002', 'title': 'پیش فاکتور مشاوره مالیاتی',
        'company_code': '1002', 'contract_code': 'C1403-002',
        'issue_date': '2024-04-15', 'valid_until': '2024-05-15',
        'status': 'IN_PROGRESS', 'currency': 'IRR',
        'items': [
            {'description': 'بررسی اسناد هزینه‌ای ۴۲ شعبه', 'qty': 42, 'unit_price': 500000},
            {'description': 'تهیه گزارش تجمیعی', 'qty': 1, 'unit_price': 15000000},
        ],
        'notes': 'در حال بررسی',
    },
    {
        'code': 'PF1403-003', 'title': 'پیش فاکتور خدمات سالانه',
        'company_code': '1001', 'contract_code': None,
        'issue_date': '2024-04-20', 'valid_until': '2024-06-30',
        'status': 'SENT', 'currency': 'IRR',
        'items': [
            {'description': 'حسابرسی سال ۱۴۰۳', 'qty': 1, 'unit_price': 800000000},
        ],
        'notes': 'ارسال شده، منتظر تأیید',
    },
]

proforma_ids = {}
for p in proformas:
    comp_id = company_ids.get(p['company_code'])
    contract_id = contract_ids.get(p['contract_code']) if p['contract_code'] else None
    items_json = json.dumps(p['items'], ensure_ascii=False)
    total = sum((float(i['qty']) * float(i['unit_price'])) for i in p['items'])
    if exists('proformas', p['code']):
        existing = exists('proformas', p['code'])
        proforma_ids[p['code']] = existing['id']
        con.execute("UPDATE proformas SET title=?,company_id=?,contract_id=?,issue_date=?,valid_until=?,status=?,total_amount=?,currency=?,items_json=?,notes=?,updated_at=? WHERE id=?",
                    (p['title'], comp_id, contract_id, p['issue_date'], p['valid_until'], p['status'], total, p['currency'], items_json, p['notes'], now(), existing['id']))
        print(f"Updated proforma {p['code']}: {p['title']} (total={total})")
    else:
        pid = uid()
        con.execute("""INSERT INTO proformas (id,code,title,company_id,person_id,contract_id,issue_date,valid_until,status,total_amount,currency,items_json,notes,created_by,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (pid, p['code'], p['title'], comp_id, None, contract_id, p['issue_date'], p['valid_until'], p['status'], total, p['currency'], items_json, p['notes'], admin_id, now(), now()))
        proforma_ids[p['code']] = pid
        print(f"Created proforma {p['code']}: {p['title']} (total={total})")

# ===== INVOICES (4 with payment states) =====
invoices = [
    {
        'code': 'INV1403-001', 'title': 'فاکتور خدمات حسابداری فروردین ۱۴۰۳',
        'company_code': '1001', 'proforma_code': 'PF1403-001', 'contract_code': 'C1403-001',
        'issue_date': '2024-04-10', 'due_date': '2024-04-25',
        'status': 'PAID', 'total_amount': 45000000, 'paid_amount': 45000000, 'currency': 'IRR',
        'notes': 'تسویه کامل',
    },
    {
        'code': 'INV1403-002', 'title': 'فاکتور مشاوره مالیاتی اردیبهشت',
        'company_code': '1002', 'proforma_code': 'PF1403-002', 'contract_code': 'C1403-002',
        'issue_date': '2024-05-01', 'due_date': '2024-06-01',
        'status': 'UNPAID', 'total_amount': 36000000, 'paid_amount': 0, 'currency': 'IRR',
        'notes': 'سررسید نزدیک، پیگیری شود',
    },
    {
        'code': 'INV1403-003', 'title': 'فاکتور خدمات حسابداری اردیبهشت ۱۴۰۳',
        'company_code': '1001', 'proforma_code': None, 'contract_code': 'C1403-001',
        'issue_date': '2024-05-10', 'due_date': '2024-05-25',
        'status': 'PARTIAL', 'total_amount': 45000000, 'paid_amount': 20000000, 'currency': 'IRR',
        'notes': 'پرداخت جزئی، ۲۵M مانده',
    },
    {
        'code': 'INV1402-099', 'title': 'فاکتور قدیمی سررسید گذشته',
        'company_code': '1002', 'proforma_code': None, 'contract_code': None,
        'issue_date': '2023-12-01', 'due_date': '2024-01-15',
        'status': 'OVERDUE', 'total_amount': 75000000, 'paid_amount': 0, 'currency': 'IRR',
        'notes': 'سررسید گذشته، نیاز به پیگیری حقوقی',
    },
]

for inv in invoices:
    comp_id = company_ids.get(inv['company_code'])
    proforma_id = proforma_ids.get(inv['proforma_code']) if inv['proforma_code'] else None
    contract_id = contract_ids.get(inv['contract_code']) if inv['contract_code'] else None
    if exists('invoices', inv['code']):
        existing = exists('invoices', inv['code'])
        con.execute("UPDATE invoices SET title=?,company_id=?,proforma_id=?,contract_id=?,issue_date=?,due_date=?,status=?,total_amount=?,paid_amount=?,currency=?,notes=?,updated_at=? WHERE id=?",
                    (inv['title'], comp_id, proforma_id, contract_id, inv['issue_date'], inv['due_date'], inv['status'], inv['total_amount'], inv['paid_amount'], inv['currency'], inv['notes'], now(), existing['id']))
        print(f"Updated invoice {inv['code']}: {inv['title']} ({inv['status']})")
    else:
        iid = uid()
        con.execute("""INSERT INTO invoices (id,code,title,company_id,person_id,proforma_id,contract_id,issue_date,due_date,status,total_amount,paid_amount,currency,items_json,notes,created_by,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (iid, inv['code'], inv['title'], comp_id, None, proforma_id, contract_id, inv['issue_date'], inv['due_date'], inv['status'], inv['total_amount'], inv['paid_amount'], inv['currency'], '[]', inv['notes'], admin_id, now(), now()))
        print(f"Created invoice {inv['code']}: {inv['title']} ({inv['status']})")

con.commit()
con.close()
print("\n✅ All realistic data inserted.")
print("Companies: 3 | Persons: 5 | Contracts: 3 | Proformas: 3 | Invoices: 4 | Company contacts: 10")

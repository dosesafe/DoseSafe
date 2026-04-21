import sqlite3
from datetime import datetime

def connect():
    return sqlite3.connect("meds.db", check_same_thread=False)

# -------------------------
# CREATE TABLES
# -------------------------
def create_tables():
    conn = connect()
    c = conn.cursor()

    # CHILDREN
    c.execute("""
    CREATE TABLE IF NOT EXISTS children (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        surname TEXT,
        dob TEXT,
        school TEXT,
        UNIQUE(name, surname, dob)
    )
    """)

    # MEDS
    c.execute("""
    CREATE TABLE IF NOT EXISTS meds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER,
        name TEXT,
        dosage TEXT,
        interval INTEGER,
        unit TEXT
    )
    """)

    # LOGS
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        med_id INTEGER,
        time_given TEXT,
        given_by TEXT
    )
    """)

    # STAFF
    c.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        pin TEXT,
        school TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    # INCIDENTS
    c.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER,
        type TEXT,
        description TEXT,
        time TEXT,
        reported_by TEXT
    )
    """)

    # ALLERGIES
    c.execute("""
    CREATE TABLE IF NOT EXISTS allergies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    # CHILD ALLERGIES
    c.execute("""
    CREATE TABLE IF NOT EXISTS child_allergies (
        child_id INTEGER,
        allergy_id INTEGER
    )
    """)

    # MED LIBRARY
    c.execute("""
    CREATE TABLE IF NOT EXISTS med_library (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        unit TEXT
    )
    """)

    # SUBSCRIPTIONS
    c.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        school TEXT PRIMARY KEY,
        status TEXT,
        expiry_date TEXT
    )
    """)

    # DEFAULT DATA
    defaults = ["Peanuts", "Dairy", "Eggs", "Gluten"]
    for a in defaults:
        try:
            c.execute("INSERT INTO allergies (name) VALUES (?)", (a,))
        except:
            pass

    meds = [
        ("Panado", "ml"),
        ("Nurofen", "ml"),
        ("Plaster", "unit"),
        ("Burnshield", "n/a")
    ]
    for m in meds:
        try:
            c.execute("INSERT INTO med_library (name, unit) VALUES (?, ?)", m)
        except:
            pass

    conn.commit()
    conn.close()

# -------------------------
# SUBSCRIPTIONS
# -------------------------
def set_subscription(school, status, expiry):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO subscriptions (school, status, expiry_date)
        VALUES (?, ?, ?)
    """, (school, status, expiry))
    conn.commit()
    conn.close()

def get_subscription(school):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT status, expiry_date FROM subscriptions WHERE school=?", (school,))
    return c.fetchone()

# -------------------------
# STAFF
# -------------------------
def add_staff(name, pin, school):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO staff (name, pin, school) VALUES (?,?,?)", (name, pin, school))
    conn.commit()
    conn.close()

def get_schools():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT DISTINCT school FROM staff WHERE active=1")
    return [s[0] for s in c.fetchall()]

def get_staff_by_school(school):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, name FROM staff WHERE school=? AND active=1", (school,))
    return c.fetchall()

def verify_staff(name, pin, school):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id FROM staff WHERE name=? AND pin=? AND school=? AND active=1",
              (name, pin, school))
    return c.fetchone()

def get_all_staff():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, name, school, active FROM staff")
    return c.fetchall()

def set_staff_active(id, active):
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE staff SET active=? WHERE id=?", (active, id))
    conn.commit()
    conn.close()

# -------------------------
# CHILD
# -------------------------
def add_child(name, surname, dob, school):
    conn = connect()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO children (name, surname, dob, school) VALUES (?,?,?,?)",
                  (name, surname, dob, school))
        conn.commit()
        return c.lastrowid
    except:
        return False
    finally:
        conn.close()

def get_children(school):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM children WHERE school=?", (school,))
    return c.fetchall()

# -------------------------
# ALLERGIES
# -------------------------
def get_allergies():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, name FROM allergies")
    return c.fetchall()

def add_child_allergies(cid, aids):
    conn = connect()
    c = conn.cursor()
    for a in aids:
        c.execute("INSERT INTO child_allergies VALUES (?,?)", (cid, a))
    conn.commit()
    conn.close()

def get_child_allergies(cid):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT a.name FROM allergies a
        JOIN child_allergies ca ON a.id = ca.allergy_id
        WHERE ca.child_id=?
    """, (cid,))
    return [x[0] for x in c.fetchall()]

# -------------------------
# MED LIBRARY
# -------------------------
def get_med_library():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM med_library")
    return c.fetchall()

def add_med_to_library(name, unit):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO med_library (name, unit) VALUES (?,?)", (name, unit))
    conn.commit()
    conn.close()

# -------------------------
# MEDS
# -------------------------
def add_med(cid, name, dose, interval, unit):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO meds VALUES (NULL,?,?,?,?,?)",
              (cid, name, dose, interval, unit))
    conn.commit()
    conn.close()

def get_meds(cid):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM meds WHERE child_id=?", (cid,))
    return c.fetchall()

# -------------------------
# LOGS
# -------------------------
def log_dose(mid, user):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO logs VALUES (NULL,?,?,?)",
              (mid, datetime.now().isoformat(), user))
    conn.commit()
    conn.close()

def get_last_dose_full(mid):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT time_given, given_by
        FROM logs
        WHERE med_id=?
        ORDER BY time_given DESC LIMIT 1
    """, (mid,))
    return c.fetchone()

# -------------------------
# INCIDENTS
# -------------------------
def add_incident(cid, t, desc, user):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO incidents VALUES (NULL,?,?,?,?,?)",
              (cid, t, desc, datetime.now().isoformat(), user))
    conn.commit()
    conn.close()

def get_incidents(cid):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM incidents WHERE child_id=? ORDER BY time DESC", (cid,))
    return c.fetchall()

# -------------------------
# REPORTS
# -------------------------
def get_today_logs(cid):
    conn = connect()
    c = conn.cursor()
    today = datetime.now().date().isoformat()

    c.execute("""
        SELECT m.name, l.time_given, l.given_by
        FROM logs l
        JOIN meds m ON l.med_id = m.id
        WHERE m.child_id=? AND DATE(l.time_given)=?
    """, (cid, today))

    return c.fetchall()

def get_today_incidents(cid):
    conn = connect()
    c = conn.cursor()
    today = datetime.now().date().isoformat()

    c.execute("""
        SELECT type, description, time, reported_by
        FROM incidents
        WHERE child_id=? AND DATE(time)=?
    """, (cid, today))

    return c.fetchall()

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

    # MEDICATIONS
    c.execute("""
    CREATE TABLE IF NOT EXISTS meds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER,
        name TEXT,
        dosage TEXT,
        interval INTEGER
    )
    """)

    # DOSE LOGS
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

    # ALLERGIES MASTER
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

    # DEFAULT ALLERGIES
    defaults = ["Peanuts", "Dairy", "Eggs", "Gluten", "Soy", "Penicillin", "Ibuprofen"]
    for a in defaults:
        try:
            c.execute("INSERT INTO allergies (name) VALUES (?)", (a,))
        except:
            pass

    conn.commit()
    conn.close()

# -------------------------
# STAFF FUNCTIONS
# -------------------------
def add_staff(name, pin, school):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO staff (name, pin, school) VALUES (?, ?, ?)", (name, pin, school))
    conn.commit()
    conn.close()

def get_all_staff():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, name, school, active FROM staff")
    data = c.fetchall()
    conn.close()
    return data

def set_staff_active(staff_id, active):
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE staff SET active=? WHERE id=?", (active, staff_id))
    conn.commit()
    conn.close()

def get_schools():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT DISTINCT school FROM staff WHERE active=1")
    data = [s[0] for s in c.fetchall()]
    conn.close()
    return data

def get_staff_by_school(school):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, name FROM staff WHERE school=? AND active=1", (school,))
    data = c.fetchall()
    conn.close()
    return data

def verify_staff(name, pin, school):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT id FROM staff
        WHERE name=? AND pin=? AND school=? AND active=1
    """, (name, pin, school))
    result = c.fetchone()
    conn.close()
    return result

# -------------------------
# CHILD FUNCTIONS
# -------------------------
def add_child(name, surname, dob, school):
    conn = connect()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO children (name, surname, dob, school)
            VALUES (?, ?, ?, ?)
        """, (name, surname, dob, school))
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
    data = c.fetchall()
    conn.close()
    return data

# -------------------------
# ALLERGIES
# -------------------------
def get_allergies():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, name FROM allergies")
    data = c.fetchall()
    conn.close()
    return data

def add_child_allergies(child_id, allergy_ids):
    conn = connect()
    c = conn.cursor()
    for aid in allergy_ids:
        c.execute("""
            INSERT INTO child_allergies (child_id, allergy_id)
            VALUES (?, ?)
        """, (child_id, aid))
    conn.commit()
    conn.close()

def get_child_allergies(child_id):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT a.name
        FROM allergies a
        JOIN child_allergies ca ON a.id = ca.allergy_id
        WHERE ca.child_id=?
    """, (child_id,))
    data = [d[0] for d in c.fetchall()]
    conn.close()
    return data

# -------------------------
# MEDICATION
# -------------------------
def add_med(child_id, name, dosage, interval):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO meds (child_id, name, dosage, interval)
        VALUES (?, ?, ?, ?)
    """, (child_id, name, dosage, interval))
    conn.commit()
    conn.close()

def get_meds(child_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM meds WHERE child_id=?", (child_id,))
    data = c.fetchall()
    conn.close()
    return data

# -------------------------
# DOSE LOGS
# -------------------------
def log_dose(med_id, given_by):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO logs (med_id, time_given, given_by)
        VALUES (?, ?, ?)
    """, (med_id, datetime.now().isoformat(), given_by))
    conn.commit()
    conn.close()

def get_last_dose(med_id):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT time_given FROM logs
        WHERE med_id=?
        ORDER BY time_given DESC LIMIT 1
    """, (med_id,))
    r = c.fetchone()
    conn.close()
    return r[0] if r else None

def get_last_dose_full(med_id):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT time_given, given_by
        FROM logs
        WHERE med_id=?
        ORDER BY time_given DESC LIMIT 1
    """, (med_id,))
    r = c.fetchone()
    conn.close()
    return r

# -------------------------
# INCIDENTS
# -------------------------
def add_incident(child_id, type, description, reported_by):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO incidents (child_id, type, description, time, reported_by)
        VALUES (?, ?, ?, ?, ?)
    """, (child_id, type, description, datetime.now().isoformat(), reported_by))
    conn.commit()
    conn.close()

def get_incidents(child_id):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM incidents
        WHERE child_id=?
        ORDER BY time DESC
    """, (child_id,))
    data = c.fetchall()
    conn.close()
    return data

# -------------------------
# DAILY REPORT
# -------------------------
def get_today_logs(child_id):
    conn = connect()
    c = conn.cursor()

    today = datetime.now().date().isoformat()

    c.execute("""
        SELECT m.name, l.time_given, l.given_by
        FROM logs l
        JOIN meds m ON l.med_id = m.id
        WHERE m.child_id=? AND DATE(l.time_given)=?
    """, (child_id, today))

    data = c.fetchall()
    conn.close()
    return data

def get_today_incidents(child_id):
    conn = connect()
    c = conn.cursor()

    today = datetime.now().date().isoformat()

    c.execute("""
        SELECT type, description, time, reported_by
        FROM incidents
        WHERE child_id=? AND DATE(time)=?
    """, (child_id, today))

    data = c.fetchall()
    conn.close()
    return data

import sqlite3
from datetime import datetime

def connect():
    return sqlite3.connect("meds.db", check_same_thread=False)

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
        interval INTEGER
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

    # ALLERGIES
    c.execute("""
    CREATE TABLE IF NOT EXISTS allergies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    # CHILD ↔ ALLERGIES
    c.execute("""
    CREATE TABLE IF NOT EXISTS child_allergies (
        child_id INTEGER,
        allergy_id INTEGER
    )
    """)

    # STAFF
    c.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        pin TEXT,
        school TEXT
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

    # PRELOAD ALLERGIES
    common_allergies = [
        "Peanuts", "Tree Nuts", "Dairy", "Eggs", "Gluten",
        "Soy", "Penicillin", "Ibuprofen", "Paracetamol", "Insect Stings"
    ]

    for allergy in common_allergies:
        try:
            c.execute("INSERT INTO allergies (name) VALUES (?)", (allergy,))
        except:
            pass

    conn.commit()
    conn.close()


# CHILD
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

def get_children():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM children")
    data = c.fetchall()
    conn.close()
    return data

def delete_child(child_id):
    conn = connect()
    c = conn.cursor()

    c.execute("DELETE FROM logs WHERE med_id IN (SELECT id FROM meds WHERE child_id=?)", (child_id,))
    c.execute("DELETE FROM meds WHERE child_id=?", (child_id,))
    c.execute("DELETE FROM child_allergies WHERE child_id=?", (child_id,))
    c.execute("DELETE FROM incidents WHERE child_id=?", (child_id,))
    c.execute("DELETE FROM children WHERE id=?", (child_id,))

    conn.commit()
    conn.close()


# ALLERGIES
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
        c.execute("INSERT INTO child_allergies VALUES (?, ?)", (child_id, aid))
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
    data = c.fetchall()
    conn.close()
    return [d[0] for d in data]


# STAFF
def get_staff_by_school(school):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, name, pin FROM staff WHERE school=?", (school,))
    data = c.fetchall()
    conn.close()
    return data

def verify_staff_pin(name, pin, school):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id FROM staff WHERE name=? AND pin=? AND school=?", (name, pin, school))
    result = c.fetchone()
    conn.close()
    return result

def add_staff(name, pin, school):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO staff (name, pin, school) VALUES (?, ?, ?)", (name, pin, school))
    conn.commit()
    conn.close()


# MEDS
def add_med(child_id, name, dosage, interval):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO meds VALUES (NULL, ?, ?, ?, ?)", (child_id, name, dosage, interval))
    conn.commit()
    conn.close()

def get_meds_by_child(child_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM meds WHERE child_id=?", (child_id,))
    data = c.fetchall()
    conn.close()
    return data


# LOGS
def log_dose(med_id, time, given_by):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO logs VALUES (NULL, ?, ?, ?)", (med_id, time, given_by))
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

def get_logs_by_med(med_id):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT time_given, given_by FROM logs
        WHERE med_id=?
        ORDER BY time_given DESC
    """, (med_id,))
    data = c.fetchall()
    conn.close()
    return data


# INCIDENTS
def add_incident(child_id, type, description, time, reported_by):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO incidents (child_id, type, description, time, reported_by)
        VALUES (?, ?, ?, ?, ?)
    """, (child_id, type, description, time, reported_by))
    conn.commit()
    conn.close()

def get_incidents(child_id):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT type, description, time, reported_by
        FROM incidents
        WHERE child_id=?
        ORDER BY time DESC
    """, (child_id,))
    data = c.fetchall()
    conn.close()
    return data


# DAILY REPORT
def get_today_logs(child_id):
    conn = connect()
    c = conn.cursor()

    today = datetime.now().date().isoformat()

    c.execute("""
        SELECT m.name, l.time_given, l.given_by
        FROM logs l
        JOIN meds m ON l.med_id = m.id
        WHERE m.child_id=? AND DATE(l.time_given)=?
        ORDER BY l.time_given ASC
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
        ORDER BY time ASC
    """, (child_id, today))

    data = c.fetchall()
    conn.close()
    return data

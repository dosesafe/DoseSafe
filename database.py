import sqlite3
from datetime import datetime

def connect():
    return sqlite3.connect("meds.db", check_same_thread=False)

def create_tables():
    conn = connect()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS children (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        surname TEXT,
        dob TEXT,
        school TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS meds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER,
        name TEXT,
        dosage TEXT,
        interval INTEGER,
        unit TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        med_id INTEGER,
        time_given TEXT,
        given_by TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        pin TEXT,
        school TEXT,
        active INTEGER DEFAULT 1
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER,
        type TEXT,
        description TEXT,
        time TEXT,
        reported_by TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS allergies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS child_allergies (
        child_id INTEGER,
        allergy_id INTEGER
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS med_library (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        unit TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS subscriptions (
        school TEXT PRIMARY KEY,
        status TEXT,
        expiry_date TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS parents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        pin TEXT,
        child_id INTEGER
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS disclaimer_acceptance (
        user TEXT,
        role TEXT,
        accepted INTEGER
    )""")

    conn.commit()
    conn.close()

# -------------------------
# DISCLAIMER
# -------------------------
def has_accepted_disclaimer(user, role):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT accepted FROM disclaimer_acceptance WHERE user=? AND role=?", (user, role))
    r = c.fetchone()
    conn.close()
    return r and r[0] == 1

def accept_disclaimer(user, role):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO disclaimer_acceptance VALUES (?,?,1)", (user, role))
    conn.commit()
    conn.close()

# -------------------------
# BASIC FUNCTIONS
# -------------------------
def add_staff(n, p, s):
    conn = connect()
    c = conn.cursor()
    c.execute(
        "INSERT INTO staff (name, pin, school) VALUES (?, ?, ?)",
        (n, p, s)
    )
    conn.commit()
    conn.close()

def get_schools():
    c = connect().cursor()
    c.execute("SELECT DISTINCT school FROM staff WHERE active=1")
    return [x[0] for x in c.fetchall()]

def verify_staff(n,p,s):
    c = connect().cursor()
    c.execute("SELECT id FROM staff WHERE name=? AND pin=? AND school=? AND active=1",(n,p,s))
    return c.fetchone()

def get_staff_by_school(s):
    return connect().cursor().execute("SELECT id,name FROM staff WHERE school=? AND active=1",(s,)).fetchall()

def add_child(n,s,d,sc):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO children VALUES (NULL,?,?,?,?)",(n,s,d,sc))
    conn.commit()
    return c.lastrowid

def get_children(sc):
    return connect().cursor().execute("SELECT * FROM children WHERE school=?",(sc,)).fetchall()

def get_allergies():
    return connect().cursor().execute("SELECT id,name FROM allergies").fetchall()

def add_child_allergies(cid,aids):
    conn = connect()
    c = conn.cursor()
    for a in aids:
        c.execute("INSERT INTO child_allergies VALUES (?,?)",(cid,a))
    conn.commit()

def add_med(cid, n, d, i, u):
    conn = connect()
    c = conn.cursor()
    c.execute(
        "INSERT INTO meds VALUES (NULL,?,?,?,?,?)",
        (cid, n, d, i, u)
    )
    conn.commit()
    conn.close()

def get_meds(cid):
    return connect().cursor().execute("SELECT * FROM meds WHERE child_id=?",(cid,)).fetchall()

def log_dose(mid, u):
    conn = connect()
    c = conn.cursor()
    c.execute(
        "INSERT INTO logs VALUES (NULL,?,?,?)",
        (mid, datetime.now().isoformat(), u)
    )
    conn.commit()
    conn.close()

def get_last_dose_full(mid):
    return connect().cursor().execute("SELECT time_given,given_by FROM logs WHERE med_id=? ORDER BY time_given DESC LIMIT 1",(mid,)).fetchone()

def add_incident(cid, t, d, u):
    conn = connect()
    c = conn.cursor()
    c.execute(
        "INSERT INTO incidents VALUES (NULL,?,?,?,?,?)",
        (cid, t, d, datetime.now().isoformat(), u)
    )
    conn.commit()
    conn.close()

def get_incidents(cid):
    return connect().cursor().execute("SELECT * FROM incidents WHERE child_id=? ORDER BY time DESC",(cid,)).fetchall()

def get_today_logs(cid):
    today = datetime.now().date().isoformat()
    return connect().cursor().execute("""
    SELECT m.name,l.time_given,l.given_by
    FROM logs l JOIN meds m ON l.med_id=m.id
    WHERE m.child_id=? AND DATE(l.time_given)=?
    """,(cid,today)).fetchall()

def get_today_incidents(cid):
    today = datetime.now().date().isoformat()
    return connect().cursor().execute("""
    SELECT type,description,time
    FROM incidents WHERE child_id=? AND DATE(time)=?
    """,(cid,today)).fetchall()

def get_med_library():
    return connect().cursor().execute("SELECT * FROM med_library").fetchall()

def add_med_to_library(n, u):
    conn = connect()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO med_library (name, unit) VALUES (?, ?)",
            (n, u)
        )
        conn.commit()
    except:
        pass
    conn.close()

def add_parent(n, p, c):
    conn = connect()
    c2 = conn.cursor()
    c2.execute(
        "INSERT INTO parents VALUES (NULL,?,?,?)",
        (n, p, c)
    )
    conn.commit()
    conn.close()

def verify_parent(n,p):
    return connect().cursor().execute("SELECT child_id FROM parents WHERE name=? AND pin=?",(n,p)).fetchone()

def get_logs_by_med(mid):
    return connect().cursor().execute("SELECT time_given,given_by FROM logs WHERE med_id=?",(mid,)).fetchall()

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
    c.execute(
        "UPDATE staff SET active=? WHERE id=?",
        (active, staff_id)
    )
    conn.commit()
    conn.close()

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
    c.execute("""
        SELECT status, expiry_date FROM subscriptions
        WHERE school=?
    """, (school,))
    result = c.fetchone()
    conn.close()
    return result

def get_all_subscriptions():
    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT school, status, expiry_date
        FROM subscriptions
    """)

    data = c.fetchall()
    conn.close()
    return data

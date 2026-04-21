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
        school TEXT
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

    # MIGRATION
    c.execute("PRAGMA table_info(meds)")
    cols = [col[1] for col in c.fetchall()]
    if "unit" not in cols:
        c.execute("ALTER TABLE meds ADD COLUMN unit TEXT DEFAULT ''")

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
        name TEXT UNIQUE,
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

    # PARENTS
    c.execute("""
    CREATE TABLE IF NOT EXISTS parents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        pin TEXT,
        child_id INTEGER
    )
    """)

    # DISCLAIMER
    c.execute("""
    CREATE TABLE IF NOT EXISTS disclaimer_acceptance (
        user TEXT,
        role TEXT,
        accepted INTEGER
    )
    """)

    # DEFAULT DATA
    allergies = ["Peanuts","Dairy","Eggs","Gluten","Penicillin","Bee stings","Latex"]
    for a in allergies:
        try:
            c.execute("INSERT INTO allergies (name) VALUES (?)",(a,))
        except: pass

    meds = [("Panado","ml"),("Nurofen","ml"),("Calpol","ml")]
    for m in meds:
        try:
            c.execute("INSERT INTO med_library (name, unit) VALUES (?,?)",m)
        except: pass

    conn.commit()
    conn.close()

# -------------------------
# DISCLAIMER
# -------------------------
def has_accepted_disclaimer(user, role):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT accepted FROM disclaimer_acceptance WHERE user=? AND role=?", (user, role))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def accept_disclaimer(user, role):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO disclaimer_acceptance VALUES (?,?,1)", (user, role))
    conn.commit()
    conn.close()

# -------------------------
# ALLERGY INTERACTION
# -------------------------
def get_allergy_warnings():
    return {
        "Penicillin": {"match": ["amoxicillin","penicillin"], "type": "block"}
    }

def get_child_allergies(cid):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT a.name FROM allergies a
        JOIN child_allergies ca ON a.id = ca.allergy_id
        WHERE ca.child_id=?
    """,(cid,))
    return [x[0] for x in c.fetchall()]

def check_med_allergy(child_id, med_name):
    allergies = get_child_allergies(child_id)
    rules = get_allergy_warnings()
    med_lower = med_name.lower()

    for allergy in allergies:
        if allergy in rules:
            for keyword in rules[allergy]["match"]:
                if keyword in med_lower:
                    return "block", allergy
    return None, None

# -------------------------
# BASIC FUNCTIONS (UNCHANGED)
# -------------------------
def add_staff(name,pin,school):
    connect().cursor().execute("INSERT INTO staff (name,pin,school) VALUES (?,?,?)",(name,pin,school))
    connect().commit()

def get_schools():
    c = connect().cursor()
    c.execute("SELECT DISTINCT school FROM staff WHERE active=1")
    return [x[0] for x in c.fetchall()]

def verify_staff(name,pin,school):
    c = connect().cursor()
    c.execute("SELECT id FROM staff WHERE name=? AND pin=? AND school=? AND active=1",(name,pin,school))
    return c.fetchone()

def get_staff_by_school(school):
    c = connect().cursor()
    c.execute("SELECT id,name FROM staff WHERE school=? AND active=1",(school,))
    return c.fetchall()

def get_all_staff():
    c = connect().cursor()
    c.execute("SELECT id,name,school,active FROM staff")
    return c.fetchall()

def set_staff_active(id,a):
    connect().cursor().execute("UPDATE staff SET active=? WHERE id=?",(a,id))
    connect().commit()

def add_child(name,surname,dob,school):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO children VALUES (NULL,?,?,?,?)",(name,surname,dob,school))
    conn.commit()
    return c.lastrowid

def get_children(school):
    c = connect().cursor()
    c.execute("SELECT * FROM children WHERE school=?",(school,))
    return c.fetchall()

def get_allergies():
    return connect().cursor().execute("SELECT id,name FROM allergies").fetchall()

def add_child_allergies(cid,aids):
    conn = connect()
    c = conn.cursor()
    for a in aids:
        c.execute("INSERT INTO child_allergies VALUES (?,?)",(cid,a))
    conn.commit()

def add_med(cid,name,dose,interval,unit):
    connect().cursor().execute("INSERT INTO meds VALUES (NULL,?,?,?,?,?)",(cid,name,dose,interval,unit))
    connect().commit()

def get_meds(cid):
    return connect().cursor().execute("SELECT * FROM meds WHERE child_id=?",(cid,)).fetchall()

def log_dose(mid,user):
    connect().cursor().execute("INSERT INTO logs VALUES (NULL,?,?,?)",(mid,datetime.now().isoformat(),user))
    connect().commit()

def get_last_dose_full(mid):
    return connect().cursor().execute("SELECT time_given,given_by FROM logs WHERE med_id=? ORDER BY time_given DESC LIMIT 1",(mid,)).fetchone()

def add_incident(cid,t,desc,user):
    connect().cursor().execute("INSERT INTO incidents VALUES (NULL,?,?,?,?,?)",(cid,t,desc,datetime.now().isoformat(),user))
    connect().commit()

def get_incidents(cid):
    return connect().cursor().execute("SELECT * FROM incidents WHERE child_id=? ORDER BY time DESC",(cid,)).fetchall()

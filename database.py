import sqlite3

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

    # MEDS (linked to child)
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
    
    conn.commit()
    conn.close()


# -------------------------
# CHILD FUNCTIONS
# -------------------------
def add_child(name, surname, dob, school):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO children (name, surname, dob, school)
        VALUES (?, ?, ?, ?)
    """, (name, surname, dob, school))
    conn.commit()
    conn.close()

def get_children():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM children")
    data = c.fetchall()
    conn.close()
    return data


# -------------------------
# MED FUNCTIONS
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

def get_meds_by_child(child_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM meds WHERE child_id=?", (child_id,))
    data = c.fetchall()
    conn.close()
    return data


# -------------------------
# LOG FUNCTIONS
# -------------------------
def log_dose(med_id, time, given_by):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO logs (med_id, time_given, given_by)
        VALUES (?, ?, ?)
    """, (med_id, time, given_by))
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
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

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

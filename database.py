import sqlite3

def connect():
    return sqlite3.connect("meds.db", check_same_thread=False)

def create_tables():
    conn = connect()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS meds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            dosage TEXT,
            interval INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            med_id INTEGER,
            time_given TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_med(name, dosage, interval):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO meds (name, dosage, interval) VALUES (?, ?, ?)",
              (name, dosage, interval))
    conn.commit()
    conn.close()


def get_meds():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM meds")
    data = c.fetchall()
    conn.close()
    return data


def log_dose(med_id, time):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO logs (med_id, time_given) VALUES (?, ?)",
              (med_id, time))
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
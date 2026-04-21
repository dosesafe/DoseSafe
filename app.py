import streamlit as st
from datetime import datetime, timedelta
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")

create_tables()

st.title("DoseSafe")
st.caption("Safe medicine tracking for children")

# -------------------------
# GET ALL STAFF (NO SCHOOL SELECT)
# -------------------------
conn = connect()
c = conn.cursor()
c.execute("SELECT name FROM staff")
staff_names = [s[0] for s in c.fetchall()]
conn.close()

# -------------------------
# LOGIN
# -------------------------
st.subheader("👩‍🏫 Staff Login")

staff_name = st.selectbox("Select Your Name", ["-- Select --"] + staff_names)
staff_pin = st.text_input("Enter PIN", type="password")

if staff_name == "-- Select --" or not staff_pin:
    st.stop()

# 🔐 VERIFY + GET SCHOOL
conn = connect()
c = conn.cursor()
c.execute("""
    SELECT school FROM staff
    WHERE name=? AND pin=?
""", (staff_name, staff_pin))

result = c.fetchone()
conn.close()

if not result:
    st.error("Invalid PIN")
    st.stop()

selected_school = result[0]

st.success(f"Logged in as {staff_name} ({selected_school})")

# -------------------------
# CHILDREN FILTERED BY SCHOOL
# -------------------------
children = get_children()
children = [c for c in children if c[4] == selected_school]

# -------------------------
# ADD CHILD
# -------------------------
with st.sidebar:
    st.header("👶 Add Child")

    name = st.text_input("First Name")
    surname = st.text_input("Surname")
    dob = st.date_input("DOB")

    allergy_data = get_allergies()
    allergy_map = {a[1]: a[0] for a in allergy_data}

    selected_allergies = st.multiselect("Allergies", list(allergy_map.keys()))

    if st.button("Add Child"):
        child_id = add_child(name, surname, str(dob), selected_school)

        if child_id:
            add_child_allergies(child_id, [allergy_map[a] for a in selected_allergies])
            st.success("Child added")
        else:
            st.warning("Child already exists")

        st.rerun()

if not children:
    st.info("No children added yet")
    st.stop()

# -------------------------
# SELECT CHILD
# -------------------------
child_options = {
    f"{c[1]} {c[2]} ({c[3]})": c[0]
    for c in children
}

selected = st.selectbox("Select Child", ["-- Select --"] + list(child_options.keys()))

if selected == "-- Select --":
    st.stop()

child_id = child_options[selected]

# -------------------------
# ALLERGIES
# -------------------------
allergies = get_child_allergies(child_id)
if allergies:
    st.error(f"⚠️ Allergies: {', '.join(allergies)}")

# -------------------------
# MEDICATION
# -------------------------
with st.expander("➕ Add Medicine"):
    med_name = st.text_input("Medicine")
    dose = st.text_input("Dosage")
    interval = st.number_input("Interval (hrs)", min_value=1)

    if st.button("Add Med"):
        add_med(child_id, med_name, dose, interval)
        st.rerun()

st.header("💊 Medications")

meds = get_meds_by_child(child_id)

for med in meds:
    med_id, _, name, dose, interval = med

    st.subheader(name)

    last = get_last_dose(med_id)

    if last:
        last_time = datetime.fromisoformat(last)
        next_time = last_time + timedelta(hours=interval)

        if datetime.now() < next_time:
            st.error("❌ Too soon")
        else:
            st.success("✅ Safe")

    if st.button(f"Give {name}", key=f"g{med_id}"):
        log_dose(med_id, datetime.now().isoformat(), staff_name)
        st.rerun()

# -------------------------
# INCIDENTS
# -------------------------
st.header("⚠️ Incidents")

with st.expander("Log Incident"):
    itype = st.selectbox("Type", ["Injury", "Illness", "Allergic Reaction", "Other"])
    desc = st.text_area("Description")

    if st.button("Log Incident"):
        add_incident(child_id, itype, desc, datetime.now().isoformat(), staff_name)
        st.rerun()

for i in get_incidents(child_id):
    t = datetime.fromisoformat(i[2])
    st.write(f"{i[0]} - {t.strftime('%H:%M')}")
    st.caption(i[1])

# -------------------------
# DAILY REPORT
# -------------------------
st.header("📤 Daily Report")

if st.button("Generate Report"):
    logs = get_today_logs(child_id)
    incs = get_today_incidents(child_id)

    report = []

    report.append("MEDICATION:")
    for l in logs:
        t = datetime.fromisoformat(l[1])
        report.append(f"{l[0]} {t.strftime('%H:%M')} ({l[2]})")

    report.append("")
    report.append("INCIDENTS:")
    for i in incs:
        t = datetime.fromisoformat(i[2])
        report.append(f"{i[0]} {t.strftime('%H:%M')} - {i[1]}")

    st.text_area("Report", "\n".join(report), height=300)

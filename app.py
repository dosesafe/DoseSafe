import streamlit as st
from datetime import datetime, timedelta
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")

create_tables()

st.title("DoseSafe")
st.caption("Safe medicine tracking for children")

# -------------------------
# ADMIN PANEL
# -------------------------
st.sidebar.header("⚙️ Admin Panel")

admin_mode = st.sidebar.checkbox("Enable Admin Mode")

if admin_mode:

    st.sidebar.subheader("➕ Add Staff")

    new_name = st.sidebar.text_input("Staff Name")
    new_pin = st.sidebar.text_input("PIN", type="password")
    new_school = st.sidebar.text_input("School Name")

    if st.sidebar.button("Add Staff"):
        if new_name and new_pin and new_school:
            try:
                add_staff(new_name, new_pin, new_school)
                st.sidebar.success("Staff added")
            except:
                st.sidebar.warning("Could not add staff")
        else:
            st.sidebar.warning("Fill all fields")

    # VIEW STAFF
    st.sidebar.subheader("👩‍🏫 Existing Staff")

    conn = connect()
    c = conn.cursor()
    c.execute("SELECT name, school FROM staff")
    staff_list = c.fetchall()
    conn.close()

    for s in staff_list:
        st.sidebar.write(f"{s[0]} ({s[1]})")

# -------------------------
# STAFF LOGIN
# -------------------------
conn = connect()
c = conn.cursor()
c.execute("SELECT name FROM staff")
staff_names = [s[0] for s in c.fetchall()]
conn.close()

st.subheader("👩‍🏫 Staff Login")

staff_name = st.selectbox("Select Your Name", ["-- Select --"] + staff_names)
staff_pin = st.text_input("Enter PIN", type="password")

if staff_name == "-- Select --" or not staff_pin:
    st.stop()

# VERIFY LOGIN + GET SCHOOL
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
# GET CHILDREN (FILTERED)
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
# SHOW ALLERGIES
# -------------------------
allergies = get_child_allergies(child_id)

if allergies:
    st.error(f"⚠️ Allergies: {', '.join(allergies)}")

# -------------------------
# DELETE CHILD
# -------------------------
confirm = st.checkbox("Confirm delete")

if st.button("🗑️ Delete Child"):
    if confirm:
        delete_child(child_id)
        st.success("Child deleted")
        st.rerun()
    else:
        st.warning("Please confirm deletion")

# -------------------------
# ADD MEDICINE
# -------------------------
with st.expander("➕ Add Medicine"):
    med_name = st.text_input("Medicine")
    dose = st.text_input("Dosage")
    interval = st.number_input("Interval (hrs)", min_value=1)

    if st.button("Add Medicine"):
        if not med_name or not dose:
            st.warning("Fill all fields")
        else:
            add_med(child_id, med_name, dose, interval)
            st.success("Added")
            st.rerun()

# -------------------------
# MEDICATION DISPLAY
# -------------------------
st.header("💊 Medications")

meds = get_meds_by_child(child_id)

if not meds:
    st.info("No medication added")

for med in meds:
    med_id, _, name, dose, interval = med

    st.subheader(name)
    st.caption(f"{dose} • every {interval} hrs")

    last = get_last_dose(med_id)

    if last:
        last_time = datetime.fromisoformat(last)
        next_time = last_time + timedelta(hours=interval)

        st.write(f"Last: {last_time.strftime('%H:%M')}")
        st.write(f"Next: {next_time.strftime('%H:%M')}")

        if datetime.now() < next_time:
            remaining = next_time - datetime.now()
            mins = int(remaining.total_seconds() / 60)
            st.error(f"❌ Too soon ({mins} min)")
        else:
            st.success("✅ Safe to give")

    else:
        st.info("No doses recorded")

    if st.button(f"💊 Give {name}", key=f"g{med_id}"):
        log_dose(med_id, datetime.now().isoformat(), staff_name)
        st.rerun()

    with st.expander("📋 Dose History"):
        logs = get_logs_by_med(med_id)

        if not logs:
            st.write("No history yet")
        else:
            for log in logs:
                t = datetime.fromisoformat(log[0])
                st.write(f"{t.strftime('%d %b %H:%M')} - {log[1]}")

    st.divider()

# -------------------------
# INCIDENT LOGGING
# -------------------------
st.header("⚠️ Incidents")

with st.expander("➕ Log Incident"):
    itype = st.selectbox("Type", ["Injury", "Illness", "Allergic Reaction", "Other"])
    desc = st.text_area("Description")

    if st.button("Log Incident"):
        if not desc:
            st.warning("Add description")
        else:
            add_incident(child_id, itype, desc, datetime.now().isoformat(), staff_name)
            st.success("Incident logged")
            st.rerun()

# INCIDENT HISTORY
incidents = get_incidents(child_id)

if incidents:
    st.subheader("📋 Incident History")

    for i in incidents:
        t = datetime.fromisoformat(i[2])
        st.write(f"⚠️ {i[0]} – {t.strftime('%d %b %H:%M')}")
        st.write(i[1])
        st.caption(f"Reported by {i[3]}")
        st.divider()

# -------------------------
# DAILY REPORT
# -------------------------
st.header("📤 Daily Report")

if st.button("Generate Report"):
    logs = get_today_logs(child_id)
    incs = get_today_incidents(child_id)

    report = []

    report.append("MEDICATION:")
    if logs:
        for l in logs:
            t = datetime.fromisoformat(l[1])
            report.append(f"- {l[0]} at {t.strftime('%H:%M')} ({l[2]})")
    else:
        report.append("- None")

    report.append("")
    report.append("INCIDENTS:")
    if incs:
        for i in incs:
            t = datetime.fromisoformat(i[2])
            report.append(f"- {i[0]} at {t.strftime('%H:%M')}")
            report.append(f"  {i[1]} (by {i[3]})")
    else:
        report.append("- None")

    st.text_area("Report Output", "\n".join(report), height=300)

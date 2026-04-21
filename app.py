import streamlit as st
from datetime import datetime, timedelta
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")

create_tables()

st.title("DoseSafe")
st.caption("Safe medicine tracking for children")

# SCHOOL
children = get_children()
schools = sorted(list(set([c[4] for c in children if c[4]])))

selected_school = st.selectbox("🏫 Select School", ["-- Select School --"] + schools)

if selected_school == "-- Select School --":
    st.stop()

# STAFF LOGIN
staff_list = get_staff_by_school(selected_school)
staff_names = [s[1] for s in staff_list]

staff_name = st.selectbox("Staff", ["-- Select --"] + staff_names)
staff_pin = st.text_input("PIN", type="password")

if staff_name == "-- Select --" or not staff_pin:
    st.stop()

if not verify_staff_pin(staff_name, staff_pin, selected_school):
    st.error("Invalid PIN")
    st.stop()

st.success(f"Logged in as {staff_name}")

# ADD CHILD
with st.sidebar:
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
            st.success("Added")
        else:
            st.warning("Exists")

        st.rerun()

# FILTER CHILDREN
children = [c for c in children if c[4] == selected_school]

child_options = {f"{c[1]} {c[2]} ({c[3]})": c[0] for c in children}

selected = st.selectbox("Select Child", ["-- Select --"] + list(child_options.keys()))

if selected == "-- Select --":
    st.stop()

child_id = child_options[selected]

# ALLERGIES
allergies = get_child_allergies(child_id)
if allergies:
    st.error(f"⚠️ Allergies: {', '.join(allergies)}")

# MEDS
with st.expander("Add Medicine"):
    name = st.text_input("Med")
    dose = st.text_input("Dose")
    interval = st.number_input("Interval", min_value=1)

    if st.button("Add Med"):
        add_med(child_id, name, dose, interval)
        st.rerun()

meds = get_meds_by_child(child_id)

for med in meds:
    med_id, _, name, dose, interval = med

    st.subheader(name)

    last = get_last_dose(med_id)

    if last:
        last_time = datetime.fromisoformat(last)
        next_time = last_time + timedelta(hours=interval)

        if datetime.now() < next_time:
            st.error("Too soon")
        else:
            st.success("Safe")

    if st.button(f"Give {name}", key=f"g{med_id}"):
        log_dose(med_id, datetime.now().isoformat(), staff_name)
        st.rerun()

# INCIDENTS
st.header("Incidents")

with st.expander("Log Incident"):
    itype = st.selectbox("Type", ["Injury", "Illness", "Allergic Reaction", "Other"])
    desc = st.text_area("Description")

    if st.button("Log"):
        add_incident(child_id, itype, desc, datetime.now().isoformat(), staff_name)
        st.rerun()

for i in get_incidents(child_id):
    t = datetime.fromisoformat(i[2])
    st.write(f"{i[0]} - {t.strftime('%H:%M')}")
    st.caption(i[1])

# DAILY REPORT
st.header("Daily Report")

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

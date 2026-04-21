import streamlit as st
from datetime import datetime
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")
create_tables()

st.sidebar.title("DoseSafe")

# -------------------------
# AUTO CREATE ADMIN (SAFE)
# -------------------------
if not verify_staff("Admin", "1234", "System"):
    add_staff("Admin", "1234", "System")
    set_subscription("System", "active", "2099-12-31")

# -------------------------
# LOGIN
# -------------------------
schools = get_schools()
school = st.sidebar.selectbox("School", ["--"] + schools)

if school == "--":
    st.stop()

staff_list = get_staff_by_school(school)
names = [s[1] for s in staff_list]

staff = st.sidebar.selectbox("Staff", ["--"] + names)
pin = st.sidebar.text_input("PIN", type="password")

if staff == "--" or not pin:
    st.stop()

if not verify_staff(staff, pin, school):
    st.error("Invalid login")
    st.stop()

# -------------------------
# SUBSCRIPTION AUTO FIX
# -------------------------
sub = get_subscription(school)

if not sub:
    set_subscription(school, "active", "2099-12-31")
    sub = get_subscription(school)

status, expiry = sub

if status != "active":
    st.error("Account inactive")
    st.stop()

if expiry:
    if datetime.now().date() > datetime.fromisoformat(expiry).date():
        st.error("Subscription expired")
        st.stop()

# -------------------------
# ADMIN CHECK
# -------------------------
is_admin = staff.lower() == "admin" and school.lower() == "system"

# -------------------------
# ADD CHILD
# -------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Add Child")

name = st.sidebar.text_input("First Name")
surname = st.sidebar.text_input("Surname")
dob = st.sidebar.date_input("DOB")

allergy_data = get_allergies()
allergy_map = {a[1]: a[0] for a in allergy_data}
selected_allergies = st.sidebar.multiselect("Allergies", list(allergy_map.keys()))

if st.sidebar.button("Add Child"):
    cid = add_child(name, surname, str(dob), school)
    if cid:
        add_child_allergies(cid, [allergy_map[a] for a in selected_allergies])
        st.rerun()

# -------------------------
# SELECT CHILD
# -------------------------
children = get_children(school)

child_map = {f"{c[1]} {c[2]}": c[0] for c in children}

selected = st.selectbox("Select Child", ["--"] + list(child_map.keys()))

if selected == "--":
    st.stop()

cid = child_map[selected]

# -------------------------
# TABS
# -------------------------
if is_admin:
    tab1, tab2, tab3, tab4 = st.tabs(["Medication","Incidents","Reports","Admin"])
else:
    tab1, tab2, tab3 = st.tabs(["Medication","Incidents","Reports"])

# -------------------------
# MEDICATION
# -------------------------
with tab1:
    for m in get_meds(cid):
        mid, _, name, dose, interval, unit = m

        st.subheader(name)
        st.caption(f"{dose} {unit} • every {interval} hrs")

        last = get_last_dose_full(mid)

        if last:
            t = datetime.fromisoformat(last[0])
            st.write(f"Last: {t.strftime('%H:%M')} ({last[1]})")

        if st.button(f"Give {name}", key=f"g{mid}"):
            log_dose(mid, staff)
            st.rerun()

    st.markdown("### Add Medication")

    lib = get_med_library()
    lib_map = {f"{m[1]} ({m[2]})": m for m in lib}

    sel = st.selectbox("Medication", list(lib_map.keys()))
    dose = st.text_input("Dosage")
    interval = st.number_input("Interval", min_value=1)

    if st.button("Add"):
        m = lib_map[sel]
        add_med(cid, m[1], dose, interval, m[2])
        st.rerun()

# -------------------------
# INCIDENTS
# -------------------------
with tab2:
    itype = st.selectbox("Type", ["Injury","Illness","Allergic Reaction","Other"])
    desc = st.text_input("Description")

    if st.button("Log"):
        add_incident(cid, itype, desc, staff)
        st.rerun()

    for i in get_incidents(cid):
        t = datetime.fromisoformat(i[4])
        st.write(f"{i[2]} - {t.strftime('%H:%M')}")

# -------------------------
# REPORTS
# -------------------------
with tab3:
    if st.button("Generate Report"):
        logs = get_today_logs(cid)
        incs = get_today_incidents(cid)

        out = []
        out.append("MEDICATION:")
        for l in logs:
            t = datetime.fromisoformat(l[1])
            out.append(f"{l[0]} {t.strftime('%H:%M')} {l[2]}")

        out.append("\nINCIDENTS:")
        for i in incs:
            t = datetime.fromisoformat(i[2])
            out.append(f"{i[0]} {t.strftime('%H:%M')}")

        st.text_area("Report", "\n".join(out), height=300)

# -------------------------
# ADMIN
# -------------------------
if is_admin:
    with tab4:
        st.subheader("Subscription Control")

        school_name = st.text_input("School Name")
        status = st.selectbox("Status", ["active","inactive"])
        expiry = st.date_input("Expiry")

        if st.button("Update Subscription"):
            set_subscription(school_name, status, str(expiry))
            st.success("Updated")

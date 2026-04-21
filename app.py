import streamlit as st
from datetime import datetime, timedelta
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")

create_tables()

ADMIN_PIN = "3434"  # change this

st.title("DoseSafe")
st.caption("Safe medicine tracking for children")

# -------------------------
# ADMIN PANEL (WITH TOGGLE)
# -------------------------
st.sidebar.header("⚙️ Admin")

if "admin_unlocked" not in st.session_state:
    st.session_state.admin_unlocked = False

if not st.session_state.admin_unlocked:
    admin_pin = st.sidebar.text_input("Enter Admin PIN", type="password")

    if admin_pin == ADMIN_PIN:
        st.session_state.admin_unlocked = True
        st.rerun()
else:
    if st.sidebar.button("🔒 Exit Admin"):
        st.session_state.admin_unlocked = False
        st.rerun()

    st.sidebar.success("Admin Mode")

    name = st.sidebar.text_input("Staff Name")
    pin = st.sidebar.text_input("PIN")
    school = st.sidebar.text_input("School")

    if st.sidebar.button("Add Staff"):
        if name and pin and school:
            add_staff(name, pin, school)
            st.sidebar.success("Staff added")
        else:
            st.sidebar.warning("Fill all fields")

    st.sidebar.subheader("👩‍🏫 Staff")

    for s in get_all_staff():
        sid, n, sch, active = s

        col1, col2 = st.sidebar.columns([3,1])

        with col1:
            status = "🟢" if active else "🔴"
            st.write(f"{status} {n} ({sch})")

        with col2:
            if active:
                if st.button("❌", key=f"d{sid}"):
                    set_staff_active(sid, 0)
                    st.rerun()
            else:
                if st.button("✅", key=f"e{sid}"):
                    set_staff_active(sid, 1)
                    st.rerun()

# -------------------------
# SCHOOL LOGIN FLOW
# -------------------------
schools = get_schools()

selected_school = st.selectbox("🏫 Select School", ["--"] + schools)

if selected_school == "--":
    st.stop()

staff_list = get_staff_by_school(selected_school)
staff_names = [s[1] for s in staff_list]

staff_name = st.selectbox("👩‍🏫 Select Your Name", ["--"] + staff_names)
staff_pin = st.text_input("Enter PIN", type="password")

if staff_name == "--" or not staff_pin:
    st.stop()

if not verify_staff(staff_name, staff_pin, selected_school):
    st.error("Invalid PIN")
    st.stop()

# -------------------------
# USER INFO (SIDEBAR)
# -------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("👤 Current User")
st.sidebar.markdown(f"### {staff_name}")
st.sidebar.caption(selected_school)

# -------------------------
# CHILD SECTION
# -------------------------
children = get_children(selected_school)

# ADD CHILD ALWAYS AVAILABLE
with st.expander("➕ Add Child", expanded=(len(children) == 0)):

    name = st.text_input("First Name")
    surname = st.text_input("Surname")
    dob = st.date_input("DOB")

    if st.button("Add Child"):
        cid = add_child(name, surname, str(dob), selected_school)

        if cid:
            st.success("Child added")
        else:
            st.warning("Child already exists")

        st.rerun()

# IF NO CHILDREN
if not children:
    st.info("Add a child to continue")
    st.stop()

# SELECT CHILD
child_map = {f"{c[1]} {c[2]}": c[0] for c in children}

selected = st.selectbox("Select Child", ["--"] + list(child_map.keys()))

if selected == "--":
    st.stop()

cid = child_map[selected]

# -------------------------
# MEDICATION
# -------------------------
st.header("💊 Medication")

meds = get_meds(cid)

for m in meds:
    mid, _, name, dose, interval = m

    st.subheader(name)
    st.caption(f"{dose} • every {interval} hrs")

    last = get_last_dose(mid)

    if last:
        last_time = datetime.fromisoformat(last)
        next_time = last_time + timedelta(hours=interval)

        if datetime.now() < next_time:
            diff = next_time - datetime.now()
            total_seconds = int(diff.total_seconds())

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60

            if hours > 0:
                st.error(f"❌ Too soon ({hours}h {minutes}m)")
            else:
                st.error(f"❌ Too soon ({minutes} min)")
        else:
            st.success("✅ Safe")

    else:
        st.info("No doses recorded")

    if st.button(f"💊 Give {name}", key=f"give_{mid}"):
        log_dose(mid, staff_name)
        st.rerun()

# ADD MED
with st.expander("➕ Add Medicine"):
    med_name = st.text_input("Medicine")
    dosage = st.text_input("Dosage")
    interval = st.number_input("Interval (hrs)", min_value=1)

    if st.button("Add Medicine"):
        if med_name and dosage:
            add_med(cid, med_name, dosage, interval)
            st.success("Added")
            st.rerun()
        else:
            st.warning("Fill all fields")

# -------------------------
# INCIDENTS
# -------------------------
st.header("⚠️ Incidents")

desc = st.text_input("Incident Description")

if st.button("Log Incident"):
    if desc:
        add_incident(cid, "General", desc, staff_name)
        st.success("Logged")
        st.rerun()
    else:
        st.warning("Enter description")

for i in get_incidents(cid):
    t = datetime.fromisoformat(i[4])
    st.write(f"{i[2]} – {t.strftime('%d %b %H:%M')}")
    st.caption(i[3])

# -------------------------
# DAILY REPORT
# -------------------------
st.header("📤 Daily Report")

if st.button("Generate Report"):

    logs = get_today_logs(cid)
    incs = get_today_incidents(cid)

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

import streamlit as st
from datetime import datetime, timedelta
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")

create_tables()

ADMIN_PIN = "9999"  # 🔒 change this later

st.title("DoseSafe")

# ---------------- ADMIN PANEL ----------------
st.sidebar.header("⚙️ Admin")

admin_access = st.sidebar.text_input("Admin PIN", type="password")

if admin_access == ADMIN_PIN:

    st.sidebar.success("Admin unlocked")

    name = st.sidebar.text_input("Name")
    pin = st.sidebar.text_input("PIN")
    school = st.sidebar.text_input("School")

    if st.sidebar.button("Add Staff"):
        add_staff(name, pin, school)
        st.sidebar.success("Added")

    st.sidebar.subheader("Staff")

    for s in get_all_staff():
        sid, n, sch, active = s

        st.sidebar.write(f"{n} ({sch})")

        if active:
            if st.sidebar.button("Disable", key=f"d{sid}"):
                set_staff_active(sid, 0)
                st.rerun()
        else:
            if st.sidebar.button("Enable", key=f"e{sid}"):
                set_staff_active(sid, 1)
                st.rerun()

# ---------------- LOGIN ----------------
school = st.selectbox("School", ["--"] + get_schools())
if school == "--":
    st.stop()

staff = get_staff_by_school(school)
names = [s[1] for s in staff]

user = st.selectbox("User", ["--"] + names)
pin = st.text_input("PIN", type="password")

if user == "--" or not pin:
    st.stop()

if not verify_staff(user, pin, school):
    st.error("Invalid login")
    st.stop()

st.sidebar.markdown(f"### {user}")
st.sidebar.caption(school)

# ---------------- CHILD ----------------
children = get_children(school)

child_map = {f"{c[1]} {c[2]}": c[0] for c in children}

selected = st.selectbox("Child", ["--"] + list(child_map.keys()))
if selected == "--":
    st.stop()

cid = child_map[selected]

# ---------------- MEDS ----------------
for m in get_meds(cid):
    mid, _, name, dose, interval = m

    st.subheader(name)

    last = get_last_dose(mid)

    if last:
        last = datetime.fromisoformat(last)
        next_time = last + timedelta(hours=interval)

        if datetime.now() < next_time:
            diff = next_time - datetime.now()
            h = diff.seconds // 3600
            m = (diff.seconds % 3600) // 60
            st.error(f"{h}h {m}m remaining")
        else:
            st.success("Safe")

    if st.button(f"Give {name}", key=mid):
        log_dose(mid, user)
        st.rerun()

# ---------------- INCIDENTS ----------------
st.header("Incidents")

desc = st.text_input("Description")
if st.button("Log Incident"):
    add_incident(cid, "General", desc, user)
    st.rerun()

for i in get_incidents(cid):
    st.write(i[2])

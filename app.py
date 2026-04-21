import streamlit as st
from datetime import datetime, timedelta
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")
create_tables()

st.sidebar.title("DoseSafe")

mode = st.sidebar.selectbox("Login Type", ["School Staff","Admin","Parent"])

# ---------------- DISCLAIMER ----------------
def show_disclaimer(user, role):
    st.warning("""
IMPORTANT DISCLAIMER

DoseSafe is a medication tracking tool only.
All medication must be prescribed by a licensed doctor.

DoseSafe is NOT liable for:
- Incorrect medication
- Dosage errors
- Reactions or harm

You accept full responsibility.
""")

    if not has_accepted_disclaimer(user, role):
        if st.checkbox("I accept"):
            if st.button("Continue"):
                accept_disclaimer(user, role)
                st.rerun()
        st.stop()

# ================= ADMIN =================
if mode == "Admin":
    u = st.sidebar.text_input("Admin Username")
    admin_pin = st.sidebar.text_input("PIN", type="password", key="admin_pin")

    if u != "Admin" or admin_pin != "1234":
        st.stop()

    show_disclaimer(u, "admin")

st.title("Admin Panel")

# -------------------------
# CREATE SCHOOL + STAFF
# -------------------------
st.subheader("➕ Create School & First Staff")

new_school = st.text_input("School Name")
new_staff = st.text_input("Staff Name")
new_pin = st.text_input("Staff PIN")

if st.button("Create School"):
    if new_school and new_staff and new_pin:
        add_staff(new_staff, new_pin, new_school)
        set_subscription(new_school, "active", "2099-12-31")
        st.success("School + Staff created")
        st.rerun()
    else:
        st.warning("Fill all fields")

# -------------------------
# STAFF LIST + ENABLE/DISABLE
# -------------------------
st.subheader("👩‍🏫 Staff Management")

staff_list = get_all_staff()

if not staff_list:
    st.warning("No staff yet")
else:
    for s in staff_list:
        sid, name, school, active = s

        col1, col2, col3 = st.columns([3,2,2])

        with col1:
            st.write(f"{name} ({school})")

        with col2:
            st.write("Active" if active else "Disabled")

        with col3:
            if active:
                if st.button("Disable", key=f"disable_{sid}"):
                    set_staff_active(sid, 0)
                    st.rerun()
            else:
                if st.button("Enable", key=f"enable_{sid}"):
                    set_staff_active(sid, 1)
                    st.rerun()

# -------------------------
# SUBSCRIPTIONS
# -------------------------
st.subheader("💳 Subscription Control")

schools = get_schools()

if not schools:
    st.warning("No schools available")
else:
    selected_school = st.selectbox("Select School", schools)

    status = st.selectbox("Status", ["active", "inactive"])

    if st.button("Update Subscription"):
        set_subscription(selected_school, status, "2099-12-31")
        st.success("Subscription updated")

# ================= PARENT =================
if mode == "Parent":
    n = st.sidebar.text_input("Name")
    parent_pin = st.sidebar.text_input("PIN", type="password", key="parent_pin")

    r = verify_parent(n, parent_pin)
    if not r:
        st.stop()

    show_disclaimer(n,"parent")

    cid = r[0]

    st.title("Parent Dashboard")

    for m in get_meds(cid):
        st.write(m[2])

    st.stop()

# ================= STAFF =================
school = st.sidebar.selectbox("School", get_schools())
staff = st.sidebar.text_input("Name")
staff_pin = st.sidebar.text_input("PIN", type="password", key="staff_pin")

if not verify_staff(staff, staff_pin, school):
    st.stop()

show_disclaimer(staff,"staff")

st.title("DoseSafe")

children = get_children(school)
cmap = {f"{c[1]} {c[2]}":c[0] for c in children}

sel = st.selectbox("Child", cmap.keys())
cid = cmap[sel]

# MEDS
for m in get_meds(cid):
    mid,_,name,dose,interval,unit = m
    st.subheader(name)

    last = get_last_dose_full(mid)

    if last:
        last_time = datetime.fromisoformat(last[0])
        next_time = last_time + timedelta(hours=interval)

        st.write(f"Last: {last_time.strftime('%H:%M')}")
        st.write(f"Next: {next_time.strftime('%H:%M')}")

    if st.button(f"Give {name}", key=mid):
        log_dose(mid,staff)
        st.rerun()

# ADD MED
st.markdown("### Add Medication")

med_mode = st.radio("Type",["Library","Custom"])

if med_mode=="Library":
    lib=get_med_library()
    lmap={f"{x[1]} ({x[2]})":x for x in lib}

    sel=st.selectbox("Medication",list(lmap.keys()))
    dose=st.text_input("Dosage")
    interval=st.number_input("Interval",1)

    if st.button("Add"):
        m=lmap[sel]
        add_med(cid,m[1],dose,interval,m[2])
        st.rerun()

else:
    n=st.text_input("Name")
    u=st.selectbox("Unit",["ml","unit","n/a"])
    d=st.text_input("Dose")
    i=st.number_input("Interval",1)

    if st.button("Add Custom"):
        add_med(cid,n,d,i,u)
        add_med_to_library(n,u)
        st.rerun()

# INCIDENTS
st.markdown("### Incidents")

t=st.selectbox("Type",["Injury","Illness","Allergic Reaction"])
d=st.text_input("Description")

if st.button("Log Incident"):
    add_incident(cid,t,d,staff)
    st.rerun()

# REPORT
if st.button("Generate Report"):
    logs=get_today_logs(cid)
    incs=get_today_incidents(cid)

    out=[]
    for l in logs:
        out.append(f"{l[0]} {l[1]} {l[2]}")

    for i in incs:
        out.append(f"{i[0]} {i[2]}")

    st.text_area("Report","\n".join(out),height=300)

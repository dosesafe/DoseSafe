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

DoseSafe is a medication tracking tool only. All medication must be prescribed by a licensed doctor.

DoseSafe is NOT liable for:
- Incorrect medication
- Dosage errors
- Reactions or harm

You accept full responsibility.
""")

    if not has_accepted_disclaimer(user, role):
        if st.checkbox("I accept", key=f"disc_{role}"):
            if st.button("Continue", key=f"cont_{role}"):
                accept_disclaimer(user, role)
                st.rerun()
        st.stop()

# ================= ADMIN =================
if mode == "Admin":
    u = st.sidebar.text_input("Admin Username", key="admin_user")
    admin_pin = st.sidebar.text_input("PIN", type="password", key="admin_pin")

    if u != "Admin" or admin_pin != "1234":
        st.stop()

    show_disclaimer(u, "admin")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    st.title("Admin Panel")

    # CREATE SCHOOL + STAFF
    st.subheader("➕ Create School & Staff")
    new_school = st.text_input("School Name")
    new_staff = st.text_input("Staff Name")
    new_pin = st.text_input("Staff PIN")

    if st.button("Create School"):
        if new_school and new_staff and new_pin:
            add_staff(new_staff, new_pin, new_school)
            set_subscription(new_school, "active", "2099-12-31")
            st.success("School + Staff created")
            st.rerun()

    # STAFF MANAGEMENT
    st.subheader("👩‍🏫 Staff Management")

    staff_list = get_all_staff()

    for s in staff_list:
        sid, name, school, active = s
        col1, col2, col3, col4 = st.columns([3,2,2,2])

        col1.write(f"{name} ({school})")
        col2.write("Active" if active else "Disabled")

        if active:
            if col3.button("Disable", key=f"disable_{sid}"):
                set_staff_active(sid, 0)
                st.rerun()
        else:
            if col3.button("Enable", key=f"enable_{sid}"):
                set_staff_active(sid, 1)
                st.rerun()

        # 🔥 RESET PIN
        new_pin_reset = col4.text_input("New PIN", key=f"pin_{sid}")
        if col4.button("Update PIN", key=f"updatepin_{sid}"):
            update_staff_pin(sid, new_pin_reset)
            st.success("PIN updated")

    # SUBSCRIPTIONS
    st.subheader("💳 Subscription Control")

    schools = get_schools()

    if schools:
        selected_school = st.selectbox("Select School", schools)
        status = st.selectbox("Status", ["active", "inactive"])
        expiry_date = st.date_input("Expiry Date")

        if st.button("Update Subscription"):
            set_subscription(selected_school, status, str(expiry_date))
            st.success("Updated")

    st.markdown("### 📋 Current Subscriptions")
    for s in get_all_subscriptions():
        st.write(s)

    st.stop()

# ================= PARENT =================
elif mode == "Parent":

    parent_mode = st.sidebar.radio("Parent Access", ["Login", "Register"])

    if parent_mode == "Login":
        name = st.sidebar.text_input("Name")
        parent_pin = st.sidebar.text_input("PIN", type="password")

        r = verify_parent(name, parent_pin)
        if not r:
            st.stop()

        show_disclaimer(name, "parent")

        if st.sidebar.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

        cid = r[0]
        parent_plan = "free"

        st.title("Parent Dashboard")

        st.markdown("### 💊 Medications")
        for m in get_meds(cid):
            st.write(f"{m[2]} — {m[3]} every {m[4]} hrs")

        st.markdown("### ⚠️ Incidents")
        for i in get_today_incidents(cid):
            st.write(f"{i[1]} — {i[2]}")

        if st.button("Generate Report"):
            logs = get_today_logs(cid)
            incs = get_today_incidents(cid)

            out = []
            for l in logs:
                out.append(f"{l[0]} {l[1]} {l[2]}")
            for i in incs:
                out.append(f"{i[0]} {i[2]}")

            st.text_area("Report", "\n".join(out), height=300)

        if parent_plan == "free":
            st.info("Upgrade to add medications")

        st.stop()

    else:
        st.title("Register")

        school = st.selectbox("School", get_schools())
        children = get_children(school)

        if not children:
            st.stop()

        cmap = {f"{c[1]} {c[2]} ({c[3]})": c[0] for c in children}

        sel = st.selectbox("Child", list(cmap.keys()))
        name = st.text_input("Name")
        pin = st.text_input("PIN")

        if st.button("Create Account"):
            add_parent(name, pin, cmap[sel])
            st.success("Created")

        st.stop()

# ================= STAFF =================
elif mode == "School Staff":

    school = st.sidebar.selectbox("School", get_schools())
    staff = st.sidebar.text_input("Name")
    pin = st.sidebar.text_input("PIN", type="password")

    if not verify_staff(staff, pin, school):
        st.stop()

    sub = get_subscription(school)
    if not sub:
        st.stop()

    status, expiry = sub
    if status != "active":
        st.stop()

    show_disclaimer(staff, "staff")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    st.title("DoseSafe")

    # ADD CHILD
    st.markdown("### 👶 Add Child")

    name = st.text_input("First Name")
    surname = st.text_input("Surname")
    dob = st.date_input("DOB")

    if st.button("Add Child"):
        add_child(name, surname, str(dob), school)
        st.success("Child added")
        st.rerun()

    # CHILD SELECT
    children = get_children(school)
    if not children:
        st.stop()

    cmap = {f"{c[1]} {c[2]} ({c[3]})": c[0] for c in children}
    sel = st.selectbox("Child", list(cmap.keys()))
    cid = cmap[sel]

    # MEDS
    for m in get_meds(cid):
        mid,_,name,dose,interval,unit = m
        st.subheader(name)

        last = get_last_dose_full(mid)
        now = datetime.now()

        if last:
            last_time = datetime.fromisoformat(last[0])
            next_time = last_time + timedelta(hours=interval)

            st.write(f"Last: {last_time.strftime('%H:%M')} ({last[1]})")
            st.write(f"Next: {next_time.strftime('%H:%M')}")

            if now < next_time:
                st.error("Too soon")
                st.button(f"Give {name}", key=f"block_{mid}", disabled=True)
            else:
                if st.button(f"Give {name}", key=f"give_{mid}"):
                    log_dose(mid, staff)
                    st.rerun()
        else:
            if st.button(f"Give {name}", key=f"first_{mid}"):
                log_dose(mid, staff)
                st.rerun()

    # ADD MED
    st.markdown("### ➕ Add Medication")

    med_mode = st.radio("Type",["Library","Custom"])

    if med_mode == "Library":
        lib = get_med_library()
        lmap = {f"{x[1]} ({x[2]})": x for x in lib}

        sel_med = st.selectbox("Medication", list(lmap.keys()))
        dose = st.text_input("Dosage")
        interval = st.number_input("Interval",1)

        if st.button("Add Med"):
            m = lmap[sel_med]
            add_med(cid, m[1], dose, interval, m[2])
            st.rerun()
    else:
        n = st.text_input("Name")
        u = st.selectbox("Unit",["ml","unit","n/a"])
        d = st.text_input("Dose")
        i = st.number_input("Interval",1)

        if st.button("Add Custom"):
            add_med(cid, n, d, i, u)
            add_med_to_library(n, u)
            st.rerun()

    # INCIDENTS
    st.markdown("### ⚠️ Incidents")

    t = st.selectbox("Type",["Injury","Illness","Allergic Reaction"])
    d = st.text_input("Description")

    if st.button("Log Incident"):
        add_incident(cid, t, d, staff)
        st.rerun()

    # REPORT
    if st.button("Generate Report"):
        logs = get_today_logs(cid)
        incs = get_today_incidents(cid)

        out = []
        for l in logs:
            out.append(f"{l[0]} {l[1]} {l[2]}")
        for i in incs:
            out.append(f"{i[0]} {i[2]}")

        st.text_area("Report", "\n".join(out), height=300)

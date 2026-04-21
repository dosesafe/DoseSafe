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

    if st.sidebar.button("🚪 Logout", key="admin_logout"):
        st.session_state.clear()
        st.rerun()

    st.title("Admin Panel")

    # CREATE SCHOOL + STAFF
    st.subheader("➕ Create School & Staff")
    new_school = st.text_input("School Name", key="new_school")
    new_staff = st.text_input("Staff Name", key="new_staff")
    new_pin = st.text_input("Staff PIN", key="new_pin")

    if st.button("Create School", key="create_school"):
        if new_school and new_staff and new_pin:
            add_staff(new_staff, new_pin, new_school)
            set_subscription(new_school, "active", "2099-12-31")
            st.success("School + Staff created")
            st.rerun()
        else:
            st.warning("Fill all fields")

    # STAFF MANAGEMENT
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

    # SUBSCRIPTIONS
    st.subheader("💳 Subscription Control")

    schools = get_schools()

    if schools:
        selected_school = st.selectbox("Select School", schools, key="sub_school")
        status = st.selectbox("Status", ["active", "inactive"], key="sub_status")
        expiry_date = st.date_input("Expiry Date", key="sub_expiry")

        if st.button("Update Subscription", key="update_sub"):
            set_subscription(selected_school, status, str(expiry_date))
            st.success(f"Updated: {selected_school} → {status}")

    st.markdown("### 📋 Current Subscriptions")

    subs = get_all_subscriptions()
    if not subs:
        st.info("No subscriptions yet")
    else:
        for s in subs:
            school, status, expiry = s
            st.write(f"🏫 {school} | {status} | expires: {expiry}")

    st.stop()

# ================= PARENT =================
elif mode == "Parent":
    name = st.sidebar.text_input("Name", key="parent_name")
    parent_pin = st.sidebar.text_input("PIN", type="password", key="parent_pin")

    r = verify_parent(name, parent_pin)
    if not r:
        st.stop()

    show_disclaimer(name, "parent")

    if st.sidebar.button("🚪 Logout", key="parent_logout"):
        st.session_state.clear()
        st.rerun()

    parent_plan = "free"  # 🔥 CURRENT MODEL

    cid = r[0]

    st.title("Parent Dashboard")

    # VIEW MEDS
    st.markdown("### 💊 Medications")
    for m in get_meds(cid):
        mid, _, name, dose, interval, unit = m
        st.write(f"{name} — {dose} every {interval} hrs")

    # VIEW INCIDENTS
    st.markdown("### ⚠️ Incidents")
    incs = get_today_incidents(cid)
    for i in incs:
        st.write(f"{i[1]} — {i[2]}")

    # REPORT
    st.markdown("### 📄 Report")
    if st.button("Generate Report", key="parent_report"):
        logs = get_today_logs(cid)
        incs = get_today_incidents(cid)

        out = []
        for l in logs:
            out.append(f"{l[0]} {l[1]} {l[2]}")

        for i in incs:
            out.append(f"{i[0]} {i[2]}")

        st.text_area("Report", "\n".join(out), height=300)

    # 🔒 LOCKED FEATURES
    st.markdown("### ➕ Add Medication")

    if parent_plan == "free":
        st.info("Upgrade to add medications and track doses at home")
        st.button("Upgrade (Coming Soon)", key="upgrade_btn")

    st.stop()

# ================= STAFF =================
elif mode == "School Staff":

    school = st.sidebar.selectbox("School", get_schools(), key="staff_school")
    staff = st.sidebar.text_input("Name", key="staff_name")
    staff_pin = st.sidebar.text_input("PIN", type="password", key="staff_pin")

    if not verify_staff(staff, staff_pin, school):
        st.stop()

    sub = get_subscription(school)
    if not sub:
        st.error("No subscription")
        st.stop()

    status, expiry = sub

    if status != "active":
        st.error("Inactive subscription")
        st.stop()

    if datetime.now().date() > datetime.fromisoformat(expiry).date():
        st.error("Subscription expired")
        st.stop()

    show_disclaimer(staff, "staff")

    if st.sidebar.button("🚪 Logout", key="staff_logout"):
        st.session_state.clear()
        st.rerun()

    st.title("DoseSafe")

    # CHILDREN
    children = get_children(school)

    if not children:
        st.warning("No children yet")
        st.stop()

    cmap = {
        f"{c[1]} {c[2]} ({c[3]})": c[0]
        for c in children
    }

    child_names = list(cmap.keys())
    sel_child = st.selectbox("Child", child_names, key="child_select")

    if sel_child not in cmap:
        st.stop()

    cid = cmap[sel_child]

    # MEDS
for m in get_meds(cid):
    mid,_,name,dose,interval,unit = m
    st.subheader(name)

    last = get_last_dose_full(mid)
    now = datetime.now()

    if last:
        last_time = datetime.fromisoformat(last[0])
        next_time = last_time + timedelta(hours=interval)

        st.write(f"🕒 Last: {last_time.strftime('%H:%M')} (by {last[1]})")
        st.write(f"⏭️ Next: {next_time.strftime('%H:%M')}")

        if now < next_time:
            remaining = next_time - now

            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60

            st.error(f"❌ Too soon ({hours}h {minutes}m remaining)")

            # 🚫 HARD BLOCK
            st.button(f"💊 Give {name}", key=f"blocked_{mid}", disabled=True)

        else:
            st.success("✅ Safe to give")

            if st.button(f"💊 Give {name}", key=f"give_{mid}"):
                log_dose(mid, staff)
                st.rerun()

    else:
        st.info("No doses recorded yet")

        if st.button(f"💊 Give {name}", key=f"first_{mid}"):
            log_dose(mid, staff)
            st.rerun()

    # ADD MED
    st.markdown("### ➕ Add Medication")

    med_mode = st.radio("Type",["Library","Custom"], key="med_mode")

    if med_mode == "Library":
        lib = get_med_library()
        lmap = {f"{x[1]} ({x[2]})": x for x in lib}

        sel_med = st.selectbox("Medication", list(lmap.keys()), key="lib_med")
        dose = st.text_input("Dosage", key="lib_dose")
        interval = st.number_input("Interval",1, key="lib_int")

        if st.button("Add", key="add_lib"):
            m = lmap[sel_med]
            add_med(cid, m[1], dose, interval, m[2])
            st.rerun()

    else:
        n = st.text_input("Name", key="c_name")
        u = st.selectbox("Unit",["ml","unit","n/a"], key="c_unit")
        d = st.text_input("Dose", key="c_dose")
        i = st.number_input("Interval",1, key="c_int")

        if st.button("Add Custom", key="add_custom"):
            add_med(cid, n, d, i, u)
            add_med_to_library(n, u)
            st.rerun()

    # INCIDENTS
    st.markdown("### ⚠️ Incidents")

    t = st.selectbox("Type",["Injury","Illness","Allergic Reaction"], key="inc_type")
    d = st.text_input("Description", key="inc_desc")

    if st.button("Log Incident", key="inc_btn"):
        add_incident(cid, t, d, staff)
        st.rerun()

    # REPORT
    st.markdown("### 📄 Report")

    if st.button("Generate Report", key="report_btn"):
        logs = get_today_logs(cid)
        incs = get_today_incidents(cid)

        out = []
        for l in logs:
            out.append(f"{l[0]} {l[1]} {l[2]}")

        for i in incs:
            out.append(f"{i[0]} {i[2]}")

        st.text_area("Report", "\n".join(out), height=300)

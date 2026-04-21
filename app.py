import streamlit as st
from datetime import datetime, timedelta
from database import *
import pandas as pd

st.set_page_config(
    page_title="DoseSafe",
    page_icon="DoseSafe.png",
    layout="centered"
)

st.sidebar.image("DoseSafe.png", use_container_width=True)
st.sidebar.markdown("---")

create_tables()

# ---------------- SESSION RESET ----------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "role" not in st.session_state:
    st.session_state["role"] = None

# ---------------- SIDEBAR ----------------


mode = st.selectbox(
    "Select Access",
    ["School Staff","Admin","Parent"]
)

# ---------------- LOGOUT ----------------
def logout():
    st.session_state.clear()
    st.rerun()

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

Use at your own risk.
""")

    if not has_accepted_disclaimer(user, role):
        if st.checkbox("I accept", key=f"disc_{role}"):
            if st.button("Continue", key=f"cont_{role}"):
                accept_disclaimer(user, role)
                st.rerun()
        st.stop()

# ================= ADMIN =================
if mode == "Admin":

    if not st.session_state.get("logged_in"):

        u = st.sidebar.text_input("Admin Username", key="admin_user")
        p = st.sidebar.text_input("PIN", type="password", key="admin_pin")

        if st.sidebar.button("Login"):
            if u == "Admin" and p == "1234":
                st.session_state["logged_in"] = True
                st.session_state["role"] = "admin"
                st.session_state["user"] = u
                st.rerun()
            else:
                st.sidebar.error("Invalid login")

        st.stop()

    show_disclaimer(st.session_state["user"], "admin")

    if st.sidebar.button("🚪 Logout"):
        logout()

    st.title("Admin Panel")

    # ---------- CREATE SCHOOL ----------
    st.subheader("➕ Create School & Staff")
    school = st.text_input("School Name")
    staff = st.text_input("Staff Name")
    pin = st.text_input("Staff PIN")

    if st.button("Create School"):
        add_staff(staff, pin, school)
        set_subscription(school, "active", "2099-12-31")
        st.success("Created")
        st.rerun()

    # ---------- STAFF ----------
    st.subheader("👩‍🏫 Staff Management")
    for s in get_all_staff():
        sid, name, school, active = s
        col1, col2, col3, col4 = st.columns([3,2,2,2])

        col1.write(f"{name} ({school})")
        col2.write("Active" if active else "Disabled")

        if active:
            if col3.button("Disable", key=f"d_{sid}"):
                set_staff_active(sid, 0)
                st.rerun()
        else:
            if col3.button("Enable", key=f"e_{sid}"):
                set_staff_active(sid, 1)
                st.rerun()

        new_pin = col4.text_input("New PIN", key=f"pin_{sid}")
        if col4.button("Update", key=f"up_{sid}"):
            update_staff_pin(sid, new_pin)
            st.success("PIN updated")

    # ---------- SUBSCRIPTIONS ----------
    st.subheader("💳 Subscriptions")

    schools = get_schools()
    if schools:
        s = st.selectbox("School", schools)
        status = st.selectbox("Status", ["active","inactive"])
        expiry = st.date_input("Expiry")

        if st.button("Update Subscription"):
            set_subscription(s, status, str(expiry))
            st.success("Updated")

    st.dataframe(pd.DataFrame(get_all_subscriptions(), columns=["School","Status","Expiry"]))

    # ---------- ALLERGIES ----------
    st.subheader("🧬 Allergy Management")

    new_allergy = st.text_input("Add Allergy")

    if st.button("Add Allergy"):
        add_allergy(new_allergy)
        st.success("Added")
        st.rerun()

    for a in get_allergies():
        st.write(f"• {a[1]}")

# ================= STAFF =================
elif mode == "School Staff":

    if not st.session_state.get("logged_in"):

        school = st.sidebar.selectbox("School", get_schools())
        name = st.sidebar.text_input("Name")
        pin = st.sidebar.text_input("PIN", type="password")

        if st.sidebar.button("Login"):
            if verify_staff(name, pin, school):
                st.session_state["logged_in"] = True
                st.session_state["role"] = "staff"
                st.session_state["school"] = school
                st.session_state["user"] = name
                st.rerun()
            else:
                st.sidebar.error("Invalid login")

        st.stop()

    show_disclaimer(st.session_state["user"], "staff")

    if st.sidebar.button("🚪 Logout"):
        logout()

    school = st.session_state["school"]
    staff = st.session_state["user"]

    st.title("DoseSafe")

    tab1, tab2, tab3, tab4 = st.tabs(["👶 Children","💊 Medication","⚠️ Incidents","📄 Reports"])

    # ---------- CHILDREN ----------
    with tab1:

        name = st.text_input("First Name")
        surname = st.text_input("Surname")
        dob = st.date_input("DOB")

        if st.button("Add Child"):
            add_child(name, surname, str(dob), school)
            st.rerun()

        children = get_children(school)

        cmap = {f"{c[1]} {c[2]} ({c[3]})": c[0] for c in children}
        sel = st.selectbox("Child", list(cmap.keys()))
        cid = cmap[sel]
        st.session_state["cid"] = cid

        # ---------- ALLERGIES ----------
        st.subheader("⚠️ Allergies")

        allergies = get_allergies()
        options = {a[1]: a[0] for a in allergies}

        selected = st.multiselect("Select Allergies", list(options.keys()))

        if st.button("Save Allergies"):
            set_child_allergies(cid, [options[s] for s in selected])
            st.success("Saved")

    # ---------- MEDICATION ----------
    with tab2:

        cid = st.session_state.get("cid")

        for m in get_meds(cid):
            mid,_,name,dose,interval,unit = m

            st.subheader(name)

            # 🚨 ALLERGY WARNING
            warnings = check_med_allergy(name, cid)
            if warnings:
                st.error(f"🚨 Allergy Warning: {', '.join(warnings)}")

            last = get_last_dose_full(mid)
            now = datetime.now()

            if last:
                last_time = datetime.fromisoformat(last[0])
                next_time = last_time + timedelta(hours=interval)

                st.write(f"Last: {last_time.strftime('%H:%M')} ({last[1]})")
                st.write(f"Next: {next_time.strftime('%H:%M')}")

                if now < next_time:
                    rem = next_time - now
                    h = rem.seconds//3600
                    m = (rem.seconds%3600)//60
                    st.error(f"Too soon ({h}h {m}m)")
                else:
                    if st.button("Give", key=f"g_{mid}"):
                        log_dose(mid, staff)
                        st.rerun()

    # ---------- INCIDENTS ----------
    with tab3:
        cid = st.session_state.get("cid")

        t = st.selectbox("Type",["Injury","Illness","Allergic Reaction"])
        d = st.text_input("Description")

        if st.button("Log Incident"):
            add_incident(cid, t, d, staff)
            st.success("Logged")

    # ---------- REPORT ----------
    with tab4:
        cid = st.session_state.get("cid")

        if st.button("Generate Report"):
            logs = get_today_logs(cid)
            incs = get_today_incidents(cid)

            out = []

            for l in logs:
                out.append(f"💊 {l[0]} — {datetime.fromisoformat(l[1]).strftime('%H:%M')} ({l[2]})")

            for i in incs:
                out.append(f"⚠️ {datetime.fromisoformat(i[0]).strftime('%H:%M')} — {i[2]}")

            st.text_area("Report", "\n".join(out), height=300)

# ================= PARENT =================
elif mode == "Parent":

    name = st.sidebar.text_input("Name")
    pin = st.sidebar.text_input("PIN", type="password")

    r = verify_parent(name, pin)

    if not r:
        st.warning("Invalid login")
        st.stop()

    show_disclaimer(name, "parent")

    if st.sidebar.button("🚪 Logout"):
        logout()

    cid = r[0]

    st.title("Parent Dashboard")

    if st.button("Generate Report"):
        logs = get_today_logs(cid)
        incs = get_today_incidents(cid)

        out = []

        for l in logs:
            out.append(f"💊 {l[0]} — {datetime.fromisoformat(l[1]).strftime('%H:%M')} ({l[2]})")

        for i in incs:
            out.append(f"⚠️ {datetime.fromisoformat(i[0]).strftime('%H:%M')} — {i[2]}")

        st.text_area("Report", "\n".join(out), height=300)

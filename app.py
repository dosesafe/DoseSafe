import streamlit as st
from datetime import datetime, timedelta
from database import *
import pandas as pd

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="DoseSafe",
    page_icon="DoseSafe.png",
    layout="centered"
)

# ---------------- LOGO ----------------
st.sidebar.image("DoseSafe.png", use_container_width=True)
st.sidebar.markdown("---")

create_tables()

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "role" not in st.session_state:
    st.session_state["role"] = None

# ---------------- LOGOUT ----------------
def logout():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ---------------- LOGIN MODE ----------------
if not st.session_state["logged_in"]:
    mode = st.selectbox("Select Access", ["School Staff", "Admin", "Parent"])
else:
    mode = st.session_state["role"]

# ---------------- DISCLAIMER ----------------
def show_disclaimer(user, role):
    st.warning("""
IMPORTANT DISCLAIMER

DoseSafe is a tracking tool only.
All medication must be prescribed by a doctor.

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

    if not st.session_state["logged_in"]:

        st.subheader("Admin Login")

        u = st.text_input("Username")
        p = st.text_input("PIN", type="password")

        if st.button("Login"):
            if u == "Admin" and p == "1234":
                st.session_state["logged_in"] = True
                st.session_state["role"] = "Admin"
                st.session_state["user"] = u
                st.rerun()
            else:
                st.error("Invalid login")

        st.stop()

    show_disclaimer(st.session_state["user"], "admin")

   if st.sidebar.button("🚪 Logout"):
    logout()

    st.title("Admin Panel")

    # CREATE SCHOOL
    st.subheader("Create School & Staff")
    school = st.text_input("School")
    staff = st.text_input("Staff")
    pin = st.text_input("PIN")

    if st.button("Create"):
        add_staff(staff, pin, school)
        set_subscription(school, "active", "2099-12-31")
        st.success("Created")
        st.rerun()

    # STAFF MANAGEMENT
    st.subheader("Staff")
    for s in get_all_staff():
        sid, name, school, active = s

        col1, col2, col3 = st.columns(3)
        col1.write(name)
        col2.write("Active" if active else "Disabled")

        if col3.button("Toggle", key=sid):
            set_staff_active(sid, 0 if active else 1)
            st.rerun()

    # SUBSCRIPTIONS
    st.subheader("Subscriptions")

    schools = get_schools()
    if schools:
        s = st.selectbox("School", schools)
        status = st.selectbox("Status", ["active", "inactive"])
        expiry = st.date_input("Expiry")

        if st.button("Update"):
            set_subscription(s, status, str(expiry))
            st.success("Updated")

    st.dataframe(pd.DataFrame(get_all_subscriptions(), columns=["School","Status","Expiry"]))

    # ALLERGIES
    st.subheader("Allergies")

    new_a = st.text_input("Add Allergy")
    if st.button("Add"):
        add_allergy(new_a)
        st.rerun()

    for a in get_allergies():
        st.write(a[1])

# ================= STAFF =================
elif mode == "School Staff":

    if not st.session_state["logged_in"]:

        st.subheader("Staff Login")

        school = st.selectbox("School", get_schools())
        name = st.text_input("Name")
        pin = st.text_input("PIN", type="password")

        if st.button("Login"):
            if verify_staff(name, pin, school):
                st.session_state["logged_in"] = True
                st.session_state["role"] = "School Staff"
                st.session_state["school"] = school
                st.session_state["user"] = name
                st.rerun()
            else:
                st.error("Invalid login")

        st.stop()

    show_disclaimer(st.session_state["user"], "staff")

    if st.sidebar.button("🚪 Logout"):
    logout()

    school = st.session_state["school"]
    staff = st.session_state["user"]

    st.title("DoseSafe")

    tabs = st.tabs(["Children","Medication","Incidents","Reports"])

    # CHILDREN
    with tabs[0]:
        name = st.text_input("First Name")
        surname = st.text_input("Surname")
        dob = st.date_input("DOB")

        if st.button("Add Child"):
            add_child(name, surname, str(dob), school)
            st.rerun()

        children = get_children(school)
        cmap = {f"{c[1]} {c[2]}": c[0] for c in children}

        sel = st.selectbox("Select Child", list(cmap.keys()))
        cid = cmap[sel]
        st.session_state["cid"] = cid

        # ALLERGIES
        st.subheader("Allergies")
        allergies = get_allergies()
        opts = {a[1]: a[0] for a in allergies}

        sel_a = st.multiselect("Select", list(opts.keys()))
        if st.button("Save Allergies"):
            set_child_allergies(cid, [opts[s] for s in sel_a])
            st.success("Saved")

    # MEDICATION
    with tabs[1]:
        cid = st.session_state.get("cid")

        for m in get_meds(cid):
            mid,_,name,dose,interval,unit = m

            st.subheader(name)

            warn = check_med_allergy(name, cid)
            if warn:
                st.error(f"⚠️ Allergy: {', '.join(warn)}")

            last = get_last_dose_full(mid)
            now = datetime.now()

            if last:
                last_time = datetime.fromisoformat(last[0])
                next_time = last_time + timedelta(hours=interval)

                st.write(f"Last: {last_time.strftime('%H:%M')}")
                st.write(f"Next: {next_time.strftime('%H:%M')}")

                if now < next_time:
                    rem = next_time - now
                    h = rem.seconds // 3600
                    m = (rem.seconds % 3600) // 60
                    st.error(f"Too soon ({h}h {m}m)")
                else:
                    if st.button("Give", key=mid):
                        log_dose(mid, staff)
                        st.rerun()

    # INCIDENTS
    with tabs[2]:
        cid = st.session_state.get("cid")

        t = st.selectbox("Type", ["Injury","Illness","Allergic Reaction"])
        d = st.text_input("Description")

        if st.button("Log"):
            add_incident(cid, t, d, staff)
            st.success("Logged")

    # REPORTS
    with tabs[3]:
        cid = st.session_state.get("cid")

        if st.button("Generate"):
            logs = get_today_logs(cid)
            incs = get_today_incidents(cid)

            out = []

            for l in logs:
                out.append(f"{l[0]} {datetime.fromisoformat(l[1]).strftime('%H:%M')} {l[2]}")

            for i in incs:
                out.append(f"{datetime.fromisoformat(i[0]).strftime('%H:%M')} {i[2]}")

            st.text_area("Report", "\n".join(out))

# ================= PARENT =================
elif mode == "Parent":

    st.subheader("Parent Login")

    name = st.text_input("Name")
    pin = st.text_input("PIN", type="password")

    r = verify_parent(name, pin)

    if not r:
        st.stop()

    show_disclaimer(name, "parent")

    if st.sidebar.button("🚪 Logout"):
    logout()

    cid = r[0]

    if st.button("Generate Report"):
        logs = get_today_logs(cid)
        incs = get_today_incidents(cid)

        out = []

        for l in logs:
            out.append(f"{l[0]} {datetime.fromisoformat(l[1]).strftime('%H:%M')} {l[2]}")

        for i in incs:
            out.append(f"{datetime.fromisoformat(i[0]).strftime('%H:%M')} {i[2]}")

        st.text_area("Report", "\n".join(out))

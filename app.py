import streamlit as st
from datetime import datetime, timedelta
from database import *
import pandas as pd

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

    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if not st.session_state["admin_logged_in"]:
        u = st.sidebar.text_input("Admin Username")
        p = st.sidebar.text_input("PIN", type="password")

        if st.sidebar.button("Login"):
            if u == "Admin" and p == "1234":
                st.session_state["admin_logged_in"] = True
                st.session_state["admin_user"] = u
                st.rerun()
            else:
                st.sidebar.error("Invalid login")

        st.stop()

    show_disclaimer(st.session_state["admin_user"], "admin")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    st.title("Admin Panel")

    st.subheader("➕ Create School & Staff")
    new_school = st.text_input("School Name")
    new_staff = st.text_input("Staff Name")
    new_pin = st.text_input("Staff PIN")

    if st.button("Create School"):
        add_staff(new_staff, new_pin, new_school)
        set_subscription(new_school, "active", "2099-12-31")
        st.success("Created")
        st.rerun()

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

        new_pin_reset = col4.text_input("New PIN", key=f"pin_{sid}")
        if col4.button("Update", key=f"up_{sid}"):
            update_staff_pin(sid, new_pin_reset)
            st.success("PIN updated")

    st.subheader("💳 Subscriptions")

    schools = get_schools()
    if schools:
        s = st.selectbox("School", schools)
        status = st.selectbox("Status", ["active","inactive"])
        expiry = st.date_input("Expiry")

        if st.button("Update Subscription"):
            set_subscription(s, status, str(expiry))
            st.success("Updated")

    st.markdown("### Current Subscriptions")

    subs = get_all_subscriptions()
    if subs:
        df = pd.DataFrame(subs, columns=["School","Status","Expiry"])
        st.dataframe(df, use_container_width=True)

    st.stop()

# ================= PARENT =================
elif mode == "Parent":

    parent_mode = st.sidebar.radio("Parent Access", ["Login","Register"])

    if parent_mode == "Login":
        name = st.sidebar.text_input("Name")
        pin = st.sidebar.text_input("PIN", type="password")

        r = verify_parent(name, pin)

        if not r:
            st.warning("Invalid login")
            st.stop()

        show_disclaimer(name, "parent")

        if st.sidebar.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

        cid = r[0]

        st.title("Parent Dashboard")

        if st.button("Generate Report"):
            logs = get_today_logs(cid)
            incs = get_today_incidents(cid)

            out = []

            for l in logs:
                # FIXED ORDER
                med_name = l[0]
                time = datetime.fromisoformat(l[1])
                given_by = l[2] if l[2] else "Unknown"

                out.append(f"💊 {med_name} — {time.strftime('%H:%M')} ({given_by})")

            for i in incs:
                time = datetime.fromisoformat(i[0])
                desc = i[2]

                out.append(f"⚠️ {time.strftime('%H:%M')} — {desc}")

            st.text_area("Report", "\n".join(out), height=300)

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
            st.success("Created & logged in")
            st.session_state["cid"] = cmap[sel]
            st.rerun()

        st.stop()

# ================= STAFF =================
elif mode == "School Staff":

    if "staff_logged_in" not in st.session_state:
        st.session_state["staff_logged_in"] = False

    if not st.session_state["staff_logged_in"]:
        school = st.sidebar.selectbox("School", get_schools())
        staff = st.sidebar.text_input("Name")
        pin = st.sidebar.text_input("PIN", type="password")

        if st.sidebar.button("Login"):
            if verify_staff(staff, pin, school):
                st.session_state["staff_logged_in"] = True
                st.session_state["staff"] = staff
                st.session_state["school"] = school
                st.rerun()
            else:
                st.sidebar.error("Invalid login")

        st.stop()

    school = st.session_state["school"]
    staff = st.session_state["staff"]

    show_disclaimer(staff, "staff")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    st.title("DoseSafe")

    tab1, tab2, tab3, tab4 = st.tabs(["👶 Children","💊 Medication","⚠️ Incidents","📄 Reports"])

    with tab1:
        name = st.text_input("First Name")
        surname = st.text_input("Surname")
        dob = st.date_input("DOB")

        if st.button("Add Child"):
            add_child(name, surname, str(dob), school)
            st.rerun()

        search = st.text_input("Search child")

        children = get_children(school)
        if search:
            children = [c for c in children if search.lower() in (c[1]+" "+c[2]).lower()]

        cmap = {f"{c[1]} {c[2]} ({c[3]})": c[0] for c in children}

        sel = st.selectbox("Child", list(cmap.keys()))
        st.session_state["cid"] = cmap[sel]

    with tab2:
        cid = st.session_state.get("cid")

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
                    rem = next_time - now
                    h = rem.seconds//3600
                    m = (rem.seconds%3600)//60
                    st.error(f"Too soon ({h}h {m}m)")
                else:
                    if st.button("Give", key=f"g_{mid}"):
                        log_dose(mid, staff)
                        st.rerun()

    with tab3:
        cid = st.session_state.get("cid")

        t = st.selectbox("Type",["Injury","Illness","Allergic Reaction"])
        d = st.text_input("Description")

        if st.button("Log Incident"):
            add_incident(cid, t, d, staff)
            st.success("Logged")

    with tab4:
        cid = st.session_state.get("cid")

        if st.button("Generate Report"):
            logs = get_today_logs(cid)
            incs = get_today_incidents(cid)

            out = []

            for l in logs:
                med_name = l[0]
                time = datetime.fromisoformat(l[1])
                given_by = l[2] if l[2] else "Unknown"

                out.append(f"💊 {med_name} — {time.strftime('%H:%M')} ({given_by})")

            for i in incs:
                time = datetime.fromisoformat(i[0])
                desc = i[2]

                out.append(f"⚠️ {time.strftime('%H:%M')} — {desc}")

            st.text_area("Report", "\n".join(out), height=300)

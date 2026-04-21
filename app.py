import streamlit as st
from datetime import datetime, timedelta
from database import *
import pandas as pd

st.set_page_config(page_title="DoseSafe", page_icon="DoseSafe.png", layout="centered")

# SIDEBAR BRANDING
st.sidebar.image("DoseSafe.png", use_container_width=True)
st.sidebar.markdown("---")

create_tables()

# ================= SESSION =================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "role" not in st.session_state:
    st.session_state["role"] = None

def logout():
    st.session_state.clear()
    st.rerun()

# ================= MODE =================
if not st.session_state["logged_in"]:
    mode = st.selectbox("Select Access", ["School Staff","Admin","Parent"])
else:
    mode = st.session_state["role"]

# ================= DISCLAIMER =================
def show_disclaimer(user, role):
    st.warning("⚠️ DoseSafe is not liable for incorrect medication. Always follow doctor instructions.")

    if not has_accepted_disclaimer(user, role):
        if st.checkbox("I accept responsibility"):
            if st.button("Continue"):
                accept_disclaimer(user, role)
                st.rerun()
        st.stop()

# ================= ADMIN =================
if mode == "Admin":

    if not st.session_state["logged_in"]:
        u = st.text_input("Username")
        p = st.text_input("PIN", type="password")

        if st.button("Login"):
            if u == "Admin" and p == "1234":
                st.session_state.update({"logged_in":True,"role":"Admin","user":u})
                st.rerun()
            else:
                st.error("Invalid login")
        st.stop()

    show_disclaimer(st.session_state["user"], "admin")

    st.sidebar.success(f"🛠️ Admin: {st.session_state['user']}")
    st.sidebar.caption("Administrator")
    if st.sidebar.button("🚪 Logout"): logout()

    st.title("Admin Panel")

    # CREATE SCHOOL
    school = st.text_input("School")
    staff = st.text_input("Staff Name")
    pin = st.text_input("Staff PIN")

    if st.button("Create School + Staff"):
        add_staff(staff, pin, school)
        set_subscription(school, "active", "2099-12-31")
        st.success("Created")
        st.rerun()

    # STAFF MANAGEMENT
    st.subheader("Staff Management")
    for s in get_all_staff():
        sid,name,school,active = s
        col1,col2,col3,col4 = st.columns([3,2,2,2])

        col1.write(f"{name} ({school})")
        col2.write("Active" if active else "Disabled")

        if col3.button("Toggle", key=f"t{sid}"):
            set_staff_active(sid,0 if active else 1)
            st.rerun()

        new_pin = col4.text_input("New PIN", key=f"p{sid}")
        if col4.button("Update", key=f"u{sid}"):
            update_staff_pin(sid,new_pin)

    # SUBSCRIPTIONS
    st.subheader("Subscriptions")
    schools = get_schools()

    if schools:
        s = st.selectbox("School", schools)
        status = st.selectbox("Status",["active","inactive"])
        expiry = st.date_input("Expiry")

        if st.button("Update Subscription"):
            set_subscription(s,status,str(expiry))

    st.dataframe(pd.DataFrame(get_all_subscriptions(),columns=["School","Status","Expiry"]))

    # ALLERGIES
    st.subheader("Allergy Master List")
    a = st.text_input("Add Allergy")
    if st.button("Add Allergy"):
        add_allergy(a)
        st.rerun()

    for x in get_allergies():
        st.write(x[1])

# ================= STAFF =================
elif mode == "School Staff":

    if not st.session_state["logged_in"]:
        school = st.selectbox("School", get_schools())
        name = st.text_input("Name")
        pin = st.text_input("PIN", type="password")

        if st.button("Login"):
            if verify_staff(name,pin,school):
                st.session_state.update({
                    "logged_in":True,
                    "role":"School Staff",
                    "school":school,
                    "user":name
                })
                st.rerun()
            else:
                st.error("Invalid login")
        st.stop()

    show_disclaimer(st.session_state["user"], "staff")

    st.sidebar.success(f"👩‍🏫 {st.session_state['user']}")
    st.sidebar.caption("Teacher")
    st.sidebar.write(f"🏫 {st.session_state['school']}")
    if st.sidebar.button("🚪 Logout"): logout()

    school = st.session_state["school"]
    staff = st.session_state["user"]

    tabs = st.tabs(["Children","Medication","Incidents","Reports"])

    # ---------- CHILDREN ----------
    with tabs[0]:
        st.subheader("Add Child")

        name = st.text_input("First Name")
        surname = st.text_input("Surname")
        dob = st.date_input("DOB")
        parent_name = st.text_input("Parent Name")
        parent_phone = st.text_input("Parent Phone")

        if st.button("Add Child"):
            add_child(name,surname,str(dob),school,parent_name,parent_phone)
            st.success("Child added")
            st.rerun()

        st.divider()

        children = get_children(school)

        if children:
            search = st.text_input("Search Child")
            filtered = [c for c in children if search.lower() in (c[1]+" "+c[2]).lower()] if search else children

            cmap = {f"{c[1]} {c[2]}":c[0] for c in filtered}
            sel = st.selectbox("Select Child", list(cmap.keys()))
            cid = cmap[sel]
            st.session_state["cid"] = cid

            # ALLERGIES
            st.subheader("Allergies")
            allg = get_allergies()
            opts = {a[1]:a[0] for a in allg}

            current = get_child_allergies(cid)
            sel_a = st.multiselect("Select", list(opts.keys()), default=current)

            if st.button("Save Allergies"):
                set_child_allergies(cid,[opts[s] for s in sel_a])
                st.success("Saved")

    # ---------- MEDICATION ----------
    with tabs[1]:
        cid = st.session_state.get("cid")

        if not cid:
            st.warning("Select a child first")
            st.stop()

        st.subheader("Add Medication")

        lib = get_med_library()
        lib_names = [x[1] for x in lib]

        choice = st.selectbox("Select from library or custom", ["Custom"] + lib_names)

        if choice == "Custom":
            m = st.text_input("Medication Name")
            u = st.selectbox("Unit",["ml","tablet","other"])

            if st.button("Add to Library"):
                add_med_to_library(m,u)
                st.rerun()
        else:
            m = choice
            u = next(x[2] for x in lib if x[1]==choice)

        d = st.text_input("Dose")
        i = st.number_input("Interval (hours)",min_value=1)

        if st.button("Add Medication"):
            add_med(cid,m,d,i,u)
            st.success("Added")
            st.rerun()

        st.divider()

        for med in get_meds(cid):
            mid,_,name,dose,interval,unit = med

            st.subheader(name)
            st.caption(f"{dose} {unit} every {interval}h")

            warn = check_med_allergy(name,cid)
            if warn:
                st.error(f"⚠️ Allergy warning: {', '.join(warn)}")

            last = get_last_dose_full(mid)
            now = datetime.now()

            if last:
                lt = datetime.fromisoformat(last[0])
                nt = lt + timedelta(hours=interval)

                st.write(f"Last: {lt.strftime('%H:%M')} ({last[1]})")
                st.write(f"Next: {nt.strftime('%H:%M')}")

                if now < nt:
                    rem = nt-now
                    h = rem.seconds//3600
                    m = (rem.seconds%3600)//60
                    st.error(f"❌ Too soon ({h}h {m}m)")
                else:
                    if st.button("Give", key=f"give{mid}"):
                        log_dose(mid,staff)
                        st.rerun()
            else:
                if st.button("Give First Dose", key=f"first{mid}"):
                    log_dose(mid,staff)
                    st.rerun()

    # ---------- INCIDENTS ----------
    with tabs[2]:
        cid = st.session_state.get("cid")

        t = st.selectbox("Type",["Injury","Illness","Allergic Reaction"])
        d = st.text_input("Description")

        if st.button("Log Incident"):
            add_incident(cid,t,d,staff)
            st.success("Logged")

    # ---------- REPORT ----------
    with tabs[3]:
        cid = st.session_state.get("cid")

        if st.button("Generate Report"):
            logs = get_today_logs(cid)
            incs = get_today_incidents(cid)

            out = []

            for l in logs:
                t = datetime.fromisoformat(l[1]).strftime('%H:%M')
                out.append(f"💊 {l[0]} — {t} ({l[2]})")

            for i in incs:
                t = datetime.fromisoformat(i[0]).strftime('%H:%M')
                out.append(f"⚠️ {t} — {i[2]}")

            st.text_area("Report","\n".join(out), height=300)

# ================= PARENT =================
elif mode == "Parent":

    # ---------- NOT LOGGED IN ----------
    if not st.session_state["logged_in"]:

        tab1, tab2 = st.tabs(["Login","Register"])

        # LOGIN
        with tab1:
            name = st.text_input("Name", key="pl")
            pin = st.text_input("PIN", type="password", key="pp")

            if st.button("Login"):
                r = verify_parent(name,pin)
                if r:
                    parent_id, phone = r

                    assign_children_to_parent(phone, parent_id)

                    st.session_state.update({
                        "logged_in":True,
                        "role":"Parent",
                        "user":name,
                        "phone":phone,
                        "parent_id":parent_id
                    })
                    st.rerun()
                else:
                    st.error("Invalid login")

        # REGISTER
        with tab2:
            name = st.text_input("Name", key="rn")
            pin = st.text_input("PIN", key="rp")
            phone = st.text_input("Phone")

            if st.button("Register"):
                pid = add_parent(name,pin,phone)
                assign_children_to_parent(phone,pid)

                st.session_state.update({
                    "logged_in":True,
                    "role":"Parent",
                    "user":name,
                    "phone":phone,
                    "parent_id":pid
                })
                st.rerun()

        st.stop()

    show_disclaimer(st.session_state["user"], "parent")

    st.sidebar.success(f"👪 {st.session_state['user']}")
    st.sidebar.caption("Parent")
    if st.sidebar.button("🚪 Logout"): logout()

    children = get_children_by_phone(st.session_state["phone"])

    if not children:
        st.warning("No children linked")
        st.stop()

    cmap = {f"{c[1]} {c[2]}":c[0] for c in children}
    sel = st.selectbox("Select Child", list(cmap.keys()))
    cid = cmap[sel]

    if st.button("Generate Report"):
        logs = get_today_logs(cid)
        incs = get_today_incidents(cid)

        out = []

        for l in logs:
            t = datetime.fromisoformat(l[1]).strftime('%H:%M')
            out.append(f"💊 {l[0]} — {t} ({l[2]})")

        for i in incs:
            t = datetime.fromisoformat(i[0]).strftime('%H:%M')
            out.append(f"⚠️ {t} — {i[2]}")

        st.text_area("Report","\n".join(out), height=300)

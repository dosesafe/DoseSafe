import streamlit as st
from datetime import datetime, timedelta
from database import *
import pandas as pd

st.set_page_config(page_title="DoseSafe", page_icon="DoseSafe.png", layout="centered")

st.sidebar.image("DoseSafe.png", use_container_width=True)
st.sidebar.markdown("---")

create_tables()

# SESSION
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "role" not in st.session_state:
    st.session_state["role"] = None

def logout():
    st.session_state.clear()
    st.rerun()

# MODE
if not st.session_state["logged_in"]:
    mode = st.selectbox("Select Access", ["School Staff","Admin","Parent"])
else:
    mode = st.session_state["role"]

# DISCLAIMER
def show_disclaimer(user, role):
    st.warning("Use at your own risk. Medication must be doctor prescribed.")

    if not has_accepted_disclaimer(user, role):
        if st.checkbox("I accept"):
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

    st.sidebar.success(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🚪 Logout"): logout()

    st.title("Admin Panel")

    # CREATE SCHOOL
    school = st.text_input("School")
    staff = st.text_input("Staff")
    pin = st.text_input("PIN")

    if st.button("Create School"):
        add_staff(staff, pin, school)
        set_subscription(school, "active", "2099-12-31")
        st.success("Created")
        st.rerun()

    # STAFF
    st.subheader("Staff")
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
    st.subheader("Allergies")
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

    st.sidebar.success(f"👤 {st.session_state['user']}")
    st.sidebar.write(f"🏫 {st.session_state['school']}")
    if st.sidebar.button("🚪 Logout"): logout()

    school = st.session_state["school"]
    staff = st.session_state["user"]

    tabs = st.tabs(["Children","Medication","Incidents","Reports"])

    # CHILDREN
    with tabs[0]:
        name = st.text_input("First Name")
        surname = st.text_input("Surname")
        dob = st.date_input("DOB")

        if st.button("Add Child"):
            add_child(name,surname,str(dob),school)
            st.rerun()

        children = get_children(school)
        cmap = {f"{c[1]} {c[2]}":c[0] for c in children}

        sel = st.selectbox("Select Child", list(cmap.keys()))
        cid = cmap[sel]
        st.session_state["cid"] = cid

        # ALLERGIES
        st.subheader("Allergies")
        allg = get_allergies()
        opts = {a[1]:a[0] for a in allg}

        sel_a = st.multiselect("Select", list(opts.keys()))
        if st.button("Save Allergies"):
            set_child_allergies(cid,[opts[s] for s in sel_a])

    # MEDICATION
    with tabs[1]:
        cid = st.session_state.get("cid")

        st.subheader("Add Medication")
        m = st.text_input("Name")
        d = st.text_input("Dose")
        i = st.number_input("Interval",min_value=1)
        u = st.selectbox("Unit",["ml","tablet","other"])

        if st.button("Add Med"):
            add_med(cid,m,d,i,u)
            st.rerun()

        for med in get_meds(cid):
            mid,_,name,dose,interval,unit = med

            st.subheader(name)

            warn = check_med_allergy(name,cid)
            if warn:
                st.error(f"⚠️ {', '.join(warn)}")

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
                    st.error(f"Too soon ({h}h {m}m)")
                else:
                    if st.button("Give", key=mid):
                        log_dose(mid,staff)
                        st.rerun()

    # INCIDENTS
    with tabs[2]:
        cid = st.session_state.get("cid")

        t = st.selectbox("Type",["Injury","Illness","Allergic Reaction"])
        d = st.text_input("Description")

        if st.button("Log"):
            add_incident(cid,t,d,staff)

    # REPORT
    with tabs[3]:
        cid = st.session_state.get("cid")

        if st.button("Generate"):
            logs = get_today_logs(cid)
            incs = get_today_incidents(cid)

            out = []

            for l in logs:
                t = datetime.fromisoformat(l[1]).strftime('%H:%M')
                out.append(f"💊 {l[0]} — {t} ({l[2]})")

            for i in incs:
                t = datetime.fromisoformat(i[0]).strftime('%H:%M')
                out.append(f"⚠️ {t} — {i[2]}")

            st.text_area("Report","\n".join(out))

# ================= PARENT =================
elif mode == "Parent":

    tab1, tab2 = st.tabs(["Login","Register"])

    # LOGIN
    with tab1:
        name = st.text_input("Name", key="pl")
        pin = st.text_input("PIN", type="password", key="pp")

        if st.button("Login"):
            r = verify_parent(name,pin)
            if r:
                st.session_state.update({
                    "logged_in":True,
                    "role":"Parent",
                    "user":name,
                    "cid":r[0]
                })
                st.rerun()
            else:
                st.error("Invalid")

    # REGISTER
    with tab2:
        name = st.text_input("Name", key="rn")
        pin = st.text_input("PIN", key="rp")

        children = get_all_children()
        cmap = {f"{c[1]} {c[2]}":c[0] for c in children}

        sel = st.selectbox("Select Child", list(cmap.keys()))

        if st.button("Register"):
            add_parent(name,pin,cmap[sel])
            st.success("Registered")

    if not st.session_state["logged_in"]:
        st.stop()

    show_disclaimer(st.session_state["user"], "parent")

    st.sidebar.success(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🚪 Logout"): logout()

    cid = st.session_state["cid"]

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

        st.text_area("Report","\n".join(out))

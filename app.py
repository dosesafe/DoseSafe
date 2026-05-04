import streamlit as st
from datetime import datetime, timedelta
from database import *
import pandas as pd

st.set_page_config(page_title="DoseSafe", page_icon="DoseSafe.png", layout="centered")

# ---------- UI STYLING ----------
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    max-width: 900px;
}
.card {
    background: white;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    margin-bottom: 12px;
}
.stButton>button {
    border-radius: 8px;
    height: 40px;
    font-weight: 600;
}
section[data-testid="stSidebar"] {
    background-color: #f9fafb;
}
</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
st.sidebar.image("DoseSafe.png", use_container_width=True)
st.sidebar.markdown("---")

create_tables()

# ---------- SESSION ----------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "role" not in st.session_state:
    st.session_state["role"] = None

def logout():
    st.session_state.clear()
    st.rerun()

# ---------- MODE ----------
if not st.session_state["logged_in"]:
    mode = st.selectbox("Select Access", ["School Staff","Admin","Parent"])
else:
    mode = st.session_state["role"]

# ---------- DISCLAIMER ----------
def show_disclaimer(user, role):
    st.warning("⚠️ Always follow doctor instructions.")

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
            if u.lower() == "admin" and p == "1234":
                st.session_state.update({"logged_in":True,"role":"Admin","user":u})
                st.rerun()
            else:
                st.error("Invalid login")
        st.stop()

    show_disclaimer(st.session_state["user"], "admin")

    st.sidebar.success(f"🛠️ {st.session_state['user']}")
    if st.sidebar.button("Logout"): logout()

    st.title("Admin Panel")

    schools = get_schools()

    existing = st.selectbox("Select School", ["-- New --"] + schools)
    new_school = st.text_input("Or New School")

    staff = st.text_input("Staff Name")
    pin = st.text_input("PIN")

    school = new_school if new_school else existing

    if st.button("Create"):
        if school == "-- New --" and not new_school:
            st.warning("Enter or select school")
            st.stop()

        school = school.strip().title()
        add_staff(staff, pin, school)
        set_subscription(school, "active", "2030-12-31")
        st.success("Done")
        st.rerun()

    st.subheader("Subscriptions")

    subs = get_all_subscriptions()
    
    st.dataframe(pd.DataFrame(subs, columns=["School","Status","Expiry"]))
    
    for s in subs:
        school, status, expiry = s
    
        st.markdown(f"### {school}")
    
        try:
            default_date = datetime.fromisoformat(expiry)
        except:
            default_date = datetime.today()
    
        new_date = st.date_input(
            f"Expiry for {school}",
            value=default_date,
            key=f"date_{school}"
        )
    
        if st.button(f"Update {school}", key=f"btn_{school}"):
            set_subscription(school, "active", str(new_date))
            st.success("Updated")
            st.rerun()

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
    st.sidebar.write(st.session_state["school"])
    if st.sidebar.button("Logout"): logout()

    school = st.session_state["school"]
    staff = st.session_state["user"]

    # ---------- SIDEBAR CHILD ----------
    st.sidebar.markdown("### 👶 Children")

    with st.sidebar.expander("Add Child"):
        n = st.text_input("Name", key="c1")
        s = st.text_input("Surname", key="c2")
        d = st.date_input("DOB", key="c3")
        pn = st.text_input("Parent", key="c4")
        pp = st.text_input("Phone", key="c5")

        if st.button("Add", key="add_child"):
            add_child(n,s,str(d),school,pn,pp)
            st.rerun()

    children = get_children(school)

    if not children:
        st.warning("No children")
        st.stop()

    cmap = {f"{c[1]} {c[2]}":c[0] for c in children}
    sel = st.sidebar.selectbox("Select Child", list(cmap.keys()))
    cid = cmap[sel]
    st.session_state["cid"] = cid

    child = next((c for c in children if c[0]==cid),None)

    if child:
        st.sidebar.success(f"{child[1]} {child[2]}")

        st.markdown(f"""
        <div class="card">
        <h3>👶 {child[1]} {child[2]}</h3>
        <p>DOB: {child[3]}</p>
        </div>
        """, unsafe_allow_html=True)

    # ---------- TABS ----------
    tabs = st.tabs(["💊 Medication","⚠️ Incidents","📊 Reports"])

    # MEDICATION
    with tabs[0]:

        lib = get_med_library()
        names = [x[1] for x in lib]

        choice = st.selectbox("Medication", ["Custom"]+names)

        if choice=="Custom":
            m = st.text_input("Name")
            u = st.selectbox("Unit",["ml","tablet"])
        else:
            m = choice
            u = next(x[2] for x in lib if x[1]==choice)

        d = st.text_input("Dose")
        i = st.number_input("Interval",min_value=1)

        if st.button("Add Medication"):
            add_med(cid,m,d,i,u)
            st.rerun()

        for med in get_meds(cid):
            mid,_,name,dose,interval,unit = med

            st.markdown(f"""
            <div class="card">
            <b>{name}</b><br>
            {dose} {unit} / {interval}h
            """, unsafe_allow_html=True)

            last = get_last_dose_full(mid)
            now = datetime.now()

            if last:
                lt = datetime.fromisoformat(last[0])
                nt = lt + timedelta(hours=interval)

                if now < nt:
                    st.warning("Too soon")
                else:
                    if st.button("Give", key=mid):
                        log_dose(mid, staff)
                        st.rerun()
            else:
                if st.button("First Dose", key=f"f{mid}"):
                    log_dose(mid, staff)
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # INCIDENTS
    with tabs[1]:
        t = st.selectbox("Type",["Injury","Illness"])
        d = st.text_input("Description")

        if st.button("Log"):
            add_incident(cid,t,d,staff)
            st.success("Saved")

    # REPORT
    with tabs[2]:
        logs = get_today_logs(cid)
        incs = get_today_incidents(cid)

        for l in logs:
            t = datetime.fromisoformat(l[1]).strftime('%H:%M')
            st.write(f"{t} 💊 {l[0]}")

        for i in incs:
            t = datetime.fromisoformat(i[1]).strftime('%H:%M')
            st.write(f"{t} ⚠️ {i[2]}")

# ================= PARENT =================
elif mode == "Parent":

    if not st.session_state["logged_in"]:

        name = st.text_input("Name")
        pin = st.text_input("PIN")

        if st.button("Login"):
            r = verify_parent(name,pin)
            if r:
                pid, phone = r
                st.session_state.update({
                    "logged_in":True,
                    "role":"Parent",
                    "phone":phone
                })
                st.rerun()
        st.stop()

    children = get_children_by_phone(st.session_state["phone"])

    cmap = {f"{c[1]} {c[2]}":c[0] for c in children}
    cid = cmap[st.selectbox("Child", list(cmap.keys()))]

    logs = get_today_logs(cid)
    incs = get_today_incidents(cid)

    for l in logs:
        t = datetime.fromisoformat(l[1]).strftime('%H:%M')
        st.write(f"{t} 💊 {l[0]}")

    for i in incs:
        t = datetime.fromisoformat(i[1]).strftime('%H:%M')
        st.write(f"{t} ⚠️ {i[2]}")

import streamlit as st
from datetime import datetime, timedelta
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")
create_tables()

st.sidebar.title("DoseSafe")

mode = st.sidebar.selectbox("Login Type", ["School Staff","Admin"])

# ================= ADMIN =================
if mode == "Admin":
    user = st.sidebar.text_input("Admin Username")
    pin = st.sidebar.text_input("PIN", type="password")

    if user != "Admin" or pin != "1234":
        st.stop()

    if not has_accepted_disclaimer(user,"admin"):
        st.warning("Accept disclaimer to continue")
        if st.button("Accept"):
            accept_disclaimer(user,"admin")
            st.rerun()
        st.stop()

    st.title("Admin Panel")

    schools = get_schools()
    school = st.selectbox("School", schools)

    status = st.selectbox("Status",["active","inactive"])
    if st.button("Update Subscription"):
        set_subscription(school,status,"2099-01-01")
        st.success("Updated")

    st.stop()

# ================= STAFF =================
school = st.sidebar.selectbox("School", get_schools())
staff = st.sidebar.text_input("Staff")
pin = st.sidebar.text_input("PIN", type="password")

if not verify_staff(staff,pin,school):
    st.stop()

if not has_accepted_disclaimer(staff,"staff"):
    st.warning("Accept disclaimer to continue")
    if st.button("Accept"):
        accept_disclaimer(staff,"staff")
        st.rerun()
    st.stop()

st.title("DoseSafe")

children = get_children(school)
cmap = {f"{c[1]} {c[2]}":c[0] for c in children}
sel = st.selectbox("Child", cmap.keys())
cid = cmap[sel]

# ---------------- MEDICATION ----------------
for m in get_meds(cid):
    mid,_,name,dose,interval,unit = m

    st.subheader(name)

    alert, allergy = check_med_allergy(cid,name)

    can_give = True

    if alert == "block":
        st.error(f"🚫 BLOCKED: {allergy}")
        can_give = False

    last = get_last_dose_full(mid)

    if last:
        last_time = datetime.fromisoformat(last[0])
        next_time = last_time + timedelta(hours=interval)

        st.write(f"Last: {last_time.strftime('%H:%M')} ({last[1]})")
        st.write(f"Next: {next_time.strftime('%H:%M')}")

        if datetime.now() < next_time:
            st.error("Too soon")
            can_give = False

    if can_give:
        if st.button(f"Give {name}", key=mid):
            log_dose(mid,staff)
            st.rerun()
    else:
        st.button(f"Give {name}", key=f"d{mid}", disabled=True)

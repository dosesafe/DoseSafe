import streamlit as st
from datetime import datetime, timedelta
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")
create_tables()

st.sidebar.title("DoseSafe")

# -------------------------
# LOGIN MODE
# -------------------------
mode = st.sidebar.selectbox("Login Type", ["School Staff","Admin"])

# ================= ADMIN =================
if mode == "Admin":
    user = st.sidebar.text_input("Admin Username")
    pin = st.sidebar.text_input("Admin PIN", type="password")

    if user != "Admin" or pin != "1234":
        st.stop()

    st.title("Admin Panel")

    # STAFF
    st.subheader("Staff")
    for s in get_all_staff():
        sid,name,school,active = s
        st.write(f"{name} ({school}) {'🟢' if active else '🔴'}")

    # ADD STAFF
    st.subheader("Add Staff")
    n = st.text_input("Name")
    p = st.text_input("PIN")
    sc = st.text_input("School")

    if st.button("Add Staff"):
        add_staff(n,p,sc)
        set_subscription(sc,"active","2099-12-31")
        st.rerun()

    # MED LIBRARY
    st.subheader("Medication Library")
    mname = st.text_input("Medication Name")
    unit = st.selectbox("Unit",["ml","unit","n/a"])

    if st.button("Add Medication"):
        add_med_to_library(mname,unit)
        st.rerun()

    for m in get_med_library():
        st.write(f"{m[1]} ({m[2]})")

    # SUBSCRIPTIONS
    st.subheader("Subscriptions")
    schools = get_schools()
    sch = st.selectbox("School",schools)
    status = st.selectbox("Status",["active","inactive"])
    expiry = st.date_input("Expiry")

    if st.button("Update Subscription"):
        set_subscription(sch,status,str(expiry))
        st.success("Updated")

    st.stop()

# ================= SCHOOL =================
schools = get_schools()
school = st.sidebar.selectbox("School",["--"]+schools)

if school == "--":
    st.stop()

staff_list = get_staff_by_school(school)
staff_names = [s[1] for s in staff_list]

staff = st.sidebar.selectbox("Staff",["--"]+staff_names)
pin = st.sidebar.text_input("PIN",type="password")

if staff == "--" or not pin:
    st.stop()

if not verify_staff(staff,pin,school):
    st.stop()

# SUB CHECK
sub = get_subscription(school)
if not sub:
    set_subscription(school,"active","2099-12-31")

# ADD CHILD
st.sidebar.subheader("Add Child")
name = st.sidebar.text_input("First Name")
surname = st.sidebar.text_input("Surname")
dob = st.sidebar.date_input("DOB")

allergies = get_allergies()
amap = {a[1]:a[0] for a in allergies}
sel_all = st.sidebar.multiselect("Allergies",list(amap.keys()))

if st.sidebar.button("Add Child"):
    cid = add_child(name,surname,str(dob),school)
    add_child_allergies(cid,[amap[a] for a in sel_all])
    st.rerun()

# MAIN
st.title("DoseSafe")

children = get_children(school)
child_map = {f"{c[1]} {c[2]}":c[0] for c in children}

selected = st.selectbox("Select Child",["--"]+list(child_map.keys()))
if selected == "--":
    st.stop()

cid = child_map[selected]

tab1,tab2,tab3 = st.tabs(["Medication","Incidents","Reports"])

# MEDS
with tab1:
    for m in get_meds(cid):
        if len(m)==6:
            mid,_,name,dose,interval,unit=m
        else:
            mid,_,name,dose,interval=m
            unit=""

        st.subheader(name)
        st.caption(f"{dose} {unit} • every {interval} hrs")

        last=get_last_dose_full(mid)

        if last:
            last_time=datetime.fromisoformat(last[0])
            next_time=last_time+timedelta(hours=interval)
            now=datetime.now()

            st.write(f"Last: {last_time.strftime('%H:%M')} ({last[1]})")
            st.write(f"Next: {next_time.strftime('%H:%M')}")

            if now<next_time:
                rem=next_time-now
                st.error(f"Too soon ({rem.seconds//60} min)")
            else:
                st.success("Safe to give")

        if st.button(f"Give {name}",key=mid):
            log_dose(mid,staff)
            st.rerun()

    st.markdown("### Add Medication")

    lib=get_med_library()
    lmap={f"{m[1]} ({m[2]})":m for m in lib}

    sel=st.selectbox("Medication",list(lmap.keys()))
    dose=st.text_input("Dosage")
    interval=st.number_input("Interval",min_value=1)

    if st.button("Add"):
        m=lmap[sel]
        add_med(cid,m[1],dose,interval,m[2])
        st.rerun()

# INCIDENTS
with tab2:
    itype=st.selectbox("Type",["Injury","Illness","Allergic Reaction","Other"])
    desc=st.text_input("Description")

    if st.button("Log Incident"):
        add_incident(cid,itype,desc,staff)
        st.rerun()

    for i in get_incidents(cid):
        t=datetime.fromisoformat(i[4])
        st.write(f"{i[2]} - {t.strftime('%H:%M')}")
        st.caption(i[3])

# REPORTS
with tab3:
    if st.button("Generate Report"):
        logs=get_today_logs(cid)
        incs=get_today_incidents(cid)

        out=[]
        out.append("MEDICATION:")
        for l in logs:
            t=datetime.fromisoformat(l[1])
            out.append(f"{l[0]} {t.strftime('%H:%M')} {l[2]}")

        out.append("\nINCIDENTS:")
        for i in incs:
            t=datetime.fromisoformat(i[2])
            out.append(f"{i[0]} {t.strftime('%H:%M')}")

        st.text_area("Report","\n".join(out),height=300)

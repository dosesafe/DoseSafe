import streamlit as st
from datetime import datetime
from database import *

st.set_page_config(page_title="DoseSafe Parent", layout="centered")

create_tables()

st.title("👪 DoseSafe Parent Portal")

# -------------------------
# LOGIN
# -------------------------
name = st.text_input("Parent Name")
pin = st.text_input("PIN", type="password")

if not name or not pin:
    st.stop()

result = verify_parent(name, pin)

if not result:
    st.error("Invalid login")
    st.stop()

child_id = result[0]

st.success("Logged in")

# -------------------------
# GET CHILD
# -------------------------
children = get_children("")  # we will filter manually

child = next((c for c in children if c[0] == child_id), None)

if not child:
    st.error("Child not found")
    st.stop()

st.header(f"{child[1]} {child[2]}")
st.caption(f"DOB: {child[3]}")

# -------------------------
# TABS
# -------------------------
tab1, tab2, tab3 = st.tabs(["Medication", "Incidents", "Daily Report"])

# -------------------------
# MEDICATION
# -------------------------
with tab1:
    st.subheader("💊 Medication History")

    meds = get_meds(child_id)

    for m in meds:
        if len(m) == 6:
            mid, _, name, dose, interval, unit = m
        else:
            mid, _, name, dose, interval = m
            unit = ""

        st.markdown(f"### {name}")
        st.caption(f"{dose} {unit}")

        logs = get_logs_by_med(mid)

        if not logs:
            st.write("No records")
        else:
            for log in logs:
                t = datetime.fromisoformat(log[0])
                st.write(f"{t.strftime('%d %b %H:%M')} — {log[1]}")

# -------------------------
# INCIDENTS
# -------------------------
with tab2:
    st.subheader("⚠️ Incidents")

    incidents = get_incidents(child_id)

    if not incidents:
        st.write("No incidents recorded")
    else:
        for i in incidents:
            t = datetime.fromisoformat(i[4])
            st.markdown(f"**{i[2]}** — {t.strftime('%d %b %H:%M')}")
            st.caption(i[3])
            st.divider()

# -------------------------
# DAILY REPORT
# -------------------------
with tab3:
    st.subheader("📊 Today's Summary")

    logs = get_today_logs(child_id)
    incs = get_today_incidents(child_id)

    st.markdown("### 💊 Medication")

    if not logs:
        st.write("No medication today")
    else:
        for l in logs:
            t = datetime.fromisoformat(l[1])
            st.write(f"{l[0]} — {t.strftime('%H:%M')} ({l[2]})")

    st.markdown("### ⚠️ Incidents")

    if not incs:
        st.write("No incidents today")
    else:
        for i in incs:
            t = datetime.fromisoformat(i[2])
            st.write(f"{i[0]} — {t.strftime('%H:%M')}")
            st.caption(i[1])

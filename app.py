import streamlit as st
from datetime import datetime
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")
create_tables()

st.sidebar.title("DoseSafe")

# -------------------------
# LOGIN MODE
# -------------------------
login_mode = st.sidebar.selectbox("Login Type", ["School Staff", "Admin"])

# =========================
# ADMIN LOGIN
# =========================
if login_mode == "Admin":
    username = st.sidebar.text_input("Admin Username")
    password = st.sidebar.text_input("Admin PIN", type="password")

    if username != "Admin" or password != "1234":
        st.stop()

    st.sidebar.success("Admin logged in")

    st.title("⚙️ Admin Panel")

    # -------------------------
    # ALL SCHOOLS
    # -------------------------
    st.subheader("🏫 Schools")
    schools = get_schools()

    if not schools:
        st.info("No schools yet")
    else:
        for s in schools:
            st.write(f"• {s}")

    st.divider()

    # -------------------------
    # STAFF MANAGEMENT
    # -------------------------
    st.subheader("👩‍🏫 Staff Management")

    for s in get_all_staff():
        sid, name, school, active = s

        col1, col2 = st.columns([3,1])

        with col1:
            status = "🟢" if active else "🔴"
            st.write(f"{status} {name} ({school})")

        with col2:
            if active:
                if st.button("Disable", key=f"d{sid}"):
                    set_staff_active(sid, 0)
                    st.rerun()
            else:
                if st.button("Enable", key=f"e{sid}"):
                    set_staff_active(sid, 1)
                    st.rerun()

    st.divider()

    # -------------------------
    # ADD STAFF
    # -------------------------
    st.subheader("➕ Add Staff")

    new_name = st.text_input("Name")
    new_pin = st.text_input("PIN")
    new_school = st.text_input("School")

    if st.button("Add Staff"):
        if new_name and new_pin and new_school:
            add_staff(new_name, new_pin, new_school)
            set_subscription(new_school, "active", "2099-12-31")
            st.success("Staff added + subscription created")
            st.rerun()
        else:
            st.warning("Fill all fields")

    st.divider()

    # -------------------------
    # SUBSCRIPTIONS
    # -------------------------
    st.subheader("💳 Subscription Control")

    school_name = st.text_input("School Name")
    status = st.selectbox("Status", ["active", "inactive"])
    expiry = st.date_input("Expiry Date")

    if st.button("Update Subscription"):
        set_subscription(school_name, status, str(expiry))
        st.success("Updated")

    st.stop()

# =========================
# SCHOOL LOGIN
# =========================
schools = get_schools()
school = st.sidebar.selectbox("School", ["--"] + schools)

if school == "--":
    st.stop()

staff_list = get_staff_by_school(school)
names = [s[1] for s in staff_list]

staff = st.sidebar.selectbox("Staff", ["--"] + names)
pin = st.sidebar.text_input("PIN", type="password")

if staff == "--" or not pin:
    st.stop()

if not verify_staff(staff, pin, school):
    st.error("Invalid login")
    st.stop()

# -------------------------
# SUBSCRIPTION CHECK
# -------------------------
sub = get_subscription(school)

if not sub:
    set_subscription(school, "active", "2099-12-31")
    sub = get_subscription(school)

status, expiry = sub

if status != "active":
    st.error("Account inactive")
    st.stop()

if expiry:
    if datetime.now().date() > datetime.fromisoformat(expiry).date():
        st.error("Subscription expired")
        st.stop()

# -------------------------
# ADD CHILD (SIDEBAR)
# -------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Add Child")

name = st.sidebar.text_input("First Name")
surname = st.sidebar.text_input("Surname")
dob = st.sidebar.date_input("DOB")

allergy_data = get_allergies()
allergy_map = {a[1]: a[0] for a in allergy_data}

selected_allergies = st.sidebar.multiselect("Allergies", list(allergy_map.keys()))

if st.sidebar.button("Add Child"):
    cid = add_child(name, surname, str(dob), school)
    if cid:
        add_child_allergies(cid, [allergy_map[a] for a in selected_allergies])
        st.rerun()

# -------------------------
# MAIN APP
# -------------------------
st.title("DoseSafe")

children = get_children(school)

if not children:
    st.info("Add a child to begin")
    st.stop()

child_map = {f"{c[1]} {c[2]}": c[0] for c in children}

selected = st.selectbox("Select Child", ["--"] + list(child_map.keys()))

if selected == "--":
    st.stop()

cid = child_map[selected]

# -------------------------
# TABS
# -------------------------
tab1, tab2, tab3 = st.tabs(["Medication", "Incidents", "Reports"])

# -------------------------
# MEDICATION
# -------------------------
with tab1:
    for m in get_meds(cid):
        mid, _, name, dose, interval, unit = m

        st.subheader(name)
        st.caption(f"{dose} {unit} • every {interval} hrs")

        last = get_last_dose_full(mid)

        if last:
            t = datetime.fromisoformat(last[0])
            st.write(f"Last: {t.strftime('%H:%M')} ({last[1]})")

        if st.button(f"Give {name}", key=f"g{mid}"):
            log_dose(mid, staff)
            st.rerun()

    st.markdown("### ➕ Add Medication")

    lib = get_med_library()
    lib_map = {f"{m[1]} ({m[2]})": m for m in lib}

    sel = st.selectbox("Medication", list(lib_map.keys()))
    dose = st.text_input("Dosage")
    interval = st.number_input("Interval", min_value=1)

    if st.button("Add"):
        m = lib_map[sel]
        add_med(cid, m[1], dose, interval, m[2])
        st.rerun()

# -------------------------
# INCIDENTS
# -------------------------
with tab2:
    itype = st.selectbox("Type", ["Injury","Illness","Allergic Reaction","Other"])
    desc = st.text_input("Description")

    if st.button("Log Incident"):
        add_incident(cid, itype, desc, staff)
        st.rerun()

    for i in get_incidents(cid):
        t = datetime.fromisoformat(i[4])
        st.write(f"{i[2]} - {t.strftime('%H:%M')}")
        st.caption(i[3])

# -------------------------
# REPORTS
# -------------------------
with tab3:
    if st.button("Generate Report"):
        logs = get_today_logs(cid)
        incs = get_today_incidents(cid)

        out = []
        out.append("MEDICATION:")
        for l in logs:
            t = datetime.fromisoformat(l[1])
            out.append(f"{l[0]} {t.strftime('%H:%M')} {l[2]}")

        out.append("\nINCIDENTS:")
        for i in incs:
            t = datetime.fromisoformat(i[2])
            out.append(f"{i[0]} {t.strftime('%H:%M')}")

        st.text_area("Report", "\n".join(out), height=300)

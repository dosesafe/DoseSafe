import streamlit as st
from datetime import datetime, timedelta
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")

create_tables()

st.sidebar.title("DoseSafe")

# -------------------------
# LOGIN (SIDEBAR)
# -------------------------
schools = get_schools()
selected_school = st.sidebar.selectbox("🏫 School", ["--"] + schools)

if selected_school == "--":
    st.stop()

staff_list = get_staff_by_school(selected_school)
staff_names = [s[1] for s in staff_list]

staff_name = st.sidebar.selectbox("👩‍🏫 Staff", ["--"] + staff_names)
staff_pin = st.sidebar.text_input("PIN", type="password")

if staff_name == "--" or not staff_pin:
    st.stop()

if not verify_staff(staff_name, staff_pin, selected_school):
    st.sidebar.error("Invalid PIN")
    st.stop()

st.sidebar.success(f"{staff_name}")

# -------------------------
# ADMIN AUTO-ACCESS
# -------------------------
is_admin = staff_name.lower() == "admin"

# -------------------------
# ADMIN PANEL (AUTO OPEN)
# -------------------------
if is_admin:
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Admin Panel")

    name = st.sidebar.text_input("Staff Name")
    pin = st.sidebar.text_input("Staff PIN")
    school = st.sidebar.text_input("School")

    if st.sidebar.button("Add Staff"):
        if name and pin and school:
            add_staff(name, pin, school)
            st.sidebar.success("Added")

    st.sidebar.subheader("Staff Management")

    for s in get_all_staff():
        sid, n, sch, active = s

        col1, col2 = st.sidebar.columns([3,1])

        with col1:
            status = "🟢" if active else "🔴"
            st.write(f"{status} {n} ({sch})")

        with col2:
            if active:
                if st.button("❌", key=f"d{sid}"):
                    set_staff_active(sid, 0)
                    st.rerun()
            else:
                if st.button("✅", key=f"e{sid}"):
                    set_staff_active(sid, 1)
                    st.rerun()

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
    cid = add_child(name, surname, str(dob), selected_school)

    if cid:
        add_child_allergies(cid, [allergy_map[a] for a in selected_allergies])
        st.sidebar.success("Child added")
    else:
        st.sidebar.warning("Child already exists")

    st.rerun()

# -------------------------
# MAIN SCREEN
# -------------------------
st.title("DoseSafe")

children = get_children(selected_school)

if not children:
    st.info("Add a child to begin")
    st.stop()

child_map = {f"{c[1]} {c[2]}": c[0] for c in children}

selected = st.selectbox("Select Child", ["--"] + list(child_map.keys()))

if selected == "--":
    st.stop()

cid = child_map[selected]
child_data = next(c for c in children if c[0] == cid)

# -------------------------
# CHILD HEADER
# -------------------------
st.subheader(f"{child_data[1]} {child_data[2]}")
st.caption(f"DOB: {child_data[3]}")

allergies = get_child_allergies(cid)
if allergies:
    st.error(f"🚨 Allergies: {', '.join(allergies)}")

st.divider()

# -------------------------
# MEDICATION
# -------------------------
st.header("💊 Medication")

meds = get_meds(cid)

for m in meds:
    mid, _, name, dose, interval = m

    last_full = get_last_dose_full(mid)

    st.subheader(name)
    st.caption(f"{dose} • every {interval} hrs")

    if last_full:
        last_time = datetime.fromisoformat(last_full[0])
        given_by = last_full[1]

        next_time = last_time + timedelta(hours=interval)
        now = datetime.now()

        st.write(f"Last: {last_time.strftime('%H:%M')} ({given_by})")
        st.write(f"Next: {next_time.strftime('%H:%M')}")

        if now < next_time:
            diff = next_time - now
            sec = int(diff.total_seconds())

            h = sec // 3600
            m = (sec % 3600) // 60

            if sec > 1800:
                st.error(f"❌ Too soon ({h}h {m}m)")
            else:
                st.warning(f"⚠️ Due soon ({m} min)")
        else:
            st.success("✅ Safe to give")
    else:
        st.info("No doses recorded")

    if st.button(f"💊 Give {name}", key=f"g{mid}"):
        log_dose(mid, staff_name)
        st.rerun()

    st.divider()

# -------------------------
# ADD MED
# -------------------------
with st.expander("➕ Add Medicine"):
    med_name = st.text_input("Medicine")
    dosage = st.text_input("Dosage")
    interval = st.number_input("Interval (hrs)", min_value=1)

    if st.button("Add Medicine"):
        add_med(cid, med_name, dosage, interval)
        st.rerun()

# -------------------------
# INCIDENTS
# -------------------------
st.header("⚠️ Incidents")

itype = st.selectbox("Type", ["Injury", "Illness", "Allergic Reaction", "Other"])
desc = st.text_input("Description")

if st.button("Log Incident"):
    add_incident(cid, itype, desc, staff_name)
    st.rerun()

for i in get_incidents(cid):
    t = datetime.fromisoformat(i[4])
    st.write(f"{i[2]} - {t.strftime('%H:%M')}")
    st.caption(f"{i[3]}")

# -------------------------
# DAILY REPORT
# -------------------------
st.header("📤 Daily Report")

if st.button("Generate Report"):

    logs = get_today_logs(cid)
    incs = get_today_incidents(cid)

    report = []

    report.append("MEDICATION:")
    if logs:
        for l in logs:
            t = datetime.fromisoformat(l[1])
            report.append(f"- {l[0]} at {t.strftime('%H:%M')} ({l[2]})")
    else:
        report.append("- None")

    report.append("")
    report.append("INCIDENTS:")
    if incs:
        for i in incs:
            t = datetime.fromisoformat(i[2])
            report.append(f"- {i[0]} at {t.strftime('%H:%M')}")
            report.append(f"  {i[1]} ({i[3]})")
    else:
        report.append("- None")

    st.text_area("Report Output", "\n".join(report), height=300)

import streamlit as st
from datetime import datetime, timedelta
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")

col1, col2 = st.columns([1, 4])

with col1:
    st.image("DoseSafe.png", width=300)

with col2:
    #st.title("DoseSafe")
    st.caption("Safe medicine tracking for children")

create_tables()

# -------------------------
# SIDEBAR - ADD CHILD
# -------------------------
with st.sidebar:
    st.header("👶 Add Child")

    name = st.text_input("First Name")
    surname = st.text_input("Surname")
    dob = st.date_input("Date of Birth")
    school = st.text_input("School")

    if st.button("Add Child"):
        if name and surname:
            add_child(name, surname, str(dob), school)
            st.success("Child added")
            st.rerun()

# -------------------------
# SELECT CHILD + SEARCH
# -------------------------
children = get_children()

if not children:
    st.info("Add a child to get started")
    st.stop()

# 🔍 SEARCH BOX (ADD HERE)
search = st.text_input("🔍 Search child (name or surname)")

# FILTER
if search:
    filtered_children = [
        c for c in children
        if search.lower() in (c[1] + " " + c[2]).lower()
    ]
else:
    filtered_children = children

if not filtered_children:
    st.warning("No matching children found")
    st.stop()

# DISPLAY LIST
child_display = [
    f"{c[1]} {c[2]} ({c[3]})" for c in filtered_children
]

selected_display = st.selectbox("Select Child", child_display)

selected_child = next(
    c for c in filtered_children
    if f"{c[1]} {c[2]} ({c[3]})" == selected_display
)

child_id = selected_child[0]

# -------------------------
# ADD MED
# -------------------------
with st.expander("➕ Add Medicine"):
    med_name = st.text_input("Medicine name")
    dosage = st.text_input("Dosage")
    interval = st.number_input("Hours between doses", min_value=1)

    if st.button("Add Medicine"):
        add_med(child_id, med_name, dosage, interval)
        st.success("Medicine added")
        st.rerun()

# -------------------------
# SHOW MEDS
# -------------------------
st.header("Today's Doses")
given_by = st.text_input("👩‍⚕️ Who is giving the medication?")

meds = get_meds_by_child(child_id)

if not meds:
    st.info("No medicines for this child yet")

for med in meds:
    id, child_id, name, dosage, interval = med

    st.subheader(name)
    st.caption(f"{dosage} • every {interval} hrs")

    last = get_last_dose(id)

    if last:
        last_time = datetime.fromisoformat(last)
        next_time = last_time + timedelta(hours=interval)
        now = datetime.now()

        minutes_ago = int((now - last_time).total_seconds() / 60)

        st.write(f"🕒 Last given: {last_time.strftime('%H:%M')} ({minutes_ago} min ago)")

        # ✅ ALWAYS show next dose time
        st.write(f"⏭️ Next dose at: {next_time.strftime('%H:%M')}")

        # Status indicator
        if now < next_time:
            remaining_seconds = int((next_time - now).total_seconds())

            hours = remaining_seconds // 3600
            minutes = (remaining_seconds % 3600) // 60

            if hours > 0:
                st.error(f"❌ Too soon ({hours}h {minutes}m remaining)")
            else:
                st.error(f"❌ Too soon ({minutes} min remaining)")
        else:
            st.success("✅ Safe to give now")

    else:
        st.info("No doses recorded yet")

    if st.button(f"💊 Give {name}", key=id, use_container_width=True):
        if not given_by:
            st.warning("Please enter who is giving the medication")
        else:
            log_dose(id, datetime.now().isoformat(), given_by)
            st.rerun()
        
    with st.expander("📋 Dose History"):
        logs = get_logs_by_med(id)

        if not logs:
            st.write("No history yet")
        else:
            for log in logs:
                time_given = datetime.fromisoformat(log[0])
                given_by_name = log[1] if log[1] else "Unknown"

                st.write(f"💊 {time_given.strftime('%d %b %H:%M')} – 👩‍⚕️ {given_by_name}")    

    st.divider()

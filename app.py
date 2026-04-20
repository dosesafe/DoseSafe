import streamlit as st
from datetime import datetime, timedelta
from database import *

st.set_page_config(page_title="DoseSafe", layout="centered")

st.title("🛡️ DoseSafe")
st.caption("Safe medicine tracking for children")

create_tables()

# -------------------------
# SIDEBAR - ADD CHILD
# -------------------------
with st.sidebar:
    st.header("👶 Add Child")
    child_name = st.text_input("Child name")

    if st.button("Add Child"):
        if child_name:
            add_child(child_name)
            st.success("Child added")
            st.rerun()

# -------------------------
# SELECT CHILD
# -------------------------
children = get_children()

if not children:
    st.info("Add a child to get started")
    st.stop()

child_names = [c[1] for c in children]
selected_name = st.selectbox("Select Child", child_names)

selected_child = next(c for c in children if c[1] == selected_name)
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
            remaining = int((next_time - now).total_seconds() / 60)
            st.error(f"❌ Too soon ({remaining} min remaining)")
        else:
            st.success("✅ Safe to give now")

    else:
        st.info("No doses recorded yet")

    if st.button(f"💊 Give {name}", key=id, use_container_width=True):
        log_dose(id, datetime.now().isoformat())
        st.rerun()

    st.divider()

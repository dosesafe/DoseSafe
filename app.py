import streamlit as st
from datetime import datetime, timedelta
from database import *

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(
    page_title="Medicine Tracker",
    layout="centered"
)

st.title("👶 Medicine Tracker")
st.caption("Track doses and know exactly when it's safe to give again")

create_tables()

# -----------------------
# ADD MED (SIDEBAR)
# -----------------------
with st.sidebar:
    st.header("➕ Add Medicine")

    name = st.text_input("Medicine Name")
    dosage = st.text_input("Dosage (e.g. 5ml)")
    interval = st.number_input("Hours between doses", min_value=1, step=1)

    if st.button("Add Medicine"):
        if name:
            add_med(name, dosage, interval)
            st.success("Added!")
            st.rerun()
        else:
            st.warning("Enter a name")

# -----------------------
# MAIN VIEW
# -----------------------
st.header("Today")

meds = get_meds()

if not meds:
    st.info("No medicines added yet")
else:
    for med in meds:
        id, name, dosage, interval = med

        st.subheader(name)
        st.caption(f"{dosage} • every {interval} hrs")

        last = get_last_dose(id)

        if last:
            last_time = datetime.fromisoformat(last)
            next_time = last_time + timedelta(hours=interval)
            now = datetime.now()

            st.write(f"🕒 Last given: {last_time.strftime('%H:%M')}")

            if now < next_time:
                st.error(f"❌ Next dose at {next_time.strftime('%H:%M')}")
            else:
                st.success("✅ Safe to give now")

        else:
            st.info("No doses recorded yet")

        # BIG BUTTON (mobile friendly)
        if st.button(f"💊 Give {name}", key=id, use_container_width=True):
            log_dose(id, datetime.now().isoformat())
            st.rerun()

        st.divider()
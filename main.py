import streamlit as st
import fastf1
import matplotlib.pyplot as plt
import os
import pandas as pd
from datetime import datetime

if not os.path.exists('cache'):
    os.makedirs('cache')

fastf1.Cache.enable_cache('cache')
st.title("F1 LAP COMPARISON TOOL 🏎️ 🏎️ ")
st.markdown("By Omkar Gajare - Bhartiya Vidya Bhavan's Sardar Patel Institute of Technology")

year = st.number_input("Select Year", min_value=2000, max_value=2025, value=2025, step=1)
@st.cache_data
def get_schedule(year):
    return fastf1.get_event_schedule(year)
try:
    schedule = get_schedule(year)
    if 'Date' in schedule.columns:
        date_col = 'Date'
    elif 'EventDate' in schedule.columns:
        date_col = 'EventDate'
    else:
        st.warning("Could not find date column in schedule; showing all races.")
        date_col = None

    if date_col:
        schedule[date_col] = pd.to_datetime(schedule[date_col]).dt.date
        today = datetime.today().date()
        available_races = schedule[schedule[date_col] <= today]['EventName'].tolist()
    else:
        available_races = schedule['EventName'].tolist()
except Exception as e:
    st.error(f"Could not get schedule from {e}")
    available_races = []
selected_race = st.selectbox("Select Race", available_races)

session_type  = st.selectbox("Select Session Type", ['FP1','FP2','FP3','Q','R'])


@st.cache_data

def load_session(year, race_name, session_type):
    session = fastf1.get_session(year, race_name, session_type)
    session.load()
    return session
try:
    session_for_drivers = load_session(year, selected_race, session_type)
    drivers_this_year = []
    for d in session_for_drivers.drivers:
        driver = session_for_drivers.get_driver(d)
        try:
            code = getattr(driver, 'Abbreviation',None) or driver["Abbreviation"]
        except Exception:
            code = str(d)
        drivers_this_year.append(code)
except Exception as e:
    st.error(f'Could not load session to get drivers: {e}')
    drivers_this_year = []
driver1 = st.selectbox("Select Driver 1", drivers_this_year)
driver2 = st.selectbox("Select Driver 2", drivers_this_year)
def compare_fastest_lap(year,race_name,session_type, driver1, driver2):
    try:
        session = load_session(year,race_name,session_type)

        lap_driver1 = session.laps.pick_driver(driver1).pick_fastest()
        lap_driver2 = session.laps.pick_driver(driver2).pick_fastest()

        if lap_driver1 is None or lap_driver2 is None:
            st.error("One or both drivers have no laps in this session.")
            return

        tel1 = lap_driver1.get_car_data().add_distance()
        tel2 = lap_driver2.get_car_data().add_distance()

        metrics = ["Speed","Throttle","Brake","Gear","RPM"]
        colors = {"driver1":"red", "driver2":"blue"}
        for metric in metrics:
            with st.expander(f"{metric} telemetry"):
                fig,ax = plt.subplots(figsize = (10,6))
                if metric in tel1.columns and metric in tel2.columns:
                    ax.plot(tel1['Distance'], tel1[metric], label = driver1, color = colors["driver1"])
                    ax.plot(tel2['Distance'], tel2[metric], label = driver2, color = colors["driver2"])
                    ax.set_xlabel('Distance [meters]')
                    ax.set_ylabel(metric)
                    ax.set_title(f"{race_name} {year} {session_type} – {driver1} vs {driver2} ({metric})")
                    ax.legend()
                    st.pyplot(fig)
                else:
                    st.warning(f"{metric} data not available for this session.")
                plt.close(fig)

    except Exception as e:
        st.error(f'Error loading session from {e}')

if st.button("Compare F1 Laptime"):
    if driver1 == driver2:
        st.warning("Please select two different drivers.")
    else:
        compare_fastest_lap(year, selected_race, session_type, driver1, driver2)
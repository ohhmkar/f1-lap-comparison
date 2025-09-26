import streamlit as st
import fastf1
import matplotlib.pyplot as plt

fastf1.Cache.enable_cache('cache')
st.title("F1 LAP COMPARISON TOOL 🏎️ 🏎️ ")
st.markdown("By Omkar Gajare - Bhartiya Vidya Bhavan's Sardar Patel Institute of Technology")

year = st.number_input("Select Year", min_value=2000, max_value=2025, value=2025, step=1)
try:
    schedule = fastf1.get_event_schedule(year)
    available_races = schedule['EventName'].tolist()
except Exception as e:
    st.error(f'Could not get schedule from {e}')
    available_races = []

selected_race = st.selectbox("Select Race", available_races)

session_type  = st.selectbox("Select Session Type", ['FP1','FP2','FP3','Qualifying','Race'])

driver_codes = [
    'HAM', 'VER', 'LEC', 'RUS', 'PER', 'SAI', 'NOR', 'ALO', 'TSU', 'OCO',
    'MAG', 'GAS', 'STR', 'BOT', 'ZHO', 'LAT', 'VET', 'MSC', 'RIC','PIA','ANT'
]
driver1 = st.selectbox("Select Driver 1", driver_codes)
driver2 = st.selectbox("Select Driver 2", driver_codes)

def compare_fastest_lap(year,race_name,session_type, driver1, driver2):
    try:
        session = fastf1.get_session(year, race_name, session_type)
        session.load()

        lap_driver1 = session.laps.pick_driver(driver1).pick_fastest_lap()
        lap_driver2 = session.laps.pick_driver(driver2).pick_fastest_lap()

        if lap_driver1 is None or lap_driver2 is None:
            st.error("One or both drivers have no laps in this session.")
            return

        tel1 = lap_driver1.get_car_data().add_distance()
        tel2 = lap_driver2.get_car_data().add_distance()

        plt.figure(figsize = (10,10))
        plt.plot(tel1['Distance'], tel1['Speed'], label = driver1, color = 'red')
        plt.plot(tel2['Distance'], tel2['Speed'], label = driver2, color = 'blue')
        plt.xlabel('Distance [meters]')
        plt.ylabel('Speed [km/h]')
        plt.title(f"{race_name} {year} {session_type} – {driver1} vs {driver2}")
        plt.legend()

        st.pyplot(plt)
        plt.close()

    except Exception as e:
        st.error(f'Error loading session from {e}')

if st.button("Compare F1 Laptime"):
    compare_fastest_lap(year,selected_race,session_type,driver1,driver2)
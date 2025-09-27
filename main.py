import streamlit as st
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import os
import pandas as pd
from datetime import datetime
from fontTools.mtiLib import parseLookupRecords

st.markdown(
    """
    <style>
    /* Main app background */
    body {
        background-color: #1e1e1e;
        color: #ffffff;             
    }

    /* Sidebar background */
    .sidebar .sidebar-content {
        background-color: #2b2b2b;
        color: #ffffff;
    }

    /* Headers and titles */
    .stTitle, h1, h2, h3 {
        color: #ff0000;
    }

    /* Buttons */
    .stButton button {
        background-color: #ff0000;
        color: #ffffff;
        border-radius: 5px;
    }

    /* Expander headers */
    .st-expander {
        background-color: #2b2b2b;
        color: #ffffff;
    }

    /* Plot container background */
    .stPlotlyChart, .element-container {
        background-color: #1e1e1e;
    }
    </style>
    """,
    unsafe_allow_html=True
)
#________________________ SETUP ____________________________

if not os.path.exists('cache'):
    os.makedirs('cache')

fastf1.Cache.enable_cache('cache')
st.title("F1 Data Analysis Dashboard 🏎️ 🏎️ ")
st.markdown("By **Omkar Gajare - Bhartiya Vidya Bhavan's Sardar Patel Institute of Technology**")

# ----------------------- SIDEBAR --------------------
with st.sidebar:
    year = st.number_input("Year", min_value=2018, max_value=datetime.now().year,value=datetime.now().year)
    session_type = st.selectbox("Select Session Type", ["FP1","FP2","FP3","Q","R"])

@st.cache_data
def get_schedule(year):
    return fastf1.get_event_schedule(year)

def get_season_standings(year):
    try:
        return fastf1.get_driver_standings(year)
    except Exception:
        return pd.DataFrame()
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
        available_races = schedule[(schedule[date_col] <= today)&(~schedule["EventName"].str.contains("Testing",case = False))]['EventName'].tolist()
    else:
        available_races = [race for race in schedule["EventName"].tolist() if "Testing" or "Test" not in race]
except Exception as e:
    st.error(f"Could not get schedule from {e}")
    available_races = []
with st.sidebar:
    selected_race = st.selectbox("Select Race", available_races)
#-------------------- LOAD SESSION ---------------------------


@st.cache_data

def load_session(year, race_name, session_type):
    session = fastf1.get_session(year, race_name, session_type)
    session.load()
    return session


session = load_session(year,selected_race,session_type)
drivers_this_year = []
for d in session.drivers:
    driver_obj = session.get_driver(d)
    try:
        code = getattr(driver_obj, "Abbreviation",None) or driver_obj["Abbreviation"]
    except:
        code = str(d)
    drivers_this_year.append(code)
selected_drivers = st.sidebar.multiselect("Select up to 5 drivers",drivers_this_year,max_selections=5)

#---------------------------- FUNCTIONS ------------------------------------------

def plot_telemetry(drivers, metrics=["Speed","Throttle","Brake","RPM"]):
    colors = plt.cm.tab10.colors
    for metric in metrics:
        with st.expander(f"{metric} Telemetry", expanded=False):
            fig, ax = plt.subplots(figsize=(10,6))
            for idx, driver in enumerate(drivers):
                lap = session.laps.pick_driver(driver).pick_fastest()
                if lap is None:
                    continue
                tel = lap.telemetry.add_distance()
                if metric in tel.columns:
                    ax.plot(tel['Distance'], tel[metric], label=driver, color=colors[idx % len(colors)])
            ax.set_xlabel("Distance [m]")
            ax.set_ylabel(metric)
            ax.set_title(f"{metric} Comparison - {selected_race} {year}")
            ax.legend()
            st.pyplot(fig)
            plt.close(fig)

def plot_laptimes(drivers):
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.tab10.colors  # fallback colors
    markers = ['o', 's', '^', 'D', 'P', '*', 'X', 'v']  # marker variety for compounds

    for idx, driver in enumerate(drivers):
        laps = session.laps.pick_driver(driver).reset_index()
        if laps.empty:
            continue

        compounds = laps['Compound'].unique()
        for i, comp in enumerate(compounds):
            comp_laps = laps[laps['Compound'] == comp]
            # pick color (you can replace this with team colors if available)
            color = colors[idx % len(colors)]
            ax.scatter(
                comp_laps['LapNumber'],
                comp_laps['LapTime'].dt.total_seconds(),
                label=f"{driver} - {comp}",
                color=color,
                marker=markers[i % len(markers)],
                s=80,
                alpha=0.8,
                edgecolors="k"
            )

    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Lap Time [s]")
    ax.invert_yaxis()
    ax.set_title(f"Lap Times - {selected_race} {year}")
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)


def plot_lap_trends(drivers):
    fig, ax = plt.subplots(figsize=(10,6))
    colors = plt.cm.tab10.colors
    for idx, driver in enumerate(drivers):
        laps = session.laps.pick_driver(driver).reset_index()
        laps = laps[laps['PitOutTime'].isna()]
        if laps.empty:
            continue
        lap_times_sec = laps['LapTime'].dt.total_seconds()
        smoothed_lap_time = lap_times_sec.rolling(window=5,min_periods=1).mean()
        ax.plot(laps['LapNumber'],smoothed_lap_time,label=driver, color=colors[idx % len(colors)])
    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Lap Time [s]")
    ax.set_title("Lap Time Trends")
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)


tab1,tab2,tab3 = st.tabs(["Telemetry 📊","⏰Lap Times","Lap Trends📊"])
with tab1:
    if len(selected_drivers) >= 2:
            plot_telemetry(selected_drivers)
    elif len(selected_drivers) == 1:
        st.info("Pick atleast 2 drivers for **Comparison**")
    else:
        st.warning("Select drivers from the sidebar 👈")
with tab2:
    if len(selected_drivers) >= 1:
        plot_laptimes(selected_drivers)
    else:
        st.warning("Select drivers from the sidebar 👈")
with tab3:
    if len(selected_drivers) >= 2:
        plot_lap_trends(selected_drivers)
    else:
        st.warning("Select drivers from the sidebar 👈")

import streamlit as st
import pandas as pd
import altair as alt
import requests
import os

API_URL = "https://smart-chicken-coop.onrender.com"  # <-- cambia esto
st.set_page_config(page_title="Egg Farm Dashboard", layout="wide")

st.title("📊 Smart_Chicken_Coop")

# --- Token Login ---
API_TOKEN = os.environ.get("API_TOKEN", "")
headers = headers = {
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {API_TOKEN}'
}

# --- Coop selection ---
coop_id = st.text_input("Coop ID", value="coop_1")

# --- Date filters ---
start_date = st.date_input("Desde", pd.to_datetime("2025-01-01"))
end_date = st.date_input("Hasta", pd.to_datetime("today"))

# --- Función para traer datos desde Flask API ---
@st.cache_data(ttl=300)
def fetch_data(endpoint):
    try:
        url = f"{API_URL}/{endpoint}?coop_id={coop_id}&start={start_date}&end={end_date}"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
        else:
            st.warning(f"Error ({res.status_code}): {res.text}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

# --- Egg Production & Feed Logs ---
st.subheader("🥚 Producción, 🍽️ Alimento servido, 💊 Desparasitación")
log_df = fetch_data("daily-logs-range")
if not log_df.empty:
    log_df["date"] = pd.to_datetime(log_df["date"])
    base = alt.Chart(log_df).encode(x='date:T')

    egg_chart = base.mark_bar(color='orange').encode(y='eggs_collected:Q').properties(title="Huevos por día")
    feed_given_chart = base.mark_line(color='green').encode(y='feed_given_g:Q').properties(title="Alimento servido (g)")
    dewormer_chart = base.mark_point(size=100).encode(
        y=alt.value(0), color=alt.condition("datum.dewormed == 1", alt.value("purple"), alt.value("transparent")),
        tooltip=["date", "dewormed"]
    ).properties(title="Días con desparasitación")

    st.altair_chart(egg_chart & feed_given_chart & dewormer_chart, use_container_width=True)

# --- Sensor Data ---
st.subheader("🌡️ Temperatura y 💧 Humedad")
sensor_df = fetch_data("sensor-data-range")
if not sensor_df.empty:
    sensor_df["timestamp"] = pd.to_datetime(sensor_df["timestamp"])
    temp_chart = alt.Chart(sensor_df).mark_line(color='red').encode(
        x='timestamp:T', y='temperature:Q', tooltip=['timestamp', 'temperature']
    ).properties(title="Temperatura (°C)")
    
    hum_chart = alt.Chart(sensor_df).mark_line(color='blue').encode(
        x='timestamp:T', y='humidity:Q', tooltip=['timestamp', 'humidity']
    ).properties(title="Humedad (%)")
    
    st.altair_chart(temp_chart & hum_chart, use_container_width=True)

# --- Feed Weight ---
st.subheader("⚖️ Peso del Comedero")
feed_df = fetch_data("feed-data-range")
if not feed_df.empty:
    feed_df["timestamp"] = pd.to_datetime(feed_df["timestamp"])
    feed_chart = alt.Chart(feed_df).mark_line(color='green').encode(
        x='timestamp:T', y='feed_weight:Q', tooltip=['timestamp', 'feed_weight']
    ).properties(title="Peso del alimento (g)")
    st.altair_chart(feed_chart, use_container_width=True)


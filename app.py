import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Weather Forecast", page_icon="🌦️", layout="centered")

st.title("🌍 OpenWeatherMap Forecast App with Interactive Map")

# Input city
city = st.text_input("Enter city name:", "Chennai")

# Load API key securely from Streamlit Secrets
API_KEY = st.secrets["c1fed68d02f226d73e811e6cce276bf6"]

if st.button("Get Weather"):
    URL = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(URL).json()

    if response.get("cod") == 200:
        temp = response['main']['temp']
        humidity = response['main']['humidity']
        weather = response['weather'][0]['description']
        rain = response.get('rain', {}).get('1h', 0)
        lat = response['coord']['lat']
        lon = response['coord']['lon']

        st.success(f"✅ Weather data for {city}")
        st.write(f"🌡️ Temperature: {temp} °C")
        st.write(f"💧 Humidity: {humidity}%")
        st.write(f"🌧️ Rainfall (last 1h): {rain} mm")
        st.write(f"☁️ Condition: {weather}")

        # Flood risk logic
        if rain > 50 or humidity > 85:
            st.error("🚨 Flood Risk Alert!")
        else:
            st.info("✅ No flood risk detected.")

        # 🗺️ Interactive Folium map
        st.subheader("🗺️ City Location")
        m = folium.Map(location=[lat, lon], zoom_start=10)
        folium.Marker(
            [lat, lon],
            tooltip=f"{city}: {weather}, {temp}°C",
            popup=f"🌡️ {temp}°C\n💧 {humidity}%\n🌧️ {rain}mm",
            icon=folium.Icon(color="blue", icon="cloud")
        ).add_to(m)

        # Render map in Streamlit
        st_folium(m, width=700, height=500)

    else:
        st.error("❌ Error: Invalid city or API key")

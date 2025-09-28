import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Weather Debug App", page_icon="🌦️", layout="centered")

st.title("🌍 OpenWeatherMap + Map (Debug Mode)")

# 🔑 Load API key safely
try:
    API_KEY = st.secrets["apikey.txt"]
    st.success("✅ API Key loaded successfully")
except Exception as e:
    st.error("❌ Could not load API Key from secrets")
    st.stop()

# 🌍 Input city
city = st.text_input("Enter city name:", "Chennai")

if st.button("Get Weather"):
    # Make API request
    URL = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(URL).json()

    # Show raw JSON for debugging
    st.subheader("🔍 API Raw Response")
    st.json(response)

    if response.get("cod") == 200:
        # Extract data
        temp = response['main']['temp']
        humidity = response['main']['humidity']
        weather = response['weather'][0]['description']
        rain = response.get('rain', {}).get('1h', 0)
        lat = response['coord']['lat']
        lon = response['coord']['lon']

        # Display clean summary
        st.subheader(f"✅ Weather in {city}")
        st.write(f"🌡️ Temp: {temp} °C")
        st.write(f"💧 Humidity: {humidity}%")
        st.write(f"🌧️ Rainfall (last 1h): {rain} mm")
        st.write(f"☁️ Condition: {weather}")

        # Flood risk check
        if rain > 50 or humidity > 85:
            st.error("🚨 Flood Risk Alert!")
        else:
            st.info("✅ No flood risk detected.")

        # Map with weather marker
        st.subheader("🗺️ City Map")
        m = folium.Map(location=[lat, lon], zoom_start=10)
        folium.Marker(
            [lat, lon],
            tooltip=f"{city}: {weather}, {temp}°C",
            popup=f"🌡️ {temp}°C | 💧 {humidity}% | 🌧️ {rain}mm",
            icon=folium.Icon(color="blue", icon="cloud")
        ).add_to(m)
        st_folium(m, width=700, height=500)

    else:
        # Fallback if API error
        st.error(f"❌ API Error: {response.get('message', 'Unknown error')}")
        st.subheader("🗺️ Showing fallback map (Chennai)")
        m = folium.Map(location=[13.08, 80.27], zoom_start=10)
        folium.Marker([13.08, 80.27], popup="Fallback: Chennai").add_to(m)
        st_folium(m, width=700, height=500)

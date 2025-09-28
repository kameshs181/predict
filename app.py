import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

st.set_page_config(page_title="Weather + Forecast App", page_icon="🌦️", layout="centered")

st.title("🌍 OpenWeatherMap: Current Weather & 5-Day Forecast")

# 🔑 Load API key
try:
    API_KEY = st.secrets["API_KEY"]
    st.success("✅ API Key loaded successfully")
except Exception:
    st.error("❌ Could not load API Key from secrets. Please add API_KEY in Streamlit Cloud → Secrets")
    st.stop()

# 🌍 Input city
city = st.text_input("Enter city name:", "Chennai")

if st.button("Get Weather & Forecast"):
    # 🌦️ Current Weather
    URL_CURRENT = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(URL_CURRENT).json()

    # 🔍 Debug: Show raw response
    st.subheader("🔍 API Raw Response (Current)")
    st.json(response)

    if response.get("cod") == 200:
        # Extract details
        temp = response['main']['temp']
        humidity = response['main']['humidity']
        weather = response['weather'][0]['description']
        rain = response.get('rain', {}).get('1h', 0)
        lat = response['coord']['lat']
        lon = response['coord']['lon']

        st.subheader(f"✅ Current Weather in {city}")
        st.write(f"🌡️ Temp: {temp} °C")
        st.write(f"💧 Humidity: {humidity}%")
        st.write(f"🌧️ Rainfall (last 1h): {rain} mm")
        st.write(f"☁️ Condition: {weather}")

        # 🚨 Flood risk
        if rain > 50 or humidity > 85:
            st.error("🚨 Flood Risk Alert!")
        else:
            st.info("✅ No flood risk detected.")

        # 🗺️ City Map
        st.subheader("🗺️ City Location")
        m = folium.Map(location=[lat, lon], zoom_start=10)
        folium.Marker(
            [lat, lon],
            tooltip=f"{city}: {weather}, {temp}°C",
            popup=f"🌡️ {temp}°C | 💧 {humidity}% | 🌧️ {rain}mm",
            icon=folium.Icon(color="blue", icon="cloud")
        ).add_to(m)
        st_folium(m, width=700, height=500)

        # 📊 5-Day Forecast
        st.subheader("📊 5-Day Forecast (3h intervals)")
        URL_FORECAST = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        forecast = requests.get(URL_FORECAST).json()

        if forecast.get("cod") == "200":
            df = pd.DataFrame([{
                "datetime": item["dt_txt"],
                "temp": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "rain": item.get("rain", {}).get("3h", 0)
            } for item in forecast["list"]])

            df["datetime"] = pd.to_datetime(df["datetime"])

            # Temperature trend
            st.line_chart(df.set_index("datetime")[["temp"]])

            # Rainfall trend
            st.bar_chart(df.set_index("datetime")[["rain"]])

            # Show data table
            st.dataframe(df.head(15))
        else:
            st.error("❌ Forecast data not available")

    else:
        st.error(f"❌ API Error: {response.get('message', 'Unknown error')}")

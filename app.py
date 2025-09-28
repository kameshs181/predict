import streamlit as st
import requests

st.set_page_config(page_title="Weather Forecast", page_icon="🌦️", layout="centered")

st.title("🌍 OpenWeatherMap Forecast App")

# Input city
city = st.text_input("Enter city name:", "Chennai")

# API Key (replace YOUR_API_KEY with your key for now)
API_KEY = "c1fed68d02f226d73e811e6cce276bf6"
URL = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

if st.button("Get Weather"):
    response = requests.get(URL).json()

    if response.get("cod") == 200:
        temp = response['main']['temp']
        humidity = response['main']['humidity']
        weather = response['weather'][0]['description']
        rain = response.get('rain', {}).get('1h', 0)

        st.success(f"✅ Weather data for {city}")
        st.write(f"🌡️ Temperature: {temp} °C")
        st.write(f"💧 Humidity: {humidity}%")
        st.write(f"🌧️ Rainfall (last 1h): {rain} mm")
        st.write(f"☁️ Condition: {weather}")

        # Simple flood risk logic
        if rain > 50 or humidity > 85:
            st.error("🚨 Flood Risk Alert!")
        else:
            st.info("✅ No flood risk detected.")
    else:
        st.error("❌ Error: Invalid city or API key")

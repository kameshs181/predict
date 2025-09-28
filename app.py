import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Weather Forecast App", page_icon="🌦️", layout="centered")

st.title("🌍 Weather & 5-Day Forecast (OpenWeatherMap)")

# 🔑 Load API Key
try:
    API_KEY = st.secrets["API_KEY"]
except Exception:
    st.error("❌ API key missing. Please add API_KEY in Streamlit Cloud → Settings → Secrets")
    st.stop()

# 🌍 Input city
city = st.text_input("Enter city name:", "Chennai")

if st.button("Get Weather & Forecast"):
    # 🌦️ Current Weather
    url_current = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url_current).json()

    if response.get("cod") == 200:
        # Extract details
        temp = response['main']['temp']
        humidity = response['main']['humidity']
        weather = response['weather'][0]['description']
        rain = response.get('rain', {}).get('1h', 0)
        lat = response['coord']['lat']
        lon = response['coord']['lon']

        st.subheader(f"✅ Current Weather in {city}")
        st.metric("🌡️ Temperature (°C)", f"{temp:.1f}")
        st.metric("💧 Humidity (%)", f"{humidity}")
        st.metric("🌧️ Rainfall (last 1h)", f"{rain} mm")
        st.write(f"☁️ Condition: **{weather}**")

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
        st.subheader("📊 5-Day Forecast (every 3 hours)")
        url_forecast = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        forecast = requests.get(url_forecast).json()

        if forecast.get("cod") == "200":
            df = pd.DataFrame([{
                "datetime": item["dt_txt"],
                "temp": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "rain": item.get("rain", {}).get("3h", 0)
            } for item in forecast["list"]])

            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime")

            st.line_chart(df[["temp"]], height=300, use_container_width=True)
            st.bar_chart(df[["rain"]], height=300, use_container_width=True)

            st.dataframe(df.head(12))  # show first 12 intervals (~1.5 days)
        else:
            st.warning("⚠️ Forecast data not available.")
    else:
        st.error(f"❌ API Error: {response.get('message', 'Unknown error')}")

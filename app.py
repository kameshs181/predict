import streamlit as st
import folium
import pandas as pd
from streamlit_folium import st_folium
from backend.weather_service import WeatherService
from backend.utils import flood_risk_alert

# -------------------------------------------------------------
# Streamlit Page Setup
# -------------------------------------------------------------
st.set_page_config(page_title="AI Weather & Forecast System 🌦️", page_icon="🌍", layout="centered")
st.title("🌍 Intelligent AI-Driven Weather Forecast & Alert System")

# -------------------------------------------------------------
# Load API Key
# -------------------------------------------------------------
try:
    API_KEY = st.secrets["API_KEY"]
except Exception:
    st.error("❌ Could not load API Key. Please add API_KEY in Streamlit Cloud → Settings → Secrets")
    st.stop()

# -------------------------------------------------------------
# Initialize Weather Service
# -------------------------------------------------------------
service = WeatherService(API_KEY)

# -------------------------------------------------------------
# User Input
# -------------------------------------------------------------
city_query = st.text_input("🔍 Enter a city name:", "Chennai")

if city_query:
    lat, lon, city = service.get_coordinates(city_query)

    if lat and lon:
        # -----------------------------------------------------
        # Current Weather
        # -----------------------------------------------------
        current = service.get_current_weather(lat, lon)

        if current:
            icon_url = f"http://openweathermap.org/img/wn/{current['icon']}@2x.png"
            weather = current["weather"].title()
            temp = current["temp"]
            humidity = current["humidity"]
            rain = current["rain"]

            col1, col2 = st.columns([1, 4])
            with col1:
                st.image(icon_url, width=80)
            with col2:
                st.subheader(f"✅ Current Weather in {city}")
                st.write(f"☁️ {weather}")

            st.metric("🌡️ Temperature (°C)", f"{temp:.1f}")
            st.metric("💧 Humidity (%)", f"{humidity}")
            st.metric("🌧️ Rainfall (last 1h)", f"{rain} mm")

            # 🚨 Flood Risk Alert
            alert = flood_risk_alert(humidity, rain)
            if "🚨" in alert:
                st.error(alert)
            elif "⚠️" in alert:
                st.warning(alert)
            else:
                st.info(alert)

            # -----------------------------------------------------
            # Interactive Map with Overlays
            # -----------------------------------------------------
            st.subheader("🗺️ City Location & Live Weather Layers")

            m = folium.Map(location=[lat, lon], zoom_start=6)

            # 🛰️ Base Layers
            folium.TileLayer("OpenStreetMap", name="OSM").add_to(m)
            folium.TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri", name="Esri Satellite", overlay=False, control=True
            ).add_to(m)
            folium.TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
                attr="Esri", name="Esri Terrain", overlay=False, control=True
            ).add_to(m)

            # 🌥️ Cloud overlay
            folium.TileLayer(
                tiles=f"https://tile.openweathermap.org/map/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
                attr="OpenWeatherMap", name="Clouds", overlay=True, control=True, opacity=0.6
            ).add_to(m)

            # 🌧️ Rain overlay
            folium.TileLayer(
                tiles=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
                attr="OpenWeatherMap", name="Precipitation", overlay=True, control=True, opacity=0.6
            ).add_to(m)

            # 💨 Wind overlay
            folium.TileLayer(
                tiles=f"https://tile.openweathermap.org/map/wind_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
                attr="OpenWeatherMap", name="Wind", overlay=True, control=True, opacity=0.6
            ).add_to(m)

            # Marker
            popup_html = f"""
                <div style="text-align:center;">
                    <h4>{city}</h4>
                    <img src="{icon_url}" width="60"><br>
                    🌡️ {temp:.1f} °C<br>
                    💧 {humidity}%<br>
                    🌧️ {rain} mm<br>
                    ☁️ {weather}
                </div>
            """
            folium.Marker(
                [lat, lon],
                tooltip=f"{city}: {weather}, {temp}°C",
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color="blue", icon="cloud")
            ).add_to(m)

            folium.LayerControl().add_to(m)
            st_folium(m, width=700, height=500)

            # -----------------------------------------------------
            # 5-Day / 3-Hour Forecast
            # -----------------------------------------------------
            st.subheader("📊 5-Day / 3-Hour Forecast")

            forecast_df = service.get_forecast(lat, lon)

            if forecast_df is not None:
                forecast_df["datetime"] = pd.to_datetime(forecast_df["datetime"])
                forecast_df = forecast_df.set_index("datetime")

                st.line_chart(forecast_df[["temp"]], height=300, use_container_width=True)
                st.bar_chart(forecast_df[["rain"]], height=300, use_container_width=True)

                # Add icons
                def add_icon(row):
                    return f'<img src="http://openweathermap.org/img/wn/{row["icon"]}.png" width="35"> {row["condition"].title()}'

                df_display = forecast_df.copy()
                df_display["Weather"] = df_display.apply(add_icon, axis=1)

                st.markdown("### Forecast Table")
                st.write(
                    df_display[["temp", "humidity", "rain", "Weather"]].head(12).to_html(escape=False),
                    unsafe_allow_html=True
                )
            else:
                st.warning("⚠️ Forecast data not available.")
        else:
            st.error("❌ Could not fetch current weather data.")
    else:
        st.warning("⚠️ No city found, please try again.")

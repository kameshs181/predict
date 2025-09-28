import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Weather Forecast App", page_icon="🌦️", layout="centered")
st.title("🌍 Intelligent Weather & Forecast System")

# 🔑 Load API Key
try:
    API_KEY = st.secrets["API_KEY"]
except Exception:
    st.error("❌ API key missing. Please add API_KEY in Streamlit Cloud → Settings → Secrets")
    st.stop()

# --- Autocomplete City Search ---
city_query = st.text_input("🔍 Search for a city:", "Chennai")

city, lat, lon = None, None, None

if city_query:
    url_geo = f"http://api.openweathermap.org/geo/1.0/direct?q={city_query}&limit=5&appid={API_KEY}"
    geo_data = requests.get(url_geo).json()

    if geo_data:
        city_options = [f"{c['name']}, {c.get('state','')} {c['country']}" for c in geo_data]
        selected = st.selectbox("Select from matches:", city_options)
        idx = city_options.index(selected)
        lat, lon = geo_data[idx]["lat"], geo_data[idx]["lon"]
        city = geo_data[idx]["name"]
    else:
        st.warning("⚠️ No city found, try another name")

# --- Fetch Weather if City Selected ---
if city and lat and lon:
    # 🌦️ Current Weather
    url_current = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(url_current).json()

    if response.get("cod") == 200:
        temp = response['main']['temp']
        humidity = response['main']['humidity']
        weather = response['weather'][0]['description']
        icon_code = response['weather'][0]['icon']
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
        rain = response.get('rain', {}).get('1h', 0)

        # --- Display Current Weather ---
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(icon_url, width=80)
        with col2:
            st.subheader(f"✅ Current Weather in {city}")
            st.write(f"☁️ {weather.title()}")

        st.metric("🌡️ Temperature (°C)", f"{temp:.1f}")
        st.metric("💧 Humidity (%)", f"{humidity}")
        st.metric("🌧️ Rainfall (last 1h)", f"{rain} mm")

        if rain > 50 or humidity > 85:
            st.error("🚨 Flood Risk Alert!")
        else:
            st.info("✅ No flood risk detected.")

        # --- Interactive Map ---
        st.subheader("🗺️ City Location")
        m = folium.Map(location=[lat, lon], zoom_start=10)

        # 🛰️ Satellite
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri", name="Esri Satellite", overlay=False, control=True
        ).add_to(m)

        # 🏔️ Terrain
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
            attr="Esri", name="Esri Terrain", overlay=False, control=True
        ).add_to(m)

        # Marker with icon popup
        popup_html = f"""
            <div style="text-align:center;">
                <h4>{city}</h4>
                <img src="{icon_url}" width="60"><br>
                🌡️ {temp:.1f} °C<br>
                💧 {humidity}%<br>
                🌧️ {rain} mm<br>
                ☁️ {weather.title()}
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

        # --- 5-Day Forecast ---
        st.subheader("📊 5-Day / 3-Hour Forecast")
        url_forecast = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        forecast = requests.get(url_forecast).json()

        if forecast.get("cod") == "200":
            df = pd.DataFrame([{
                "datetime": item["dt_txt"],
                "temp": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "rain": item.get("rain", {}).get("3h", 0),
                "icon": item["weather"][0]["icon"],
                "condition": item["weather"][0]["description"]
            } for item in forecast["list"]])

            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime")

            st.line_chart(df[["temp"]], height=300, use_container_width=True)
            st.bar_chart(df[["rain"]], height=300, use_container_width=True)

            # Add weather icons inline
            def add_icon(row):
                return f'<img src="http://openweathermap.org/img/wn/{row["icon"]}.png" width="35"> {row["condition"].title()}'

            df_display = df.copy()
            df_display["Weather"] = df_display.apply(add_icon, axis=1)

            st.markdown("### Forecast Table")
            st.write(df_display[["temp", "humidity", "rain", "Weather"]].head(12).to_html(escape=False), unsafe_allow_html=True)

        else:
            st.warning("⚠️ Forecast data not available.")
    else:
        st.error(f"❌ API Error: {response.get('message', 'Unknown error')}")

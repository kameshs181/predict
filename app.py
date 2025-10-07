import streamlit as st
import pandas as pd
import pydeck as pdk
from backend.weather_service import WeatherService
from backend.utils import flood_risk_alert
import hashlib
import os

# -------------------- APP CONFIG --------------------
st.set_page_config(page_title="AI Weather Forecast", layout="wide")

# -------------------- HELPER FUNCTIONS --------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(email, password, users_df):
    hashed = hash_password(password)
    user_row = users_df[users_df['email'] == email]
    if not user_row.empty and user_row.iloc[0]['password'] == hashed:
        return True
    return False

def add_user(email, password, users_df):
    hashed = hash_password(password)
    if email in users_df['email'].values:
        return False  # User already exists
    users_df.loc[len(users_df)] = [email, hashed]
    users_df.to_csv("users.csv", index=False)
    return True

# -------------------- LOAD USERS --------------------
if not os.path.exists("users.csv"):
    users_df = pd.DataFrame(columns=["email", "password"])
    users_df.to_csv("users.csv", index=False)
else:
    users_df = pd.read_csv("users.csv")

# -------------------- LOGIN / SIGNUP --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

auth_choice = st.radio("Login or Sign Up", ["Login", "Sign Up"])

if auth_choice == "Login":
    st.subheader("🔒 Login")
    st.text_input("Email", key="email")
    st.text_input("Password", type="password", key="password")
    if st.button("Sign In"):
        if check_credentials(st.session_state.email, st.session_state.password, users_df):
            st.session_state.logged_in = True
            st.success("✅ Login successful!")
        else:
            st.error("❌ Invalid email or password")
    st.stop() if not st.session_state.logged_in else None

else:  # Sign Up
    st.subheader("📝 Sign Up")
    st.text_input("Email", key="new_email")
    st.text_input("Password", type="password", key="new_password")
    st.text_input("Confirm Password", type="password", key="confirm_password")
    if st.button("Register"):
        if st.session_state.new_password != st.session_state.confirm_password:
            st.error("❌ Passwords do not match")
        else:
            success = add_user(st.session_state.new_email, st.session_state.new_password, users_df)
            if success:
                st.success("✅ Account created! Please log in.")
            else:
                st.error("❌ User already exists")
    st.stop()

# -------------------- MAIN APP --------------------
st.title("🌦️ AI-Driven Weather Forecast & Disaster Alert System")

# -------------------- LOAD API KEY --------------------
try:
    API_KEY = st.secrets["API_KEY"]
except KeyError:
    st.error("❌ Could not load API Key. Add API_KEY in Streamlit Cloud → Secrets.")
    st.stop()

# Initialize Weather Service
weather_service = WeatherService(API_KEY)

# -------------------- USER INPUT --------------------
city = st.text_input("🏙️ Enter City Name", "Chennai")

if st.button("Get Weather Info"):
    with st.spinner("Fetching weather data..."):
        lat, lon, city_name = weather_service.get_coordinates(city)

        if lat and lon:
            current = weather_service.get_current_weather(lat, lon)
            forecast = weather_service.get_forecast(lat, lon)

            if current:
                # -------------------- CURRENT WEATHER --------------------
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader(f"📍 {city_name}")
                    st.metric("🌡️ Temperature (°C)", f"{current['temp']}°C")
                    st.metric("💧 Humidity (%)", f"{current['humidity']}%")
                    st.write(f"**Condition:** {current['weather'].title()}")
                    st.image(f"http://openweathermap.org/img/wn/{current['icon']}@2x.png")

                with col2:
                    st.subheader("🚨 Disaster Alert Panel")
                    flood_alert = flood_risk_alert(current["humidity"], current["rain"])
                    st.write(f"**Flood Risk:** {flood_alert}")

                    wind_speed = current["wind"]
                    if wind_speed > 20:
                        st.warning(f"⚠️ Strong Winds Detected: {wind_speed} m/s")
                    else:
                        st.success(f"✅ Wind Speed Normal: {wind_speed} m/s")

                    temp = current["temp"]
                    if temp > 40:
                        st.warning("🔥 Extreme Heat Alert!")
                    elif temp < 5:
                        st.warning("❄️ Extreme Cold Alert!")
                    else:
                        st.success("🌡️ Temperature Normal")

                # -------------------- INTERACTIVE MAP --------------------
                st.subheader("🗺️ Live Weather Map (Clouds + Wind + Rain)")

                layers = []
                layers.append(pdk.Layer(
                    "TileLayer",
                    data=None,
                    tile_size=256,
                    get_tile_url=f"https://tile.openweathermap.org/map/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
                    opacity=0.5,
                ))
                layers.append(pdk.Layer(
                    "TileLayer",
                    data=None,
                    tile_size=256,
                    get_tile_url=f"https://tile.openweathermap.org/map/wind_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
                    opacity=0.6,
                ))
                layers.append(pdk.Layer(
                    "TileLayer",
                    data=None,
                    tile_size=256,
                    get_tile_url=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
                    opacity=0.7,
                ))
                layers.append(pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame([{"lat": lat, "lon": lon}]),
                    get_position=["lon", "lat"],
                    get_color=[255, 0, 0],
                    get_radius=7000,
                ))

                st.pydeck_chart(pdk.Deck(
                    map_style="mapbox://styles/mapbox/satellite-streets-v12",
                    initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=6, pitch=45),
                    layers=layers,
                ))

                # -------------------- FORECAST --------------------
                if forecast is not None:
                    st.subheader("📈 5-Day Forecast Trend")
                    st.line_chart(forecast.set_index("datetime")[["temp", "humidity", "rain"]])

            else:
                st.error("❌ Could not fetch current weather data. Try another city.")
        else:
            st.error("❌ City not found. Please enter a valid name.")

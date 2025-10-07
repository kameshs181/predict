import streamlit as st
import pandas as pd
import pydeck as pdk
from backend.weather_service import WeatherService
from backend.utils import flood_risk_alert
import hashlib
import os

# -------------------- APP CONFIG --------------------
st.set_page_config(page_title="AI Weather Forecast", layout="wide")

# -------------------- CUSTOM CSS --------------------
st.markdown("""
<style>
body {
    background-color: #f0f2f6;
    font-family: 'Segoe UI', sans-serif;
}
h1, h2, h3 {
    color: #0a2463;
}
.card {
    background-color: #ffffff;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0px 4px 8px rgba(0,0,0,0.1);
}
.metric-text {
    font-size: 1.2rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

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
        return False
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

auth_choice = st.sidebar.radio("Login or Sign Up", ["Login", "Sign Up"])

if auth_choice == "Login":
    st.sidebar.subheader("🔒 Login")
    st.sidebar.text_input("Email", key="email")
    st.sidebar.text_input("Password", type="password", key="password")
    if st.sidebar.button("Sign In"):
        if check_credentials(st.session_state.email, st.session_state.password, users_df):
            st.session_state.logged_in = True
            st.sidebar.success("✅ Login successful!")
        else:
            st.sidebar.error("❌ Invalid email or password")
    st.stop() if not st.session_state.logged_in else None

else:
    st.sidebar.subheader("📝 Sign Up")
    st.sidebar.text_input("Email", key="new_email")
    st.sidebar.text_input("Password", type="password", key="new_password")
    st.sidebar.text_input("Confirm Password", type="password", key="confirm_password")
    if st.sidebar.button("Register"):
        if st.session_state.new_password != st.session_state.confirm_password:
            st.sidebar.error("❌ Passwords do not match")
        else:
            success = add_user(st.session_state.new_email, st.session_state.new_password, users_df)
            if success:
                st.sidebar.success("✅ Account created! Please log in.")
            else:
                st.sidebar.error("❌ User already exists")
    st.stop()

# -------------------- MAIN APP --------------------
st.title("🌦️ AI Weather & Disaster Forecast Dashboard")

# -------------------- LOAD API KEY --------------------
try:
    API_KEY = st.secrets["API_KEY"]
except KeyError:
    st.error("❌ Could not load API Key. Add API_KEY in Streamlit Cloud → Secrets.")
    st.stop()

weather_service = WeatherService(API_KEY)

# -------------------- CITY INPUT --------------------
city = st.sidebar.text_input("🏙️ Enter City Name", "Chennai")

if st.sidebar.button("Get Weather Info"):
    with st.spinner("Fetching weather data..."):
        lat, lon, city_name = weather_service.get_coordinates(city)

        if lat and lon:
            current = weather_service.get_current_weather(lat, lon)
            forecast = weather_service.get_forecast(lat, lon)

            if current:
                # -------------------- METRICS CARDS --------------------
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown('<div class="card"><h4>🌡️ Temperature</h4><p class="metric-text">{:.1f}°C</p></div>'.format(current['temp']), unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="card"><h4>💧 Humidity</h4><p class="metric-text">{:.0f}%</p></div>'.format(current['humidity']), unsafe_allow_html=True)
                with col3:
                    st.markdown('<div class="card"><h4>🌧️ Rain</h4><p class="metric-text">{:.1f} mm</p></div>'.format(current.get('rain', 0)), unsafe_allow_html=True)
                with col4:
                    st.markdown('<div class="card"><h4>💨 Wind Speed</h4><p class="metric-text">{:.1f} m/s</p></div>'.format(current.get('wind', 0)), unsafe_allow_html=True)

                # -------------------- DISASTER ALERT --------------------
                st.subheader("🚨 Disaster Alert Panel")
                flood_alert = flood_risk_alert(current["humidity"], current["rain"])
                if "High" in flood_alert:
                    st.error(flood_alert)
                elif "Moderate" in flood_alert:
                    st.warning(flood_alert)
                else:
                    st.success(flood_alert)

                if current.get("wind", 0) > 20:
                    st.warning("⚠️ Strong Winds Detected")
                temp = current["temp"]
                if temp > 40:
                    st.warning("🔥 Extreme Heat Alert!")
                elif temp < 5:
                    st.warning("❄️ Extreme Cold Alert!")

                # -------------------- MAP --------------------
                st.subheader("🗺️ Live Weather Map")
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

                # -------------------- FORECAST CHART --------------------
                if forecast is not None:
                    st.subheader("📈 5-Day Forecast")
                    st.line_chart(forecast.set_index("datetime")[["temp", "humidity", "rain"]])

            else:
                st.error("❌ Could not fetch current weather data.")
        else:
            st.error("❌ City not found.")

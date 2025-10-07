import streamlit as st
import pandas as pd
import pydeck as pdk
from backend.weather_service import WeatherService
from backend.utils import flood_risk_alert
import hashlib
import os
import csv

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="🌦️ AI Weather Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- CUSTOM CSS --------------------
st.markdown("""
<style>
/* Background gradient */
body {
    background: linear-gradient(135deg, #74ebd5 0%, #ACB6E5 100%);
    font-family: 'Segoe UI', sans-serif;
}

/* Card style */
.card {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 8px 16px rgba(0,0,0,0.2);
    margin-bottom: 20px;
}

/* Metric text */
.metric-text { font-size: 1.4rem; font-weight: bold; color:#0a2463; }

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #0a2463;
    color: white;
}

/* Buttons */
.stButton>button {
    background-color: #0a2463;
    color: white;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
}

/* Headers */
h1, h2, h3 { color: #0a2463; }
</style>
""", unsafe_allow_html=True)

# -------------------- HELPER FUNCTIONS --------------------
def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()
def check_credentials(email, password, users_df):
    hashed = hash_password(password)
    user_row = users_df[users_df['email'] == email]
    return not user_row.empty and user_row.iloc[0]['password'] == hashed
def add_user(email, password, users_df):
    hashed = hash_password(password)
    if email in users_df['email'].values: return False
    users_df.loc[len(users_df)] = [email, hashed]
    users_df.to_csv("users.csv", index=False)
    return True

# -------------------- LOAD USERS SAFELY --------------------
users_file = "users.csv"
if not os.path.exists(users_file) or os.stat(users_file).st_size == 0:
    with open(users_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["email", "password"])

try:
    users_df = pd.read_csv(users_file)
except pd.errors.EmptyDataError:
    users_df = pd.DataFrame(columns=["email", "password"])
    users_df.to_csv(users_file, index=False)

# -------------------- NAVIGATION --------------------
menu = ["🏠 Home", "🔑 Sign Up / Login", "☀️ Current Weather", "🗺️ Map", "📈 Forecast", "ℹ️ About"]
choice = st.sidebar.radio("Navigate", menu)

# -------------------- HOME --------------------
if choice == "🏠 Home":
    st.markdown("<h1 style='text-align:center'>🌦️ AI Weather & Disaster Forecast</h1>", unsafe_allow_html=True)
    st.image("https://i.ibb.co/2kKjv6F/logo.png", width=200)
    st.markdown("""
    <div class="card">
    <h3>Welcome!</h3>
    <p>This AI-Driven Weather Forecast & Disaster Alert System provides:</p>
    <ul>
    <li>Real-time weather metrics</li>
    <li>Disaster risk alerts (floods, rainfall)</li>
    <li>Interactive maps with cloud, wind & precipitation layers</li>
    <li>5-day weather forecasts</li>
    </ul>
    <p>Use the sidebar to navigate through the app.</p>
    </div>
    """, unsafe_allow_html=True)

# -------------------- LOGIN / SIGN UP --------------------
elif choice == "🔑 Sign Up / Login":
    st.subheader("Authentication")
    auth_choice = st.radio("Choose Action", ["Login", "Sign Up"])
    
    if auth_choice == "Login":
        st.text_input("Email", key="email")
        st.text_input("Password", type="password", key="password")
        if st.button("Sign In"):
            if check_credentials(st.session_state.email, st.session_state.password, users_df):
                st.success("✅ Login successful!")
                st.session_state.logged_in = True
            else: st.error("❌ Invalid email or password")
    else:
        st.text_input("Email", key="new_email")
        st.text_input("Password", type="password", key="new_password")
        st.text_input("Confirm Password", type="password", key="confirm_password")
        if st.button("Register"):
            if st.session_state.new_password != st.session_state.confirm_password:
                st.error("❌ Passwords do not match")
            else:
                success = add_user(st.session_state.new_email, st.session_state.new_password, users_df)
                if success: st.success("✅ Account created! Please log in.")
                else: st.error("❌ User already exists")

# -------------------- WEATHER DASHBOARD --------------------
else:
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("⚠️ Please log in to access this section.")
        st.stop()

    try:
        API_KEY = st.secrets["API_KEY"]
    except KeyError:
        st.error("❌ Add API_KEY in Streamlit Secrets.")
        st.stop()

    weather_service = WeatherService(API_KEY)
    city = st.sidebar.text_input("Enter City", "Chennai")

    if city:
        lat, lon, city_name = weather_service.get_coordinates(city)
        current = weather_service.get_current_weather(lat, lon) if lat else None
        forecast = weather_service.get_forecast(lat, lon) if lat else None

        if current:
            if choice == "☀️ Current Weather":
                st.markdown("<h2>Current Weather Metrics</h2>", unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.markdown(f'<div class="card"><h4>🌡️ Temperature</h4><p class="metric-text">{current["temp"]}°C</p></div>', unsafe_allow_html=True)
                with col2: st.markdown(f'<div class="card"><h4>💧 Humidity</h4><p class="metric-text">{current["humidity"]}%</p></div>', unsafe_allow_html=True)
                with col3: st.markdown(f'<div class="card"><h4>🌧️ Rain</h4><p class="metric-text">{current.get("rain",0)} mm</p></div>', unsafe_allow_html=True)
                with col4: st.markdown(f'<div class="card"><h4>💨 Wind</h4><p class="metric-text">{current.get("wind",0)} m/s</p></div>', unsafe_allow_html=True)

                st.subheader("🚨 Disaster Alerts")
                flood_alert = flood_risk_alert(current["humidity"], current["rain"])
                if "High" in flood_alert: st.error(flood_alert)
                elif "Moderate" in flood_alert: st.warning(flood_alert)
                else: st.success(flood_alert)

            elif choice == "🗺️ Map":
                st.subheader("Interactive Weather Map")
                layers = [
                    pdk.Layer("TileLayer", data=None, tile_size=256,
                              get_tile_url=f"https://tile.openweathermap.org/map/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}", opacity=0.5),
                    pdk.Layer("TileLayer", data=None, tile_size=256,
                              get_tile_url=f"https://tile.openweathermap.org/map/wind_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}", opacity=0.6),
                    pdk.Layer("TileLayer", data=None, tile_size=256,
                              get_tile_url=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}", opacity=0.7),
                    pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{"lat":lat,"lon":lon}]),
                              get_position=["lon","lat"], get_color=[255,0,0], get_radius=7000)
                ]
                st.pydeck_chart(pdk.Deck(
                    map_style="mapbox://styles/mapbox/satellite-streets-v12",
                    initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=6, pitch=45),
                    layers=layers
                ))

            elif choice == "📈 Forecast":
                st.subheader("5-Day Forecast")
                if forecast is not None:
                    st.line_chart(forecast.set_index("datetime")[["temp","humidity","rain"]])

        else:
            st.error("❌ City not found.")

# -------------------- ABOUT PAGE --------------------
if choice == "ℹ️ About":
    st.subheader("About This Project")
    st.markdown("""
    Developed by [Your Name].  
    AI-Driven Weather Forecast & Disaster Alert System using OpenWeatherMap API and Streamlit.  
    Professional UI/UX design with interactive charts, maps, and disaster alerts.
    """)

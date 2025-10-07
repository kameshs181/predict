import streamlit as st
import pandas as pd
import pydeck as pdk
from streamlit_lottie import st_lottie
import hashlib, os, csv, requests
from backend.weather_service import WeatherService
from backend.utils import flood_risk_alert
from streamlit_autorefresh import st_autorefresh
from pydeck import AmbientLight, LightingEffect

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="🌦️ AI Weather Dashboard",
    page_icon="🌍",
    layout="wide"
)

# -------------------- CSS --------------------
st.markdown("""
<style>
body {font-family:'Segoe UI', sans-serif; transition: background 1s ease;}
.card {background-color:#ffffff; padding:25px; border-radius:15px; box-shadow:0px 10px 20px rgba(0,0,0,0.2); margin-bottom:30px; transition: transform 0.3s;}
.card:hover {transform: translateY(-5px);}
.metric-text {font-size:1.6rem; font-weight:bold; color:#0a2463;}
h1,h2,h3{color:#0a2463;}
.stButton>button{background-color:#0a2463; color:white; border-radius:10px; padding:10px 20px; font-weight:bold;}
.section {opacity:0; transform:translateY(50px); transition: all 1s ease; margin-bottom:50px;}
.section.visible {opacity:1; transform:translateY(0);}
</style>
""", unsafe_allow_html=True)

# -------------------- HELPERS --------------------
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
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

# -------------------- USERS --------------------
users_file = "users.csv"
if not os.path.exists(users_file) or os.stat(users_file).st_size == 0:
    with open(users_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["email", "password"])
try:
    users_df = pd.read_csv(users_file)
except pd.errors.EmptyDataError:
    users_df = pd.DataFrame(columns=["email","password"])
    users_df.to_csv(users_file,index=False)

# -------------------- HERO --------------------
st.markdown("<div class='section visible' style='background-image:url(https://images.unsplash.com/photo-1501973801540-537f08ccae7f?auto=format&fit=crop&w=1650&q=80); background-size:cover; border-radius:15px; padding:80px; color:white; text-align:center;'><h1>🌦️ AI Weather & Disaster Forecast</h1><p style='font-size:1.3rem;'>Real-time weather, forecasts, and disaster alerts</p></div>",unsafe_allow_html=True)

# -------------------- LOGIN / SIGN UP --------------------
st.markdown("<div class='section visible'><h2>🔑 Login / Sign Up</h2></div>",unsafe_allow_html=True)
auth_choice = st.radio("Choose Action", ["Login", "Sign Up"], horizontal=True)
if auth_choice == "Login":
    st.text_input("Email", key="email")
    st.text_input("Password", type="password", key="password")
    if st.button("Sign In"):
        if check_credentials(st.session_state.email, st.session_state.password, users_df):
            st.success("✅ Login successful!")
            st.session_state.logged_in=True
        else:
            st.error("❌ Invalid email or password")
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
if "logged_in" in st.session_state and st.session_state.logged_in:
    try: API_KEY = st.secrets["API_KEY"]
    except KeyError:
        st.error("❌ Add API_KEY in Streamlit Secrets.")
        st.stop()

    weather_service = WeatherService(API_KEY)
    city = st.text_input("Enter City","Chennai",key="city_input")

    # Auto-refresh every 60 seconds
    st_autorefresh(interval=60*1000, key="weather_refresh")

    if city:
        lat, lon, city_name = weather_service.get_coordinates(city)
        current = weather_service.get_current_weather(lat, lon) if lat else None
        forecast = weather_service.get_forecast(lat, lon) if lat else None

        if current:
            # -------------------- BACKGROUND & LOTTIE --------------------
            weather_main = current.get("weather","Clear").lower()
            if "rain" in weather_main:
                st.markdown('<body style="background: linear-gradient(120deg,#74c0fc,#4dabf7);">', unsafe_allow_html=True)
                lottie_weather = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_jh8c1c6f.json")
            elif "cloud" in weather_main:
                st.markdown('<body style="background: linear-gradient(120deg,#d3d3d3,#868e96);">', unsafe_allow_html=True)
                lottie_weather = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_XM2oVv.json")
            elif "storm" in weather_main:
                st.markdown('<body style="background: linear-gradient(120deg,#6c757d,#495057);">', unsafe_allow_html=True)
                lottie_weather = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_svy4ivvy.json")
            else:
                st.markdown('<body style="background: linear-gradient(120deg,#ffd166,#ff6b6b);">', unsafe_allow_html=True)
                lottie_weather = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_iwmd6pyr.json")

            # -------------------- CURRENT WEATHER --------------------
            st.markdown("<div class='section visible'><h2>☀️ Current Weather</h2></div>",unsafe_allow_html=True)
            col_lottie, col1, col2, col3, col4 = st.columns([2,1,1,1,1])
            with col_lottie:
                st_lottie(lottie_weather, height=200, key="weather_lottie")

            # Metrics
            col1.metric("🌡️ Temp", f"{int(current['temp'])}°C")
            col2.metric("💧 Humidity", f"{current['humidity']}%")
            col3.metric("🌧️ Rain", f"{current.get('rain',0)} mm")
            col4.metric("💨 Wind", f"{current.get('wind',0)} m/s")

            # -------------------- DISASTER ALERTS --------------------
            st.markdown("<div class='section visible'><h2>🚨 Disaster Alerts</h2></div>",unsafe_allow_html=True)
            flood_alert = flood_risk_alert(current["humidity"], current["rain"])
            if "High" in flood_alert: st.error(flood_alert)
            elif "Moderate" in flood_alert: st.warning(flood_alert)
            else: st.success(flood_alert)

            # -------------------- HIGH-QUALITY INTERACTIVE MAP --------------------
            st.markdown("<div class='section visible'><h2>🗺️ Interactive Map</h2></div>",unsafe_allow_html=True)

            layers = [
                pdk.Layer(
                    "TileLayer",
                    data=None,
                    tile_size=256,
                    get_tile_url=f"https://tile.openweathermap.org/map/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
                    opacity=0.5
                ),
                pdk.Layer(
                    "TileLayer",
                    data=None,
                    tile_size=256,
                    get_tile_url=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
                    opacity=0.6
                ),
                pdk.Layer(
                    "TileLayer",
                    data=None,
                    tile_size=256,
                    get_tile_url=f"https://tile.openweathermap.org/map/wind_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}",
                    opacity=0.6
                ),
                # City marker
                pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame([{"lat": lat, "lon": lon}]),
                    get_position=["lon", "lat"],
                    get_color=[255, 0, 0],
                    get_radius=20000,
                    pickable=True,
                    auto_highlight=True
                ),
                # 3D temperature column
                pdk.Layer(
                    "ColumnLayer",
                    data=pd.DataFrame([{"lat": lat, "lon": lon, "temp": current["temp"]}]),
                    get_position=["lon", "lat"],
                    get_elevation="temp*500",
                    elevation_scale=50,
                    radius=20000,
                    get_fill_color=[255,100,100],
                    pickable=True,
                    auto_highlight=True
                )
            ]

            ambient_light = AmbientLight(color=[255,255,255], intensity=0.8)
            deck = pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=6, pitch=45),
                layers=layers,
                effects=[LightingEffect(ambient_light)],
                tooltip={"text": "City: {}\nTemp: {}°C".format(city_name, int(current['temp']))}
            )
            st.pydeck_chart(deck)

            # -------------------- 5-DAY FORECAST --------------------
            st.markdown("<div class='section visible'><h2>📈 5-Day Forecast</h2></div>",unsafe_allow_html=True)
            if forecast is not None:
                st.line_chart(forecast.set_index("datetime")[["temp","humidity","rain"]])

# -------------------- ABOUT --------------------
st.markdown("<div class='section visible'><h2>ℹ️ About This Project</h2></div>",unsafe_allow_html=True)
st.markdown("""
Developed by [Your Name].  
Professional AI Weather Forecast & Disaster Alert Dashboard with **high-quality map, 3D markers, slide-in UI/UX, live metrics, Lottie animations, and disaster alerts**.
""")

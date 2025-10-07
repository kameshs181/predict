import requests
import pandas as pd

class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_coordinates(self, city):
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={self.api_key}"
        res = requests.get(url).json()
        if res:
            return res[0]["lat"], res[0]["lon"], res[0]["name"]
        return None, None, None

    def get_current_weather(self, lat, lon):
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
        res = requests.get(url).json()
        if res.get("cod") == 200:
            return {
                "temp": res["main"]["temp"],
                "humidity": res["main"]["humidity"],
                "weather": res["weather"][0]["description"],
                "icon": res["weather"][0]["icon"],
                "rain": res.get("rain", {}).get("1h", 0),
                "wind": res.get("wind", {}).get("speed", 0)
            }
        return None

    def get_forecast(self, lat, lon):
        url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
        res = requests.get(url).json()
        if res.get("cod") == "200":
            data = [{
                "datetime": item["dt_txt"],
                "temp": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "rain": item.get("rain", {}).get("3h", 0),
                "icon": item["weather"][0]["icon"],
                "condition": item["weather"][0]["description"]
            } for item in res["list"]]
            return pd.DataFrame(data)
        return None

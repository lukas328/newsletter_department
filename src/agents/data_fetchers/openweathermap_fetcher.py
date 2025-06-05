# newsletter_project/src/agents/data_fetchers/openweathermap_fetcher.py
"""Fetcher for weather data using OpenWeatherMap API."""

import requests
import logging
from typing import List

from src.agents.data_fetchers.base_fetcher import BaseDataFetcher
from src.models.data_models import WeatherInfo
from src.utils.config_loader import get_api_key

logger = logging.getLogger(__name__)

class OpenWeatherMapFetcher(BaseDataFetcher):
    """Fetches 5 day weather forecast for a given city."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, city: str = "Zurich", api_key_name: str = "OPENWEATHER_API_KEY", units: str = "metric"):
        source_name = f"OpenWeatherMap {city}"
        super().__init__(source_name=source_name)
        self.city = city
        self.api_key = get_api_key(api_key_name)
        self.units = units

    def fetch_data(self) -> List[WeatherInfo]:
        params = {
            "q": self.city,
            "appid": self.api_key,
            "units": self.units,
        }
        try:
            logger.info(f"Fetching weather for {self.city} from OpenWeatherMap")
            resp = requests.get(self.BASE_URL, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return []

        forecast_list = data.get("list", [])
        if not forecast_list:
            logger.warning("No forecast data returned from OpenWeatherMap")
            return []

        daily_data = {}
        for entry in forecast_list:
            ts = entry.get("dt_txt")
            if not ts:
                continue
            day = ts.split(" ")[0]
            if day not in daily_data:
                daily_data[day] = entry
            if len(daily_data) == 5:
                break

        weather_infos: List[WeatherInfo] = []
        for day, entry in daily_data.items():
            main = entry.get("main", {})
            weather = entry.get("weather", [{}])[0]
            wind = entry.get("wind", {})
            temp = main.get("temp")
            condition = weather.get("description", "")
            humidity = main.get("humidity")
            wind_speed = wind.get("speed")
            icon = weather.get("icon")
            icon_url = f"https://openweathermap.org/img/wn/{icon}@2x.png" if icon else None
            snippet = f"{day}: {temp}°C, {condition}"
            info = WeatherInfo(
                location=self.city,
                temperature_celsius=temp,
                condition=condition,
                humidity_percent=humidity,
                wind_speed_kmh=wind_speed,
                icon_url=icon_url,
                forecast_snippet=snippet,
            )
            weather_infos.append(info)
        logger.info(f"Fetched {len(weather_infos)} weather entries from OpenWeatherMap")
        return weather_infos

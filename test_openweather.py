from unittest.mock import patch
import os
from src.agents.data_fetchers.openweathermap_fetcher import OpenWeatherMapFetcher
from src.models.data_models import WeatherInfo

sample_response = {
    "list": [
        {"dt_txt": "2025-06-01 12:00:00", "main": {"temp": 20, "humidity": 50}, "weather": [{"description": "sunny", "icon": "01d"}], "wind": {"speed": 5}},
        {"dt_txt": "2025-06-02 12:00:00", "main": {"temp": 21, "humidity": 55}, "weather": [{"description": "cloudy", "icon": "02d"}], "wind": {"speed": 4}},
        {"dt_txt": "2025-06-03 12:00:00", "main": {"temp": 22, "humidity": 60}, "weather": [{"description": "rain", "icon": "09d"}], "wind": {"speed": 3}},
        {"dt_txt": "2025-06-04 12:00:00", "main": {"temp": 19, "humidity": 65}, "weather": [{"description": "sunny", "icon": "01d"}], "wind": {"speed": 2}},
        {"dt_txt": "2025-06-05 12:00:00", "main": {"temp": 18, "humidity": 70}, "weather": [{"description": "rain", "icon": "09d"}], "wind": {"speed": 6}},
    ]
}

@patch("requests.get")
def test_fetch_weather(mock_get):
    mock_get.return_value.json.return_value = sample_response
    mock_get.return_value.raise_for_status.return_value = None
    os.environ["OPENWEATHER_API_KEY"] = "dummy"
    fetcher = OpenWeatherMapFetcher(city="Zurich", api_key_name="OPENWEATHER_API_KEY")
    data = fetcher.fetch_data()
    assert len(data) == 5
    assert all(isinstance(d, WeatherInfo) for d in data)

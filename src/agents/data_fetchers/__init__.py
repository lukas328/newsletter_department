from .newsapi_fetcher import NewsAPIFetcher
her import BaseDataFetcher

from .europeana_fetcher import EuropeanaFetcher
from .openweathermap_fetcher import OpenWeatherMapFetcher
from .google_calendar_fetcher import GoogleCalendarFetcher
from .base_fetcher import BaseDataFetcher

__all__ = ["NewsAPIFetcher", "OpenWeatherMapFetcher","EuropeanaFetcher","GoogleCalendarFetcher","BaseDataFetcher",]

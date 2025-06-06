"""Convenience imports for the data fetcher package."""

from .base_fetcher import BaseDataFetcher
from .newsapi_fetcher import NewsAPIFetcher
from .openweathermap_fetcher import OpenWeatherMapFetcher
from .google_calendar_fetcher import GoogleCalendarFetcher
from .birthday_sheet_fetcher import BirthdaySheetFetcher
from .todoist_fetcher import TodoistFetcher
from .europeana_fetcher import EuropeanaFetcher
from .zenquotes_fetcher import ZenQuotesFetcher
from .eventbrite_fetcher import EventbriteFetcher
from .openai_web_event_fetcher import OpenAIWebEventFetcher
from .openai_link_event_fetcher import OpenAILinkEventFetcher

__all__ = [
    "BaseDataFetcher",
    "NewsAPIFetcher",
    "OpenWeatherMapFetcher",
    "GoogleCalendarFetcher",
    "BirthdaySheetFetcher",
    "TodoistFetcher",
    "EuropeanaFetcher",
    "ZenQuotesFetcher",
    "EventbriteFetcher",
    "OpenAIWebEventFetcher",
    "OpenAILinkEventFetcher",
]

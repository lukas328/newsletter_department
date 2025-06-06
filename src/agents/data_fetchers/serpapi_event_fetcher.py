import logging
from typing import List, Optional, Dict, Any
import requests

from .base_fetcher import BaseDataFetcher
from src.models.data_models import Event
from src.utils.config_loader import get_api_key

logger = logging.getLogger(__name__)


class SerpApiEventFetcher(BaseDataFetcher):
    """Fetches event results from Google search via SerpAPI."""

    API_URL = "https://serpapi.com/search.json"

    def __init__(self, query: str = "events in Zurich", location: Optional[str] = None, api_key_env: str = "SERPAPI_API_KEY"):
        super().__init__(source_name="Google Events")
        self.query = query
        self.location = location
        self.api_key = get_api_key(api_key_env)

    def fetch_data(self) -> List[Event]:
        params: Dict[str, Any] = {
            "engine": "google",
            "q": self.query,
            "api_key": self.api_key,
            "hl": "en",
        }
        if self.location:
            params["location"] = self.location
        try:
            logger.info("Fetching events from SerpAPI with query '%s'", self.query)
            resp = requests.get(self.API_URL, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("Error fetching events from SerpAPI: %s", exc, exc_info=True)
            return []

        events = []
        for item in data.get("events_results", []):
            try:
                start = item.get("date", {}).get("start_date")
                end = item.get("date", {}).get("end_date")
                evt = Event(
                    summary=item.get("title"),
                    start_time=start,
                    end_time=end,
                    location=item.get("address"),
                    description=item.get("snippet"),
                    url=item.get("link"),
                    source="Google Events",
                )
                events.append(evt)
            except Exception as e_item:
                logger.warning("Skipping SerpAPI event due to error: %s", e_item)
        logger.info("Fetched %d events from SerpAPI", len(events))
        return events

import logging
from typing import List, Optional, Dict, Any
import requests
from datetime import datetime

from .base_fetcher import BaseDataFetcher
from src.models.data_models import Event
from src.utils.config_loader import get_api_key

logger = logging.getLogger(__name__)

class EventbriteFetcher(BaseDataFetcher):
    """Fetches events from the Eventbrite API"""

    BASE_URL = "https://www.eventbriteapi.com/v3/events/search/"

    def __init__(self,
                 token_env_var: str = "EVENTBRITE_OAUTH_TOKEN",
                 query: Optional[str] = None,
                 categories: Optional[str] = None,
                 location_address: str = "Zurich",
                 within: str = "10km",
                 sort_by: str = "date"):
        super().__init__(source_name="Eventbrite")
        self.token = get_api_key(token_env_var)
        self.query = query
        self.categories = categories
        self.location_address = location_address
        self.within = within
        self.sort_by = sort_by

    def fetch_data(self) -> List[Event]:
        params: Dict[str, Any] = {
            "location.address": self.location_address,
            "expand": "venue",
            "within": self.within,
            "sort_by": self.sort_by,
        }
        if self.query:
            params["q"] = self.query
        if self.categories:
            params["categories"] = self.categories

        headers = {"Authorization": f"Bearer {self.token}"}
        logger.info(f"Frage Eventbrite API ab: {params}")
        events: List[Event] = []
        try:
            response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=20)
            logger.debug(f"Eventbrite Status Code: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            for item in data.get("events", []):
                try:
                    venue = item.get("venue", {})
                    start = item.get("start", {}).get("utc")
                    end = item.get("end", {}).get("utc")
                    event = Event(
                        summary=item.get("name", {}).get("text"),
                        start_time=start,
                        end_time=end,
                        location=venue.get("address", {}).get("localized_address_display"),
                        description=item.get("description", {}).get("text"),
                        url=item.get("url"),
                        source="Eventbrite",
                    )
                    events.append(event)
                except Exception as e:
                    logger.warning(f"Überspringe Event aufgrund Fehler: {e}", exc_info=False)
        except Exception as e:
            logger.error(f"Fehler beim Abruf von Eventbrite: {e}", exc_info=True)
        logger.info(f"{len(events)} Events von Eventbrite erhalten")
        return events
